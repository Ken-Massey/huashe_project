import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

from common import ensure_dir, write_json


def load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def iter_clause_functions(module):
    for name in sorted(dir(module)):
        if name.startswith("clause_") and callable(getattr(module, name)):
            yield name, getattr(module, name)


def result_to_dict(result):
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if isinstance(result, dict):
        return result
    return {"raw_result": str(result)}


def filled_attributes(case_data):
    return {
        key: value
        for key, value in (case_data.get("attributes") or {}).items()
        if value is not None and value != ""
    }


def has_any(values, keys):
    return any(values.get(key) not in (None, "", []) for key in keys)


def text_has(text, words):
    return any(word in text for word in words)


def parse_number(value):
    if value is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else None


def evidence(values, keys):
    return {key: values.get(key) for key in keys if values.get(key) not in (None, "", [])}


def base_notes(*items):
    return [item for item in items if item]


def set_decision(item, *, status, applicable, result, audit_basis, evidence_fields=None, notes=None):
    item["status"] = status
    item["applicable"] = applicable
    item["result"] = result
    item["audit_basis"] = audit_basis
    item["audit_evidence"] = evidence_fields or {}
    item["notes"] = notes or []
    return item


def is_major_impact(values):
    level = str(values.get("impact_level") or values.get("external_work_impact_level") or "")
    major = values.get("whether_major_impact_work")
    return major is True or any(token in level for token in ["特级", "一级", "重大"])


def is_control_zone_case(values):
    return values.get("is_in_control_protection_zone") is True


def is_special_zone_case(values):
    return values.get("is_in_special_protection_zone") is True


def is_pit_case(values):
    work_type = str(values.get("main_external_work_type") or values.get("external_work_types") or "")
    return bool(values.get("pit_depth") or values.get("pit_involved") is True or "基坑" in work_type)


def has_assessment(values):
    return has_any(values, ["calculation_methods", "software_used", "calculation_result_summary", "overall_conclusion", "final_review_opinion"])


def has_calculation(values):
    return has_any(
        values,
        [
            "calculation_methods",
            "software_used",
            "max_metro_vertical_displacement",
            "max_metro_horizontal_displacement",
            "max_metro_differential_settlement",
            "calculation_result_summary",
        ],
    )


def has_monitoring(values):
    return values.get("monitoring_required") is True or has_any(values, ["monitoring_requirements", "monitoring_items", "monitoring_frequency"])


def has_protection(values):
    return has_any(
        values,
        [
            "protection_scheme_required",
            "protection_scheme_provided",
            "measure_for_excavation",
            "measure_for_support",
            "measure_for_dewatering",
            "measure_for_emergency",
            "overall_conclusion",
            "final_review_opinion",
        ],
    )


def has_investigation(values):
    return has_any(
        values,
        [
            "geological_condition_summary",
            "soil_layers",
            "main_soil_near_metro",
            "groundwater_type",
            "existing_condition_summary",
            "metro_structure_condition",
        ],
    )


def unrelated_clause(title, values):
    title = title or ""
    relation_rules = [
        ("接口", ["interface_modification_involved", "interface_modification_type"]),
        ("爆破", ["blasting_involved", "vibration_velocity"]),
        ("油气", ["oil_gas_pipeline_involved"]),
        ("燃气", ["gas_pipeline_involved"]),
        ("天然气", ["gas_pipeline_involved"]),
        ("加油", ["gas_station_involved"]),
        ("加气", ["gas_station_involved"]),
        ("高压电力", ["high_voltage_power_involved"]),
        ("架空电力", ["overhead_power_line_involved"]),
        ("水下", ["underwater_work_involved"]),
        ("采砂", ["underwater_work_involved"]),
        ("抛锚", ["underwater_work_involved"]),
        ("拖锚", ["underwater_work_involved"]),
        ("拆除", ["demolition_involved"]),
        ("注浆", ["grouting_involved"]),
        ("旋喷", ["jet_grouting_involved"]),
        ("桩", ["pile_foundation_involved", "pile_type"]),
        ("顶管", ["pipe_jacking_involved"]),
        ("矿山法", ["mining_tunnel_involved"]),
        ("隧道工程", ["tunnel_work_involved"]),
        ("接口改造", ["interface_modification_involved", "interface_modification_type"]),
        ("病害", ["existing_disease_type", "disease_level", "underground_structure_disease"]),
    ]
    for word, fields in relation_rules:
        if word in title and not has_any(values, fields):
            return True, f"未抽取到与“{word}”相关的案例属性，判定该专项条文暂不适用。"
    return False, ""


