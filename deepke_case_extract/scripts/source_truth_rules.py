import re


SOURCE_MD = r"D:\电脑管家迁移文件\微信聊天记录搬家\xwechat_files\wxid_94l1iosvlu9x22_ca46\msg\file\2026-06\城市轨道交通结构安全保护技术规程.md"


def has_value(value):
    return value not in (None, "", [], {})


def truthy(value):
    if value is True:
        return True
    if value is False or value is None:
        return False
    text = str(value).strip().lower()
    return text in {"true", "是", "有", "已", "已开展", "已编制", "需要", "应", "yes", "1"}


def falsy(value):
    if value is False:
        return True
    if value is True or value is None:
        return False
    text = str(value).strip().lower()
    return text in {"false", "否", "无", "未", "未开展", "未编制", "不需要", "no", "0"}


def text_has(value, words):
    text = str(value or "")
    return any(word in text for word in words)


def candidate_items(values, field):
    candidates = (values.get("__field_candidates__") or {}).get(field) or []
    if isinstance(candidates, dict):
        candidates = list(candidates.values())
    return [item for item in candidates if isinstance(item, dict)]


def candidate_values(values, field):
    return [item.get("value") for item in candidate_items(values, field) if has_value(item.get("value"))]


def field_texts(values, fields):
    texts = []
    for field in fields:
        if has_value(values.get(field)):
            texts.append(str(values.get(field)))
        for item in candidate_items(values, field):
            if has_value(item.get("value")):
                texts.append(str(item.get("value")))
            if has_value(item.get("source_text")):
                texts.append(str(item.get("source_text")))
    return texts


def text_evidence(values, fields, words):
    result = {}
    for field in fields:
        hits = []
        for text in field_texts(values, [field]):
            if text_has(text, words):
                hits.append(text)
        if hits:
            result[field] = hits[:3]
    return result


def has_text_evidence(values, fields, words):
    return bool(text_evidence(values, fields, words))


def any_truthy(values, fields):
    for field in fields:
        if truthy(values.get(field)):
            return True
        if any(truthy(value) for value in candidate_values(values, field)):
            return True
    return False


def any_falsy(values, fields):
    for field in fields:
        if falsy(values.get(field)):
            return True
        if any(falsy(value) for value in candidate_values(values, field)):
            return True
    return False


def is_rail_transit_monitoring(values):
    object_text = str(values.get("monitoring_object") or "")
    sentence_text = " ".join(
        str(values.get(key) or "")
        for key in ["monitoring_sentence", "monitoring_requirements", "monitoring_items"]
    )
    texts = [object_text, sentence_text] + field_texts(
        values,
        ["monitoring_object", "monitoring_sentence", "monitoring_requirements", "monitoring_items", "monitoring_objects"],
    )
    rail_words = ["轨道交通结构", "轨道交通", "地铁", "盾构区间", "区间结构", "隧道", "既有结构", "1号线"]
    monitoring_words = ["安全监测", "结构监测", "变形监测", "沉降监测", "水平位移监测", "竖向位移监测", "监测点", "监测项目", "监测频率", "监测"]
    background_words = [
        "Peck",
        "正态分布",
        "地层损失",
        "沉降槽",
        "观测数据",
        "盾构机的种类",
        "现状监测的基础上",
        "振动预测",
        "环境影响评价",
        "技术导则",
        "类比调查",
    ]
    for text in texts:
        if not text or text_has(text, background_words):
            continue
        if text_has(text, rail_words) and text_has(text, monitoring_words):
            return True
    return False


def has_non_rail_monitoring(values):
    return has_any(values, ["general_monitoring_required", "monitoring_sentence", "monitoring_items", "monitoring_object"]) and not is_rail_transit_monitoring(values)


def parse_number(value):
    if value is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else None


def level_rank(value):
    text = str(value or "")
    if "特" in text:
        return 4
    if "一" in text or "1" in text:
        return 3
    if "二" in text or "2" in text:
        return 2
    if "三" in text or "3" in text:
        return 1
    if "四" in text or "4" in text:
        return 0
    return None


def impact_level(values):
    for key in ["final_impact_level", "adjusted_impact_level", "initial_impact_level", "impact_level", "external_work_impact_level"]:
        rank = level_rank(values.get(key))
        if rank is not None:
            return rank, key, values.get(key)
    return None, None, None


def is_control_zone(values):
    return truthy(values.get("is_in_control_protection_zone"))


