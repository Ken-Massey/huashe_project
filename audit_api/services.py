from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any, Callable

from pypdf import PdfReader

from deepke_case_extract import (
    run_extract_case_attributes,
    run_extract_plan_text,
    run_match_new_case_advice,
)
from stage1_reply_system.input_builder import build_input
from stage1_reply_system.document_processing import extract_pdf
from stage1_reply_system.pipeline import run_stage1_pipeline
from stage1_reply_system.review_generation import (
    render_audit_record_docx,
    render_reply_draft_docx,
    render_reply_draft_markdown,
    render_review_markdown,
)

from .config import DEEPKE_PYTHON, RESULT_ROOT, STAGE1_DATABASE
from .dynamic_audit import dynamic_opinions
from .ima_rag import _regulation_reference, run_ima_rag_audit
from .mineru_parser import (
    MinerUError,
    extract_pdf_with_mineru,
    mineru_cache_available,
    mineru_cloud_available,
)
from .regulation_rules import extract_regulation
from .reply_writer import generate_formal_reply_content


Progress = Callable[[str], None]
STAGE2_EXECUTION_LOCK = threading.Lock()


PROTECTION_ZONE_FLAGS = {
    "特别保护区": (True, True),
    "控制保护区（非特别保护区）": (True, False),
    "保护区外": (False, False),
    "待判断": (None, None),
}


def _first_number(text: str, patterns: list[str]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            try:
                return float(match.group(1))
            except (TypeError, ValueError):
                continue
    return None


def _smart_document_text(source_file: Path) -> tuple[str, dict[str, Any]]:
    suffix = source_file.suffix.lower()
    if suffix in {".pdf", ".docx", ".txt", ".md"}:
        try:
            text, rows, method = extract_regulation(source_file)
            page_count = None
            if suffix == ".pdf":
                try:
                    page_count = len(PdfReader(str(source_file), strict=False).pages)
                except Exception:
                    page_count = None
            return text, {
                "page_count": page_count,
                "extraction_method": method,
                "row_count": len(rows),
                "text_length": len(text),
            }
        except Exception as exc:
            if suffix != ".pdf":
                raise
            extraction = extract_pdf(source_file, max_pages=30)
            text = extraction.get("full_text", "")
            return text, {
                "page_count": extraction.get("source_page_count"),
                "extraction_method": f"legacy_fallback_after_{type(exc).__name__}",
                "text_length": len(text or ""),
            }
    raise ValueError(f"不支持的资料格式：{suffix}")


def _letter_plain_text(source_file: Path) -> tuple[str, dict[str, Any]]:
    suffix = source_file.suffix.lower()
    if suffix in {".pdf", ".docx", ".txt", ".md"}:
        return _smart_document_text(source_file)
    raise ValueError(f"不支持的资料格式：{suffix}")


def _infer_document_type(filename: str, text: str) -> tuple[str, float, str]:
    name = re.sub(r"\s+", "", filename)
    body = re.sub(r"\s+", "", text[:12000])
    sample = f"{name}\n{body}"
    rules: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
        ("safety_assessment_report", ("安全性影响", "安全影响", "安全评估", "安全评价", "预评估报告", "专项评估报告"), ("评估结论", "影响等级", "结构安全性影响")),
        ("construction_scheme", ("施工方案", "专项施工", "施工组织设计", "支护施工", "降水施工", "桩基和支护"), ("施工工序", "施工方法", "施工部署", "应急措施")),
        ("design_scheme", ("设计方案", "方案设计", "初步设计", "施工图设计", "设计文件"), ("设计说明", "总平面图", "基坑支护设计", "结构设计")),
        ("monitoring_scheme", ("监测方案", "监测设计"), ("监测频率", "报警值", "监测点")),
        ("regulation", ("规范", "规程", "标准", "技术标准", "管理办法", "保护条例"), ("条文", "强制性条文", "控制值", "限值")),
        ("letter", ("征求意见函", "征求意见的函", "报审函", "申请函", "请示", "备案函"), ("贵司", "贵单位", "特此致函", "请予审核")),
    ]
    scored: list[tuple[str, int, list[str]]] = []
    for doc_type, name_terms, body_terms in rules:
        hits: list[str] = []
        score = 0
        for term in name_terms:
            if term in name:
                hits.append(f"文件名:{term}")
                score += 4
        for term in body_terms:
            if term in body:
                hits.append(f"正文:{term}")
                score += 1
        for term in name_terms:
            if term in body:
                hits.append(f"正文:{term}")
                score += 1
        if score:
            scored.append((doc_type, score, hits))
    if not scored:
        return "case_material", 0.55, "未发现明确文件类型特征"
    doc_type, score, hits = max(scored, key=lambda item: item[1])
    return doc_type, min(0.99, 0.55 + score * 0.06), "、".join(hits[:4])


