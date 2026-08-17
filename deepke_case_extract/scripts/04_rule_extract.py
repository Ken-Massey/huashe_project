import argparse
import re
from pathlib import Path
from common import ensure_dir, first_match, read_jsonl, write_jsonl


def has_negative(text, keywords):
    return any(
        re.search(rf"(?:未|不|无|无需|不需|不再|未设置|未开展|不进行)[^。\n；;]*{keyword}", text)
        or re.search(rf"{keyword}[^。\n；;]*(?:未|不|无|无需|不需|不再|未设置|未开展|不进行)", text)
        for keyword in keywords
    )


def has_required(text, keywords):
    return any(
        re.search(rf"(?:应|需|须|需要|必须|加强|进行|开展|实施|设置|布设)[^。\n；;]*{keyword}", text)
        or re.search(rf"{keyword}[^。\n；;]*(?:应|需|须|需要|必须|加强|进行|开展|实施|设置|布设)", text)
        for keyword in keywords
    )


def is_metro_monitoring_text(text):
    metro_words = ["轨道交通", "地铁", "盾构", "区间", "隧道", "既有结构", "城市轨道交通结构", "轨道交通结构"]
    monitoring_words = ["安全监测", "保护性监测", "结构监测", "变形监测", "沉降监测", "水平位移监测", "竖向位移监测", "地下水位监测", "承压水位监测"]
    return "监测" in text and any(word in text for word in metro_words + monitoring_words)


def has_monitoring_text(text):
    return "监测" in text or "监控" in text or "观测" in text


def extract_monitoring_sentence(text):
    if not has_monitoring_text(text):
        return None
    return first_match([r"([^。\n；;]*(?:监测|监控|观测)[^。\n；;]*)"], text)


def extract_monitoring_items(text):
    if not has_monitoring_text(text):
        return None
    items = []
    item_words = [
        "位移",
        "水平位移",
        "竖向位移",
        "沉降",
        "差异沉降",
        "变形",
        "倾斜",
        "裂缝",
        "地下水位",
        "承压水位",
        "土体分层竖向位移",
        "深层水平位移",
        "巡视",
    ]
    for word in item_words:
        if word in text:
            items.append(word)
    return "、".join(dict.fromkeys(items)) if items else None


def extract_monitoring_object(text):
    if not has_monitoring_text(text):
        return None
    object_patterns = [
        ("轨道交通结构", r"(?:轨道交通|地铁|1号线|盾构区间|隧道|区间结构|既有结构|城市轨道交通结构)[^。\n；;]*(?:监测|监控|观测)"),
        ("周边市政设施", r"(?:周边市政设施|市政设施|市政管线|管线|燃气|电力)[^。\n；;]*(?:监测|监控|观测)"),
        ("建筑物", r"(?:建筑物|建筑|主体结构|房屋)[^。\n；;]*(?:监测|监控|观测)"),
        ("地下水", r"(?:地下水位|承压水位|水位)[^。\n；;]*(?:监测|监控|观测)"),
        ("土体", r"(?:土体|地表|地层)[^。\n；;]*(?:监测|监控|观测)"),
    ]
    for label, pattern in object_patterns:
        if re.search(pattern, text):
            return label
    return "未明确"


def is_rail_transit_monitoring_object(value):
    return value in {"轨道交通结构"} or text_has_any(str(value or ""), ["轨道交通", "地铁", "盾构", "区间结构", "隧道", "既有结构"])


def text_has_any(text, words):
    return any(word in text for word in words)


def extract_monitoring_required(text):
    if not is_metro_monitoring_text(text):
        return None
    negative_patterns = [
        r"(?:未设置|未开展|不进行|无需|不需|不再)[^。\n；;]*(?:安全监测|保护性监测|结构监测|轨道交通[^。\n；;]*监测|地铁[^。\n；;]*监测|既有结构[^。\n；;]*监测)",
        r"(?:安全监测|保护性监测|结构监测|轨道交通[^。\n；;]*监测|地铁[^。\n；;]*监测|既有结构[^。\n；;]*监测)[^。\n；;]*(?:未设置|未开展|不进行|无需|不需|不再)",
    ]
    if any(re.search(pattern, text) for pattern in negative_patterns):
        return False
    positive_patterns = [
        r"(?:应|需|须|需要|必须|加强|进行|开展|实施|设置|布设)[^。\n；;]*(?:安全监测|保护性监测|结构监测|轨道交通[^。\n；;]*监测|地铁[^。\n；;]*监测|既有结构[^。\n；;]*监测)",
        r"(?:安全监测|保护性监测|结构监测|轨道交通[^。\n；;]*监测|地铁[^。\n；;]*监测|既有结构[^。\n；;]*监测)[^。\n；;]*(?:应|需|须|需要|必须|加强|进行|开展|实施|设置|布设)",
    ]
    if any(re.search(pattern, text) for pattern in positive_patterns):
        return True
    return None


