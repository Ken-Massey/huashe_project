from typing import Any

from .common import decision_base, get_path, raise_one_level


IMPACT_MATRIX = {
    "A": {"非常接近": "特级", "接近": "特级", "较接近": "一级", "不接近": "二级"},
    "B": {"非常接近": "特级", "接近": "一级", "较接近": "二级", "不接近": "三级"},
    "C": {"非常接近": "一级", "接近": "二级", "较接近": "三级", "不接近": "四级"},
    "D": {"非常接近": "二级", "接近": "三级", "较接近": "四级", "不接近": "四级"},
}


def _relative_clearance(data: dict[str, Any]) -> tuple[float | None, str]:
    relation = get_path(data, "project.relative_relationship")
    horizontal = get_path(data, "pit.minimum_horizontal_clearance_m")
    vertical = get_path(data, "pit.minimum_vertical_clearance_m")
    if relation == "交叉":
        return (vertical if vertical is not None else horizontal), "交叉关系优先采用竖向净距"
    return (horizontal if horizontal is not None else vertical), "单侧/双侧关系优先采用水平净距"


def _method_parameter(data: dict[str, Any]) -> tuple[float | None, str | None, str]:
    method = get_path(data, "metro_structure.structure_method")
    mapping = {
        "明挖": ("metro_structure.original_excavation_depth_m", "H"),
        "暗挖（矿山法）": ("metro_structure.mined_tunnel_span_m", "W"),
        "盾构": ("metro_structure.outer_diameter_or_width_m", "D"),
        "高架": ("metro_structure.elevated_pile_diameter_m", "P"),
    }
    if method not in mapping:
        return None, None, "未知结构施工方法"
    path, symbol = mapping[method]
    return get_path(data, path), path, symbol


def _approach_degree(method: str, clearance: float, parameter: float) -> str:
    ratio = clearance / parameter
    if method == "明挖":
        limits = (0.5, 1.0, 2.0)
    elif method == "暗挖（矿山法）":
        limits = (1.0, 1.5, 2.5)
    elif method == "盾构":
        limits = (1.0, 2.0, 3.0)
    else:
        limits = (3.0, 10.0, 20.0)
    if ratio <= limits[0]:
        return "非常接近"
    if ratio <= limits[1]:
        return "接近"
    if ratio <= limits[2]:
        return "较接近"
    return "不接近"


def _pit_influence_zone(data: dict[str, Any], clearance: float) -> tuple[str | None, list[str]]:
    relation = get_path(data, "project.relative_relationship")
    depth = get_path(data, "pit.pit_depth_m")
    soft_soil = get_path(data, "geology.is_soft_soil")
    notes: list[str] = []
    if relation == "交叉":
        return "A", ["附录A.0.3-1将结构正上方划入强烈影响区A。"]
    if depth is None or depth <= 0:
        return None, ["缺少有效基坑深度h1。"]
    ratio = clearance / depth
    use_large_boundary = soft_soil is not False
    b_upper = 1.5 if use_large_boundary else 1.0
    c_upper = 3.0 if use_large_boundary else 2.0
    if soft_soil is None:
        notes.append("软弱土条件未知，按附录A.0.3-1较大临界范围从严计算。")
    elif soft_soil:
        notes.append("软弱土范围按附录A.0.3-1注2采用较大临界值。")
    if ratio <= 0.7:
        return "A", notes
    if ratio <= b_upper:
        return "B", notes
    if ratio <= c_upper:
        return "C", notes
    return "D", notes