def is_pit_above_metro(values):
    return (
        truthy(values.get("whether_pit_above_metro"))
        or truthy(values.get("whether_above_metro"))
        or text_has(values.get("relative_position"), ["正上方", "上方"])
        or text_has(values.get("relation_type"), ["上跨"])
    )


def is_major_impact(values):
    rank, _, _ = impact_level(values)
    if truthy(values.get("whether_major_impact_work")):
        return True
    if rank is not None and rank >= 3:
        return True
    if rank == 2 and (
        truthy(values.get("soft_soil_present"))
        or truthy(values.get("muddy_soil_present"))
        or truthy(values.get("bad_geology_present"))
        or truthy(values.get("special_soil_present"))
    ):
        return True
    if truthy(values.get("whether_confined_water_drawdown")):
        return True
    return False


def has_any(values, fields):
    return any(has_value(values.get(field)) or any(has_value(value) for value in candidate_values(values, field)) for field in fields)


def missing_false_or_unknown(values, fields):
    missing = []
    explicit_false = []
    for field in fields:
        value = values.get(field)
        if truthy(value) or (has_value(value) and not falsy(value)):
            continue
        if falsy(value):
            explicit_false.append(field)
        else:
            missing.append(field)
    return missing, explicit_false


def make_result(clause, status, result, basis, evidence=None, missing=None, source_note=None):
    return {
        "source_rule_applied": True,
        "source_rule_status": status,
        "source_rule_result": result,
        "source_rule_basis": basis,
        "source_rule_evidence": evidence or {},
        "source_rule_missing_fields": missing or [],
        "source_rule_source_file": SOURCE_MD,
        "source_rule_note": source_note or "该判断仅使用规程原文中能够明确推出的要求；原文未明确量化时不凭空编造阈值。",
    }


