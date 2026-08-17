from typing import Any

from .common import decision_base, get_path


def evaluate_monitoring_need(data: dict[str, Any], impact: dict[str, Any]) -> dict[str, Any]:
    result = decision_base(
        "是否需要保护监测",
        "stage1_reply_system.rules.monitoring.evaluate_monitoring_need",
        ["4.1.2", "7.1.1", "7.1.2", "7.1.3"],
    )
    in_control_zone = get_path(data, "review_context.is_in_control_protection_zone")
    level = impact.get("final_impact_level")
    result["inputs"] = {
        "is_in_control_protection_zone": in_control_zone,
        "final_impact_level": level,
    }
    if in_control_zone is None:
        result["missing_fields"].append("review_context.is_in_control_protection_zone")
        return result
    if in_control_zone is False:
        result.update(status="complete", result="通常不触发")
        result["calculation_steps"].append("项目不在控制保护区内，7.1.1的触发条件不成立。")
        return result
    if level in ("特级", "一级"):
        result.update(status="complete", result="必须监测且建议自动化")
        result["calculation_steps"].append("按7.1.1必须监测；特级、一级按7.1.3宜采用自动化监测。")
    else:
        result.update(status="complete", result="必须监测")
        result["calculation_steps"].append("在控制保护区内从事外部作业，按7.1.1应进行安全监测。")
    return result