def _classify_project_document(filename: str, text: str) -> tuple[str, float, str]:
    document_type, confidence, reason = _infer_document_type(filename, text)
    if document_type == "letter":
        return "letter", confidence, reason
    if document_type == "regulation":
        return "attachment", confidence, reason
    if document_type in {"safety_assessment_report", "design_scheme", "construction_scheme", "monitoring_scheme"}:
        return "case", confidence, reason
    sample = f"{filename}\n{text[:12000]}"
    letter_terms = (
        "征求地铁意见", "征求意见的函", "征求意见函", "申请备案", "报审函",
        "请示", "致函", "特此致函", "贵司", "贵部",
    )
    case_terms = (
        "安全影响评价报告", "安全影响评估报告", "安全评估报告", "专项评估报告",
        "施工方案", "设计方案", "专项方案", "监测方案", "专家意见回复",
        "工程概况", "计算分析", "风险分析", "评估结论",
    )
    letter_hits = [term for term in letter_terms if term in sample]
    case_hits = [term for term in case_terms if term in sample]
    if re.search(r"(?:意见|报审|申请|备案).{0,8}函", filename):
        letter_hits.append("文件名函件特征")
    if re.search(r"(?:报告|方案|评估|评价|论证)", filename):
        case_hits.append("文件名案例特征")
    if case_hits and len(case_hits) > len(letter_hits):
        return "case", min(0.98, 0.68 + len(case_hits) * 0.06), "、".join(case_hits[:3])
    if letter_hits:
        return "letter", min(0.98, 0.72 + len(letter_hits) * 0.06), "、".join(letter_hits[:3])
    if case_hits:
        return "case", 0.72, "、".join(case_hits[:3])
    return "case", 0.55, "未发现明确函件特征，按项目材料默认作为案例/方案"


def _first_text_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            return re.sub(r"\s+", "", match.group(1)).strip("，。；;、 ")
    return None


def _infer_project_type(compact: str) -> str | None:
    for keyword, value in (
        ("基坑", "基坑"),
        ("桩基", "桩基"),
        ("管线", "管线"),
        ("道路", "道路"),
        ("桥梁", "桥梁"),
        ("高压线", "电力"),
        ("电力杆线", "电力"),
        ("涉地铁", "涉铁工程"),
    ):
        if keyword in compact:
            return value
    return None


