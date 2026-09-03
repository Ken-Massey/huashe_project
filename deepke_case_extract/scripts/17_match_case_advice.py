import argparse
import json
import math
import re
import sys
from pathlib import Path

from common import ensure_dir, read_document_paragraphs, write_json
from importlib.util import module_from_spec, spec_from_file_location


def load_builder():
    script = Path(__file__).with_name("16_build_case_advice_database.py")
    spec = spec_from_file_location("case_advice_builder", script)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def extract_from_case_json(path):
    data = load_json(path)
    attrs = data.get("attributes") or data.get("measured_values") or {}
    text_blob = "\n".join(f"{key}={value}" for key, value in attrs.items() if value not in (None, "", [], {}))
    features = builder.extract_features(text_blob, category="", case_name=data.get("doc_id") or Path(path).stem)
    field_map = {
        "metro_line": "metro_line_name",
        "metro_asset": "metro_asset_type",
        "relation": "relation_type",
        "support_method": "support_method",
        "dewatering_type": "dewatering_type",
        "pit_depth_m": "pit_depth",
        "minimum_clearance_m": "minimum_horizontal_clearance",
    }
    for target, source in field_map.items():
        value = attrs.get(source)
        if value in (None, "", [], {}):
            continue
        if target.endswith("_m"):
            features[target] = builder.extract_number(value)
        else:
            features[target] = str(value)
    features["case_name"] = data.get("doc_id") or Path(path).stem
    features["in_control_protection_zone"] = bool(attrs.get("is_in_control_protection_zone") or features.get("in_control_protection_zone"))
    features["in_special_protection_zone"] = bool(attrs.get("is_in_special_protection_zone") or features.get("in_special_protection_zone"))
    return features


def extract_from_document(path):
    text, _ = builder.document_text(path)
    return builder.extract_features(text, category="", case_name=Path(path).stem)


def extract_query_features(input_path):
    path = Path(input_path)
    if path.suffix.lower() == ".json":
        return extract_from_case_json(path)
    if path.suffix.lower() in {".docx", ".pdf", ".txt"}:
        return extract_from_document(path)
    raise ValueError(f"暂不支持输入类型: {path.suffix}")


def set_similarity(a, b):
    a = set(a or [])
    b = set(b or [])
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def exact_similarity(a, b):
    if not a or not b:
        return 0.0
    return 1.0 if str(a).lower() == str(b).lower() else 0.0


def loose_text_similarity(a, b):
    if not a or not b:
        return 0.0
    a = str(a)
    b = str(b)
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.75
    return 0.0


def numeric_similarity(a, b, scale):
    if a is None or b is None:
        return 0.0
    try:
        distance = abs(float(a) - float(b))
    except (TypeError, ValueError):
        return 0.0
    return math.exp(-(distance / scale) ** 2)


def bool_similarity(a, b):
    if a is None or b is None:
        return 0.0
    return 1.0 if bool(a) == bool(b) else 0.0


def similarity(query, candidate):
    parts = []

    def add(name, score, weight):
        parts.append({"name": name, "score": round(score, 4), "weight": weight, "weighted": score * weight})

    add("工程类型", set_similarity(query.get("work_types"), candidate.get("work_types")), 0.22)
    add("关键词", set_similarity(query.get("keywords"), candidate.get("keywords")), 0.24)
    add("轨道线路", loose_text_similarity(query.get("metro_line"), candidate.get("metro_line")), 0.08)
    add("轨道结构类型", loose_text_similarity(query.get("metro_asset"), candidate.get("metro_asset")), 0.08)
    add("空间关系", loose_text_similarity(query.get("relation"), candidate.get("relation")), 0.08)
    add("支护形式", loose_text_similarity(query.get("support_method"), candidate.get("support_method")), 0.06)
    add("降水类型", loose_text_similarity(query.get("dewatering_type"), candidate.get("dewatering_type")), 0.06)
    add("基坑深度", numeric_similarity(query.get("pit_depth_m"), candidate.get("pit_depth_m"), scale=8.0), 0.08)
    add("最小净距", numeric_similarity(query.get("minimum_clearance_m"), candidate.get("minimum_clearance_m"), scale=20.0), 0.06)
    add("保护区属性", bool_similarity(query.get("in_control_protection_zone"), candidate.get("in_control_protection_zone")), 0.02)
    add("特别保护区属性", bool_similarity(query.get("in_special_protection_zone"), candidate.get("in_special_protection_zone")), 0.02)

    total = sum(part["weighted"] for part in parts)
    return round(total, 4), parts