def auto_evaluate(item, values):
    clause = str(item.get("clause", ""))
    title = str(item.get("title") or item.get("basis") or "")

    # Terms and scope clauses are reference clauses, not project compliance checks.
    if clause.startswith("2."):
        return set_decision(
            item,
            status="not_applicable",
            applicable=False,
            result="术语定义条文不作为单个案例的合规性审核项。",
            audit_basis="chapter_2_terms",
        )

    unrelated, reason = unrelated_clause(title, values)
    if unrelated:
        return set_decision(
            item,
            status="not_applicable",
            applicable=False,
            result=reason,
            audit_basis="keyword_non_applicability",
        )

    if clause in {"1.0.1", "1.0.2", "1.0.3"}:
        ok = has_any(values, ["metro_asset_type", "metro_line_name", "main_external_work_type"])
        return set_decision(
            item,
            status="compliant" if ok else "pending_review",
            applicable=True,
            result="案例涉及城市轨道交通结构安全保护，属于规程适用范围。" if ok else "缺少轨道交通结构或外部作业信息，需复核是否适用。",
            audit_basis="scope_check",
            evidence_fields=evidence(values, ["metro_asset_type", "metro_line_name", "main_external_work_type"]),
        )

    if clause in {"3.1.3", "4.1.1"}:
        if not is_control_zone_case(values):
            return set_decision(item, status="not_applicable", applicable=False, result="未位于控制保护区，条文条件未触发。", audit_basis="control_zone_applicability")
        ok = has_investigation(values) and has_protection(values)
        missing = []
        if not has_investigation(values):
            missing.append("现状/地质水文/环境调查信息")
        if not has_protection(values):
            missing.append("结构安全保护方案或保护措施")
        return set_decision(
            item,
            status="compliant" if ok else "non_compliant",
            applicable=True,
            result="控制保护区内外部作业已抽取到调查信息和保护措施。" if ok else "控制保护区内外部作业缺少：" + "、".join(missing),
            audit_basis="control_zone_investigation_protection",
            evidence_fields=evidence(values, ["is_in_control_protection_zone", "soil_layers", "groundwater_type", "measure_for_excavation", "overall_conclusion"]),
        )

    if clause == "4.1.2":
        if not is_major_impact(values):
            return set_decision(item, status="not_applicable", applicable=False, result="未识别为重大影响外部作业。", audit_basis="major_impact_applicability")
        ok = has_assessment(values) and has_monitoring(values) and has_protection(values)
        return set_decision(
            item,
            status="compliant" if ok else "pending_review",
            applicable=True,
            result="重大影响外部作业已抽取到评估、监测和保护措施。" if ok else "疑似重大影响外部作业，评估/监测/应急预案信息需复核。",
            audit_basis="major_impact_requirements",
            evidence_fields=evidence(values, ["calculation_methods", "monitoring_required", "measure_for_emergency", "overall_conclusion"]),
        )

    if clause in {"3.1.4", "3.1.5"}:
        keys = ["is_in_control_protection_zone", "is_in_special_protection_zone", "control_zone_intrusion_length", "special_zone_intrusion_length"]
        ok = has_any(values, keys)
        return set_decision(
            item,
            status="compliant" if ok else "pending_review",
            applicable=True,
            result="已抽取保护区/特别保护区空间关系信息。" if ok else "缺少保护区或特别保护区空间关系信息。",
            audit_basis="protection_zone_relation",
            evidence_fields=evidence(values, keys),
        )

    if clause in {"3.2.1", "3.2.2", "3.2.3", "3.2.4", "3.2.5", "3.2.6"}:
        if clause == "3.2.2" and not is_pit_case(values):
            return set_decision(item, status="not_applicable", applicable=False, result="未识别为基坑/隧道类外部作业。", audit_basis="work_type_applicability")
        if has_any(values, ["impact_level", "external_work_impact_level"]):
            status = "compliant"
            result = "已抽取外部作业影响等级。"
        else:
            status = "pending_review"
            result = "未抽取影响等级，需按作业特点、空间关系、结构类型、地质水文条件复核。"
        return set_decision(
            item,
            status=status,
            applicable=True,
            result=result,
            audit_basis="impact_level_check",
            evidence_fields=evidence(values, ["main_external_work_type", "pit_depth", "minimum_horizontal_clearance", "metro_asset_type", "soil_layers"]),
        )

    if clause.startswith("3.3."):
        if has_any(values, ["minimum_horizontal_clearance", "minimum_vertical_clearance"]):
            status = "compliant"
            result = "已抽取外部作业与轨道交通结构净距，可进入净距控制值复核。"
        else:
            status = "pending_review"
            result = "未抽取净距，需人工复核是否满足净距控制值。"
        return set_decision(
            item,
            status=status,
            applicable=True,
            result=result,
            audit_basis="clearance_check",
            evidence_fields=evidence(values, ["minimum_horizontal_clearance", "minimum_vertical_clearance", "relative_position"]),
        )

    if clause.startswith("3.4.") or clause.startswith("4.3."):
        ok = has_calculation(values)
        return set_decision(
            item,
            status="compliant" if ok else "pending_review",
            applicable=True,
            result="已抽取计算/评估方法或结构变形计算结果。" if ok else "缺少计算分析或结构安全控制指标结果，需复核。",
            audit_basis="calculation_assessment_check",
            evidence_fields=evidence(
                values,
                [
                    "calculation_methods",
                    "software_used",
                    "max_metro_vertical_displacement",
                    "max_metro_horizontal_displacement",
                    "max_metro_differential_settlement",
                    "overall_conclusion",
                ],
            ),
        )

    if clause.startswith("4.4.3") and values.get("dewatering_type"):
        return set_decision(
            item,
            status="compliant" if has_protection(values) else "pending_review",
            applicable=True,
            result="存在降水作业，已抽取降水方式；需结合净距和专项方案复核。" if has_protection(values) else "存在降水作业，但未抽取明确保护措施。",
            audit_basis="dewatering_drilling_work",
            evidence_fields=evidence(values, ["dewatering_type", "minimum_horizontal_clearance", "measure_for_dewatering", "measure_for_excavation"]),
        )

    if clause.startswith("7."):
        if not is_control_zone_case(values):
            return set_decision(item, status="not_applicable", applicable=False, result="未位于控制保护区，监测条文条件未触发。", audit_basis="monitoring_applicability")
        ok = has_monitoring(values)
        return set_decision(
            item,
            status="compliant" if ok else "non_compliant",
            applicable=True,
            result="控制保护区内外部作业已抽取到安全监测要求。" if ok else "控制保护区内外部作业未抽取到安全监测要求。",
            audit_basis="monitoring_required_check",
            evidence_fields=evidence(values, ["monitoring_required", "monitoring_requirements", "main_external_work_type", "pit_depth"]),
        )

    if clause.startswith("8."):
        if not has_any(values, ["existing_disease_type", "disease_level", "underground_structure_disease"]):
            return set_decision(item, status="not_applicable", applicable=False, result="未抽取到既有结构病害信息，病害治理条文暂不适用。", audit_basis="disease_applicability")

    # Generic applicable project clauses.
    if text_has(title, ["安全评估", "保护方案", "保护措施"]):
        ok = has_assessment(values) or has_protection(values)
        return set_decision(
            item,
            status="compliant" if ok else "pending_review",
            applicable=True,
            result="已抽取安全评估结论或保护措施。" if ok else "未抽取足够安全评估或保护措施信息。",
            audit_basis="generic_assessment_protection",
            evidence_fields=evidence(values, ["overall_conclusion", "final_review_opinion", "measure_for_excavation"]),
        )

    return set_decision(
        item,
        status="pending_review",
        applicable=True,
        result="当前属性不足以自动判断该条文，需人工复核。",
        audit_basis="no_specific_auto_rule",
        evidence_fields={},
        notes=base_notes("可继续补充该条文与案例属性之间的映射规则。"),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_json_dir")
    parser.add_argument("--chapter-dir", default="../chapter_1_functions")
    parser.add_argument("-o", "--output", default="outputs/auto_audit_results")
    args = parser.parse_args()

    out_dir = Path(args.output)
    ensure_dir(out_dir)

    modules = []
    module_errors = []
    for chapter_file in sorted(Path(args.chapter_dir).glob("chapter_*_functions.py")):
        try:
            modules.append((chapter_file.name, load_module(chapter_file)))
        except Exception as exc:
            module_errors.append({"module_file": str(chapter_file), "error": repr(exc)})

    for case_path in Path(args.case_json_dir).glob("*.case.json"):
        case_data = json.loads(case_path.read_text(encoding="utf-8"))
        values = filled_attributes(case_data)
        clause_results = []
        call_errors = []
        confirmed_items = case_data.get("confirmed_items") or []

        for module_file, module in modules:
            for function_name, function in iter_clause_functions(module):
                try:
                    raw = function(
                        applicable=True,
                        confirmed_items=confirmed_items,
                        measured_values=values,
                        notes=[],
                        strict=False,
                    )
                    item = result_to_dict(raw)
                    item["module_file"] = module_file
                    item["function"] = function_name
                    clause_results.append(auto_evaluate(item, values))
                except Exception as exc:
                    call_errors.append({"module_file": module_file, "function": function_name, "error": repr(exc)})

        summary = {}
        for item in clause_results:
            status = item.get("status", "unknown")
            summary[status] = summary.get(status, 0) + 1

        output = {
            "format_version": "auto_rule_audit_v1",
            "doc_id": case_data.get("doc_id"),
            "source_case_json": str(case_path),
            "summary": summary,
            "filled_attribute_count": len(values),
            "key_measured_values": {
                key: values.get(key)
                for key in [
                    "project_name",
                    "metro_line_name",
                    "metro_asset_type",
                    "is_in_control_protection_zone",
                    "is_in_special_protection_zone",
                    "main_external_work_type",
                    "pit_depth",
                    "minimum_horizontal_clearance",
                    "monitoring_required",
                    "overall_conclusion",
                ]
                if values.get(key) is not None
            },
            "module_load_errors": module_errors,
            "call_errors": call_errors,
            "clause_results": clause_results,
        }
        out_path = out_dir / case_path.name.replace(".case.json", ".auto_audit.json")
        write_json(out_path, output)
        print(f"auto audit: {out_path.name}, clauses={len(clause_results)}, summary={summary}")


if __name__ == "__main__":
    main()
