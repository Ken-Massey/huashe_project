import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

from common import ensure_dir, write_json
from source_truth_rules import evaluate_clause


TOPIC_RULES = [
    {
        "topic": "轨道交通结构基本信息",
        "fields": ["metro_line_name", "metro_section_name", "metro_asset_type", "metro_structure_method"],
        "keywords": ["轨道", "地铁", "盾构", "区间", "车站", "结构"],
        "clause_prefixes": ["1.", "3.1"],
    },
    {
        "topic": "控制保护区/特别保护区空间关系",
        "fields": [
            "is_in_control_protection_zone",
            "is_in_special_protection_zone",
            "control_zone_intrusion_length",
            "special_zone_intrusion_length",
            "minimum_horizontal_clearance",
            "minimum_vertical_clearance",
        ],
        "keywords": ["控制保护区", "特别保护区", "净距", "距离", "邻近", "穿越", "侵入"],
        "clause_prefixes": ["3.1", "4.1"],
    },
    {
        "topic": "基坑工程",
        "fields": [
            "main_external_work_type",
            "external_work_types",
            "pit_involved",
            "pit_length",
            "pit_width",
            "pit_depth",
            "support_method",
            "dewatering_type",
        ],
        "keywords": ["基坑", "开挖", "围护", "支护", "降水", "地下车库"],
        "clause_prefixes": ["3.2", "4.1", "5.", "6.", "7."],
    },
    {
        "topic": "结构计算与变形控制",
        "fields": [
            "calculation_methods",
            "software_used",
            "max_metro_vertical_displacement",
            "max_metro_horizontal_displacement",
            "max_metro_differential_settlement",
            "max_building_tilt",
            "calculation_result_summary",
        ],
        "keywords": ["计算", "模型", "MIDAS", "GTS", "位移", "沉降", "倾斜", "变形"],
        "clause_prefixes": ["4.", "6.", "7."],
    },
    {
        "topic": "监测要求",
        "fields": [
            "monitoring_required",
            "monitoring_items",
            "monitoring_frequency",
            "monitoring_alarm_value",
            "monitoring_requirements",
        ],
        "keywords": ["监测", "报警", "频率", "变形监测", "沉降监测"],
        "clause_prefixes": ["4.", "7.", "8."],
    },
    {
        "topic": "保护措施与施工控制",
        "fields": [
            "protection_scheme_required",
            "protection_scheme_provided",
            "measure_for_excavation",
            "measure_for_support",
            "measure_for_dewatering",
            "measure_for_emergency",
            "overall_conclusion",
            "final_review_opinion",
        ],
        "keywords": ["保护措施", "施工控制", "应急", "专项方案", "停止降水", "封顶"],
        "clause_prefixes": ["4.", "5.", "6.", "7.", "8."],
    },
]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def non_empty(value):
    return value not in (None, "", [], {})


def filled_values(case_data):
    values = {}
    for source_key in ["attributes", "measured_values"]:
        for key, value in (case_data.get(source_key) or {}).items():
            if non_empty(value):
                values[key] = value
    payload_values = (case_data.get("rule_check_payload") or {}).get("measured_values") or {}
    for key, value in payload_values.items():
        if non_empty(value):
            values[key] = value
    values["__field_candidates__"] = case_data.get("field_candidates") or {}
    values["__all_evidence__"] = case_data.get("evidence") or []
    return values


def source_map(case_data):
    result = {}
    detail = case_data.get("field_detail") or []
    if isinstance(detail, dict):
        detail = [{"field_name": key, **value} for key, value in detail.items()]
    for item in detail:
        field = item.get("field_name")
        if not field or not non_empty(item.get("value")):
            continue
        result.setdefault(field, []).append(
            {
                "value": item.get("value"),
                "source_file": item.get("source_file"),
                "source_page": item.get("source_page"),
                "source_paragraph": item.get("source_paragraph"),
                "source_section": item.get("source_section"),
                "source_text": item.get("source_text"),
                "confidence": item.get("confidence"),
            }
        )
    for field, candidates in (case_data.get("field_candidates") or {}).items():
        for item in candidates:
            if not non_empty(item.get("value")):
                continue
            result.setdefault(field, []).append(
                {
                    "value": item.get("value"),
                    "source_file": item.get("source_file"),
                    "source_page": item.get("source_page"),
                    "source_paragraph": item.get("source_paragraph"),
                    "source_section": item.get("source_section"),
                    "source_text": item.get("source_text"),
                    "confidence": item.get("confidence"),
                }
            )
    return result


def build_confirmed_items(values, case_data):
    items = list((case_data.get("rule_check_payload") or {}).get("confirmed_items") or [])
    items.extend(case_data.get("confirmed_items") or [])
    for key, value in values.items():
        if str(key).startswith("__"):
            continue
        items.append(f"{key}={value}")
    return sorted(set(str(item) for item in items if str(item).strip()))