def recognize_letter(source_file: Path) -> dict[str, Any]:
    """Classify a project document and extract conservative, form-ready values."""
    raw_text, metadata = _letter_plain_text(source_file)
    text = re.sub(r"[ \t]+", " ", raw_text.replace("\u3000", " "))
    compact = re.sub(r"\s+", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    head = "\n".join(lines[:35])
    filename = source_file.stem
    document_type, type_confidence, type_reason = _infer_document_type(source_file.name, text)

    project_match = re.search(
        r"关于[《“\"]?(.{2,120}?(?:工程|项目))[》”\"]?(?:规划|设计|施工|方案|征求|报审|的函|函)",
        head,
        re.S,
    )
    project_name = re.sub(r"\s+", "", project_match.group(1)) if project_match else ""
    if not project_name:
        filename_match = re.search(r"(.{2,100}?(?:工程|项目))", filename)
        project_name = filename_match.group(1).strip("（）()_- ") if filename_match else ""

    applicant = ""
    for line in lines[:45]:
        candidate = line.rstrip("：:")
        if re.search(r"(?:公司|集团|管理局|建设局|指挥部|委员会|人民政府|设计院)$", candidate):
            if 3 <= len(candidate) <= 80 and candidate not in project_name:
                applicant = candidate
                break

    project_stage = next(
        (value for value in ("出让", "规划", "设计", "施工") if value in filename or value in head),
        None,
    )
    if not project_stage:
        if document_type == "design_scheme":
            project_stage = "设计"
        elif document_type == "construction_scheme":
            project_stage = "施工"
    relationship = None
    if re.search(r"交叉|上跨|下穿|穿越|临近穿越", compact):
        relationship = "交叉"
    elif re.search(r"两侧|双侧", compact):
        relationship = "双侧"
    elif re.search(r"单侧|一侧|邻近|临近|毗邻|侧穿|侧邻|近接", compact):
        relationship = "单侧"

    structure_method = None
    for keyword, value in (
        ("盾构", "盾构"),
        ("矿山法", "暗挖（矿山法）"),
        ("暗挖", "暗挖（矿山法）"),
        ("明挖", "明挖"),
        ("高架", "高架"),
    ):
        if keyword in compact:
            structure_method = value
            break

    metro_line_match = re.search(r"((?:地铁|轨道交通|南京地铁)?\s*(?:S\d+|\d+|[一二三四五六七八九十]+)\s*号线)", text)
    metro_line_name = re.sub(r"\s+", "", metro_line_match.group(1)) if metro_line_match else ""
    metro_line_name = re.sub(r"^(?:地铁|轨道交通|南京地铁)", "", metro_line_name)
    metro_section_name = _first_text_match(text, [
        r"((?:[\u4e00-\u9fffA-Za-z0-9]+站)\s*[~～至-]\s*(?:[\u4e00-\u9fffA-Za-z0-9]+站)(?:区间|区间隧道)?)",
        r"((?:区间|隧道)[^。\n]{0,40}(?:左线|右线|上下行|上行|下行)?)",
    ])

    protection_zone_location = None
    if "特别保护区" in compact:
        protection_zone_location = "特别保护区"
    elif "控制保护区" in compact:
        protection_zone_location = "控制保护区（非特别保护区）"
    elif "保护区外" in compact:
        protection_zone_location = "保护区外"

    support_components = [
        value for keyword, value in (
            ("钻孔灌注桩", "钻孔灌注桩"),
            ("围护桩", "围护桩"),
            ("地下连续墙", "地下连续墙"),
            ("地连墙", "地下连续墙"),
            ("SMW", "SMW工法桩"),
            ("三轴搅拌桩", "三轴搅拌桩"),
            ("止水帷幕", "止水帷幕"),
            ("内支撑", "内支撑"),
            ("钢支撑", "钢支撑"),
            ("混凝土支撑", "混凝土支撑"),
            ("放坡", "放坡"),
            ("非挤土工程桩", "非挤土工程桩"),
            ("挤土工程桩", "挤土工程桩"),
            ("锚杆", "锚杆"),
            ("锚索", "锚索"),
            ("土钉", "土钉"),
        )
        if keyword in compact
    ]

    other_involvements = [
        value for value in ("红线", "接口", "临时结构", "协议") if value in compact
    ]
    fields = {
        "project_name": project_name or None,
        "applicant": applicant or None,
        "project_type": _infer_project_type(compact),
        "project_stage": project_stage,
        "relative_relationship": relationship,
        "other_involvements": other_involvements or None,
        "metro_line_name": metro_line_name or None,
        "metro_section_name": metro_section_name,
        "structure_method": structure_method,
        "structure_condition": "较差" if re.search(r"病害|渗漏|裂缝|破损", compact) else None,
        "buried_depth_m": _first_number(text, [
            r"(?:结构|隧道|区间)[^。\n]{0,30}(?:埋深|覆土厚度|隧顶覆土)(?:约|约为|为|厚度为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
            r"(?:埋深|覆土厚度|隧顶覆土)(?:约|约为|为|厚度为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
        ]),
        "outer_diameter_or_width_m": _first_number(text, [
            r"(?:盾构外径|隧道外径|结构宽度|外径)(?:约|约为|为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
            r"直径(?:约|约为|为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
        ]),
        "pit_depth_m": _first_number(text, [
            r"基坑[^。\n]{0,40}(?:开挖深度|深度|挖深|坑深|深)(?:约|约为|为|最大约为|最大为|最深约为|最深为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
            r"(?:开挖深度|挖深|坑深)(?:约|约为|为|最大约为|最大为|最深约为|最深为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
        ]),
        "pit_length_m": _first_number(text, [
            r"基坑[^。\n]{0,40}(?:长度|长)(?:约|约为|为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
        ]),
        "minimum_horizontal_clearance_m": _first_number(text, [
            r"(?:最小水平净距|水平净距|水平距离|最小净距|最近距离|最小距离)(?:约|约为|为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
            r"(?:距|距离)[^。\n]{0,30}(?:地铁|隧道|结构|区间)[^。\n]{0,30}(?:约|约为|为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
        ]),
        "minimum_vertical_clearance_m": _first_number(text, [
            r"(?:最小竖向净距|竖向净距|竖向距离)(?:约|约为|为)?\s*(\d+(?:\.\d+)?)\s*(?:m|米)",
        ]),
        "dewatering_method": next(
            (value for value in ("轻型井点降水", "喷射井点降水", "深井井点降水", "管井降水", "井点降水", "集水明排", "明沟排水", "疏干井降水", "止水帷幕") if value in compact),
            None,
        ),
        "terrain_zone": "漫滩" if "漫滩" in compact else None,
        "is_soft_soil": True if re.search(r"软土|淤泥质土|粉质黏土", compact) else None,
        "is_complex_geology_or_hydrology": True if re.search(r"承压水|复杂水文|复杂地质|富水", compact) else None,
        "support_components": support_components or None,
        "protection_zone_location": protection_zone_location,
    }
    recognized = {key: value for key, value in fields.items() if value not in (None, "", [])}
    document_role, role_confidence, role_reason = _classify_project_document(source_file.name, text)
    return {
        "source_file": source_file.name,
        "document_role": document_role,
        "role_confidence": round(role_confidence, 2),
        "role_reason": role_reason,
        "document_type": document_type,
        "document_type_confidence": round(type_confidence, 2),
        "document_type_reason": type_reason,
        "recognized_count": len(recognized),
        "fields": recognized,
        "metadata": metadata,
        "text_preview": re.sub(r"\s+", " ", text)[:6000],
    }


def _pdf_extraction_quality(source_file: Path, paragraph_file: str | Path) -> dict[str, Any]:
    rows = []
    with Path(paragraph_file).open("r", encoding="utf-8") as stream:
        for line in stream:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(item.get("text") or "").strip():
                rows.append(item)
    try:
        page_count = len(PdfReader(str(source_file), strict=False).pages)
    except Exception:
        page_count = 0
    text = "".join(str(item.get("text") or "") for item in rows)
    covered_pages = {
        item.get("source_page") for item in rows if isinstance(item.get("source_page"), int)
    }
    return {
        "page_count": page_count,
        "covered_pages": len(covered_pages),
        "character_count": len(text),
        "characters_per_page": len(text) / max(1, page_count),
        "coverage_ratio": len(covered_pages) / max(1, page_count),
        "replacement_ratio": text.count("\ufffd") / max(1, len(text)),
    }


def _extract_stage2_case_text(
    source_file: Path,
    *,
    task_id: str,
    output_root: Path,
    options: dict[str, Any],
    progress: Progress,
) -> dict[str, Any]:
    parser_mode = str(options.get("pdf_parser") or "auto").lower()
    can_use_mineru = source_file.suffix.lower() == ".pdf" and mineru_cloud_available()
    cached = can_use_mineru and mineru_cache_available(source_file)
    if can_use_mineru and (parser_mode == "mineru" or cached):
        reason = "复用MinerU缓存" if cached else "按指定方式使用MinerU"
        progress(f"{reason}解析案例全文、表格和页码")
        rows = extract_pdf_with_mineru(source_file, progress)
        return run_extract_plan_text(
            source_file,
            run_id=task_id,
            output_root=output_root,
            python_executable=DEEPKE_PYTHON,
            progress=progress,
            preparsed_rows=rows,
        )

    extraction = run_extract_plan_text(
        source_file,
        run_id=task_id,
        output_root=output_root,
        python_executable=DEEPKE_PYTHON,
        progress=progress,
    )
    if not can_use_mineru or parser_mode == "native":
        return extraction
    quality = _pdf_extraction_quality(source_file, extraction["paragraph_jsonl"])
    needs_ocr = (
        quality["characters_per_page"] < 120
        or quality["coverage_ratio"] < 0.55
        or quality["replacement_ratio"] > 0.02
    )
    if not needs_ocr:
        progress(
            "案例PDF文本质量良好，保留更快的本地解析"
            f"（{quality['characters_per_page']:.0f}字/页）"
        )
        return extraction
    progress("检测到扫描页或文字缺失，正在切换MinerU识别案例")
    try:
        rows = extract_pdf_with_mineru(source_file, progress)
    except MinerUError:
        progress("MinerU暂不可用，继续使用已完成的本地案例解析")
        return extraction
    return run_extract_plan_text(
        source_file,
        run_id=task_id,
        output_root=output_root,
        python_executable=DEEPKE_PYTHON,
        progress=progress,
        preparsed_rows=rows,
    )


def _attachment_summaries(attachments: dict[str, Path] | None) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for key, path in (attachments or {}).items():
        text = ""
        try:
            text, _metadata = _letter_plain_text(path)
        except Exception:
            text = ""
        summaries.append({
            "key": key,
            "name": path.name,
            "path": str(path),
            "text_excerpt": re.sub(r"\s+", " ", text).strip()[:6000],
        })
    return summaries


def _paragraph_jsonl_excerpt(paragraph_jsonl: str | Path, limit: int = 6000) -> str:
    source = Path(paragraph_jsonl)
    if not source.exists():
        return ""
    fragments: list[str] = []
    total = 0
    with source.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = re.sub(r"\s+", " ", str(item.get("text") or "")).strip()
            if not text:
                continue
            fragments.append(text)
            total += len(text)
            if total >= limit:
                break
    return " ".join(fragments)[:limit]


def _add_source_document_context(
    options: dict[str, Any],
    source_file: Path,
    paragraph_jsonl: str | Path,
) -> None:
    excerpt = _paragraph_jsonl_excerpt(paragraph_jsonl)
    if not excerpt:
        return
    manual_context = dict(options.get("manual_context") or {})
    uploaded = list(manual_context.get("uploaded_documents") or [])
    source_record = {
        "name": source_file.name,
        "role": "case",
        "text_excerpt": excerpt,
    }
    uploaded = [
        item for item in uploaded
        if not (isinstance(item, dict) and item.get("name") == source_file.name and item.get("role") == "case")
    ]
    uploaded.insert(0, source_record)
    manual_context["uploaded_documents"] = uploaded
    manual_context["source_document_name"] = source_file.name
    manual_context["source_document_text_excerpt"] = excerpt
    options["manual_context"] = manual_context


def _append_attachment_paragraphs(
    paragraph_jsonl: str | Path,
    attachments: dict[str, Path] | None,
) -> str:
    summaries = _attachment_summaries(attachments)
    if not summaries:
        return str(paragraph_jsonl)
    source = Path(paragraph_jsonl)
    target = source.with_name(f"{source.stem}_with_attachments.jsonl")
    rows: list[str] = []
    if source.exists():
        rows.extend(source.read_text(encoding="utf-8", errors="replace").splitlines())
    next_id = len(rows) + 1
    for summary in summaries:
        text = summary.get("text_excerpt") or ""
        if not text:
            continue
        rows.append(json.dumps({
            "paragraph_id": next_id,
            "source_page": None,
            "text": f"补充附件《{summary['name']}》：{text}",
        }, ensure_ascii=False))
        next_id += 1
    target.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return str(target)


def _apply_protection_zone_flags(review_context: dict[str, Any]) -> None:
    location = review_context.get("protection_zone_location")
    if location not in PROTECTION_ZONE_FLAGS:
        return
    in_control, in_special = PROTECTION_ZONE_FLAGS[location]
    review_context["is_in_control_protection_zone"] = in_control
    review_context["is_in_special_protection_zone"] = in_special


def _read_json(path_value: str | None) -> dict[str, Any]:
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _audit_details(summary: dict[str, Any]) -> dict[str, Any]:
    report = _read_json(summary.get("non_compliant_report_json"))
    opinion = _read_json(summary.get("generated_review_opinion_json"))
    items = []
    for item in report.get("non_compliant_items") or []:
        items.append({
            key: item.get(key)
            for key in (
                "clause", "chapter", "section", "title", "status", "result", "audit_basis",
                "module_file", "function", "judgement_source", "matched_fields", "match_reason",
                "evidence_sources",
            )
        })
    opinions = [
        {
            key: item.get(key)
            for key in ("number", "opinion", "source_clause", "source_function", "source_result")
        }
        for item in opinion.get("generated_opinions") or []
    ]
    return {
        "summary": report.get("summary") or summary.get("matched_rule_audit_summary") or {},
        "non_compliant_count": report.get("non_compliant_count", len(items)),
        "non_compliant_items": items,
        "generated_opinions": opinions,
    }


def _write_rag_audit(audit: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_file = target / "ima_rag_audit.json"
    markdown_file = target / "ima_rag_audit.md"
    json_file.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    report = audit["risk_report"]
    lines = [
        "# LLM + RAG 案例审核报告", "",
        f"- 综合风险等级：{report.get('overall_risk_level') or '待判断'}",
        f"- 审核方式：{report.get('report_method')}", "",
        str(report.get("overview") or ""), "",
        "## 审核结论", "",
    ]
    for index, item in enumerate(report.get("findings") or [], 1):
        lines.extend([
            f"### {index}. {item.get('title') or '审核事项'}（{item.get('risk_level') or '提示'}）",
            "",
            str(item.get("analysis") or ""),
            "",
            f"- 判断：{item.get('judgement')}",
            f"- 对比过程：{item.get('comparison') or '不涉及数值计算'}",
            f"- 建议：{item.get('recommendation') or '无'}",
            "",
        ])
    markdown_file.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(json_file), "markdown": str(markdown_file)}


def _run_dynamic_for_case(
    case_json: str | Path,
    output_dir: str | Path,
    progress: Progress | None = None,
    case_overrides: dict[str, Any] | None = None,
    project_archive_context: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    case_path = Path(case_json)
    data = json.loads(case_path.read_text(encoding="utf-8"))
    if case_overrides:
        data["incoming_letter_context"] = {
            key: value
            for key, value in case_overrides.items()
            if value not in (None, "", [])
        }
    if project_archive_context:
        data["project_archive_context"] = project_archive_context
    run_root = case_path.parent.parent.parent
    paragraph_files = sorted(
        (run_root / "data" / "texts").glob("*.paragraphs.jsonl"),
        key=lambda item: item.stat().st_size,
        reverse=True,
    )
    case_document = paragraph_files[0] if paragraph_files else case_path
    audit = run_ima_rag_audit(data, case_document, progress=progress)
    return audit, _write_rag_audit(audit, output_dir)


def _archive_result_fields(context: dict[str, Any] | None) -> dict[str, Any]:
    if not context:
        return {}
    project = context.get("project") or {}
    stage = context.get("current_stage") or {}
    return {
        "archive_binding": {
            "project_id": project.get("project_id"),
            "project_name": project.get("project_name"),
            "stage_id": stage.get("stage_id"),
            "stage_name": stage.get("stage_name"),
        },
        "project_archive_context": context,
        "historical_stage_count": int(context.get("previous_stage_count") or 0),
    }


def _merge_dynamic_details(details: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    if audit.get("format_version") == "pure_llm_rag_audit_v1":
        report = audit.get("risk_report") or {}
        non_compliant = [
            item for item in report.get("findings") or []
            if item.get("judgement") == "non_compliant"
        ]
        return {
            "summary": audit.get("summary") or {},
            "non_compliant_count": len(non_compliant),
            "non_compliant_items": [{
                "clause": "、".join(
                    _regulation_reference(ref)
                    for ref in item.get("regulation_evidence") or []
                ),
                "title": item.get("title"),
                "status": "non_compliant",
                "result": item.get("analysis"),
                "audit_basis": "；".join(
                    str(ref.get("quote") or "") for ref in item.get("regulation_evidence") or []
                ),
                "module_file": "ima_rag",
                "function": "LLM+RAG语义审核",
                "judgement_source": "知识库规程全文与案例全文",
                "matched_fields": [],
                "match_reason": item.get("comparison"),
                "evidence_sources": [
                    str(ref.get("quote") or "") for ref in item.get("case_evidence") or []
                ],
            } for item in non_compliant],
            "generated_opinions": [{
                "number": index,
                "opinion": item.get("recommendation") or item.get("analysis"),
                "source_clause": "、".join(
                    _regulation_reference(ref)
                    for ref in item.get("regulation_evidence") or []
                ),
                "source_function": "LLM+RAG语义审核",
                "source_result": item.get("judgement"),
            } for index, item in enumerate(report.get("findings") or [], 1)],
            "audit_method": "pure_llm_rag",
        }
    result = dict(details)
    dynamic_items = []
    for item in audit.get("results") or []:
        if item.get("audit_status") != "non_compliant":
            continue
        execution = item.get("execution") or {}
        dynamic_items.append({
            "clause": item.get("clause"),
            "title": item.get("rule_name"),
            "status": "non_compliant",
            "result": execution.get("calculation") or execution.get("message"),
            "audit_basis": item.get("source_text"),
            "module_file": "dynamic_regulation_engine",
            "function": f"dynamic_rule:{item.get('rule_id')}",
            "judgement_source": item.get("regulation_title"),
            "matched_fields": list((execution.get("inputs") or {}).keys()),
            "match_reason": f"知识库已发布{item.get('rule_type')}规则",
            "evidence_sources": [item.get("source_text")] if item.get("source_text") else [],
        })
    result["non_compliant_items"] = list(result.get("non_compliant_items") or []) + dynamic_items
    result["non_compliant_count"] = len(result["non_compliant_items"])
    result["summary"] = dict(result.get("summary") or {})
    result["summary"]["non_compliant"] = int(result["summary"].get("non_compliant") or 0) + len(dynamic_items)
    result["generated_opinions"] = list(result.get("generated_opinions") or []) + [
        {
            "number": len(result.get("generated_opinions") or []) + index,
            "opinion": opinion["conclusion"],
            "source_clause": "、".join(opinion["regulation_clauses"]),
            "source_function": opinion["function"],
            "source_result": opinion["result"],
        }
        for index, opinion in enumerate(dynamic_opinions(audit), 1)
    ]
    result["dynamic_regulation_summary"] = audit.get("summary") or {}
    return result


def _rag_review_opinions(audit: dict[str, Any]) -> list[dict[str, Any]]:
    report = audit.get("risk_report") or {}
    opinions = []
    for item in report.get("findings") or []:
        if item.get("judgement") == "compliant":
            continue
        opinions.append({
            "topic": item.get("title"),
            "review_status": item.get("judgement") or "risk",
            "conclusion": item.get("recommendation") or item.get("analysis"),
            "result": item.get("judgement"),
            "function": "LLM+RAG语义审核",
            "regulation_clauses": [
                f"{_regulation_reference(ref)} {ref.get('quote') or ''}".strip()
                for ref in item.get("regulation_evidence") or []
            ],
            "inputs": {},
            "calculation_steps": [item.get("comparison")] if item.get("comparison") else [],
            "missing_fields": [],
            "review_notes": [
                str(ref.get("quote") or "") for ref in item.get("case_evidence") or []
            ],
        })
    return opinions


def _prepare_stage1_input(
    source_file: Path,
    payload: dict[str, Any],
    task_id: str,
    attachments: dict[str, Path] | None = None,
) -> dict[str, Any]:
    attachments = attachments or {}
    if all(key in payload for key in ("project", "metro_structure", "pit", "review_context")):
        manual_input = json.loads(json.dumps(payload, ensure_ascii=False))
        _apply_protection_zone_flags(manual_input["review_context"])
        if manual_input["metro_structure"].get("disease_severity") == "存在病害":
            manual_input["metro_structure"]["disease_severity"] = "未知"
            notes = manual_input["review_context"].get("manual_notes")
            compatibility_note = "原始病害情况：存在病害，但严重程度未明确，需人工复核。"
            manual_input["review_context"]["manual_notes"] = "；".join(
                item for item in (notes, compatibility_note) if item
            )
        manual_input["case_id"] = manual_input.get("case_id") or task_id
        documents = manual_input.setdefault("source_documents", [])
        incoming = next((item for item in documents if item.get("role") == "incoming_letter"), None)
        if incoming is None:
            incoming = {"role": "incoming_letter", "path": str(source_file)}
            documents.insert(0, incoming)
        else:
            incoming["path"] = str(source_file)
        for key, value in {
            "sha256": None,
            "text_extraction_method": "not_extracted",
            "document_date": None,
            "page_count": None,
        }.items():
            incoming.setdefault(key, value)
        for role, key in (("scheme", "scheme_file"), ("expert_opinion", "expert_opinion_file")):
            attachment = attachments.get(key)
            if attachment is None:
                continue
            manual_input["pit"][key] = str(attachment)
            document = next((item for item in documents if item.get("role") == role), None)
            if document is None:
                document = {"role": role}
                documents.append(document)
            document.update(
                path=str(attachment),
                sha256=None,
                text_extraction_method="not_extracted",
                document_date=None,
                page_count=None,
            )
        return manual_input

    values = dict(payload)
    if values.get("disease_severity") == "存在病害":
        values["disease_severity"] = "未知"
        compatibility_note = "原始病害情况：存在病害，但严重程度未明确，需人工复核。"
        values["manual_notes"] = "；".join(
            item for item in (values.get("manual_notes"), compatibility_note) if item
        )
    values["incoming_letter"] = str(source_file)
    values["case_id"] = values.get("case_id") or task_id
    for key, path in attachments.items():
        values[key] = str(path)
    return build_input(values)


def stage1_worker(
    source_file: Path,
    payload: dict[str, Any],
    attachments: dict[str, Path] | None = None,
    *,
    archive_context: dict[str, Any] | None = None,
):
    def run(task_id: str, progress: Progress) -> dict[str, Any]:
        manual_input = _prepare_stage1_input(source_file, payload, task_id, attachments)
        result = run_stage1_pipeline(
            source_file,
            manual_input,
            STAGE1_DATABASE,
            RESULT_ROOT / "stage1",
            run_name=task_id,
            progress=progress,
        )
        progress("正在使用纯LLM+RAG知识库补充审核")
        output_dir = Path(result["output_dir"])
        merged = json.loads((output_dir / "04_merged_input.json").read_text(encoding="utf-8"))
        if archive_context:
            progress("正在读取项目前序阶段审核记录")
            merged["project_archive_context"] = archive_context
        dynamic_audit = run_ima_rag_audit(
            merged, output_dir / "04_merged_input.json", progress=progress
        )
        dynamic_files = _write_rag_audit(dynamic_audit, output_dir)
        package = result["review_package"]
        package["dynamic_regulation_audit"] = dynamic_audit
        package["audit_opinions"].extend(_rag_review_opinions(dynamic_audit))
        progress("正在按照正式回函模板拟写审核意见")
        package["formal_reply"] = generate_formal_reply_content(
            package,
            merged,
            dynamic_audit,
        )
        (output_dir / "07_review_package.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
        audit_opinion_file = output_dir / "审核意见.md"
        final_reply_file = output_dir / "最终版复函.docx"
        audit_opinion_file.write_text(render_review_markdown(package), encoding="utf-8")
        (output_dir / "回函草稿.md").write_text(render_reply_draft_markdown(package), encoding="utf-8")
        render_reply_draft_docx(package, final_reply_file)
        render_audit_record_docx(package, output_dir / "内部自动审核记录.docx")
        result["summary"]["dynamic_regulation_summary"] = dynamic_audit["summary"]
        (output_dir / "run_summary.json").write_text(json.dumps(result["summary"], ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "stage": "stage1",
            "summary": result["summary"],
            "dynamic_regulation_audit": dynamic_audit,
            "dynamic_regulation_files": dynamic_files,
            "output_dir": result["output_dir"],
            "artifact_files": [str(audit_opinion_file), str(final_reply_file)],
            **_archive_result_fields(archive_context),
        }

    return run


def stage2_audit_worker(source_file: Path, options: dict[str, Any], attachments: dict[str, Path] | None = None):
    def run(task_id: str, progress: Progress) -> dict[str, Any]:
        with STAGE2_EXECUTION_LOCK:
            extraction = _extract_stage2_case_text(
                source_file,
                task_id=task_id,
                output_root=RESULT_ROOT / "stage2_audit",
                options=options,
                progress=progress,
            )
        _add_source_document_context(options, source_file, extraction["paragraph_jsonl"])
        progress("正在执行纯LLM+RAG知识库审核，不调用规则函数")
        attachment_summaries = _attachment_summaries(attachments)
        paragraph_source = _append_attachment_paragraphs(extraction["paragraph_jsonl"], attachments)
        if attachment_summaries:
            progress("正在合并补充附件正文并纳入本轮审核上下文")
        case_context = {
            "document_name": source_file.name,
            "document_type": source_file.suffix.lower(),
            "attachment_documents": attachment_summaries,
            "manual_context": options.get("manual_context") or {},
        }
        archive_context = options.get("project_archive_context")
        if archive_context:
            progress("正在读取项目前序阶段审核记录")
            case_context["project_archive_context"] = archive_context
        dynamic_audit = run_ima_rag_audit(
            case_context, paragraph_source, progress=progress
        )
        dynamic_files = _write_rag_audit(
            dynamic_audit, Path(extraction["run_dir"]) / "reports" / "ima_rag"
        )
        return {
            "stage": "stage2_audit",
            "summary": extraction,
            "audit_details": _merge_dynamic_details({}, dynamic_audit),
            "dynamic_regulation_audit": dynamic_audit,
            "dynamic_regulation_files": dynamic_files,
            "output_dir": extraction["run_dir"],
            "artifact_roots": [extraction["run_dir"]],
            **_archive_result_fields(archive_context),
        }

    return run


def advice_worker(source_file: Path, options: dict[str, Any]):
    def run(task_id: str, progress: Progress) -> dict[str, Any]:
        output_dir = RESULT_ROOT / "stage2_advice" / task_id
        with STAGE2_EXECUTION_LOCK:
            case_source = source_file
            audit_result = None
            if source_file.suffix.lower() != ".json":
                progress("先提取新案例属性并执行案例审核")
                audit_result = run_extract_case_attributes(
                    source_file,
                    run_id=task_id,
                    output_root=RESULT_ROOT / "stage2_advice" / "audit",
                    python_executable=DEEPKE_PYTHON,
                    progress=progress,
                )
                case_source = Path(audit_result["case_json"])
            result = run_match_new_case_advice(
                case_source,
                output_dir=output_dir,
                rebuild_database=bool(options.get("rebuild_database", False)),
                top_k=int(options.get("top_k", 5)),
                python_executable=DEEPKE_PYTHON,
                progress=progress,
            )
        dynamic_audit, dynamic_files = _run_dynamic_for_case(
            case_source,
            output_dir / "dynamic_regulations",
            progress,
            project_archive_context=options.get("project_archive_context"),
        )
        best = result.get("best_match") or {}
        return {
            "stage": "stage2_advice",
            "summary": {
                "best_case": best.get("case_name"),
                "similarity": best.get("score"),
                "advice_count": len(best.get("advices") or []),
            },
            "match_result": result,
            "audit_summary": audit_result,
            "dynamic_regulation_audit": dynamic_audit,
            "dynamic_regulation_opinions": _rag_review_opinions(dynamic_audit),
            "dynamic_regulation_files": dynamic_files,
            "output_dir": str(output_dir),
            "artifact_roots": [str(output_dir)],
            **_archive_result_fields(options.get("project_archive_context")),
        }

    return run


def stage2_full_worker(source_file: Path, options: dict[str, Any], attachments: dict[str, Path] | None = None):
    def run(task_id: str, progress: Progress) -> dict[str, Any]:
        attachment_summaries = _attachment_summaries(attachments)
        if attachment_summaries:
            manual_context = dict(options.get("manual_context") or {})
            uploaded = list(manual_context.get("uploaded_documents") or [])
            uploaded.extend({
                "name": item["name"],
                "role": "attachment",
                "text_excerpt": item.get("text_excerpt") or "",
            } for item in attachment_summaries)
            manual_context["uploaded_documents"] = uploaded
            options["manual_context"] = manual_context
        with STAGE2_EXECUTION_LOCK:
            audit = run_extract_case_attributes(
                source_file,
                run_id=task_id,
                output_root=RESULT_ROOT / "stage2_full" / "audit",
                python_executable=DEEPKE_PYTHON,
                progress=progress,
            )
            _add_source_document_context(options, source_file, audit["paragraph_jsonl"])
            case_json = Path(audit["case_json"])
            advice_dir = RESULT_ROOT / "stage2_full" / "advice" / task_id
            advice = run_match_new_case_advice(
                case_json,
                output_dir=advice_dir,
                rebuild_database=bool(options.get("rebuild_database", False)),
                top_k=int(options.get("top_k", 5)),
                python_executable=DEEPKE_PYTHON,
                progress=progress,
            )
        dynamic_audit, dynamic_files = _run_dynamic_for_case(
            case_json,
            Path(audit["run_dir"]) / "reports" / "dynamic_regulations",
            progress,
            case_overrides=options.get("manual_context"),
            project_archive_context=options.get("project_archive_context"),
        )
        best = advice.get("best_match") or {}
        return {
            "stage": "stage2_full",
            "audit_summary": audit,
            "audit_details": _merge_dynamic_details(_audit_details(audit), dynamic_audit),
            "dynamic_regulation_audit": dynamic_audit,
            "dynamic_regulation_opinions": _rag_review_opinions(dynamic_audit),
            "dynamic_regulation_files": dynamic_files,
            "advice_summary": {
                "best_case": best.get("case_name"),
                "similarity": best.get("score"),
                "advice_count": len(best.get("advices") or []),
            },
            "advice_result": advice,
            "output_dir": audit["run_dir"],
            "artifact_roots": [audit["run_dir"], str(advice_dir)],
            **_archive_result_fields(options.get("project_archive_context")),
        }

    return run
