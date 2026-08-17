import argparse
import ast
import json
import re
from pathlib import Path

from common import ensure_dir, write_json


FIELD_GROUPS = {
    "case_basic": [
        "case_id",
        "case_name",
        "case_type",
        "project_stage",
        "report_type",
        "report_date",
        "city",
        "district",
        "final_conclusion",
        "risk_level",
    ],
    "project_info": [
        "project_name",
        "construction_unit",
        "design_unit",
        "assessment_unit",
        "project_location",
        "total_land_area",
        "total_building_area",
        "underground_area",
        "basement_floor_count",
        "basement_depth",
        "main_structure_type",
        "foundation_type",
        "project_schedule",
        "whether_existing_project",
        "whether_new_construction",
        "whether_demolition_involved",
    ],
    "metro_asset": [
        "metro_line_name",
        "metro_section_name",
        "metro_asset_type",
        "metro_operation_status",
        "metro_structure_method",
        "metro_structure_form",
        "metro_outer_diameter_or_width",
        "metro_buried_depth",
        "metro_track_depth",
        "metro_existing_condition",
        "metro_disease_status",
        "metro_monitoring_history",
        "metro_design_documents_available",
        "metro_as_built_documents_available",
    ],
    "spatial_relation": [
        "is_in_control_protection_zone",
        "is_in_special_protection_zone",
        "control_zone_intrusion_length",
        "special_zone_intrusion_length",
        "minimum_horizontal_clearance",
        "minimum_vertical_clearance",
        "minimum_3d_clearance",
        "relation_type",
        "crossing_angle",
        "parallel_length",
        "overlap_length",
        "relative_position",
        "nearest_metro_asset",
        "nearest_metro_ring_or_stationing",
        "distance_to_tunnel_outer_edge",
        "distance_to_station_outer_edge",
        "distance_to_auxiliary_structure",
        "whether_above_metro",
        "whether_below_metro",
        "whether_side_of_metro",
        "whether_crossing_metro",
        "whether_parallel_metro",
        "number_of_affected_lines",
        "number_of_affected_tunnels",
    ],
    "external_work": [
        "external_work_types",
        "main_external_work_type",
        "work_stage",
        "work_scope",
        "work_area",
        "work_depth",
        "work_length",
        "work_width",
        "work_duration",
        "construction_sequence",
        "whether_multiple_works",
        "whether_simultaneous_works",
        "whether_adjacent_projects",
        "whether_design_change",
        "whether_construction_change",
        "whether_major_impact_work",
        "impact_level",
        "impact_level_basis",
        "need_special_assessment",
        "need_expert_review",
    ],
    "impact_level": [
        "approach_degree",
        "engineering_influence_zone",
        "initial_impact_level",
        "adjusted_impact_level",
        "final_impact_level",
        "impact_level_adjustment_reasons",
        "whether_level_raised_due_to_geology",
        "whether_level_raised_due_to_confined_water",
        "whether_level_raised_due_to_existing_disease",
        "whether_level_raised_due_to_large_pit",
        "whether_special_grade",
        "whether_first_grade",
        "whether_second_grade",
        "whether_major_impact_work",
    ],
    "load_change": [
        "load_change_type",
        "unloading_area",
        "unloading_depth",
        "unloading_volume",
        "estimated_unloading_value",
        "loading_area",
        "additional_load_value",
        "temporary_stack_load",
        "construction_vehicle_load",
        "heavy_equipment_load",
        "whether_large_area_unloading",
        "whether_above_metro_unloading",
        "whether_above_metro_loading",
        "distance_from_load_change_to_metro",
        "load_change_duration",
        "backfill_material",
        "backfill_compaction_requirement",
        "whether_load_change_calculated",
        "calculated_additional_stress",
        "calculated_metro_deformation",
        "control_measure",
    ],
    "foundation_pile": [
        "foundation_type",
        "pile_involved",
        "pile_type",
        "pile_diameter",
        "pile_length",
        "pile_spacing",
        "pile_count",
        "pile_tip_elevation",
        "pile_tip_soil_layer",
        "pile_construction_method",
        "pile_soil_displacement_type",
        "minimum_clearance_pile_to_metro",
        "pile_tip_relation_to_tunnel",
        "pile_bottom_below_tunnel_bottom",
        "within_2d_range",
        "whether_rock_socketed_pile",
        "whether_friction_pile",
        "whether_test_pile",
        "test_pile_count",
        "pile_sequence",
        "whether_jump_piling",
        "whether_near_to_far_or_far_to_near",
        "whether_anti_squeezing_measure",
        "whether_casing_used",
        "whether_mud_wall_protection",
        "whether_hole_collapse_risk",
        "whether_pile_effect_assessed",
    ],
    "additional_settlement": [
        "whether_additional_settlement_considered",
        "building_load_model",
        "foundation_settlement_calculation_method",
        "predicted_total_settlement",
        "predicted_differential_settlement",
        "predicted_post_construction_settlement",
        "predicted_long_term_settlement",
        "predicted_tunnel_additional_settlement",
        "predicted_tunnel_uplift",
        "predicted_tunnel_horizontal_displacement",
        "predicted_tunnel_convergence",
        "settlement_control_value",
        "differential_settlement_control_value",
        "whether_high_rise_building",
        "whether_non_rock_socketed_friction_pile",
        "whether_soft_soil_area",
        "whether_additional_deformation_monitoring_required",
        "monitoring_duration_after_completion",
        "settlement_stability_criterion",
    ],
    "excavation": [
        "pit_involved",
        "pit_length",
        "pit_width",
        "pit_area",
        "pit_depth",
        "local_deep_pit_depth",
        "distance_pit_edge_to_metro",
        "pit_position_relative_to_metro",
        "whether_pit_crosses_metro",
        "whether_pit_above_metro",
        "whether_side_pit",
        "whether_split_pit",
        "split_pit_scheme",
        "excavation_sequence",
        "excavation_layering",
        "excavation_blocking",
        "time_limit_for_excavation",
        "whether_time_space_effect_considered",
        "predicted_retaining_wall_displacement",
        "predicted_ground_settlement",
        "predicted_metro_vertical_displacement",
        "predicted_metro_horizontal_displacement",
        "predicted_metro_convergence",
        "predicted_metro_differential_settlement",
        "whether_bottom_slab_timely_cast",
        "whether_long_exposure_risk",
        "whether_local_deep_pit_after_slab",
    ],
    "retaining_support": [
        "support_method",
        "retaining_structure_type",
        "retaining_structure_depth",
        "retaining_structure_stiffness",
        "support_system_type",
        "strut_type",
        "anchor_involved",
        "anchor_length",
        "anchor_end_clearance_to_metro",
        "soil_nail_involved",
        "soil_nail_clearance_to_metro",
        "whether_anchor_intrudes_protection_zone",
        "whether_support_near_metro_strengthened",
        "whether_servo_strut_used",
        "whether_support_removal_plan",
        "whether_replacement_support_plan",
        "gap_between_retaining_and_basement_wall",
        "gap_backfill_material",
        "waterproof_level_near_metro",
        "risk_of_support_failure",
    ],
    "dewatering": [
        "dewatering_involved",
        "dewatering_type",
        "whether_confined_water",
        "whether_confined_water_drawdown",
        "dewatering_depth",
        "water_level_drawdown",
        "dewatering_duration",
        "target_water_level",
        "aquifer_type",
        "permeable_layer_thickness",
        "whether_deep_sand_layer",
        "whether_soft_soil",
        "cutoff_wall_type",
        "cutoff_wall_depth",
        "whether_closed_cutoff",
        "whether_recharge",
        "recharge_scheme",
        "whether_pumping_test",
        "whether_seepage_analysis",
        "whether_metro_structural_safety_checked",
        "predicted_groundwater_change_near_metro",
        "predicted_settlement_due_to_dewatering",
        "groundwater_monitoring_required",
        "confined_water_monitoring_required",
        "stop_dewatering_condition",
        "emergency_measure_for_water_inrush",
        "risk_of_quicksand",
        "risk_of_piping",
        "risk_of_bottom_heave",
    ],
    "geology_hydrology": [
        "geomorphology",
        "site_elevation",
        "soil_layers",
        "main_soil_near_metro",
        "soft_soil_present",
        "muddy_soil_present",
        "sand_layer_present",
        "karst_present",
        "fault_fracture_zone_present",
        "bad_geology_present",
        "special_soil_present",
        "groundwater_type",
        "phreatic_water_level",
        "confined_water_level",
        "hydraulic_connection",
        "permeability_coefficient",
        "soil_compression",
        "soil_shear_strength",
        "geotechnical_report_source",
        "geology_risk_summary",
    ],
    "assessment_calculation": [
        "assessment_required",
        "assessment_performed",
        "assessment_stage",
        "calculation_methods",
        "software_used",
        "model_dimension",
        "model_boundary_condition",
        "construction_stages_modeled",
        "load_cases",
        "dewatering_modeled",
        "pile_construction_modeled",
        "excavation_modeled",
        "metro_structure_modeled",
        "soil_structure_interaction_considered",
        "calculation_control_standard",
        "calculation_result_summary",
        "max_metro_vertical_displacement",
        "max_metro_horizontal_displacement",
        "max_metro_convergence",
        "max_metro_differential_settlement",
        "max_metro_curvature_radius",
        "max_additional_stress",
        "max_vibration_velocity",
        "max_building_settlement",
        "max_building_differential_settlement",
        "max_building_tilt",
        "whether_result_within_limit",
        "calculation_conclusion",
    ],
    "monitoring": [
        "monitoring_required",
        "monitoring_objects",
        "monitoring_items",
        "monitoring_layout_range",
        "monitoring_section_spacing",
        "monitoring_point_count",
        "automatic_monitoring_required",
        "initial_value_collection_required",
        "monitoring_frequency",
        "monitoring_duration",
        "warning_thresholds",
        "alarm_response_measures",
        "whether_track_bed_monitoring",
        "whether_track_geometry_monitoring",
        "whether_groundwater_monitoring",
        "whether_confined_water_monitoring",
        "whether_deep_soil_displacement_monitoring",
        "whether_vibration_monitoring",
        "whether_video_patrol",
        "whether_manual_patrol",
        "monitoring_stability_criterion",
    ],
    "existing_condition": [
        "pre_construction_investigation_required",
        "pre_construction_investigation_done",
        "investigation_scope",
        "investigation_content",
        "existing_deformation",
        "existing_settlement",
        "existing_convergence",
        "existing_cracks",
        "existing_leakage",
        "segment_joint_opening",
        "segment_dislocation",
        "track_bed_void",
        "disease_type",
        "disease_grade",
        "structure_safety_state_grade",
        "whether_disease_treatment_required",
        "whether_special_disease_assessment_required",
        "remaining_deformation_capacity",
        "existing_monitoring_data_available",
    ],
    "protection_measures": [
        "protection_scheme_required",
        "protection_scheme_provided",
        "measure_for_excavation",
        "measure_for_support",
        "measure_for_pile",
        "measure_for_dewatering",
        "measure_for_load_change",
        "measure_for_vibration",
        "measure_for_existing_disease",
        "measure_for_emergency",
        "measure_for_construction_sequence",
        "measure_for_backfill",
        "measure_for_waterproof",
        "measure_for_third_party_facilities",
        "whether_measures_match_risk",
        "whether_dynamic_adjustment_mechanism",
        "whether_emergency_plan_required",
        "whether_emergency_plan_provided",
    ],
    "environmental_impact": [
        "environmental_impact_involved",
        "vibration_assessment_required",
        "noise_assessment_required",
        "sensitive_target_type",
        "sensitive_target_distance_to_track_center",
        "sensitive_target_distance_to_tunnel",
        "train_speed",
        "train_marshalling",
        "operation_period",
        "daytime_limit",
        "nighttime_limit",
        "predicted_vibration_daytime",
        "predicted_vibration_nighttime",
        "predicted_secondary_noise",
        "vibration_compliance",
        "noise_compliance",
        "required_vibration_reduction_distance",
        "actual_distance",
        "whether_vibration_mitigation_required",
        "vibration_mitigation_measures",
        "whether_environmental_special_review_required",
    ],
    "review_conclusion": [
        "overall_conclusion",
        "main_risks",
        "non_compliance_items",
        "conditional_requirements",
        "supplement_required",
        "special_assessment_required",
        "expert_review_required",
        "construction_restrictions",
        "monitoring_requirements",
        "environmental_requirements",
        "follow_up_requirements",
        "final_review_opinion",
    ],
}