def extract_general_monitoring_required(text):
    if not has_monitoring_text(text):
        return None
    if has_negative(text, ["监测", "监控", "观测"]):
        return False
    if has_required(text, ["监测", "监控", "观测"]):
        return True
    return None


def extract_bool_requirement(text, keyword):
    if has_negative(text, [keyword]):
        return False
    if has_required(text, [keyword]):
        return True
    return None


def sentence_with(text, keywords):
    keyword_expr = "|".join(re.escape(word) for word in keywords)
    if not keyword_expr:
        return None
    return first_match([rf"([^。\n；;]*(?:{keyword_expr})[^。\n；;]*)"], text)


def extract_phrase_requirement(text, positive_keywords, negative_keywords=None):
    negative_keywords = negative_keywords or positive_keywords
    if has_negative(text, negative_keywords):
        return False
    if has_required(text, positive_keywords):
        return True
    return None


def extract_common_fields(text):
    """Extract high-value audit evidence regardless of the current module label."""
    d = {}

    investigation_sentence = sentence_with(text, ["现状调查", "现场调查", "工前调查", "资料收集", "既有结构现状", "既有线现状", "既有病害"])
    if investigation_sentence:
        d["pre_construction_investigation_done"] = True
        d["investigation_content"] = investigation_sentence
        d["existing_condition_summary"] = investigation_sentence
        if text_has_any(investigation_sentence, ["轨道交通", "地铁", "盾构", "区间", "既有结构", "隧道"]):
            d["metro_existing_condition"] = investigation_sentence
    if "现状监测" in text:
        d["existing_monitoring_data_available"] = True
        d["metro_monitoring_history"] = sentence_with(text, ["现状监测"])

    geology_sentence = sentence_with(text, ["工程地质", "水文地质", "地质条件", "土层", "地层", "地下水", "潜水", "承压水", "勘察报告"])
    if geology_sentence:
        d["geological_condition_summary"] = geology_sentence
        if text_has_any(geology_sentence, ["风险", "不良", "软土", "淤泥", "砂土", "流砂", "管涌", "突涌"]):
            d["geology_risk_summary"] = geology_sentence

    protection_sentence = sentence_with(text, ["保护方案", "保护措施", "专项保护", "控制保护措施", "确保", "保证", "停止降水", "回填", "加固", "减震", "隔振", "应急"])
    if protection_sentence and text_has_any(protection_sentence, ["保护", "控制", "安全", "停止降水", "回填", "加固", "减震", "隔振", "应急"]):
        d["protection_scheme_provided"] = True
        d["measure_for_excavation"] = protection_sentence
        if "支护" in protection_sentence or "围护" in protection_sentence:
            d["measure_for_support"] = protection_sentence
        if "降水" in protection_sentence or "水位" in protection_sentence:
            d["measure_for_dewatering"] = protection_sentence
        if "应急" in protection_sentence:
            d["whether_emergency_plan_provided"] = True
            d["measure_for_emergency"] = protection_sentence

    if "降水" in text or "井点" in text or "水位" in text:
        d["dewatering_involved"] = True
        dewatering_sentence = sentence_with(text, ["降水", "井点", "管井", "深井", "水位", "回灌", "按需降压", "停止降水"])
        if dewatering_sentence:
            d["measure_for_dewatering"] = dewatering_sentence
        impact_sentence = sentence_with(text, ["降水施工影响", "降水影响", "水位降低", "地层沉降", "沉降", "变形", "结构安全验算", "受力安全"])
        if (
            impact_sentence
            and text_has_any(impact_sentence, ["降水", "水位", "井点", "地下水", "承压水", "潜水"])
            and text_has_any(impact_sentence, ["沉降", "变形", "影响", "验算", "降低", "降深"])
        ):
            d["predicted_settlement_due_to_dewatering"] = impact_sentence
            d["predicted_groundwater_change_near_metro"] = impact_sentence
        if text_has_any(text, ["结构安全验算", "受力安全验算", "安全性验算"]):
            d["whether_metro_structural_safety_checked"] = True

    groundwater_monitoring = extract_bool_requirement(text, "地下水位监测")
    if groundwater_monitoring is not None:
        d["whether_groundwater_monitoring"] = groundwater_monitoring
        d["groundwater_monitoring_required"] = groundwater_monitoring
    confined_monitoring = extract_bool_requirement(text, "承压水位监测")
    if confined_monitoring is not None:
        d["whether_confined_water_monitoring"] = confined_monitoring
        d["confined_water_monitoring_required"] = confined_monitoring

    if text_has_any(text, ["安全评估", "安全评价", "影响评估", "影响评价", "本次评估", "本次评价"]):
        d["assessment_performed"] = True
    calculation_sentence = sentence_with(text, ["计算结果", "模拟结果", "分析结果", "理论计算", "数值模拟", "影响可控", "满足", "不满足"])
    if calculation_sentence and text_has_any(calculation_sentence, ["计算", "模拟", "分析", "影响", "满足", "不满足"]):
        d["calculation_result_summary"] = calculation_sentence

    monitoring_sentence = extract_monitoring_sentence(text)
    if monitoring_sentence:
        d["general_monitoring_required"] = extract_general_monitoring_required(text)
        d["monitoring_sentence"] = monitoring_sentence
        d["monitoring_object"] = extract_monitoring_object(text)
        d["monitoring_items"] = extract_monitoring_items(text)
        d["monitoring_requirements"] = first_match([r"((?:应|需|须|加强|开展|进行|布设|设置|不对|不进行|未开展|不开展)[^。\n；;]*(?:监测|监控|观测)[^。\n；;]*)"], text) or monitoring_sentence
        metro_monitoring = extract_monitoring_required(text)
        if metro_monitoring is not None:
            d["monitoring_required"] = metro_monitoring

    return {k: v for k, v in d.items() if v not in [None, ""]}