def text_blob(*parts):
    return "\n".join(str(part) for part in parts if part)


def clause_number_from_name(function_name):
    return function_name.replace("clause_", "").replace("_", ".")


def clause_matches_prefix(clause, prefixes):
    return any(str(clause).startswith(prefix) for prefix in prefixes)


def keyword_hit(text, keywords):
    return [word for word in keywords if word and word in text]


def load_mapping(path):
    if not path:
        return {}
    path = Path(path)
    if not path.exists():
        return {}
    data = load_json(path)
    return {item["function"]: item for item in data.get("mappings", [])}


def match_function(function_name, preview, values, mapping_by_function=None):
    clause = preview.get("clause") or clause_number_from_name(function_name)
    clause_text = text_blob(
        preview.get("title"),
        preview.get("basis"),
        " ".join(preview.get("requirements") or []),
    )
    value_text = text_blob(*[f"{key}={value}" for key, value in values.items() if not str(key).startswith("__")])
    all_text = f"{clause_text}\n{value_text}"

    mapping = (mapping_by_function or {}).get(function_name)
    if mapping:
        matched_fields = [
            field for field in mapping.get("input_fields", [])
            if non_empty(values.get(field))
        ]
        matched_keywords = keyword_hit(all_text, mapping.get("trigger_keywords", []))
        if matched_fields:
            return [
                {
                    "topic": "、".join(mapping.get("topics", [])),
                    "matched_fields": matched_fields,
                    "matched_keywords": matched_keywords,
                    "clause_prefix_match": True,
                    "reason": "；".join(mapping.get("mapping_reason", []))
                    or "根据函数-属性映射表，当前案例存在该条文相关属性。",
                    "mapping_source": "rule_function_field_mapping.json",
                }
            ]

    matches = []
    for rule in TOPIC_RULES:
        matched_fields = [field for field in rule["fields"] if non_empty(values.get(field))]
        matched_keywords = keyword_hit(all_text, rule["keywords"])
        prefix_match = clause_matches_prefix(clause, rule["clause_prefixes"])
        if matched_fields and (matched_keywords or prefix_match):
            matches.append(
                {
                    "topic": rule["topic"],
                    "matched_fields": matched_fields,
                    "matched_keywords": matched_keywords,
                    "clause_prefix_match": prefix_match,
                    "reason": (
                        f"案例已抽取到{rule['topic']}相关属性，"
                        f"且条文编号或条文关键词与该主题匹配。"
                    ),
                }
            )

    if str(clause).startswith("1.0."):
        matches.append(
            {
                "topic": "总则适用范围",
                "matched_fields": [field for field in ["metro_asset_type", "main_external_work_type"] if non_empty(values.get(field))],
                "matched_keywords": [],
                "clause_prefix_match": True,
                "reason": "总则条文用于判断案例是否属于规程适用范围。",
            }
        )

    return matches


def preview_function(function):
    try:
        result = function(
            applicable=True,
            confirmed_items=[],
            measured_values={},
            notes=[],
            strict=False,
        )
        return result_to_dict(result)
    except Exception as exc:
        return {"preview_error": repr(exc)}


def call_function(function, confirmed_items, measured_values, strict):
    result = function(
        applicable=True,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=[],
        strict=strict,
    )
    return result_to_dict(result)


def apply_source_truth_rule(item, values):
    rule_result = evaluate_clause(item.get("clause"), values)
    if not rule_result:
        item["judgement_source"] = "chapter_function"
        return item

    item["chapter_function_status"] = item.get("status")
    item["chapter_function_result"] = item.get("result")
    item["source_truth_rule"] = rule_result
    item["judgement_source"] = "source_truth_rule"
    item["status"] = rule_result["source_rule_status"]
    item["result"] = rule_result["source_rule_result"]
    item["audit_basis"] = rule_result["source_rule_basis"]
    item["audit_evidence"] = rule_result.get("source_rule_evidence", {})
    if item["status"] == "non_compliant":
        item["non_compliant_explanation"] = {
            "reason": rule_result["source_rule_result"],
            "missing_items": rule_result.get("source_rule_missing_fields", []),
            "related_attributes": rule_result.get("source_rule_evidence", {}),
            "basis": rule_result["source_rule_basis"],
            "source_file": rule_result["source_rule_source_file"],
        }
    return item


