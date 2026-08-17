import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

from common import ensure_dir, read_document_paragraphs, write_json
from importlib.util import module_from_spec, spec_from_file_location


def load_opinion_helpers():
    script = Path(__file__).with_name("14_build_opinion_database.py")
    spec = spec_from_file_location("opinion_db_builder", script)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opinion_helpers = load_opinion_helpers()


REPORT_EXTENSIONS = {".docx", ".pdf"}
SKIP_PREFIXES = ("~$",)
REPORT_HINTS = ["安评", "安全", "评估", "评价", "报告", "预评估"]
ADVICE_HINTS = ["意见", "回复", "建议", "审查", "专家"]


def safe_read(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        return read_pdf_sampled_paragraphs(path)
    try:
        return read_document_paragraphs(path)
    except Exception:
        try:
            return opinion_helpers.safe_read_paragraphs(path)
        except Exception as exc:
            print(f"skip reading {path}: {exc}")
            return []


def read_pdf_sampled_paragraphs(path, first_pages=12, last_pages=18):
    import pdfplumber

    rows = []
    with pdfplumber.open(str(path)) as pdf:
        page_count = len(pdf.pages)
        indexes = set(range(min(first_pages, page_count)))
        indexes.update(range(max(0, page_count - last_pages), page_count))
        for page_idx in sorted(indexes):
            text = pdf.pages[page_idx].extract_text() or ""
            text = text.replace("\r", "\n")
            for para in re.split(r"\n+", text):
                para = para.strip()
                if para:
                    rows.append({"page": page_idx + 1, "text": para})
    return rows


def document_text(path, max_chars=200000):
    paragraphs = safe_read(path)
    text = "\n".join(item.get("text", "") for item in paragraphs if item.get("text"))
    return text[:max_chars], paragraphs


def score_report_file(path):
    name = path.name
    score = path.stat().st_size / 1024 / 1024
    for hint in REPORT_HINTS:
        if hint in name:
            score += 20
    for hint in ADVICE_HINTS:
        if hint in name:
            score -= 6
    if "ppt" in path.suffix.lower():
        score -= 100
    return score


def choose_report_file(files):
    candidates = [path for path in files if path.suffix.lower() in REPORT_EXTENSIONS and not path.name.startswith(SKIP_PREFIXES)]
    if not candidates:
        return None
    return max(candidates, key=score_report_file)


def case_dirs(root):
    root = Path(root)
    result = []
    for folder in root.rglob("*"):
        if not folder.is_dir():
            continue
        files = [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in REPORT_EXTENSIONS]
        if files:
            result.append(folder)
    return sorted(result)


def case_sources(root):
    root = Path(root)
    sources = []
    direct_files = [path for path in root.iterdir() if path.is_file() and path.suffix.lower() in REPORT_EXTENSIONS and not path.name.startswith(SKIP_PREFIXES)]
    for path in direct_files:
        sources.append({"case_name": path.stem, "category": None, "case_folder": root, "files": [path]})

    for category_dir in sorted([path for path in root.iterdir() if path.is_dir()]):
        category = category_dir.name
        category_direct_files = [path for path in category_dir.iterdir() if path.is_file() and path.suffix.lower() in REPORT_EXTENSIONS and not path.name.startswith(SKIP_PREFIXES)]
        for path in category_direct_files:
            sources.append({"case_name": path.stem, "category": category, "case_folder": category_dir, "files": [path]})

        for child in sorted([path for path in category_dir.iterdir() if path.is_dir()]):
            files = [path for path in child.rglob("*") if path.is_file() and path.suffix.lower() in REPORT_EXTENSIONS and not path.name.startswith(SKIP_PREFIXES)]
            if files:
                sources.append({"case_name": child.name, "category": category, "case_folder": child, "files": files})
    return sources


def nearest_category(root, folder):
    try:
        rel = folder.relative_to(root)
    except ValueError:
        return None
    return rel.parts[0] if rel.parts else None


def first_match(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return m.group(1).strip(" ：:，,；;。 ")
    return None


def contains_any(text, words):
    return any(word in text for word in words)


def extract_number(value):
    if value is None:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(m.group()) if m else None


def infer_work_types(text, category=""):
    mapping = {
        "基坑": ["基坑", "开挖", "支护", "围护"],
        "道路桥梁": ["道路", "桥梁", "上跨", "下穿", "高架", "匝道"],
        "管线": ["管线", "顶管", "盾构", "牵引管", "污水", "雨水", "电力", "燃气"],
        "高填深挖": ["高填", "深挖", "边坡", "填方", "挖方"],
        "桩基": ["桩基", "钻孔灌注桩", "管桩", "试桩"],
        "降水": ["降水", "井点", "承压水", "地下水"],
    }
    types = set()
    for label, words in mapping.items():
        if label in category or contains_any(text, words):
            types.add(label)
    return sorted(types)


def extract_keywords(text):
    words = [
        "控制保护区",
        "特别保护区",
        "基坑",
        "支护",
        "围护",
        "地下连续墙",
        "钻孔灌注桩",
        "隔离桩",
        "降水",
        "承压水",
        "地下水位",
        "监测",
        "保护性监测",
        "初始状态调查",
        "现状调查",
        "专项保护方案",
        "应急预案",
        "专家评审",
        "严禁堆载",
        "回填",
        "停止降水",
        "减震",
        "隔振",
        "振动",
        "上跨",
        "下穿",
        "邻近",
        "侧穿",
        "地铁",
        "轨道交通",
        "隧道",
        "区间",
        "车站",
    ]
    return sorted({word for word in words if word in text})


def extract_features(text, category="", case_name=""):
    pit_depth = first_match([r"开挖深度(?:约|为)?\s*([0-9.]+m)", r"挖深(?:约|为)?\s*([0-9.]+m)", r"基坑深度(?:约|为)?\s*([0-9.]+m)"], text)
    clearance = first_match([r"最小净距(?:约|为)?\s*([0-9.]+m)", r"最近距离(?:约|为)?\s*([0-9.]+m)", r"距离[^。；;\n]{0,30}?(?:约|为)\s*([0-9.]+m)"], text)
    metro_line = first_match([r"(?:地铁|轨道交通)\s*([0-9A-Za-zS]+号线)", r"([0-9A-Za-zS]+号线)"], text)
    relation = first_match([r"(上跨|下穿|侧穿|邻近|临近|穿越|并行|平行)"], text)
    support = first_match([r"(地下连续墙|钻孔灌注桩|咬合桩|钢板桩|放坡|排桩|隔离桩|三轴搅拌桩)"], text)
    dewatering = first_match([r"(轻型井点降水|管井降水|深井降水|疏干降水|坑内降水|承压水降压|降水)"], text)
    metro_asset = first_match([r"(区间隧道|盾构区间|隧道|车站|高架|桥梁|车辆段|停车场)"], text)
    return {
        "case_name": case_name,
        "category": category,
        "work_types": infer_work_types(text, category),
        "metro_line": metro_line,
        "metro_asset": metro_asset,
        "relation": relation,
        "support_method": support,
        "dewatering_type": dewatering,
        "pit_depth_m": extract_number(pit_depth),
        "minimum_clearance_m": extract_number(clearance),
        "in_control_protection_zone": "控制保护区" in text,
        "in_special_protection_zone": "特别保护区" in text,
        "monitoring_required": contains_any(text, ["监测", "保护性监测", "监控量测"]),
        "keywords": extract_keywords(text),
    }


def extract_advices_from_document(path):
    paragraphs = safe_read(path)
    advices = []
    for section in opinion_helpers.extract_opinion_sections(paragraphs, section="auto"):
        for item in opinion_helpers.split_numbered_opinions(section["paragraphs"]):
            advices.append(
                {
                    "section": section["section"],
                    "section_title": section["title"],
                    "number": item["number"],
                    "text": item["text"],
                    "source_file": str(path),
                }
            )
    if not advices:
        advices.extend(extract_fallback_advices(paragraphs, path))
    return advices


def extract_fallback_advices(paragraphs, path):
    texts = [item.get("text", "").strip() for item in paragraphs if item.get("text", "").strip()]
    starts = [idx for idx, text in enumerate(texts) if "建议" in text and len(text) < 80]
    if not starts:
        starts = [idx for idx, text in enumerate(texts) if "建议" in text]
    if not starts:
        return []
    start = starts[-1]
    tail = texts[start + 1 : start + 80]
    opinions = opinion_helpers.split_numbered_opinions(tail)
    return [
        {
            "section": "建议",
            "section_title": texts[start],
            "number": item["number"],
            "text": item["text"],
            "source_file": str(path),
        }
        for item in opinions
    ]


def numbered_advice_candidates(paragraphs, path):
    texts = [item.get("text", "").strip() for item in paragraphs if item.get("text", "").strip()]
    start_indexes = [
        idx
        for idx, text in enumerate(texts)
        if (
            re.search(r"(评估建议|审查意见|专家意见|审核意见|结论与建议|评价与建议|分析结论和建议)$", text)
            or re.match(r"^\d+(?:\.\d+)*\.?\s*建议$", text)
        )
    ]
    if not start_indexes:
        return []
    scan_indexes = set()
    for start in start_indexes:
        for idx in range(start + 1, min(len(texts), start + 80)):
            scan_indexes.add(idx)
    candidates = []
    advice_words = [
        "地铁",
        "轨道",
        "隧道",
        "区间",
        "车站",
        "基坑",
        "管线",
        "沟槽",
        "降水",
        "回填",
        "监测",
        "保护",
        "应急",
        "堆载",
        "病害",
        "专家",
        "审查",
        "施工",
    ]
    for idx, text in enumerate(texts):
        if idx not in scan_indexes:
            continue
        m = re.match(r"^(?:\(?([0-9]+)\)?[）、.．、])\s*(.+)", text)
        if not m:
            continue
        body = m.group(2).strip()
        if len(body) < 4:
            continue
        if not any(word in body for word in advice_words):
            continue
        candidates.append(
            {
                "section": "自动识别建议",
                "section_title": "自动识别编号建议",
                "number": int(m.group(1)),
                "text": body,
                "source_file": str(path),
            }
        )
    return candidates


def collect_advices(files, report_file):
    ordered = []
    if report_file:
        ordered.append(report_file)
    ordered.extend(path for path in files if path != report_file)

    advices = []
    seen = set()
    for path in ordered:
        extracted = extract_advices_from_document(path)
        if not extracted:
            extracted.extend(numbered_advice_candidates(safe_read(path), path))
        for item in extracted:
            key = item["text"]
            if key in seen:
                continue
            seen.add(key)
            advices.append(item)
    return advices


def build_database(root, output):
    root = Path(root)
    records = []
    for source in case_sources(root):
        folder = source["case_folder"]
        files = source["files"]
        report_file = choose_report_file(files)
        if not report_file:
            continue
        category = source["category"]
        text, _ = document_text(report_file)
        advices = collect_advices(files, report_file)
        if not advices:
            print(f"case skipped no advice: {source['case_name']}", flush=True)
            continue
        features = extract_features(text, category=category or "", case_name=source["case_name"])
        records.append(
            {
                "case_id": f"case_{len(records)+1:04d}",
                "case_name": source["case_name"],
                "category": category,
                "case_folder": str(folder),
                "report_file": str(report_file),
                "features": features,
                "advice_count": len(advices),
                "advices": advices,
            }
        )
        print(f"case added: {source['case_name']}, advices={len(advices)}", flush=True)
    database = {
        "format_version": "case_advice_database_v1",
        "source_root": str(root),
        "case_count": len(records),
        "records": records,
    }
    write_json(output, database)
    print(f"case advice database: {output}, cases={len(records)}")
    return database


def main():
    parser = argparse.ArgumentParser(description="Build a case-advice database from historical safety assessment case folders.")
    parser.add_argument("root", help="历史案例根目录，例如 项目安全评估")
    parser.add_argument("-o", "--output", default="data/case_advice_database.json")
    args = parser.parse_args()
    ensure_dir(Path(args.output).parent)
    build_database(args.root, args.output)


if __name__ == "__main__":
    main()