SECTION_GROUP_RULES = [
    {
        "prefixes": ["1."],
        "topics": ["总则/适用范围"],
        "groups": ["case_basic", "project_info", "metro_asset", "spatial_relation", "external_work"],
        "keywords": ["适用", "城市轨道交通", "结构安全保护", "外部作业", "总则"],
        "reason": "第1章用于判断案例是否属于城市轨道交通结构安全保护规程的适用范围。",
    },
    {
        "prefixes": ["2."],
        "topics": ["术语定义"],
        "groups": ["metro_asset", "spatial_relation", "external_work", "impact_level"],
        "keywords": ["术语", "定义", "控制保护区", "特别保护区", "外部作业", "影响等级"],
        "reason": "第2章主要是术语定义，通常不直接判定合规，但用于解释后续属性含义。",
    },
    {
        "prefixes": ["3.1"],
        "topics": ["保护区与空间关系"],
        "groups": ["metro_asset", "spatial_relation", "external_work", "project_info"],
        "keywords": ["保护区", "特别保护区", "控制保护区", "净距", "范围", "结构"],
        "reason": "3.1条文通常涉及轨道结构保护范围、控制保护区和特别保护区识别。",
    },
    {
        "prefixes": ["3.2"],
        "topics": ["影响等级划分"],
        "groups": ["spatial_relation", "external_work", "impact_level", "geology_hydrology", "existing_condition"],
        "keywords": ["影响等级", "特级", "一级", "二级", "接近程度", "影响区", "地质", "病害"],
        "reason": "3.2条文通常用于外部作业影响等级划分。",
    },
    {
        "prefixes": ["3.3"],
        "topics": ["资料调查与现状调查"],
        "groups": ["project_info", "metro_asset", "geology_hydrology", "existing_condition"],
        "keywords": ["资料", "调查", "现状", "地质", "水文", "病害", "既有结构"],
        "reason": "3.3条文通常要求收集资料、调查既有结构和工程地质水文条件。",
    },
    {
        "prefixes": ["3.4"],
        "topics": ["评估与审查要求"],
        "groups": ["external_work", "assessment_calculation", "monitoring", "protection_measures", "review_conclusion"],
        "keywords": ["评估", "审查", "专项", "专家", "计算", "监测", "保护措施"],
        "reason": "3.4条文通常涉及安全评估、专项审查、监测和保护措施要求。",
    },
    {
        "prefixes": ["4."],
        "topics": ["外部作业通用控制"],
        "groups": [
            "project_info",
            "metro_asset",
            "spatial_relation",
            "external_work",
            "impact_level",
            "assessment_calculation",
            "monitoring",
            "protection_measures",
            "review_conclusion",
        ],
        "keywords": ["外部作业", "安全评估", "控制", "保护措施", "监测", "应急", "施工"],
        "reason": "第4章为外部作业安全控制通用要求，需要综合调用工程、空间关系、评估、监测和保护措施属性。",
    },
    {
        "prefixes": ["5.1"],
        "topics": ["新建/改建工程通用要求"],
        "groups": ["project_info", "external_work", "spatial_relation", "assessment_calculation", "protection_measures"],
        "keywords": ["新建", "改建", "通用", "保护", "评估", "方案"],
        "reason": "5.1条文通常为建设工程影响轨道结构的通用要求。",
    },
    {
        "prefixes": ["5.2"],
        "topics": ["基坑工程"],
        "groups": ["excavation", "retaining_support", "dewatering", "spatial_relation", "geology_hydrology", "assessment_calculation", "monitoring", "protection_measures"],
        "keywords": ["基坑", "开挖", "分层", "分块", "限时", "围护", "支撑", "降水", "底板", "防水"],
        "reason": "源文件第5.2节为基坑工程，涉及基坑开挖、分坑、围护支撑、降水和底板及时施工等要求。",
    },
    {
        "prefixes": ["5.3"],
        "topics": ["隧道工程"],
        "groups": ["external_work", "spatial_relation", "geology_hydrology", "assessment_calculation", "monitoring", "protection_measures"],
        "keywords": ["隧道", "上穿", "下穿", "侧穿", "盾构", "顶管", "穿越", "非开挖", "试验段", "自动化监测"],
        "reason": "源文件第5.3节为隧道工程，涉及新建隧道上穿、下穿或侧穿城市轨道交通结构的控制要求。",
    },
    {
        "prefixes": ["5.4"],
        "topics": ["基础工程"],
        "groups": ["foundation_pile", "load_change", "additional_settlement", "spatial_relation", "geology_hydrology", "assessment_calculation", "monitoring", "protection_measures"],
        "keywords": ["基础", "浅基础", "桩基", "非挤土桩", "挤土", "试桩", "跳桩", "附加荷载", "附加应力"],
        "reason": "源文件第5.4节为基础工程，涉及浅基础、地基处理、桩基作业和附加荷载等要求。",
    },
    {
        "prefixes": ["5.5"],
        "topics": ["降水与地下水控制"],
        "groups": ["dewatering", "geology_hydrology", "excavation", "assessment_calculation", "monitoring", "protection_measures"],
        "keywords": ["降水", "承压水", "潜水", "止水", "回灌", "抽水", "管涌", "流砂", "突涌"],
        "reason": "5.5条文通常涉及基坑降水、地下水变化和水土风险控制。",
    },
    {
        "prefixes": ["5.6"],
        "topics": ["其他工程"],
        "groups": ["load_change", "additional_settlement", "spatial_relation", "assessment_calculation", "monitoring", "protection_measures", "environmental_impact"],
        "keywords": ["道路", "桥梁", "管线", "顶管", "拖拉管", "明挖", "爆破", "冻结", "起重", "吊装", "钻探", "河道", "水利", "拆除"],
        "reason": "源文件第5.6节为其他工程，涉及道路桥梁、地下管线、爆破、起重吊装、钻探、水利和拆除等外部作业要求。",
    },
    {
        "prefixes": ["6."],
        "topics": ["既有结构病害与处理"],
        "groups": ["existing_condition", "metro_asset", "assessment_calculation", "monitoring", "protection_measures", "review_conclusion"],
        "keywords": ["既有", "病害", "裂缝", "渗漏", "错台", "变形", "整治", "状态调查"],
        "reason": "第6章通常涉及既有轨道结构状态、病害调查、评估和处理要求。",
    },
    {
        "prefixes": ["7."],
        "topics": ["监测与施工过程控制"],
        "groups": ["monitoring", "assessment_calculation", "excavation", "retaining_support", "dewatering", "protection_measures", "review_conclusion"],
        "keywords": ["监测", "报警", "频率", "初始值", "自动化", "巡查", "施工过程", "控制值"],
        "reason": "第7章通常涉及施工期间监测布点、频率、报警值、巡查和动态控制。",
    },
    {
        "prefixes": ["8."],
        "topics": ["环境振动/噪声影响"],
        "groups": ["environmental_impact", "metro_asset", "spatial_relation", "assessment_calculation", "monitoring", "review_conclusion"],
        "keywords": ["振动", "噪声", "二次结构噪声", "敏感点", "减振", "环境"],
        "reason": "第8章通常涉及轨道交通运营振动、噪声及敏感目标环境影响评价。",
    },
]


