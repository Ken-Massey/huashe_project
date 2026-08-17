from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .regulation_rules import RegulationRepository, RuleEngine


ALIASES = {
    "project.project_type": ("project_type", "main_external_work_type"),
    "project.project_stage": ("project_stage", "work_stage"),
    "project.relative_relationship": ("relative_relationship", "relation_type"),
    "pit.minimum_horizontal_clearance_m": ("minimum_horizontal_clearance", "horizontal_clearance", "distance"),
    "pit.minimum_vertical_clearance_m": ("minimum_vertical_clearance", "vertical_clearance"),
    "pit.pit_depth_m": ("pit_depth", "work_depth"),
    "pit.pit_length_m": ("pit_length", "work_length"),
    "pit.dewatering_method": ("dewatering_method",),
    "metro_structure.outer_diameter_or_width_m": ("metro_outer_diameter_or_width", "tunnel_diameter", "D"),
    "metro_structure.buried_depth_m": ("metro_buried_depth",),
    "metro_structure.structure_method": ("metro_structure_method",),
    "metro_structure.structure_condition": ("metro_existing_condition",),
    "review_context.is_in_control_protection_zone": ("is_in_control_protection_zone",),
    "review_context.is_in_special_protection_zone": ("is_in_special_protection_zone",),
}
ACTION_LABELS = {
    "safety_assessment_required": "需要开展安全评估",
    "monitoring_required": "需要实施保护监测",
    "protective_monitoring_required": "需要实施保护监测",
}


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(child, dict):
                result.update(_flatten(child, path))
            elif not isinstance(child, list):
                result[path] = child
                result.setdefault(str(key), child)
    return result


def canonical_facts(case_data: dict[str, Any]) -> dict[str, Any]:
    facts = _flatten(case_data)
    attributes = case_data.get("attributes")
    if isinstance(attributes, dict):
        for key, item in attributes.items():
            value = item.get("value") if isinstance(item, dict) and "value" in item else item
            if value not in (None, ""):
                facts[key] = value
    for source, targets in ALIASES.items():
        value = facts.get(source)
        if value in (None, ""):
            continue
        for target in targets:
            facts.setdefault(target, value)
    for key, value in list(facts.items()):
        if key.endswith("_m"):
            facts.setdefault(key[:-2], value)
    return facts


def _scope_matches(scope: Any, facts: dict[str, Any]) -> bool:
    if not scope:
        return True
    conditions = scope if isinstance(scope, list) else [scope]
    for condition in conditions:
        if not isinstance(condition, dict) or not condition.get("field"):
            return False
        if not RuleEngine._compare_value(
            facts.get(condition["field"]), condition.get("operator", "=="), condition.get("value")
        ):
            return False
    return True


def _audit_status(rule: dict[str, Any], execution_status: str | None) -> str:
    action = rule.get("action") or {}
    trigger_rule = any(
        bool(value) and (str(key).endswith("_required") or str(key).startswith("require_"))
        for key, value in action.items()
    )
    if trigger_rule and execution_status == "matched":
        return "triggered"
    if trigger_rule and execution_status == "not_matched":
        return "not_triggered"
    return {
        "matched": "compliant", "not_matched": "non_compliant", "derived": "derived",
        "insufficient_data": "insufficient_data", "not_applicable": "not_applicable",
        "invalid_rule": "error", "calculation_error": "error",
    }.get(execution_status or "", execution_status or "error")


def _used_fields(rule: dict[str, Any]) -> list[str]:
    rule_type = rule.get("rule_type") or "numeric_rule"
    if rule_type == "conditional_rule":
        return list(dict.fromkeys(
            [item.get("field") for item in rule.get("conditions") or []] + [(rule.get("requirement") or {}).get("field")]
        ))
    if rule_type == "lookup_table_rule":
        return list(dict.fromkeys((rule.get("selectors") or []) + [rule.get("output_field")]))
    return list((rule.get("inputs") or {}).keys())