def is_environmental_vibration_text(text):
    return any(
        word in text
        for word in ["环境振动", "Z振级", "振动达标", "振动控制标准", "二次结构噪声", "70dB", "减振", "隔振"]
    )


def has_structural_control_context(text):
    return any(
        word in text
        for word in [
            "结构安全控制指标",
            "安全控制指标",
            "附加变形",
            "累计变形",
            "道床",
            "轨道结构变位",
            "结构变形",
            "变形控制",
            "变形保护",
            "建筑物变形保护",
            "沉降",
            "位移",
            "倾斜",
            "差异沉降",
        ]
    )


def extract_vibration_compliance(text):
    if not is_environmental_vibration_text(text):
        return None
    negative = [
        r"不满足[^。\n；;]*(?:环境振动|振动控制标准|振动达标)",
        r"(?:环境振动|振动控制标准|振动达标)[^。\n；;]*不满足",
        r"(?:Z振级|振级)[^。\n；;]*(?:超过|超出)[^。\n；;]*70dB",
        r"(?:超过|超出)[^。\n；;]*70dB",
    ]
    if any(re.search(pattern, text) for pattern in negative):
        return False
    positive = [
        r"满足[^。\n；;]*(?:环境振动|振动控制标准|振动达标)",
        r"(?:环境振动|振动控制标准|振动达标)[^。\n；;]*满足",
        r"(?:Z振级|振级)[^。\n；;]*(?:小于|不超过|未超过)[^。\n；;]*70dB",
    ]
    if any(re.search(pattern, text) for pattern in positive):
        return True
    return None


def extract_result_within_limit(text):
    # 3.4.3 checks structural deformation/control limits. Environmental vibration
    # compliance is a different field, otherwise vibration sentences create false positives.
    if is_environmental_vibration_text(text) and not has_structural_control_context(text):
        return None
    negative = [
        r"不满足[^。\n；;]*(?:结构安全控制指标|安全控制指标|附加变形|累计变形|结构变形|轨道结构变位|变形控制|变形保护|建筑物变形保护|控制限值|控制值)",
        r"(?:结构安全控制指标|安全控制指标|附加变形|累计变形|结构变形|轨道结构变位|变形控制|变形保护|建筑物变形保护|控制限值|控制值)[^。\n；;]*不满足",
        r"(?:超过|超出)[^。\n；;]*(?:结构安全控制指标|安全控制指标|附加变形|累计变形|结构变形|轨道结构变位|控制限值|控制值)",
    ]
    if any(re.search(pattern, text) for pattern in negative):
        return False
    positive = [
        r"满足[^。\n；;]*(?:结构安全控制指标|安全控制指标|附加变形|累计变形|结构变形|轨道结构变位|变形控制|变形保护|建筑物变形保护|控制限值|控制值)",
        r"(?:结构安全控制指标|安全控制指标|附加变形|累计变形|结构变形|轨道结构变位|变形控制|变形保护|建筑物变形保护|控制限值|控制值)[^。\n；;]*满足",
        r"(?:未超过|不超过|小于)[^。\n；;]*(?:结构安全控制指标|安全控制指标|附加变形|累计变形|结构变形|轨道结构变位|控制限值|控制值)",
    ]
    if any(re.search(pattern, text) for pattern in positive) and not any(re.search(pattern, text) for pattern in negative):
        return True
    return None


