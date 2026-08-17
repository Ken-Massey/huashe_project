from typing import Any

from .common import decision_base, get_path


HORIZONTAL_LIMITS = {
    "围护桩": {"地下装配式": 7.0, "地下现浇": 5.0, "地面结构": 5.0, "高架结构": 5.0},
    "地下连续墙": {"地下装配式": 7.0, "地下现浇": 5.0, "地面结构": 5.0, "高架结构": 5.0},
    "非挤土工程桩": {"地下装配式": 5.0, "地下现浇": 3.0, "地面结构": 3.0, "高架结构": 3.0},
    "挤土工程桩": {"地下装配式": 30.0, "地下现浇": 20.0, "地面结构": 6.0, "高架结构": 6.0},
    "锚杆": {"地下装配式": 10.0, "地下现浇": 6.0, "地面结构": 6.0, "高架结构": 6.0},
    "锚索": {"地下装配式": 10.0, "地下现浇": 6.0, "地面结构": 6.0, "高架结构": 6.0},
    "土钉": {"地下装配式": 10.0, "地下现浇": 6.0, "地面结构": 6.0, "高架结构": 6.0},
}


def evaluate_setback_distance(data: dict[str, Any]) -> dict[str, Any]:
    result = decision_base(
        "退让距离/净距控制",
        "stage1_reply_system.rules.setback.evaluate_setback_distance",
        ["3.3.1", "3.3.4", "3.3.5", "5.2.4"],
    )
    category = get_path(data, "metro_structure.structure_category")
    diameter = get_path(data, "metro_structure.outer_diameter_or_width_m")
    cross_river = get_path(data, "metro_structure.is_cross_river_segment")
    soft_soil = get_path(data, "geology.is_soft_soil")
    components = get_path(data, "pit.support_components", []) or []
    horizontal = get_path(data, "pit.minimum_horizontal_clearance_m")
    vertical = get_path(data, "pit.minimum_vertical_clearance_m")
    result["inputs"] = {
        "structure_category": category,
        "outer_diameter_or_width_m": diameter,
        "is_cross_river_segment": cross_river,
        "is_soft_soil": soft_soil,
        "support_components": components,
        "minimum_horizontal_clearance_m": horizontal,
        "minimum_vertical_clearance_m": vertical,
    }

    if not category:
        result["missing_fields"].append("metro_structure.structure_category")
    if not components:
        result["missing_fields"].append("pit.support_components")
    if result["missing_fields"]:
        return result

    factor = 3.0 if cross_river is True else 1.0
    if factor == 3.0:
        result["calculation_steps"].append("按3.3.4，越江（河、湖）地下结构的相应净距控制值取表列值的3倍。")

    items: list[dict[str, Any]] = []
    for component in components:
        item: dict[str, Any] = {
            "component": component,
            "direction": None,
            "actual_m": None,
            "base_limit_m": None,
            "applied_limit_m": None,
            "status": "insufficient",
            "result": "无法确定",
        }
        if component in HORIZONTAL_LIMITS:
            item["direction"] = "水平投影净距"
            item["actual_m"] = horizontal
            base_limit = HORIZONTAL_LIMITS[component].get(category)
            if base_limit is None:
                item["result"] = "表3.3.1无对应结构类型控制值"
            elif horizontal is None:
                item["result"] = "缺少水平净距"
            else:
                applied_limit = base_limit * factor
                item["base_limit_m"] = base_limit
                item["applied_limit_m"] = applied_limit
                item["status"] = "pass" if horizontal >= applied_limit else "fail"
                item["result"] = "满足" if item["status"] == "pass" else "不满足"
        elif component == "上方基坑":
            item["direction"] = "竖向净距"
            item["actual_m"] = vertical
            if category != "地下装配式":
                item["result"] = "表3.3.1对该结构类型未给出上方基坑数值"
            elif diameter is None:
                item["result"] = "缺少既有结构外径或宽度D"
            elif vertical is None:
                item["result"] = "缺少竖向净距"
            else:
                base_limit = max(4.0, diameter)
                applied_limit = base_limit * factor
                item["base_limit_m"] = base_limit
                item["applied_limit_m"] = applied_limit
                item["status"] = "pass" if vertical >= applied_limit else "fail"
                item["result"] = "满足" if item["status"] == "pass" else "不满足"
        else:
            item["result"] = "表3.3.1未配置该构件，需人工复核"
        items.append(item)

    result["control_items"] = items
    statuses = {item["status"] for item in items}
    if "fail" in statuses:
        result["status"] = "fail"
        result["result"] = "不满足常规净距控制值，需专题专项论证"
        result["requires_special_study"] = True
    elif statuses == {"pass"}:
        result["status"] = "pass"
        result["result"] = "满足常规净距控制值"
        result["requires_special_study"] = False
    else:
        result["status"] = "insufficient"
        result["result"] = "资料不足"
        result["requires_special_study"] = None

    if soft_soil is True and result["status"] == "pass":
        result["status"] = "review"
        result["result"] = "满足表列值，但软弱土地区需从严复核"
        result["review_notes"].append("表3.3.1注4要求软弱土地区适当提高净距控制值，但规程未给定统一提高数值。")
    elif soft_soil is None:
        result["review_notes"].append("软弱土条件未知，尚未执行表3.3.1注4的从严复核。")

    result["calculation_steps"].append("按表3.3.1对每一种支护构件分别比较实际净距和控制值。")
    return result