def run_dynamic_regulation_audit(
    case_data: dict[str, Any], repository: RegulationRepository | None = None
) -> dict[str, Any]:
    repository = repository or RegulationRepository()
    facts = canonical_facts(case_data)
    rules = repository.executable_rules()
    ordered = sorted(rules, key=lambda item: (item["rule"].get("rule_type") != "lookup_table_rule", item["rule_id"]))
    results: list[dict[str, Any]] = []
    for item in ordered:
        rule = item["rule"]
        if not _scope_matches(rule.get("scope"), facts):
            execution = {"status": "not_applicable", "message": "案例不满足规则适用范围。"}
        else:
            execution = RuleEngine.execute(rule, facts)
            if execution.get("status") == "derived":
                facts[execution["derived_field"]] = execution.get("derived_value")
        source = rule.get("source") or {}
        result = {
            "rule_id": item["rule_id"],
            "rule_name": rule.get("name") or item.get("name"),
            "rule_type": rule.get("rule_type") or "numeric_rule",
            "rule_updated_at": item.get("updated_at"),
            "regulation_id": item.get("regulation_id"),
            "regulation_title": item.get("regulation_title"),
            "regulation_version": item.get("regulation_version"),
            "clause": source.get("clause"),
            "source_page": source.get("page"),
            "source_text": source.get("original_text"),
            "input_values": {field: facts.get(field) for field in _used_fields(rule) if field},
            "status": execution.get("status"),
            "audit_status": _audit_status(rule, execution.get("status")),
            "execution": execution,
        }
        results.append(result)
    counts = Counter(item["audit_status"] for item in results)
    return {
        "format_version": "dynamic_regulation_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "published_rule_count": len(rules),
        "summary": {
            "compliant": counts["compliant"],
            "non_compliant": counts["non_compliant"],
            "triggered": counts["triggered"],
            "not_triggered": counts["not_triggered"],
            "derived": counts["derived"],
            "insufficient_data": counts["insufficient_data"],
            "not_applicable": counts["not_applicable"],
            "error": counts["error"],
        },
        "results": results,
        "derived_values": {
            item["execution"]["derived_field"]: item["execution"].get("derived_value")
            for item in results if item["audit_status"] == "derived"
        },
    }


def dynamic_opinions(audit: dict[str, Any]) -> list[dict[str, Any]]:
    opinions = []
    for item in audit.get("results") or []:
        # Missing optional inputs across unrelated rules are not review opinions.
        # Only definite failures and requirements actually triggered by this case
        # should be surfaced to users; RAG reports list genuinely critical gaps.
        if item.get("audit_status") not in {"non_compliant", "triggered"}:
            continue
        execution = item.get("execution") or {}
        if item["audit_status"] == "non_compliant":
            conclusion = f"不符合《{item['regulation_title']}》{item.get('clause') or '相关条文'}：{execution.get('calculation') or execution.get('message') or item['rule_name']}"
        elif item["audit_status"] == "triggered":
            action = "、".join(ACTION_LABELS.get(key, key) for key, value in (execution.get("action") or {}).items() if value) or item["rule_name"]
            conclusion = f"根据《{item['regulation_title']}》{item.get('clause') or '相关条文'}，本案例已触发：{action}。"
        opinions.append({
            "topic": item.get("rule_name"),
            "review_status": "requires_revision" if item["audit_status"] == "non_compliant" else "requirement_triggered",
            "conclusion": conclusion,
            "result": item["audit_status"],
            "function": f"dynamic_rule:{item['rule_id']}",
            "regulation_clauses": [f"{item['regulation_title']} {item.get('clause') or ''}".strip()],
            "inputs": execution.get("inputs") or {},
            "calculation_steps": [execution.get("calculation")] if execution.get("calculation") else [],
            "missing_fields": execution.get("missing_fields") or [],
            "review_notes": [item.get("source_text")] if item.get("source_text") else [],
            "rule_id": item["rule_id"],
            "rule_type": item["rule_type"],
        })
    return opinions


def render_dynamic_audit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# 知识库动态规程审核结果", "",
        f"- 已执行发布规则：{audit['published_rule_count']} 条",
        f"- 符合：{summary['compliant']} 条",
        f"- 不符合：{summary['non_compliant']} 条",
        f"- 触发评估/监测等要求：{summary['triggered']} 条",
        f"- 资料不足：{summary['insufficient_data']} 条", "",
    ]
    for index, item in enumerate(audit.get("results") or [], 1):
        execution = item.get("execution") or {}
        lines.extend([
            f"## {index}. {item['rule_name']}", "",
            f"- 审核状态：`{item['audit_status']}`（执行状态：`{item['status']}`）",
            f"- 审核规则：`{item['rule_id']}`（{item['rule_type']}）",
            f"- 规程：{item['regulation_title']} {item.get('regulation_version') or ''}",
            f"- 条文：{item.get('clause') or '未标注'}",
        ])
        if execution.get("calculation"):
            lines.append(f"- 计算/判断：{execution['calculation']}")
        if execution.get("missing_fields"):
            lines.append("- 缺少字段：" + "、".join(execution["missing_fields"]))
        if item.get("source_text"):
            lines.append(f"- 条文原文：{item['source_text']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_dynamic_audit(audit: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / "dynamic_regulation_audit.json"
    md_path = folder / "dynamic_regulation_audit.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_dynamic_audit_markdown(audit), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}
