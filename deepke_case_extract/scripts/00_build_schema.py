import argparse
import re
from common import read_docx_paragraphs, write_json


CORE_FIELD_PLAN = {
    "Case": ["case_name", "case_type", "project_stage", "report_type", "final_conclusion", "risk_level"],
    "ProjectInfo": ["project_name", "construction_unit", "design_unit", "assessment_unit", "project_location", "total_land_area", "total_building_area", "underground_area", "foundation_type", "project_schedule"],
    "MetroAsset": ["metro_line_name", "metro_section_name", "metro_asset_type", "metro_operation_status", "metro_structure_method", "metro_buried_depth", "metro_special_section"],
    "SpatialRelation": ["is_in_control_protection_zone", "is_in_special_protection_zone", "control_zone_intrusion_length", "special_zone_intrusion_length", "minimum_horizontal_clearance", "minimum_vertical_clearance", "relation_type", "relative_position", "nearest_metro_asset"],
    "ExternalWork": ["external_work_type", "case_type"],
    "ExcavationWork": ["pit_depth", "pit_size", "excavation_method", "excavation_sequence"],
    "RetainingSupportSystem": ["support_type", "retaining_structure_type"],
    "DewateringWork": ["dewatering_type", "groundwater_type", "dewatering_stop_condition"],
    "GeologyHydrology": ["soil_layer", "groundwater_level", "soft_soil_involved", "sand_layer_involved"],
    "AssessmentCalculation": ["calculation_method", "software_name", "max_settlement", "max_horizontal_displacement", "max_differential_settlement", "max_tilt"],
    "MonitoringPlan": ["monitoring_required", "monitoring_items", "monitoring_frequency", "alarm_thresholds"],
    "ProtectionMeasures": ["protection_scheme_required", "protection_measures", "measure_for_excavation", "measure_for_support", "measure_for_dewatering", "measure_for_backfill", "measure_for_emergency"],
    "ReviewConclusion": ["overall_conclusion", "main_risks", "construction_restrictions", "monitoring_requirements", "final_review_opinion"],
}


def build_schema(paragraph_rows):
    paragraphs = [r["text"] for r in paragraph_rows]
    modules = {}
    current = None
    for i, text in enumerate(paragraphs):
        m = re.match(r"^([A-Za-z][A-Za-z0-9_]+)\s+[\u4e00-\u9fff].*$", text)
        if m and text not in {"属性名", "中文含义"}:
            current = m.group(1)
            modules.setdefault(current, {})
            continue
        if current and re.match(r"^[a-z][a-z0-9_]*$", text):
            field = text
            meaning = paragraphs[i + 1] if i + 1 < len(paragraphs) else ""
            modules[current][field] = {
                "field": field,
                "meaning": meaning,
                "core": field in CORE_FIELD_PLAN.get(current, []),
            }

    core_modules = {}
    for module, fields in modules.items():
        selected = {k: v for k, v in fields.items() if v["core"]}
        if selected:
            core_modules[module] = selected
    return {"modules": modules, "core_modules": core_modules, "core_field_plan": CORE_FIELD_PLAN}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("schema_docx")
    parser.add_argument("-o", "--output", default="data/schema/case_schema.json")
    args = parser.parse_args()
    schema = build_schema(read_docx_paragraphs(args.schema_docx))
    write_json(args.output, schema)
    print(f"schema saved: {args.output}")
    print(f"modules={len(schema['modules'])}, core_modules={len(schema['core_modules'])}")


if __name__ == "__main__":
    main()

