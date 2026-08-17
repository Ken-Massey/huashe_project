import argparse
from pathlib import Path
from common import ensure_dir, read_jsonl, write_json
import json
import re


FIELD_ALIASES = {
    # First-stage extractor names -> fields defined in case_schema.json.
    "external_work_type": "main_external_work_type",
    "calculation_method": "calculation_methods",
    "software_name": "software_used",
    "max_settlement": "max_metro_vertical_displacement",
    "max_horizontal_displacement": "max_metro_horizontal_displacement",
    "max_differential_settlement": "max_metro_differential_settlement",
    "max_tilt": "max_building_tilt",
    "support_type": "support_method",
    "soil_layer": "soil_layers",
    "protection_measures": "measure_for_excavation",
}


RULE_CHECK_FIELDS = [
    "metro_asset_type",
    "is_in_control_protection_zone",
    "is_in_special_protection_zone",
    "minimum_horizontal_clearance",
    "minimum_vertical_clearance",
    "pit_depth",
    "main_external_work_type",
    "support_method",
    "dewatering_type",
]


def load_schema_fields(schema_path):
    if not schema_path:
        return [], {}
    path = Path(schema_path)
    if not path.exists():
        return [], {}
    data = json.loads(path.read_text(encoding="utf-8"))
    fields = []
    field_modules = {}
    for module, module_fields in data.get("modules", {}).items():
        for field in module_fields:
            fields.append(field)
            field_modules[field] = module
    return fields, field_modules


def remap_field(field):
    return FIELD_ALIASES.get(field, field)


def expand_field(field, value):
    if field != "pit_size":
        return [(remap_field(field), value)]
    text = str(value or "")
    numbers = re.findall(r"\d+(?:\.\d+)?\s*m", text, flags=re.IGNORECASE)
    expanded = []
    if numbers:
        expanded.append(("pit_length", numbers[0].replace(" ", "")))
    if len(numbers) >= 2:
        expanded.append(("pit_width", numbers[1].replace(" ", "")))
    return expanded or [("work_scope", value)]


def empty_detail(field, field_modules):
    return {
        "field_name": field,
        "value": None,
        "module": field_modules.get(field),
        "source_file": None,
        "source_page": None,
        "source_paragraph": None,
        "source_section": None,
        "source_text": None,
        "confidence": 0.0,
        "extraction_method": None,
    }


def better(new, old):
    if old is None:
        return True
    field = new.get("field_name")
    if field in {
        "general_monitoring_required",
        "monitoring_sentence",
        "monitoring_object",
        "monitoring_items",
        "monitoring_requirements",
    }:
        def monitoring_score(item):
            text = str(item.get("source_text") or "")
            value = item.get("value")
            score = float(item.get("confidence", 0))
            if value is False:
                score += 0.50
            if "不对" in text or "不进行" in text or "未开展" in text or "不开展" in text:
                score += 0.45
            if any(word in text for word in ["加强", "开展", "进行", "应", "需", "须", "布设", "设置"]):
                score += 0.30
            if any(word in text for word in ["周边市政设施", "市政设施", "轨道交通", "地铁", "盾构区间", "区间结构", "隧道"]):
                score += 0.30
            if value == "未明确":
                score -= 0.60
            if "观测数据" in text or "预测模型" in text or "现状监测的基础上" in text:
                score -= 0.40
            return score

        ns = monitoring_score(new)
        os = monitoring_score(old)
        if ns != os:
            return ns > os
    nc = float(new.get("confidence", 0))
    oc = float(old.get("confidence", 0))
    if nc != oc:
        return nc > oc
    return len(str(new.get("source_text", ""))) < len(str(old.get("source_text", "")))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("normalized_dir")
    parser.add_argument("-o", "--output", default="outputs/final_json")
    parser.add_argument("--schema", default="data/schema/case_schema.json")
    parser.add_argument(
        "--include-null-schema-fields",
        action="store_true",
        default=True,
        help="Include every field from case_schema.json with null value when not extracted.",
    )
    args = parser.parse_args()
    ensure_dir(args.output)

    schema_fields, field_modules = load_schema_fields(args.schema)
    schema_field_set = set(schema_fields)

    for path in Path(args.normalized_dir).glob("*.normalized.jsonl"):
        rows = read_jsonl(path)
        field_detail = {}
        field_candidates = {}
        evidence = []
        extra_extracted_fields = []
        for row in rows:
            original_field = row["field_name"]
            raw_value = row.get("normalized_value", row.get("field_value"))
            for field, value in expand_field(original_field, raw_value):
                item = {
                    "field_name": field,
                    "value": value,
                    "module": row["module"],
                    "source_file": row["source_file"],
                    "source_page": row.get("source_page"),
                    "source_paragraph": row["source_paragraph"],
                    "source_section": row["source_section"],
                    "source_text": row["source_text"],
                    "confidence": row["confidence"],
                    "extraction_method": row["extraction_method"],
                }
                if original_field != field:
                    item["original_field_name"] = original_field
                if schema_field_set and field not in schema_field_set:
                    extra_extracted_fields.append({"original_field_name": original_field, **item})
                field_candidates.setdefault(field, []).append(item)
                if better(item, field_detail.get(field)):
                    field_detail[field] = item
                evidence.append(item)

        if schema_fields and args.include_null_schema_fields:
            ordered_fields = schema_fields + sorted(field for field in field_detail if field not in schema_field_set)
        else:
            ordered_fields = sorted(field_detail)

        attributes = {field: field_detail[field]["value"] if field in field_detail else None for field in ordered_fields}
        measured_values = dict(attributes)
        field_detail_list = [field_detail.get(field, empty_detail(field, field_modules)) for field in ordered_fields]
        sorted_candidates = {}
        for field, candidates in field_candidates.items():
            chosen = field_detail.get(field)
            ordered = []
            if chosen is not None:
                ordered.append(chosen)
            for item in candidates:
                if item is chosen:
                    continue
                ordered.append(item)
            sorted_candidates[field] = ordered
        low = [item for item in field_detail_list if item["value"] is not None and float(item["confidence"]) < 0.7]
        rule_payload = {k: attributes.get(k) for k in RULE_CHECK_FIELDS if k in attributes}
        result = {
            "format_version": "case_attribute_json_v2",
            "doc_id": rows[0]["doc_id"] if rows else path.stem,
            "source_file": rows[0].get("source_file") if rows else None,
            "schema_file": str(Path(args.schema)),
            "schema_field_count": len(schema_fields),
            "attributes": attributes,
            "measured_values": measured_values,
            "confirmed_items": [f"{field}={value}" for field, value in attributes.items() if value is not None],
            "field_detail": field_detail_list,
            "field_candidates": sorted_candidates,
            "evidence": evidence,
            "manual_review_required": low,
            "extra_extracted_fields": extra_extracted_fields,
            "schema_check_report": {
                "total_schema_fields": len(schema_fields),
                "filled_schema_fields": sum(1 for value in attributes.values() if value is not None),
                "extra_field_count": len(extra_extracted_fields),
                "extra_field_names": sorted({item["original_field_name"] for item in extra_extracted_fields}),
            },
            "rule_check_payload": {
                "measured_values": rule_payload,
                "confirmed_items": [f"{field}={value}" for field, value in rule_payload.items() if value is not None],
                "notes": [],
            },
        }
        out = Path(args.output) / path.name.replace(".normalized.jsonl", ".case.json")
        write_json(out, result)
        print(f"merged: {out.name}, filled_fields={result['schema_check_report']['filled_schema_fields']}")


if __name__ == "__main__":
    main()
