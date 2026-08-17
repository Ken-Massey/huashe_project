from typing import Any

from .common import decision_base, get_path


def evaluate_safety_assessment_need(data: dict[str, Any], impact: dict[str, Any]) -> dict[str, Any]:
    result = decision_base(
        "是否需要安全评估",
        "stage1_reply_system.rules.assessment.evaluate_safety_assessment_need",
        ["3.2.6", "4.1.2", "4.3.1", "4.3.6"],
    )
    in_control_zone = get_path(data, "review_context.is_in_control_protection_zone")
    level = impact.get("final_impact_level")
    major = impact.get("is_major_impact_work")
    result["inputs"] = {
        "is_in_control_protection_zone": in_control_zone,
        "final_impact_level": level,
        "is_major_impact_work": major,
    }
    if in_control_zone is None:
        result["missing_fields"].append("review_context.is_in_control_protection_zone")
        return result
    if in_control_zone is False:
        result.update(status="complete", result="通常不要求")
        result["calculation_steps"].append("项目不在控制保护区内，4.1.2的触发条件不成立。")
        return result
    if level is None or major is None:
        result["missing_fields"].append("calculated.final_impact_level|calculated.is_major_impact_work")
        return result
    if major:
        result.update(status="complete", result="必须进行")
        result["calculation_steps"].append("控制保护区内的重大影响外部作业按4.1.2应进行安全评估。")
    elif level == "二级":
        result.update(status="complete", result="建议进行")
        result["calculation_steps"].append("二级影响外部作业按4.1.2宜进行安全评估。")
    else:
        result.update(status="complete", result="通常不要求")
        result["calculation_steps"].append("项目在控制保护区内，但未达到4.1.2规定的重大影响或二级建议条件。")
    return result
