from typing import Any


IMPACT_LEVELS = ["特级", "一级", "二级", "三级", "四级"]


def get_path(data: dict[str, Any], path: str, default: Any = None) -> Any:
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def raise_one_level(level: str) -> str:
    if level not in IMPACT_LEVELS:
        return level
    return IMPACT_LEVELS[max(0, IMPACT_LEVELS.index(level) - 1)]


def decision_base(name: str, function_name: str, clauses: list[str]) -> dict[str, Any]:
    return {
        "decision_name": name,
        "function": function_name,
        "regulation_clauses": clauses,
        "status": "insufficient",
        "result": "资料不足",
        "inputs": {},
        "calculation_steps": [],
        "missing_fields": [],
        "review_notes": [],
    }