def extract(module, text):
    d = extract_common_fields(text)
    if module == "ProjectInfo":
        d.update({
            "project_name": first_match([r"(?:工程名称|项目名称)[:：]\s*([^。\n；;]+)", r"本项目为([^，。\n；;]+)"], text),
            "project_location": first_match([r"(?:建设地点|项目地点)[:：]\s*([^。\n；;]+)", r"位于([^。\n；;]+)"], text),
            "construction_unit": first_match([r"(?:建设单位|委托单位)[:：]\s*([^。\n；;]+)"], text),
            "total_land_area": first_match([r"总用地面积\s*([0-9.]+(?:平方米|m2|㎡))"], text),
            "total_building_area": first_match([r"总建筑面积\s*([0-9.]+(?:平方米|m2|㎡))"], text),
            "underground_area": first_match([r"地下建筑面积(?:约)?\s*([0-9.]+(?:平方米|m2|㎡))"], text),
            "foundation_type": first_match([r"采用([^。\n；;]*(?:桩基础|筏板基础|桩筏基础|钻孔灌注桩|管桩)[^。\n；;]*)"], text),
        })
    if module == "MetroAsset":
        d.update({
            "metro_line_name": first_match([r"(?:轨道交通|地铁)\s*([0-9A-Za-z]+号线)", r"([0-9A-Za-z]+号线)"], text),
            "metro_section_name": first_match([r"([^\s，。；;]*站[~～至][^\s，。；;]*站(?:区间|盾构区间))", r"([^\s，。；;]*出入场线(?:区间|盾构区间))"], text),
            "metro_asset_type": first_match([r"(盾构区间)", r"(地下车站)", r"(车站附属结构)", r"(高架结构)"], text),
            "metro_structure_method": first_match([r"(盾构法|盾构|明挖法|矿山法|顶管法)"], text),
            "metro_buried_depth": first_match([r"埋深[:：]?\s*([0-9.]+m[~～至\\-]+[0-9.]+m)"], text),
        })
    if module == "SpatialRelation":
        d.update({
            "is_in_control_protection_zone": True if "控制保护区" in text else None,
            "is_in_special_protection_zone": True if "特别保护区" in text else None,
            "control_zone_intrusion_length": first_match([r"侵入[^，。；;]*控制保护区[^0-9。；;]*([0-9.]+m)"], text),
            "special_zone_intrusion_length": first_match([r"侵入[^，。；;]*特别保护区[^0-9。；;]*([0-9.]+m)"], text),
            "minimum_vertical_clearance": first_match([
                r"(?:正上方|上方基坑)[^。；;]*?最小净距约?\s*([0-9.]+m)",
                r"(?:正上方|上方基坑)[^。；;]*?净距(?:约|为|不小于|不足)?\s*([0-9.]+m)",
                r"竖向净距(?:约|为|不小于|不足)?\s*([0-9.]+m)",
            ], text),
            "minimum_horizontal_clearance": first_match([
                r"水平(?:投影)?净距(?:约|为|不小于)?\s*([0-9.]+m)",
                r"最小水平净距约?\s*([0-9.]+m)",
                r"最小净距约?\s*([0-9.]+m)",
                r"最近距离约?\s*([0-9.]+m)",
                r"距离[^，。；;]*?约\s*([0-9.]+m)",
            ], text),
            "relation_type": first_match([r"(上跨|下穿|侧穿|平行|邻近|毗邻|斜交)"], text),
            "relative_position": first_match([r"(正上方|侧方|侧上方|西侧|东侧|南侧|北侧)"], text),
            "whether_pit_above_metro": True if ("基坑" in text and "正上方" in text) or "上方基坑" in text else None,
            "whether_above_metro": True if "正上方" in text or "上方基坑" in text else None,
        })
    if module in {"ExternalWork", "ExcavationWork", "RetainingSupportSystem", "DewateringWork", "GeologyHydrology"}:
        d.update({
            "external_work_type": first_match([r"(基坑工程|基坑|桩基|管线|道路|勘察|降水工程|修缮工程)"], text),
            "pit_depth": first_match([r"挖深约?\s*([0-9.]+m)", r"开挖深度约?\s*([0-9.]+m)", r"基坑深度约?\s*([0-9.]+m)"], text),
            "pit_size": first_match([r"基坑.*?长约?([0-9.]+m.*?宽约?[0-9.]+m)"], text),
            "support_type": first_match([r"采用([^。\n；;]*放坡[^。\n；;]*)", r"采用([^。\n；;]*(?:钢板桩|地下连续墙|排桩|支护)[^。\n；;]*)"], text),
            "dewatering_type": first_match([r"采用([^。\n；;]*(?:井点降水|轻型井点|管井降水|深井降水|疏干降水|降水)[^。\n；;]*)"], text),
            "groundwater_type": first_match([r"(孔隙潜水|承压水|潜水|地下水)"], text),
            "soil_layer": first_match([r"(粉砂|粉土|淤泥质粉质粘土|杂填土|黏土|粘土)"], text),
        })
    if module in {"AssessmentCalculation", "MonitoringPlan", "ProtectionMeasures", "ReviewConclusion"}:
        monitoring_required = extract_monitoring_required(text)
        monitoring_sentence = extract_monitoring_sentence(text)
        monitoring_object = extract_monitoring_object(text)
        d.update({
            "calculation_method": first_match([r"(Peck[^，。；;]*计算)", r"(理论计算)", r"(数值模拟)"], text),
            "software_name": first_match([r"(MIDAS/GTS)", r"(Midas/GTS)"], text),
            "assessment_performed": extract_bool_requirement(text, "安全评估"),
            "protection_scheme_provided": extract_bool_requirement(text, "保护方案"),
            "whether_emergency_plan_provided": extract_bool_requirement(text, "应急预案"),
            "whether_result_within_limit": extract_result_within_limit(text),
            "vibration_compliance": extract_vibration_compliance(text),
            "max_settlement": first_match([r"最大沉降(?:量|变形)?为?\s*([0-9.]+mm)"], text),
            "max_horizontal_displacement": first_match([r"最大(?:水平|侧向)(?:位移|变形)(?:量)?为?\s*([0-9.]+mm)"], text),
            "max_differential_settlement": first_match([r"最大(?:差异|不均匀)沉降\s*([0-9.]+mm)"], text),
            "max_tilt": first_match([r"最大(?:整体)?倾斜(?:值)?为?\s*([0-9.]+)"], text),
            "monitoring_required": monitoring_required,
            "general_monitoring_required": extract_general_monitoring_required(text),
            "monitoring_sentence": monitoring_sentence,
            "monitoring_object": monitoring_object,
            "monitoring_items": extract_monitoring_items(text),
            "whether_groundwater_monitoring": extract_bool_requirement(text, "地下水位监测"),
            "whether_confined_water_monitoring": extract_bool_requirement(text, "承压水位监测"),
            "initial_value_collection_required": extract_bool_requirement(text, "初始值"),
            "automatic_monitoring_required": extract_bool_requirement(text, "自动化监测"),
            "monitoring_requirements": first_match([r"((?:应|需|须|加强|开展|进行|布设|设置)[^。\n；;]*(?:监测|监控|观测)[^。\n；;]*)"], text),
            "protection_measures": first_match([r"((?:应|需|须)[^。\n；;]*(?:保护|控制|加固|回填|减震|隔振|应急)[^。\n；;]*)"], text),
            "overall_conclusion": first_match([r"([^。\n]*(?:影响可控|满足[^。\n]*要求|不满足[^。\n]*要求)[^。\n]*)"], text),
            "final_review_opinion": first_match([r"([^。\n]*(?:影响可控|满足[^。\n]*要求|不满足[^。\n]*要求)[^。\n]*)"], text),
        })
    return {k: v for k, v in d.items() if v not in [None, ""]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("chunks_dir")
    parser.add_argument("-o", "--output", default="outputs/raw_extract")
    args = parser.parse_args()
    ensure_dir(args.output)
    for path in Path(args.chunks_dir).glob("*.chunks.jsonl"):
        out = []
        for row in read_jsonl(path):
            fields = extract(row["module"], row["text"])
            for field, value in fields.items():
                out.append({
                    "doc_id": row["doc_id"],
                    "module": row["module"],
                    "field_name": field,
                    "field_value": value,
                    "source_file": row["source_file"],
                    "source_page": row["source_page"],
                    "source_paragraph": row["paragraph_id"],
                    "source_section": row["section"],
                    "source_text": row["text"],
                    "confidence": 0.9 if value is False else 0.75,
                    "extraction_method": "rule",
                })
        out_path = Path(args.output) / path.name.replace(".chunks.jsonl", ".raw_extract.jsonl")
        write_jsonl(out_path, out)
        print(f"rule extracted: {out_path.name}, rows={len(out)}")


if __name__ == "__main__":
    main()