def flatten_groups(group_names):
    fields = []
    for group_name in group_names:
        fields.extend(FIELD_GROUPS[group_name])
    return sorted(set(fields))


def clause_from_function(function_name):
    return function_name.replace("clause_", "").replace("_", ".")


def parse_functions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("clause_"):
            yield node.name


def matching_rules(clause):
    matches = []
    for rule in SECTION_GROUP_RULES:
        if any(clause.startswith(prefix) for prefix in rule["prefixes"]):
            matches.append(rule)
    return matches


def compact_title_from_schema(module_path, function_name):
    # The generated rule files expose CLAUSE_*_INPUT_SCHEMA constants.
    # Some files may contain mojibake, so title is only used as auxiliary text.
    constant = function_name.upper() + "_INPUT_SCHEMA"
    text = module_path.read_text(encoding="utf-8")
    pattern = rf"{re.escape(constant)}\s*:\s*dict\[str,\s*Any\]\s*=\s*(\{{.*?\n\}})\n\n"
    match = re.search(pattern, text, flags=re.S)
    if not match:
        return None
    raw = match.group(1)
    title_match = re.search(r"'title':\s*'([^']*)'", raw)
    return title_match.group(1) if title_match else None


def build_mapping(chapter_dir):
    mappings = []
    for path in sorted(Path(chapter_dir).glob("chapter_*_functions.py")):
        for function_name in parse_functions(path):
            clause = clause_from_function(function_name)
            rules = matching_rules(clause)
            if rules:
                field_groups = sorted({group for rule in rules for group in rule["groups"]})
                fields = flatten_groups(field_groups)
                topics = sorted({topic for rule in rules for topic in rule["topics"]})
                keywords = sorted({keyword for rule in rules for keyword in rule["keywords"]})
                reasons = [rule["reason"] for rule in rules]
                applicable_mode = "match_by_clause_prefix_and_filled_fields"
            else:
                field_groups = ["case_basic"]
                fields = flatten_groups(field_groups)
                topics = ["未分类条文"]
                keywords = []
                reasons = ["未命中章节规则，默认仅保留案例基础字段，需人工补充映射。"]
                applicable_mode = "manual_review_required"
            mappings.append(
                {
                    "module_file": path.name,
                    "function": function_name,
                    "clause": clause,
                    "title": compact_title_from_schema(path, function_name),
                    "topics": topics,
                    "field_groups": field_groups,
                    "input_fields": fields,
                    "trigger_keywords": keywords,
                    "applicable_mode": applicable_mode,
                    "mapping_reason": reasons,
                }
            )
    return mappings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter-dir", default="../chapter_1_functions")
    parser.add_argument("-o", "--output", default="data/schema/rule_function_field_mapping.json")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    chapter_dir = Path(args.chapter_dir)
    if not chapter_dir.is_absolute():
        chapter_dir = (project_root / chapter_dir).resolve()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (project_root / output_path).resolve()

    mappings = build_mapping(chapter_dir)
    output = {
        "format_version": "rule_function_field_mapping_v1",
        "description": "Map clause functions in chapter_1_functions folder to case attribute fields. The audit dispatcher uses this table to decide which function should receive which final_json attributes.",
        "chapter_dir": str(chapter_dir),
        "field_groups": FIELD_GROUPS,
        "section_group_rules": SECTION_GROUP_RULES,
        "function_count": len(mappings),
        "mappings": mappings,
    }
    ensure_dir(output_path.parent)
    write_json(output_path, output)
    print(f"wrote {output_path} functions={len(mappings)}")


if __name__ == "__main__":
    main()