def evaluate_impact_level(data: dict[str, Any]) -> dict[str, Any]:
    result = decision_base(
        "影响等级及提级",
        "stage1_reply_system.rules.impact_level.evaluate_impact_level",
        ["3.2.1", "3.2.2", "3.2.4", "3.2.5", "3.2.6", "附录A.0.1-A.0.3"],
    )
    method = get_path(data, "metro_structure.structure_method")
    clearance, clearance_note = _relative_clearance(data)
    parameter, parameter_path, symbol = _method_parameter(data)
    result["inputs"] = {
        "structure_method": method,
        "relative_relationship": get_path(data, "project.relative_relationship"),
        "minimum_horizontal_clearance_m": get_path(data, "pit.minimum_horizontal_clearance_m"),
        "minimum_vertical_clearance_m": get_path(data, "pit.minimum_vertical_clearance_m"),
        "method_parameter_symbol": symbol,
        "method_parameter_m": parameter,
        "pit_depth_m": get_path(data, "pit.pit_depth_m"),
    }
    result["calculation_steps"].append(clearance_note)
    if not method:
        result["missing_fields"].append("metro_structure.structure_method")
    if clearance is None:
        result["missing_fields"].append("pit.minimum_horizontal_clearance_m|pit.minimum_vertical_clearance_m")
    if parameter is None or parameter <= 0:
        result["missing_fields"].append(parameter_path or "metro_structure.method_parameter")
    if result["missing_fields"]:
        return result

    approach = _approach_degree(method, clearance, parameter)
    zone, zone_notes = _pit_influence_zone(data, clearance)
    result["review_notes"].extend(zone_notes)
    if zone is None:
        result["missing_fields"].append("pit.pit_depth_m")
        return result

    initial = IMPACT_MATRIX[zone][approach]
    result["minimum_relative_clearance_m"] = clearance
    result["approach_degree"] = approach
    result["engineering_influence_zone"] = zone
    result["initial_impact_level"] = initial
    result["calculation_steps"].extend([
        f"按附录A.0.2，以L={clearance:g}m和{symbol}={parameter:g}m计算接近程度为{approach}。",
        f"按附录A.0.3-1，基坑工程影响分区为{zone}区。",
        f"按表3.2.2，{zone}区与{approach}组合得到初始影响等级{initial}。",
    ])

    mandatory: list[str] = []
    discretionary: list[str] = []
    if get_path(data, "geology.is_complex_geology_or_hydrology") is True or get_path(data, "geology.has_geological_hazard") is True:
        mandatory.append("复杂工程地质、水文地质条件或地质灾害（3.2.5第1款）")
    if get_path(data, "pit.confined_water_drawdown") is True:
        mandatory.append("涉及抽降承压水（3.2.5第2款）")
    if get_path(data, "metro_structure.is_special_section") is True or get_path(data, "metro_structure.disease_severity") == "严重":
        discretionary.append("特殊区段或严重结构病害（3.2.5第3款）")
    pit_depth = get_path(data, "pit.pit_depth_m")
    pit_length = get_path(data, "pit.pit_length_m")
    pit_area = get_path(data, "pit.pit_area_m2")
    if pit_depth is not None and pit_depth > 5 and ((pit_length is not None and pit_length > 100) or (pit_area is not None and pit_area > 10000)):
        discretionary.append("基坑深度超过5m且邻近侧边长超过100m或面积超过10000m2（3.2.5第4款）")

    all_reasons = mandatory + discretionary
    final_level = raise_one_level(initial) if all_reasons else initial
    result["mandatory_level_raise_reasons"] = mandatory
    result["discretionary_level_raise_reasons"] = discretionary
    result["level_raise_reasons"] = all_reasons
    result["level_raised"] = bool(all_reasons)
    result["final_impact_level"] = final_level
    if all_reasons:
        result["calculation_steps"].append(f"按3.2.5从{initial}提高一级至{final_level}；多个因素不自动叠加多级。")
    if discretionary:
        result["review_notes"].append("3.2.5第3、4款使用“可提高一级”，程序按从严口径给出建议等级，最终需人工确认。")
    if get_path(data, "metro_structure.structure_condition") == "较差" and get_path(data, "metro_structure.disease_severity") in (None, "未知"):
        result["review_notes"].append("结构状态为较差，但病害严重程度未知，需人工确认是否触发3.2.5第3款。")

    soft_soil = get_path(data, "geology.is_soft_soil") is True
    bad_geology = get_path(data, "geology.is_complex_geology_or_hydrology") is True or get_path(data, "geology.has_geological_hazard") is True
    confined = get_path(data, "pit.confined_water_drawdown") is True
    crossing = get_path(data, "project.relative_relationship") == "交叉"
    major = final_level in ("特级", "一级") or (final_level == "二级" and (soft_soil or bad_geology)) or confined or crossing
    result["is_major_impact_work"] = major
    result["status"] = "review" if discretionary else "complete"
    result["result"] = final_level
    return result
