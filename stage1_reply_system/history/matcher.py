"""Explainable mixed-attribute and Chinese-text similarity matching."""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from .database import load_history_cases


def _ngrams(text: str, sizes: tuple[int, ...] = (2, 3)) -> Counter[str]:
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", text.lower())
    return Counter(value[i:i + size] for size in sizes for i in range(max(0, len(value) - size + 1)))


def _cosine(left: str, right: str) -> float:
    a, b = _ngrams(left), _ngrams(right)
    if not a or not b:
        return 0.0
    numerator = sum(value * b.get(key, 0) for key, value in a.items())
    denominator = math.sqrt(sum(value * value for value in a.values()) * sum(value * value for value in b.values()))
    return numerator / denominator if denominator else 0.0


def _equal(left: object, right: object) -> float | None:
    if left in (None, "", []) or right in (None, "", []):
        return None
    if isinstance(left, list) or isinstance(right, list):
        a, b = set(left if isinstance(left, list) else [left]), set(right if isinstance(right, list) else [right])
        return len(a & b) / len(a | b) if a and b else 0.0
    return 1.0 if left == right else 0.0


def _numeric(left: object, right: object, scale: float) -> float | None:
    if left is None or right is None:
        return None
    return math.exp(-abs(float(left) - float(right)) / scale)


def _query_data(project_input: dict[str, object], letter_text: str) -> dict[str, object]:
    project = project_input.get("project", {})
    metro = project_input.get("metro_structure", {})
    pit = project_input.get("pit", {})
    return {
        "project_name": project.get("project_name"),
        "stage": project.get("project_stage"),
        "project_type": project.get("project_type"),
        "relationship": project.get("relative_relationship"),
        "methods": [metro.get("structure_method")] if metro.get("structure_method") else [],
        "lines": [metro.get("metro_line_name")] if metro.get("metro_line_name") else [],
        "pit_depth": pit.get("pit_depth_m"),
        "horizontal": pit.get("minimum_horizontal_clearance_m"),
        "vertical": pit.get("minimum_vertical_clearance_m"),
        "text": "\n".join(filter(None, [
            project.get("project_name"), project.get("project_address"), project.get("construction_content"), letter_text,
        ])),
    }


def match_similar_replies(
    project_input: dict[str, object],
    database_path: str | Path,
    *,
    letter_text: str = "",
    top_k: int = 3,
    minimum_score: float = 0.45,
) -> dict[str, object]:
    query = _query_data(project_input, letter_text)
    weights = {
        "project_name": 0.18,
        "project_stage": 0.17,
        "project_type": 0.15,
        "relative_relationship": 0.10,
        "structure_method": 0.10,
        "metro_line": 0.08,
        "pit_depth": 0.06,
        "horizontal_clearance": 0.05,
        "vertical_clearance": 0.03,
        "letter_semantics": 0.08,
    }
    matches: list[dict[str, object]] = []
    for case in load_history_cases(database_path):
        if not str(case.get("advice_text") or "").strip():
            continue
        components = {
            "project_name": _cosine(str(query["project_name"] or ""), str(case["project_name"] or "")),
            "project_stage": _equal(query["stage"], case["stage"]),
            "project_type": _equal(query["project_type"], case["project_type"]),
            "relative_relationship": _equal(query["relationship"], case["relative_relationship"]),
            "structure_method": _equal(query["methods"], case["structure_methods"]),
            "metro_line": _equal(query["lines"], case["metro_lines"]),
            "pit_depth": _numeric(query["pit_depth"], case["pit_depth_m"], 5.0),
            "horizontal_clearance": _numeric(query["horizontal"], case["minimum_horizontal_clearance_m"], 20.0),
            "vertical_clearance": _numeric(query["vertical"], case["minimum_vertical_clearance_m"], 10.0),
            "letter_semantics": _cosine(str(query["text"]), f"{case['project_name']}\n{case['incoming_text']}\n{case['reply_text'][:1600]}"),
        }
        available = [(key, score) for key, score in components.items() if score is not None]
        denominator = sum(weights[key] for key, _ in available)
        score = sum(weights[key] * value for key, value in available) / denominator if denominator else 0.0
        matches.append({
            "history_case_id": case["case_id"],
            "history_quality_status": case["quality_status"],
            "history_quality_issues": case["quality_issues"],
            "project_name": case["project_name"],
            "stage": case["stage"],
            "similarity_score": round(score, 4),
            "component_scores": {key: (None if value is None else round(value, 4)) for key, value in components.items()},
            "primary_reply_file": case["primary_reply_file"],
            "editable_reply_file": case["editable_reply_file"],
            "official_reply_file": case["official_reply_file"],
            "incoming_file": case["incoming_file"],
            "advice_text": case["advice_text"],
            "advice_items": case["advice_items"],
            "advice_is_verbatim": True,
        })
    matches.sort(key=lambda item: float(item["similarity_score"]), reverse=True)
    top = matches[:top_k]
    selected = top[0] if top else None
    threshold_met = bool(selected and float(selected["similarity_score"]) >= minimum_score)
    return {
        "match_status": "matched" if threshold_met else ("best_available" if selected else "not_available"),
        "minimum_score": minimum_score,
        "threshold_met": threshold_met,
        "selected_match": selected,
        "candidates": top,
        "query_summary": query,
        "note": (
            "selected_match始终为当前数据库中相似度最高的可用回函；达到阈值时作为高可信范例，"
            "未达到阈值时仅作为语言风格参考，不直接沿用其中的项目事实。"
            if selected else "数据库中没有可用于匹配的历史回函。"
        ),
    }
