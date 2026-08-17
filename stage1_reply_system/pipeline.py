"""End-to-end stage-one processing pipeline."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from stage1_reply_system.document_processing import extract_letter_fields, extract_pdf, merge_extracted_with_manual
from stage1_reply_system.review_generation import (
    build_review_package,
    render_audit_record_docx,
    render_reply_draft_docx,
    render_reply_draft_markdown,
    render_review_markdown,
)
from stage1_reply_system.validation import validate_input


Progress = Callable[[str], None]


def _safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\s]+', "_", value.strip()).strip("_")
    return value[:80] or "case"


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _calculation_input_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    project = data.get("project") or {}
    metro = data.get("metro_structure") or {}
    pit = data.get("pit") or {}
    geology = data.get("geology") or {}
    context = data.get("review_context") or {}
    return {
        "project_type": project.get("project_type"),
        "project_stage": project.get("project_stage"),
        "relative_relationship": project.get("relative_relationship"),
        "structure_method": metro.get("structure_method"),
        "buried_depth_m": metro.get("buried_depth_m"),
        "outer_diameter_or_width_m": metro.get("outer_diameter_or_width_m"),
        "is_special_section": metro.get("is_special_section"),
        "pit_depth_m": pit.get("pit_depth_m"),
        "pit_length_m": pit.get("pit_length_m"),
        "minimum_horizontal_clearance_m": pit.get("minimum_horizontal_clearance_m"),
        "minimum_vertical_clearance_m": pit.get("minimum_vertical_clearance_m"),
        "support_components": pit.get("support_components") or [],
        "terrain_zone": geology.get("terrain_zone"),
        "is_soft_soil": geology.get("is_soft_soil"),
        "is_complex_geology_or_hydrology": geology.get("is_complex_geology_or_hydrology"),
        "protection_zone_location": context.get("protection_zone_location"),
    }


def run_stage1_pipeline(
    pdf_file: str | Path,
    manual_input: dict[str, Any],
    database_file: str | Path,
    output_root: str | Path,
    *,
    run_name: str | None = None,
    progress: Progress | None = None,
) -> dict[str, Any]:
    notify = progress or (lambda message: None)
    pdf_path = Path(pdf_file).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    database_path = Path(database_file).resolve()
    if not database_path.exists():
        raise FileNotFoundError(f"历史回函数据库不存在：{database_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = run_name or manual_input.get("project", {}).get("project_name") or pdf_path.stem
    output_dir = Path(output_root).resolve() / f"{_safe_name(str(label))}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)

    incoming = next(
        (document for document in manual_input.get("source_documents", []) if document.get("role") == "incoming_letter"),
        None,
    )
    if incoming is not None:
        incoming["path"] = str(pdf_path)

    notify("1/5 正在提取函件文字")
    extraction = extract_pdf(pdf_path)
    fields = extract_letter_fields(extraction)

    notify("2/5 正在合并人工参数与抽取字段")
    merge_result = merge_extracted_with_manual(manual_input, fields)
    merged = merge_result["merged_input"]
    incoming = next(
        (document for document in merged["source_documents"] if document.get("role") == "incoming_letter"),
        None,
    )
    if incoming:
        incoming["path"] = str(pdf_path)
        incoming["page_count"] = extraction["page_count"]
    validation_errors = validate_input(merged)
    if validation_errors:
        _write_json(output_dir / "validation_errors.json", validation_errors)
        raise ValueError("统一输入未通过 Schema 校验：\n" + "\n".join(validation_errors))

    notify("3/5 正在执行规程计算")
    package = build_review_package(
        merged,
        database_path,
        letter_text=extraction["full_text"],
    )

    notify("4/5 正在保存审核包")
    _write_json(output_dir / "00_manual_input.json", manual_input)
    _write_json(output_dir / "01_pdf_text.json", extraction)
    _write_json(output_dir / "02_extracted_fields.json", fields)
    _write_json(output_dir / "03_merge_report.json", {key: value for key, value in merge_result.items() if key != "merged_input"})
    _write_json(output_dir / "04_merged_input.json", merged)
    _write_json(output_dir / "05_calculation.json", package["calculation"])
    _write_json(output_dir / "06_history_match.json", package["history_match"])
    _write_json(output_dir / "07_review_package.json", package)
    (output_dir / "函件全文.txt").write_text(extraction["full_text"], encoding="utf-8")
    (output_dir / "审核意见.md").write_text(render_review_markdown(package), encoding="utf-8")
    (output_dir / "回函草稿.md").write_text(render_reply_draft_markdown(package), encoding="utf-8")
    render_reply_draft_docx(package, output_dir / "最终版复函.docx")
    render_audit_record_docx(package, output_dir / "内部自动审核记录.docx")

    selected_history = package["history_match"].get("selected_match") or {}
    summary = {
        "format_version": "stage1_pipeline_run_v1",
        "case_id": merged["case_id"],
        "source_pdf": str(pdf_path),
        "output_dir": str(output_dir),
        "overall_status": package["overall_status"],
        "decision_summary": package["calculation"]["summary"],
        "calculation_input_snapshot": _calculation_input_snapshot(merged),
        "missing_required_inputs": package["missing_required_inputs"],
        "history_match_project": package["historical_advice"]["source_project"],
        "history_match_similarity": package["historical_advice"]["source_similarity"],
        "history_match_case_id": selected_history.get("history_case_id"),
        "history_match_quality_status": selected_history.get("history_quality_status"),
        "history_match_quality_issues": selected_history.get("history_quality_issues", []),
        "history_match_reply_file": selected_history.get("primary_reply_file"),
        "history_match_component_scores": selected_history.get("component_scores", {}),
        "merge_conflicts": len(merge_result["conflicts"]),
        "extraction_review_required": len(merge_result["review_required"]),
    }
    _write_json(output_dir / "run_summary.json", summary)
    notify("5/5 审核完成")
    return {"output_dir": str(output_dir), "summary": summary, "review_package": package}