def evaluate_clause(clause, values):
    clause = str(clause)
    if clause == "3.1.4":
        basis = "3.1.4 城市轨道交通沿线应设置控制保护区。地下车站与隧道结构外边线外侧不小于50m；过江（河、湖）段不小于100m；地面和高架车站、路基和桥梁外侧不小于30m；附属建（构）筑物及车辆基地用地范围外侧不小于10m。"
        if has_value(values.get("is_in_control_protection_zone")):
            return make_result(
                clause,
                "compliant" if truthy(values.get("is_in_control_protection_zone")) else "non_compliant",
                "已识别控制保护区属性。" if truthy(values.get("is_in_control_protection_zone")) else "案例属性显示未设置或未进入控制保护区，与3.1.4控制保护区要求不一致。",
                basis,
                {"is_in_control_protection_zone": values.get("is_in_control_protection_zone")},
            )
        return make_result(clause, "pending_review", "未抽取到控制保护区范围或是否进入控制保护区，需人工复核。", basis, missing=["is_in_control_protection_zone"])

    if clause == "3.1.5":
        basis = "3.1.5 在城市轨道交通控制保护区范围内应设置特别保护区；地下车站与隧道结构外边线外侧不小于5m，过江（河、湖）段不小于50m；地面和高架车站、路基和桥梁外侧不小于3m；附属建（构）筑物及车辆基地用地范围外侧不小于5m。"
        if not is_control_zone(values):
            return make_result(clause, "not_applicable", "未识别为控制保护区内作业，特别保护区要求暂不适用。", basis, {"is_in_control_protection_zone": values.get("is_in_control_protection_zone")})
        if has_value(values.get("is_in_special_protection_zone")):
            return make_result(
                clause,
                "compliant" if truthy(values.get("is_in_special_protection_zone")) else "non_compliant",
                "已识别特别保护区属性。" if truthy(values.get("is_in_special_protection_zone")) else "控制保护区内未识别特别保护区设置或进入关系，与3.1.5要求不一致。",
                basis,
                {"is_in_special_protection_zone": values.get("is_in_special_protection_zone")},
            )
        return make_result(clause, "pending_review", "未抽取到特别保护区属性，需人工复核。", basis, missing=["is_in_special_protection_zone"])

    if clause == "3.2.5":
        basis = "3.2.5 特殊情况下外部作业影响等级调整：复杂工程地质和水文地质或存在地质灾害时应提高一级；涉及抽降承压水时应提高一级；结构特殊区段、结构病害严重或结构变形较大时可提高一级；基坑深度超过5m且临近侧边长超100m或开挖面积超10000m2时可提高一级。"
        triggers = {}
        if truthy(values.get("bad_geology_present")) or truthy(values.get("special_soil_present")):
            triggers["bad_or_special_geology"] = True
        if truthy(values.get("whether_confined_water_drawdown")):
            triggers["whether_confined_water_drawdown"] = values.get("whether_confined_water_drawdown")
        pit_depth = parse_number(values.get("pit_depth"))
        pit_length = parse_number(values.get("pit_length"))
        pit_area = parse_number(values.get("pit_area"))
        if pit_depth is not None and pit_depth > 5 and ((pit_length is not None and pit_length > 100) or (pit_area is not None and pit_area > 10000)):
            triggers["large_pit_trigger"] = {"pit_depth": values.get("pit_depth"), "pit_length": values.get("pit_length"), "pit_area": values.get("pit_area")}
        if not triggers:
            return make_result(clause, "compliant", "未识别到3.2.5列明的影响等级提高触发条件。", basis)
        if has_any(values, ["adjusted_impact_level", "final_impact_level", "impact_level_adjustment_reasons"]):
            return make_result(clause, "compliant", "已识别影响等级调整或调整依据字段。", basis, triggers)
        return make_result(clause, "pending_review", "识别到影响等级可能需提高的触发条件，但未抽取到调整后的影响等级或调整依据。", basis, triggers, ["adjusted_impact_level", "final_impact_level", "impact_level_adjustment_reasons"])

    if clause == "3.2.6":
        basis = "3.2.6 重大影响外部作业主要包括：影响等级为特级、一级；二级且周边土体以淤泥、淤泥质土等高压缩性土为主或存在不良地质、特殊性岩土；对地下水影响较大的作业特别是抽降承压水；穿越轨道交通地下结构的作业。"
        major = is_major_impact(values)
        if major and truthy(values.get("whether_major_impact_work")):
            return make_result(clause, "compliant", "案例已标识为重大影响外部作业。", basis, {"whether_major_impact_work": values.get("whether_major_impact_work")})
        if major and falsy(values.get("whether_major_impact_work")):
            return make_result(clause, "non_compliant", "按3.2.6触发重大影响条件，但属性标识为非重大影响外部作业。", basis, {"whether_major_impact_work": values.get("whether_major_impact_work")})
        if major:
            return make_result(clause, "pending_review", "按3.2.6疑似重大影响外部作业，但未抽取到是否重大影响字段。", basis, missing=["whether_major_impact_work"])
        return make_result(clause, "compliant", "未识别到3.2.6列明的重大影响触发条件。", basis)

    if clause == "3.3.1":
        basis = "3.3.1 外部作业净距控制值宜符合表3.3.1；上方基坑竖向净距不宜小于1.0D且不小于4.0m；下穿隧道竖向净距不宜小于1.0D且不小于2.0m；对不满足净距控制值的，须经专题专项论证确定。"
        work_text = " ".join(str(values.get(k) or "") for k in ["main_external_work_type", "external_work_types", "relation_type"])
        checks = []
        if is_pit_above_metro(values) or "上方基坑" in work_text:
            checks.append(("minimum_vertical_clearance", 4.0, "上方基坑竖向净距不小于4.0m"))
        if truthy(values.get("whether_crossing_metro")) and text_has(work_text, ["隧道", "穿越"]):
            checks.append(("minimum_vertical_clearance", 2.0, "下穿隧道竖向净距不小于2.0m"))
        if text_has(work_text, ["钻探", "钻孔"]):
            checks.append(("minimum_horizontal_clearance", 6.0, "钻探孔水平投影净距：装配式地下结构不小于6.0m"))
        if text_has(work_text, ["围护桩", "地下连续墙"]):
            checks.append(("minimum_horizontal_clearance", 7.0, "围护桩、地下连续墙水平投影净距：装配式地下结构不小于7.0m"))
        if text_has(work_text, ["锚杆", "锚索", "土钉"]):
            checks.append(("minimum_horizontal_clearance", 10.0, "锚杆、锚索、土钉末端水平投影净距：装配式地下结构不小于10.0m"))
        if not checks:
            return make_result(clause, "pending_review", "未能根据当前属性确定表3.3.1中的具体外部作业类别，需人工复核净距控制值。", basis)
        failures = []
        missing = []
        evidence = {}
        for field, limit, desc in checks:
            value = parse_number(values.get(field))
            evidence[field] = values.get(field)
            if value is None:
                missing.append(field)
            elif value < limit:
                failures.append(f"{desc}，当前值为{values.get(field)}")
        if failures and not truthy(values.get("need_special_assessment")):
            return make_result(clause, "non_compliant", "；".join(failures) + "；且未识别专题专项论证。", basis, evidence, ["need_special_assessment"])
        if failures:
            return make_result(clause, "pending_review", "净距低于表3.3.1控制值，但已识别专题专项论证字段，需人工复核论证结论。", basis, evidence)
        if missing:
            return make_result(clause, "pending_review", "缺少净距字段，无法按表3.3.1计算。", basis, evidence, missing)
        return make_result(clause, "compliant", "已抽取净距满足当前可识别类别的表3.3.1控制值。", basis, evidence)

    if clause == "3.4.3":
        basis = "3.4.3 外部作业引起的城市轨道交通结构附加变形不得超过安全控制指标的控制值，附加荷载及累计变形不得超过安全控制指标的安全限值，道床与轨道结构变位不得影响列车运营安全。"
        if truthy(values.get("whether_result_within_limit")):
            return make_result(clause, "compliant", "计算结果字段显示满足控制限值。", basis, {"whether_result_within_limit": values.get("whether_result_within_limit")})
        if falsy(values.get("whether_result_within_limit")):
            return make_result(clause, "non_compliant", "计算结果字段显示未满足控制限值。", basis, {"whether_result_within_limit": values.get("whether_result_within_limit")})
        if has_any(values, ["max_metro_vertical_displacement", "max_metro_horizontal_displacement", "max_metro_differential_settlement"]):
            return make_result(clause, "pending_review", "已抽取变形计算值，但缺少对应控制指标限值，不能凭空判定是否超限。", basis)
        return make_result(clause, "pending_review", "缺少结构附加变形或控制指标字段，需人工复核。", basis)

    if clause == "4.1.1":
        basis = "4.1.1 在城市轨道交通控制保护区内从事外部作业时，应事先开展现状调查、地质条件及环境调查，并制定结构安全保护方案。"
        if not is_control_zone(values):
            return make_result(clause, "not_applicable", "未识别为控制保护区内外部作业。", basis)
        required_groups = {
            "现状调查": ["pre_construction_investigation_done", "existing_condition_summary", "metro_existing_condition", "existing_deformation", "existing_settlement", "existing_cracks", "existing_leakage"],
            "地质水文/环境调查": ["soil_layers", "groundwater_type", "geological_condition_summary", "geology_risk_summary", "main_soil_near_metro"],
            "结构安全保护方案": ["protection_scheme_provided", "measure_for_excavation", "measure_for_support", "measure_for_dewatering", "overall_conclusion", "final_review_opinion"],
        }
        evidence = {}
        group_keywords = {
            "现状调查": ["现状调查", "现场调查", "工前调查", "资料收集", "既有结构现状", "既有线现状", "既有病害", "现状监测"],
            "地质水文/环境调查": ["工程地质", "水文地质", "地质条件", "土层", "地层", "地下水", "潜水", "承压水", "勘察报告"],
            "结构安全保护方案": ["保护方案", "保护措施", "专项保护", "控制保护措施", "保证", "确保", "停止降水", "回填", "加固", "应急"],
        }
        missing = []
        for name, fields in required_groups.items():
            group_evidence = text_evidence(values, fields, group_keywords[name])
            if has_any(values, fields) or group_evidence:
                evidence[name] = group_evidence or {field: values.get(field) for field in fields if has_value(values.get(field))}
            else:
                missing.append(name)
        if missing:
            return make_result(clause, "non_compliant", "控制保护区内外部作业缺少：" + "、".join(missing), basis, evidence=evidence, missing=missing)
        return make_result(clause, "compliant", "已抽取现状调查、地质水文/环境调查和结构安全保护方案相关内容。", basis, evidence=evidence)

    if clause == "4.1.2":
        basis = "4.1.2 在城市轨道交通控制保护区内从事重大影响外部作业时，应对既有结构进行安全评估和安全监测，在结构安全保护方案的基础上制定应急预案。外部作业影响等级为二级时，宜按上述规定执行。"
        rank, rank_field, rank_value = impact_level(values)
        if not is_control_zone(values):
            return make_result(clause, "not_applicable", "未识别为控制保护区内外部作业。", basis)
        if not is_major_impact(values) and rank != 2:
            return make_result(clause, "not_applicable", "未识别为重大影响外部作业或二级外部作业。", basis, {rank_field: rank_value} if rank_field else {})
        mandatory = {
            "安全评估": ["assessment_performed", "calculation_methods", "calculation_result_summary", "overall_conclusion"],
            "安全监测": ["monitoring_required", "monitoring_items", "monitoring_requirements"],
            "应急预案": ["whether_emergency_plan_provided", "measure_for_emergency"],
            "结构安全保护方案": ["protection_scheme_provided", "measure_for_excavation", "measure_for_support", "measure_for_dewatering"],
        }
        missing = [name for name, fields in mandatory.items() if not has_any(values, fields)]
        if missing and is_major_impact(values):
            return make_result(clause, "non_compliant", "重大影响外部作业缺少：" + "、".join(missing), basis, {rank_field: rank_value} if rank_field else {}, missing)
        if missing:
            return make_result(clause, "pending_review", "二级外部作业宜按重大影响要求执行，当前缺少：" + "、".join(missing), basis, {rank_field: rank_value} if rank_field else {}, missing)
        return make_result(clause, "compliant", "已抽取安全评估、安全监测、应急预案和结构安全保护方案相关内容。", basis)

    if clause == "5.1.2":
        basis = "5.1.2 外部作业工程实施方案包括外部作业设计和施工方案、安全评估、轨道交通结构专项保护方案和应急预案等。同一场地存在多项外部作业时，应综合考虑叠加影响。"
        required = {
            "外部作业设计/施工方案": ["work_stage", "construction_sequence", "project_schedule", "assessment_stage"],
            "安全评估": ["assessment_performed", "calculation_methods", "calculation_result_summary", "overall_conclusion"],
            "专项保护方案": ["protection_scheme_provided", "measure_for_excavation", "measure_for_support", "measure_for_dewatering"],
            "应急预案": ["whether_emergency_plan_provided", "measure_for_emergency"],
        }
        missing = [name for name, fields in required.items() if not has_any(values, fields)]
        if missing:
            return make_result(clause, "pending_review", "实施方案完整性需复核，缺少：" + "、".join(missing), basis, missing=missing)
        return make_result(clause, "compliant", "已抽取实施方案、安全评估、专项保护方案和应急预案相关内容。", basis)

    if clause == "5.2.4":
        basis = "5.2.4 当外部基坑位于城市轨道交通结构正上方时，竖向净距控制宜满足本规程表3.3.1的相关规定，有特殊要求时应通过专项评估确定既有结构上方的残余覆土厚度。"
        if not is_pit_above_metro(values):
            return make_result(clause, "not_applicable", "未识别为城市轨道交通结构正上方基坑。", basis)
        clearance = parse_number(values.get("minimum_vertical_clearance"))
        if clearance is None:
            return make_result(clause, "pending_review", "上方基坑缺少竖向净距，无法按表3.3.1判断。", basis, missing=["minimum_vertical_clearance"])
        if clearance < 4.0 and not truthy(values.get("assessment_performed")):
            return make_result(clause, "non_compliant", f"上方基坑竖向净距{values.get('minimum_vertical_clearance')}小于4.0m，且未识别专项评估。", basis, {"minimum_vertical_clearance": values.get("minimum_vertical_clearance")})
        if clearance < 4.0:
            return make_result(clause, "pending_review", "竖向净距低于4.0m，但已识别专项评估字段，需人工复核评估结论。", basis)
        return make_result(clause, "compliant", "上方基坑竖向净距不小于4.0m。", basis, {"minimum_vertical_clearance": values.get("minimum_vertical_clearance")})

    if clause == "5.2.7":
        basis = "5.2.7 基坑土方开挖时应充分考虑时空效应，遵循“分层、分块、限时”的原则；重型机械设备、土方运输车辆的行进路线应避开城市轨道交通正上方区域，地面荷载应满足设计要求。"
        if not (truthy(values.get("pit_involved")) or text_has(values.get("main_external_work_type"), ["基坑"])):
            return make_result(clause, "not_applicable", "未识别为基坑工程。", basis)
        missing = []
        if not has_any(values, ["excavation_layering"]):
            missing.append("分层开挖")
        if not has_any(values, ["excavation_blocking"]):
            missing.append("分块开挖")
        if not has_any(values, ["time_limit_for_excavation", "construction_sequence"]):
            missing.append("限时/施工时序")
        if missing:
            return make_result(clause, "pending_review", "基坑开挖原则需复核，缺少：" + "、".join(missing), basis, missing=missing)
        return make_result(clause, "compliant", "已抽取基坑分层、分块、限时或施工时序相关信息。", basis)

    if clause == "5.2.10":
        basis = "5.2.10 基坑开挖影响深度内的潜水、微承压水与承压水控制应符合本规程第5.5节的相关规定。"
        if not (truthy(values.get("pit_involved")) or text_has(values.get("main_external_work_type"), ["基坑"])):
            return make_result(clause, "not_applicable", "未识别为基坑工程。", basis)
        if not has_any(values, ["groundwater_type", "dewatering_type", "dewatering_involved"]):
            return make_result(clause, "pending_review", "未抽取基坑影响深度内地下水或降水信息，需复核是否适用第5.5节。", basis)
        if has_any(values, ["dewatering_type", "measure_for_dewatering", "stop_dewatering_condition"]):
            return make_result(clause, "compliant", "已抽取地下水/降水控制相关信息，可衔接第5.5节复核。", basis)
        return make_result(clause, "pending_review", "有地下水信息但缺少降水控制措施。", basis, missing=["dewatering_type", "measure_for_dewatering"])

    if clause == "5.2.11":
        basis = "5.2.11 基坑开挖至基底设计高程时，应及时施做垫层和结构底板，严禁基坑长时间暴露；基坑内局部深坑宜在浅部底板施工完成后开挖。"
        if not (truthy(values.get("pit_involved")) or text_has(values.get("main_external_work_type"), ["基坑"])):
            return make_result(clause, "not_applicable", "未识别为基坑工程。", basis)
        if falsy(values.get("whether_bottom_slab_timely_cast")) or truthy(values.get("whether_long_exposure_risk")):
            return make_result(clause, "non_compliant", "属性显示未及时施做底板或存在长时间暴露风险。", basis, {"whether_bottom_slab_timely_cast": values.get("whether_bottom_slab_timely_cast"), "whether_long_exposure_risk": values.get("whether_long_exposure_risk")})
        if truthy(values.get("whether_bottom_slab_timely_cast")):
            return make_result(clause, "compliant", "已识别及时施做垫层和结构底板。", basis)
        return make_result(clause, "pending_review", "未抽取基坑底板及时施工或长时间暴露风险字段。", basis, missing=["whether_bottom_slab_timely_cast", "whether_long_exposure_risk"])

    if clause == "5.5.1":
        basis = "5.5.1 控制保护区内的降水工程，应采取措施避免流砂、管涌、坑底突涌及降水引起的地层较大沉降等破坏，编制合理的降水方案，预估承压水水位降低情况及降水施工影响。"
        if not (truthy(values.get("dewatering_involved")) or has_value(values.get("dewatering_type"))):
            return make_result(clause, "not_applicable", "未识别降水工程。", basis)
        missing = []
        evidence = {}
        dewatering_scheme_fields = ["dewatering_type", "measure_for_dewatering", "recharge_scheme", "stop_dewatering_condition"]
        dewatering_scheme_evidence = text_evidence(values, dewatering_scheme_fields, ["降水", "井点", "管井", "深井", "回灌", "按需降压", "停止降水", "水位"])
        if not (has_any(values, dewatering_scheme_fields) or dewatering_scheme_evidence):
            missing.append("降水方案/降水措施")
        else:
            evidence["降水方案/降水措施"] = dewatering_scheme_evidence or {field: values.get(field) for field in dewatering_scheme_fields if has_value(values.get(field))}
        if truthy(values.get("whether_confined_water")) and not has_any(values, ["confined_water_level", "water_level_drawdown", "predicted_groundwater_change_near_metro"]):
            missing.append("承压水水位降低预估")
        else:
            confined_evidence = text_evidence(values, ["confined_water_level", "water_level_drawdown", "predicted_groundwater_change_near_metro"], ["承压水", "水位降低", "水位", "降深", "降压"])
            if confined_evidence:
                evidence["承压水水位降低预估"] = confined_evidence
        impact_fields = ["predicted_settlement_due_to_dewatering", "calculation_result_summary", "whether_metro_structural_safety_checked", "predicted_groundwater_change_near_metro"]
        impact_evidence = text_evidence(values, impact_fields, ["降水施工影响", "降水影响", "水位降低", "地下水位变化", "降水引起", "降水导致", "承压水", "受力安全验算"])
        if not (impact_evidence or truthy(values.get("whether_metro_structural_safety_checked"))):
            missing.append("降水施工影响预估")
        else:
            evidence["降水施工影响预估"] = impact_evidence or {field: values.get(field) for field in impact_fields if has_value(values.get(field))}
        if missing:
            return make_result(clause, "non_compliant", "降水工程缺少：" + "、".join(missing), basis, evidence=evidence, missing=missing)
        return make_result(clause, "compliant", "已抽取降水方案、承压水/地下水变化或施工影响预估相关信息。", basis, evidence=evidence)

    if clause == "5.5.2":
        basis = "5.5.2 当外部降水作业引起城市轨道交通结构周边地下水位变化时，应验算既有结构的受力安全。"
        if not has_any(values, ["predicted_groundwater_change_near_metro", "water_level_drawdown", "dewatering_type"]):
            return make_result(clause, "not_applicable", "未识别外部降水导致地下水位变化。", basis)
        if truthy(values.get("whether_metro_structural_safety_checked")) or has_any(values, ["calculation_methods", "calculation_result_summary"]):
            return make_result(clause, "compliant", "已识别既有结构受力安全验算或计算分析。", basis)
        return make_result(clause, "non_compliant", "识别到降水/地下水位变化，但未抽取既有结构受力安全验算。", basis, missing=["whether_metro_structural_safety_checked", "calculation_methods"])

    if clause == "5.5.6":
        basis = "5.5.6 当需要抽降承压水时，应根据现场抽水试验及渗流场计算结果，结合开挖工况，按“按需降压”的原则确定降水方案，并防止抽水带走土层细颗粒。"
        if not (truthy(values.get("whether_confined_water")) or truthy(values.get("whether_confined_water_drawdown"))):
            return make_result(clause, "not_applicable", "未识别抽降承压水。", basis)
        missing = []
        if not truthy(values.get("whether_pumping_test")):
            missing.append("现场抽水试验")
        if not truthy(values.get("whether_seepage_analysis")):
            missing.append("渗流场计算/分析")
        if not has_any(values, ["dewatering_type", "dewatering_modeled", "measure_for_dewatering"]):
            missing.append("按需降压降水方案")
        if missing:
            return make_result(clause, "non_compliant", "抽降承压水缺少：" + "、".join(missing), basis, missing=missing)
        return make_result(clause, "compliant", "已抽取抽水试验、渗流分析和降水方案相关信息。", basis)

    if clause == "7.1.1":
        basis = "7.1.1 在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测，监测工作不得影响轨道交通的正常运营。"
        if not is_control_zone(values):
            return make_result(clause, "not_applicable", "未识别为控制保护区内外部作业。", basis)
        rail_monitoring_evidence = text_evidence(
            values,
            ["monitoring_required", "monitoring_object", "monitoring_items", "monitoring_sentence", "monitoring_requirements", "monitoring_objects"],
            ["轨道交通", "地铁", "盾构", "区间结构", "隧道", "既有结构", "安全监测", "结构监测", "变形监测", "沉降监测"],
        )
        non_rail_evidence = text_evidence(
            values,
            ["general_monitoring_required", "monitoring_object", "monitoring_items", "monitoring_sentence", "monitoring_requirements"],
            ["周边市政设施", "市政设施", "管线", "建筑物", "房屋", "地表", "土体"],
        )
        negative_monitoring = any_falsy(values, ["monitoring_required", "general_monitoring_required"])
        if truthy(values.get("monitoring_required")) or is_rail_transit_monitoring(values):
            return make_result(
                clause,
                "compliant",
                "已识别对受影响轨道交通结构的安全监测要求或监测项目。",
                basis,
                rail_monitoring_evidence
                or {
                    "monitoring_required": values.get("monitoring_required"),
                    "monitoring_object": values.get("monitoring_object"),
                    "monitoring_items": values.get("monitoring_items"),
                    "monitoring_sentence": values.get("monitoring_sentence"),
                },
            )
        if negative_monitoring:
            return make_result(
                clause,
                "non_compliant",
                "控制保护区内外部作业存在不开展或不需要监测的表达，且未识别受影响轨道交通结构安全监测要求。",
                basis,
                text_evidence(values, ["monitoring_required", "general_monitoring_required", "monitoring_sentence", "monitoring_requirements"], ["不对", "不进行", "未开展", "不开展", "无需", "不需"]),
            )
        if has_non_rail_monitoring(values):
            return make_result(
                clause,
                "non_compliant",
                "已识别监测内容，但监测对象不是受影响的轨道交通结构，不能满足7.1.1要求。",
                basis,
                non_rail_evidence
                or {
                    "monitoring_object": values.get("monitoring_object"),
                    "monitoring_items": values.get("monitoring_items"),
                    "monitoring_sentence": values.get("monitoring_sentence"),
                    "general_monitoring_required": values.get("general_monitoring_required"),
                },
            )
        if falsy(values.get("monitoring_required")):
            return make_result(clause, "non_compliant", "控制保护区内外部作业属性显示不需要安全监测。", basis, {"monitoring_required": values.get("monitoring_required")})
        return make_result(clause, "non_compliant", "控制保护区内外部作业未抽取到轨道交通结构安全监测要求。", basis, missing=["monitoring_required", "monitoring_object", "monitoring_items"])

    if clause == "7.1.2":
        basis = "7.1.2 应在外部作业实施前完成监测点布设并采集初始值，施工过程中应进行动态监测，监测成果应准确及时反映监测对象变化特征和安全状态。"
        if not (truthy(values.get("monitoring_required")) or is_rail_transit_monitoring(values)):
            return make_result(clause, "not_applicable", "未识别轨道交通结构安全监测要求。", basis)
        missing = []
        if not truthy(values.get("initial_value_collection_required")):
            missing.append("实施前采集初始值")
        if not has_any(values, ["monitoring_frequency", "monitoring_duration"]):
            missing.append("施工过程动态监测安排")
        if missing:
            return make_result(clause, "pending_review", "监测方案完整性需复核，缺少：" + "、".join(missing), basis, missing=missing)
        return make_result(clause, "compliant", "已抽取初始值采集和动态监测安排。", basis)

    if clause == "7.1.3":
        basis = "7.1.3 监测方法宜采用仪器量测、现场巡视或远程视频监控等多种手段相结合；当外部作业影响等级为特级、一级时，宜采用自动化监测。"
        if not (truthy(values.get("monitoring_required")) or is_rail_transit_monitoring(values)):
            return make_result(clause, "not_applicable", "未识别轨道交通结构安全监测要求。", basis)
        rank, rank_field, rank_value = impact_level(values)
        if rank is not None and rank >= 3 and not truthy(values.get("automatic_monitoring_required")):
            return make_result(clause, "pending_review", "特级/一级影响等级宜采用自动化监测，当前未抽取自动化监测要求。", basis, {rank_field: rank_value} if rank_field else {}, ["automatic_monitoring_required"])
        if truthy(values.get("automatic_monitoring_required")):
            return make_result(clause, "compliant", "已识别自动化监测要求。", basis)
        return make_result(clause, "pending_review", "未抽取监测方法信息，需人工复核。", basis)

    if clause == "7.2.6":
        basis = "7.2.6 外部降水作业时，应对既有结构附近地下水位进行监测；实施抽降承压水作业时，还应监测既有结构附近承压水位。软土地区轨道交通结构对外部作业敏感时，应对附近土体分层竖向位移或深层水平位移进行监测。"
        if not (truthy(values.get("dewatering_involved")) or has_value(values.get("dewatering_type"))):
            return make_result(clause, "not_applicable", "未识别外部降水作业。", basis)
        missing = []
        evidence = {}
        groundwater_evidence = text_evidence(values, ["whether_groundwater_monitoring", "groundwater_monitoring_required", "monitoring_items", "monitoring_requirements", "monitoring_sentence"], ["地下水位监测", "水位监测", "地下水"])
        if not (truthy(values.get("whether_groundwater_monitoring")) or truthy(values.get("groundwater_monitoring_required")) or groundwater_evidence):
            missing.append("地下水位监测")
        else:
            evidence["地下水位监测"] = groundwater_evidence or {
                "whether_groundwater_monitoring": values.get("whether_groundwater_monitoring"),
                "groundwater_monitoring_required": values.get("groundwater_monitoring_required"),
            }
        confined_evidence = text_evidence(values, ["whether_confined_water_monitoring", "confined_water_monitoring_required", "monitoring_items", "monitoring_requirements", "monitoring_sentence"], ["承压水位监测", "承压水", "水位监测"])
        if (truthy(values.get("whether_confined_water")) or truthy(values.get("whether_confined_water_drawdown"))) and not (truthy(values.get("whether_confined_water_monitoring")) or truthy(values.get("confined_water_monitoring_required")) or confined_evidence):
            missing.append("承压水位监测")
        elif confined_evidence:
            evidence["承压水位监测"] = confined_evidence
        if missing:
            return make_result(clause, "non_compliant", "外部降水作业缺少：" + "、".join(missing), basis, evidence=evidence, missing=missing)
        return make_result(clause, "compliant", "已抽取地下水位/承压水位监测要求。", basis, evidence=evidence)

    return None
