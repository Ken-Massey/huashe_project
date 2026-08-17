import argparse
import json
from pathlib import Path
from common import ensure_dir, read_jsonl, write_jsonl


PROMPT_FILE = {
    "ProjectInfo": "project_info_prompt.txt",
    "MetroAsset": "metro_asset_prompt.txt",
    "SpatialRelation": "spatial_relation_prompt.txt",
    "ExternalWork": "external_work_prompt.txt",
    "ExcavationWork": "external_work_prompt.txt",
    "RetainingSupportSystem": "external_work_prompt.txt",
    "DewateringWork": "external_work_prompt.txt",
    "GeologyHydrology": "external_work_prompt.txt",
    "AssessmentCalculation": "assessment_prompt.txt",
    "MonitoringPlan": "assessment_prompt.txt",
    "ProtectionMeasures": "assessment_prompt.txt",
    "ReviewConclusion": "assessment_prompt.txt",
}

FALLBACK_SCHEMA = {
    "ProjectInfo": {
        "project_name": "项目名称",
        "construction_unit": "建设单位/委托单位",
        "design_unit": "设计单位",
        "assessment_unit": "评估单位",
        "project_location": "项目地点",
        "total_land_area": "总用地面积",
        "total_building_area": "总建筑面积",
        "underground_area": "地下建筑面积",
        "foundation_type": "基础形式",
        "project_schedule": "项目工期/施工时序",
    },
    "MetroAsset": {
        "metro_line_name": "轨道交通线路名称",
        "metro_section_name": "区间/车站/附属结构名称",
        "metro_asset_type": "轨道交通结构类型",
        "metro_operation_status": "地铁状态",
        "metro_structure_method": "施工方法",
        "metro_buried_depth": "结构埋深",
        "metro_special_section": "特殊区段",
    },
    "SpatialRelation": {
        "is_in_control_protection_zone": "是否位于控制保护区内",
        "is_in_special_protection_zone": "是否位于特别保护区内",
        "control_zone_intrusion_length": "侵入控制保护区长度/范围",
        "special_zone_intrusion_length": "侵入特别保护区长度/范围",
        "minimum_horizontal_clearance": "最小水平净距",
        "minimum_vertical_clearance": "最小竖向净距",
        "relation_type": "空间关系类型",
        "relative_position": "相对位置",
        "nearest_metro_asset": "最近轨道交通结构对象",
    },
    "ExternalWork": {
        "external_work_type": "外部作业类型",
        "case_type": "案例类型/外部作业类别",
    },
    "ExcavationWork": {
        "pit_depth": "基坑开挖深度",
        "pit_size": "基坑尺寸",
        "excavation_method": "开挖方式",
        "excavation_sequence": "开挖顺序",
    },
    "RetainingSupportSystem": {
        "support_type": "支护/围护形式",
        "retaining_structure_type": "围护结构类型",
    },
    "DewateringWork": {
        "dewatering_type": "降水方式",
        "groundwater_type": "地下水类型",
        "dewatering_stop_condition": "停止降水条件",
    },
    "GeologyHydrology": {
        "soil_layer": "土层",
        "groundwater_level": "地下水位",
        "soft_soil_involved": "是否涉及软土",
        "sand_layer_involved": "是否涉及砂层",
    },
    "AssessmentCalculation": {
        "calculation_method": "计算/评估方法",
        "software_name": "计算软件",
        "max_settlement": "最大沉降",
        "max_horizontal_displacement": "最大水平位移",
        "max_differential_settlement": "最大差异沉降",
        "max_tilt": "最大倾斜",
    },
    "MonitoringPlan": {
        "monitoring_required": "是否需要监测",
        "monitoring_items": "监测项目",
        "monitoring_frequency": "监测频率",
        "alarm_thresholds": "报警值/预警值",
    },
    "ProtectionMeasures": {
        "protection_scheme_required": "是否需要保护方案",
        "protection_measures": "保护措施",
        "measure_for_excavation": "基坑开挖保护措施",
        "measure_for_support": "支护保护措施",
        "measure_for_dewatering": "降水保护措施",
        "measure_for_backfill": "回填控制措施",
        "measure_for_emergency": "应急措施",
    },
    "ReviewConclusion": {
        "overall_conclusion": "总体审查/评价结论",
        "main_risks": "主要风险",
        "construction_restrictions": "施工限制条件",
        "monitoring_requirements": "监测要求",
        "final_review_opinion": "最终审查意见",
    },
}


def schema_for(module, schema):
    fields = schema.get("core_modules", {}).get(module, {})
    if not fields:
        return FALLBACK_SCHEMA.get(module, {})
    return {name: meta.get("meaning", "") for name, meta in fields.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("chunks_dir")
    parser.add_argument("schema_json")
    parser.add_argument("-o", "--output", default="outputs/deepke_inputs")
    parser.add_argument("--prompts-dir", default="prompts")
    args = parser.parse_args()
    ensure_dir(args.output)
    schema = json.loads(Path(args.schema_json).read_text(encoding="utf-8"))
    for path in Path(args.chunks_dir).glob("*.chunks.jsonl"):
        rows = []
        for row in read_jsonl(path):
            module = row["module"]
            s = schema_for(module, schema)
            if not s:
                continue
            prompt_name = PROMPT_FILE.get(module)
            prompt = ""
            if prompt_name and (Path(args.prompts_dir) / prompt_name).exists():
                prompt = (Path(args.prompts_dir) / prompt_name).read_text(encoding="utf-8")
            rows.append({
                "doc_id": row["doc_id"],
                "module": module,
                "instruction": prompt,
                "schema": s,
                "input": row["text"],
                "source_file": row["source_file"],
                "source_page": row["source_page"],
                "source_paragraph": row["paragraph_id"],
                "source_section": row["section"],
            })
        out = Path(args.output) / path.name.replace(".chunks.jsonl", ".deepke_input.jsonl")
        write_jsonl(out, rows)
        print(f"deepke inputs: {out.name}, rows={len(rows)}")


if __name__ == "__main__":
    main()
