from datetime import datetime
from typing import Any

from .assessment import evaluate_safety_assessment_need
from .impact_level import evaluate_impact_level
from .monitoring import evaluate_monitoring_need
from .setback import evaluate_setback_distance


def evaluate_project(data: dict[str, Any]) -> dict[str, Any]:
    setback = evaluate_setback_distance(data)
    impact = evaluate_impact_level(data)
    assessment = evaluate_safety_assessment_need(data, impact)
    monitoring = evaluate_monitoring_need(data, impact)
    return {
        "format_version": "stage1_calculation_result_v1",
        "case_id": data.get("case_id"),
        "calculated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "summary": {
            "setback_distance": setback["result"],
            "impact_level": impact["result"],
            "safety_assessment": assessment["result"],
            "protective_monitoring": monitoring["result"],
        },
        "decisions": {
            "setback_distance": setback,
            "impact_level": impact,
            "safety_assessment": assessment,
            "protective_monitoring": monitoring,
        },
    }