def rank_cases(query_features, database, top_k=5):
    ranked = []
    for record in database.get("records", []):
        score, parts = similarity(query_features, record.get("features") or {})
        ranked.append(
            {
                "score": score,
                "case_id": record.get("case_id"),
                "case_name": record.get("case_name"),
                "original_file_name": record.get("original_file_name"),
                "category": record.get("category"),
                "case_folder": record.get("case_folder"),
                "report_file": record.get("report_file"),
                "advice_count": record.get("advice_count"),
                "similarity_breakdown": parts,
                "features": record.get("features"),
                "advices": record.get("advices") or [],
            }
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:top_k]


def write_markdown(path, query_features, matches):
    best = matches[0] if matches else None
    lines = [
        "# 案例匹配与建议复用结果",
        "",
        "## 新案例属性摘要",
        "",
    ]
    for key in ["case_name", "work_types", "metro_line", "metro_asset", "relation", "support_method", "dewatering_type", "pit_depth_m", "minimum_clearance_m", "keywords"]:
        lines.append(f"- `{key}`：{query_features.get(key)}")
    lines.extend(["", "## 最相似案例", ""])
    if not best:
        lines.append("未匹配到历史案例。")
    else:
        lines.extend(
            [
                f"- 案例名称：{best.get('case_name')}",
                f"- 文件名称：{best.get('original_file_name') or best.get('case_name')}",
                f"- 案例类别：{best.get('category')}",
                f"- 相似度：{best.get('score')}",
                f"- 案例文件夹：`{best.get('case_folder')}`",
                f"- 报告文件：`{best.get('report_file')}`",
                "",
                "### 相似度构成",
                "",
            ]
        )
        for part in best.get("similarity_breakdown", []):
            lines.append(f"- {part['name']}：得分 {part['score']}，权重 {part['weight']}")
        lines.extend(["", "## 可直接复制的评审建议", ""])
        for idx, advice in enumerate(best.get("advices", []), start=1):
            lines.append(f"{idx}、{advice.get('text')}")
            lines.append("")
        lines.extend(["", "## Top 匹配列表", ""])
        for idx, item in enumerate(matches, start=1):
            lines.append(f"{idx}. {item.get('case_name')}，相似度 {item.get('score')}，建议数 {item.get('advice_count')}")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Match a new case to the historical case-advice database and copy the best case's review advices.")
    parser.add_argument("input", help="新案例文件，支持 *.case.json、docx、pdf。")
    parser.add_argument("--database", default="data/case_advice_database.json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("-o", "--output", default="outputs/case_advice_match")
    args = parser.parse_args()

    database = load_json(args.database)
    query = extract_query_features(args.input)
    matches = rank_cases(query, database, top_k=args.top_k)
    result = {
        "format_version": "case_advice_match_v1",
        "query_input": str(args.input),
        "query_features": query,
        "database": str(args.database),
        "match_count": len(matches),
        "best_match": matches[0] if matches else None,
        "matches": matches,
    }

    output = Path(args.output)
    if output.suffix.lower() in {".json", ".md"}:
        json_path = output.with_suffix(".json")
        md_path = output.with_suffix(".md")
    else:
        ensure_dir(output)
        json_path = output / "case_advice_match.json"
        md_path = output / "case_advice_match.md"
    write_json(json_path, result)
    write_markdown(md_path, query, matches)
    print(f"case advice match: {md_path}")


if __name__ == "__main__":
    main()