def audit_one(case_path, chapter_dir, output_dir, strict=False, include_skipped=True, mapping_path=None):
    case_data = load_json(case_path)
    values = filled_values(case_data)
    sources = source_map(case_data)
    confirmed_items = build_confirmed_items(values, case_data)
    mapping_by_function = load_mapping(mapping_path)

    modules = []
    module_errors = []
    for chapter_file in sorted(Path(chapter_dir).glob("chapter_*_functions.py")):
        try:
            modules.append((chapter_file.name, load_module(chapter_file)))
        except Exception as exc:
            module_errors.append({"module_file": str(chapter_file), "error": repr(exc)})

    called_results = []
    skipped_results = []
    call_errors = []

    for module_file, module in modules:
        for function_name, function in iter_clause_functions(module):
            preview = preview_function(function)
            matches = match_function(function_name, preview, values, mapping_by_function)
            if not matches:
                if include_skipped:
                    skipped_results.append(
                        {
                            "module_file": module_file,
                            "function": function_name,
                            "clause": preview.get("clause") or clause_number_from_name(function_name),
                            "title": preview.get("title"),
                            "skip_reason": "未匹配到与本案例已抽取属性相关的关键词或条文编号主题。",
                        }
                    )
                continue

            try:
                item = call_function(function, confirmed_items, values, strict)
                item = apply_source_truth_rule(item, values)
                matched_fields = sorted(
                    set(field for match in matches for field in match.get("matched_fields", []))
                )
                item["module_file"] = module_file
                item["function"] = function_name
                item["match_reason"] = matches
                item["matched_fields"] = matched_fields
                item["matched_field_values"] = {field: values.get(field) for field in matched_fields}
                item["matched_field_sources"] = {field: sources.get(field, []) for field in matched_fields}
                if item.get("status") == "non_compliant" and not item.get("non_compliant_explanation"):
                    item["non_compliant_explanation"] = {
                        "reason": item.get("result"),
                        "missing_items": item.get("missing_items", []),
                        "related_attributes": item["matched_field_values"],
                    }
                called_results.append(item)
            except Exception as exc:
                call_errors.append(
                    {
                        "module_file": module_file,
                        "function": function_name,
                        "matches": matches,
                        "error": repr(exc),
                    }
                )

    summary = {
        "called": len(called_results),
        "skipped": len(skipped_results),
        "call_errors": len(call_errors),
    }
    for item in called_results:
        status = item.get("status", "unknown")
        summary[status] = summary.get(status, 0) + 1

    output = {
        "format_version": "matched_rule_audit_v1",
        "doc_id": case_data.get("doc_id"),
        "source_case_json": str(case_path),
        "strict": strict,
        "mapping_file": str(mapping_path) if mapping_path else None,
        "summary": summary,
        "filled_attribute_count": len([key for key in values if not str(key).startswith("__")]),
        "measured_values": {key: value for key, value in values.items() if not str(key).startswith("__")},
        "module_load_errors": module_errors,
        "call_errors": call_errors,
        "called_clause_results": called_results,
        "non_compliant_results": [
            item for item in called_results if item.get("status") == "non_compliant"
        ],
        "skipped_clause_results": skipped_results,
    }
    out_path = Path(output_dir) / Path(case_path).name.replace(".case.json", ".matched_audit.json")
    write_json(out_path, output)
    print(f"matched audit: {out_path}, summary={summary}")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Match final_json attributes to chapter rule functions, call matched functions, and explain the result."
    )
    parser.add_argument("case_json", help="*.case.json file or folder containing case JSON files.")
    parser.add_argument("--chapter-dir", default="../chapter_1_functions", help="Folder containing chapter_*_functions.py.")
    parser.add_argument("-o", "--output", default="outputs/matched_rule_audit", help="Output folder.")
    parser.add_argument(
        "--mapping",
        default="data/schema/rule_function_field_mapping.json",
        help="函数-属性映射表。默认使用 data/schema/rule_function_field_mapping.json。",
    )
    parser.add_argument("--strict", action="store_true", help="Use strict mode. Missing requirement items become non_compliant.")
    parser.add_argument("--no-skipped", action="store_true", help="Do not write skipped clause details.")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    case_input = Path(args.case_json)
    if not case_input.is_absolute():
        case_input = (project_root / case_input).resolve()

    chapter_dir = Path(args.chapter_dir)
    if not chapter_dir.is_absolute():
        chapter_dir = (project_root / chapter_dir).resolve()

    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = (project_root / output_dir).resolve()
    ensure_dir(output_dir)

    mapping_path = Path(args.mapping) if args.mapping else None
    if mapping_path and not mapping_path.is_absolute():
        mapping_path = (project_root / mapping_path).resolve()

    if case_input.is_dir():
        case_files = sorted(case_input.glob("*.case.json"))
    else:
        case_files = [case_input]
    if not case_files:
        raise FileNotFoundError(f"No *.case.json found: {case_input}")

    for case_path in case_files:
        audit_one(
            case_path=case_path,
            chapter_dir=chapter_dir,
            output_dir=output_dir,
            strict=args.strict,
            include_skipped=not args.no_skipped,
            mapping_path=mapping_path,
        )


if __name__ == "__main__":
    main()
