import argparse
import json
from pathlib import Path

from common import ensure_dir, write_json


DEFAULT_RULE_FIELDS = [
    "case_name",
    "case_type",
    "project_name",
    "project_location",
    "construction_unit",
    "metro_line_name",
    "metro_section_name",
    "metro_asset_type",
    "metro_structure_method",
    "is_in_control_protection_zone",
    "is_in_special_protection_zone",
    "minimum_horizontal_clearance",
    "minimum_vertical_clearance",
    "relative_position",
    "control_zone_intrusion_length",
    "special_zone_intrusion_length",
    "main_external_work_type",
    "external_work_types",
    "pit_involved",
    "pit_depth",
    "pit_length",
    "pit_width",
    "pit_area",
    "distance_pit_edge_to_metro",
    "pit_position_relative_to_metro",
    "whether_pit_crosses_metro",
    "whether_pit_above_metro",
    "whether_side_pit",
    "support_method",
    "support_system_type",
    "dewatering_type",
    "dewatering_depth",
    "soil_layers",
    "main_soil_near_metro",
    "groundwater_type",
    "calculation_methods",
    "software_used",
    "calculation_result_summary",
    "max_metro_vertical_displacement",
    "max_metro_horizontal_displacement",
    "max_metro_differential_settlement",
    "max_building_settlement",
    "max_building_differential_settlement",
    "max_building_tilt",
    "monitoring_required",
    "monitoring_requirements",
    "protection_scheme_required",
    "protection_scheme_provided",
    "measure_for_excavation",
    "measure_for_support",
    "measure_for_dewatering",
    "measure_for_emergency",
    "overall_conclusion",
    "final_review_opinion",
]


def load_case(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compact_values(attributes, fields, include_all_filled):
    if include_all_filled:
        return {key: value for key, value in attributes.items() if value is not None}
    return {key: attributes.get(key) for key in fields if attributes.get(key) is not None}


def make_confirmed_items(values):
    items = []
    if values.get("is_in_control_protection_zone") is True:
        items.append("位于控制保护区")
    if values.get("is_in_special_protection_zone") is True:
        items.append("位于特别保护区")
    if values.get("metro_asset_type"):
        items.append(f"轨道交通设施类型={values['metro_asset_type']}")
    if values.get("metro_structure_method"):
        items.append(f"轨道交通结构形式={values['metro_structure_method']}")
    if values.get("main_external_work_type"):
        items.append(f"外部作业类型={values['main_external_work_type']}")
    if values.get("pit_depth"):
        items.append(f"基坑深度={values['pit_depth']}")
    if values.get("support_method"):
        items.append(f"支护方法={values['support_method']}")
    if values.get("dewatering_type"):
        items.append(f"降水方式={values['dewatering_type']}")
    if values.get("minimum_horizontal_clearance"):
        items.append(f"最小水平净距={values['minimum_horizontal_clearance']}")
    if values.get("minimum_vertical_clearance"):
        items.append(f"最小竖向净距={values['minimum_vertical_clearance']}")
    return items


def collect_sources(case_data, values):
    detail = case_data.get("field_detail", [])
    if isinstance(detail, dict):
        detail = [{"field_name": key, **value} for key, value in detail.items()]
    sources = []
    wanted = set(values)
    for item in detail:
        field = item.get("field_name")
        if field in wanted and item.get("value") is not None:
            sources.append(
                {
                    "field_name": field,
                    "source_file": item.get("source_file"),
                    "source_page": item.get("source_page"),
                    "source_paragraph": item.get("source_paragraph"),
                    "source_text": item.get("source_text"),
                    "confidence": item.get("confidence"),
                }
            )
    return sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_json_dir")
    parser.add_argument("-o", "--output", default="outputs/rule_json")
    parser.add_argument(
        "--include-all-filled",
        action="store_true",
        help="Include every non-null extracted attribute instead of only the default rule fields.",
    )
    args = parser.parse_args()

    out_dir = Path(args.output)
    ensure_dir(out_dir)

    for path in Path(args.case_json_dir).glob("*.case.json"):
        case_data = load_case(path)
        values = compact_values(
            case_data.get("attributes", {}),
            DEFAULT_RULE_FIELDS,
            args.include_all_filled,
        )
        result = {
            "format_version": "rule_check_input_v1",
            "doc_id": case_data.get("doc_id"),
            "source_file": case_data.get("source_file"),
            "measured_values": values,
            "confirmed_items": make_confirmed_items(values),
            "notes": [],
            "sources": collect_sources(case_data, values),
        }
        out_path = out_dir / path.name.replace(".case.json", ".rule.json")
        write_json(out_path, result)
        print(f"rule json: {out_path.name}, fields={len(values)}")


if __name__ == "__main__":
    main()
