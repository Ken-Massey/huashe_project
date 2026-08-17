"""Combine deterministic regulation decisions with matched historical advice."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from stage1_reply_system.history.advice import extract_attention_subsection
from stage1_reply_system.history.matcher import match_similar_replies
from stage1_reply_system.rules import evaluate_project


FIELD_LABELS = {
    "pit.support_components": "基坑支护构件类型",
    "pit.minimum_horizontal_clearance_m": "最小水平净距",
    "pit.minimum_vertical_clearance_m": "最小竖向净距",
    "metro_structure.structure_category": "轨道交通结构类别",
    "metro_structure.outer_diameter_or_width_m": "盾构隧道外径或结构宽度D",
    "metro_structure.original_excavation_depth_m": "既有明挖结构原开挖深度H",
    "metro_structure.mined_tunnel_span_m": "矿山法隧道毛洞跨度W",
    "metro_structure.elevated_pile_diameter_m": "高架桥梁单桩桩径P",
    "review_context.is_in_control_protection_zone": "是否位于轨道交通控制保护区",
    "calculated.final_impact_level": "最终影响等级",
    "calculated.is_major_impact_work": "是否属于重大影响外部作业",
}


def _expand_missing(value: str, data: dict[str, Any]) -> list[str]:
    if value == "pit.minimum_horizontal_clearance_m|pit.minimum_vertical_clearance_m":
        relationship = data.get("project", {}).get("relative_relationship")
        if relationship in ("单侧", "双侧"):
            return ["pit.minimum_horizontal_clearance_m"]
        if relationship == "交叉":
            return ["pit.minimum_vertical_clearance_m"]
    return [part for part in value.split("|") if part and not part.startswith("calculated.")]


def _missing_fields(calculation: dict[str, Any], data: dict[str, Any]) -> list[dict[str, str]]:
    fields: list[str] = []
    for decision in calculation["decisions"].values():
        for raw in decision.get("missing_fields", []):
            fields.extend(_expand_missing(raw, data))
    unique = list(dict.fromkeys(fields))
    return [{"field": field, "label": FIELD_LABELS.get(field, field)} for field in unique]


def _decision_opinion(key: str, decision: dict[str, Any]) -> dict[str, Any]:
    result = decision["result"]
    if decision["status"] == "insufficient":
        conclusion = f"现有资料不足以判断{decision['decision_name']}，应补充相关参数后重新计算。"
        review_status = "pending_input"
    elif key == "setback_distance" and decision["status"] == "fail":
        conclusion = "现有净距不满足规程常规控制值，应开展专题专项论证并优化方案。"
        review_status = "requires_revision"
    elif key == "setback_distance" and decision["status"] == "review":
        conclusion = "净距满足表列值，但存在规程要求从严复核的条件，应由专业人员复核。"
        review_status = "manual_review"
    else:
        conclusion = f"审核结论：{result}。"
        review_status = "complete"
    return {
        "decision_key": key,
        "topic": decision["decision_name"],
        "review_status": review_status,
        "conclusion": conclusion,
        "result": result,
        "function": decision["function"],
        "regulation_clauses": decision["regulation_clauses"],
        "inputs": decision.get("inputs", {}),
        "calculation_steps": decision.get("calculation_steps", []),
        "missing_fields": decision.get("missing_fields", []),
        "review_notes": decision.get("review_notes", []),
    }


def _project_facts(data: dict[str, Any]) -> list[dict[str, Any]]:
    project = data["project"]
    metro = data["metro_structure"]
    pit = data["pit"]
    facts = (
        ("项目名称", project.get("project_name")),
        ("报审单位", project.get("applicant")),
        ("项目阶段", project.get("project_stage")),
        ("项目类型", project.get("project_type")),
        ("项目位置", project.get("project_address")),
        ("建设内容", project.get("construction_content")),
        ("相对关系", project.get("relative_relationship")),
        ("地铁线路", metro.get("metro_line_name")),
        ("地铁区间", metro.get("metro_section_name")),
        ("结构形式", metro.get("structure_method")),
        ("结构状态", metro.get("structure_condition")),
        ("结构埋深", metro.get("buried_depth_m")),
        ("基坑深度", pit.get("pit_depth_m")),
        ("基坑长度", pit.get("pit_length_m")),
        ("最小水平净距", pit.get("minimum_horizontal_clearance_m")),
        ("最小竖向净距", pit.get("minimum_vertical_clearance_m")),
    )
    return [{"label": label, "value": value} for label, value in facts if value not in (None, "", [])]


def build_review_package(
    data: dict[str, Any],
    database_path: str | Path,
    *,
    letter_text: str = "",
    match_threshold: float = 0.45,
) -> dict[str, Any]:
    calculation = evaluate_project(data)
    history_match = match_similar_replies(
        data,
        database_path,
        letter_text=letter_text,
        minimum_score=match_threshold,
    )
    missing = _missing_fields(calculation, data)
    opinions = [
        _decision_opinion(key, decision)
        for key, decision in calculation["decisions"].items()
    ]

    selected = history_match.get("selected_match")
    attention = extract_attention_subsection(selected["advice_text"]) if selected else {
        "attention_text": "", "attention_items": [], "anchor": None, "status": "not_available"
    }
    historical_advice = {
        "status": "available" if attention["attention_items"] else "manual_selection_required",
        "copied_verbatim": bool(attention["attention_items"]),
        "attention_text": attention["attention_text"],
        "attention_items": attention["attention_items"],
        "source_project": selected["project_name"] if selected else None,
        "source_reply_file": selected["primary_reply_file"] if selected else None,
        "source_similarity": selected["similarity_score"] if selected else None,
        "extraction_anchor": attention["anchor"],
        "note": "仅复制历史回函的注意事项，不复制历史项目位置、净距和工程规模。",
    }

    setback = calculation["decisions"]["setback_distance"]
    if missing:
        overall_status = "blocked_by_missing_data"
    elif setback["status"] == "fail":
        overall_status = "requires_special_study"
    else:
        overall_status = "ready_for_human_review"

    return {
        "format_version": "stage1_review_package_v1",
        "case_id": data.get("case_id"),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "overall_status": overall_status,
        "formal_issuance_allowed": False,
        "formal_issuance_note": "系统输出为辅助审核草稿，补齐资料并经专业人员复核、审批后方可正式出具。",
        "project_facts": _project_facts(data),
        "calculation": calculation,
        "audit_opinions": opinions,
        "missing_required_inputs": missing,
        "historical_advice": historical_advice,
        "history_match": history_match,
    }
