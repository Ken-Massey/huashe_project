"""Parse project identity and exact review/advice sections from reply text."""

from __future__ import annotations

import re
from pathlib import Path


STAGE_PATTERNS = (
    ("施工", re.compile(r"施工(?:阶段|方案|图)?")),
    ("设计", re.compile(r"设计(?:备案|阶段|方案|文件|图)?")),
    ("规划", re.compile(r"规划(?:阶段|方案|设计)?")),
    ("出让", re.compile(r"出让(?:阶段|条件)?")),
)


def infer_stage(*texts: str) -> str | None:
    joined = " ".join(texts)
    explicit = re.search(r"(出让|规划|设计|施工)阶段", joined)
    if explicit:
        return explicit.group(1)
    if "设计备案" in joined:
        return "设计"
    for stage, pattern in STAGE_PATTERNS:
        if pattern.search(joined):
            return stage
    return None


def normalize_title(text: str) -> str:
    value = Path(text).stem
    value = re.sub(r"^\[BHQ\]", "", value, flags=re.I)
    value = re.sub(r"^(?:宁|南京)?地铁[^号]{0,30}号\s*", "", value)
    value = re.sub(r"^[（(]?\d{4}[）)]?\s*", "", value)
    value = re.sub(r"^(?:关于|对)", "", value)
    value = re.sub(r"(?:征求)?(?:地铁)?意见的?(?:复函|函复)$", "", value)
    value = re.sub(r"(?:复函|回函)$", "", value)
    value = re.sub(r"[\s_—－-]+", "", value)
    value = re.sub(r"[，。、“”‘’()（）\[\]【】]", "", value)
    return value


def extract_project_name(title_or_text: str) -> str | None:
    first_lines = [line.strip() for line in title_or_text.splitlines()[:20] if line.strip()]
    candidates = [line for line in first_lines if "复函" in line or "回函" in line]
    raw = candidates[0] if candidates else first_lines[0] if first_lines else title_or_text
    value = normalize_title(raw)
    value = re.sub(r"(?:规划设计|规划|设计|施工|出让)(?:阶段|方案|图设计|备案)?$", "", value)
    return value or None


def extract_advice_section(text: str) -> dict[str, object]:
    """Return the exact opinion body and its top-level numbered items."""
    anchors = (
        r"(?:经研究[，,]?)?具体意见(?:函复)?如下[：:]",
        r"(?:经研究[，,]?)?(?:现将)?(?:有关|具体)?意见(?:函复)?如下[：:]",
        r"请[^。；\n]{0,40}注意如下事项[：:]",
        r"注意事项(?:如下)?[：:]",
    )
    start = None
    anchor = None
    for pattern in anchors:
        match = re.search(pattern, text)
        if match and (start is None or match.start() < start):
            start = match.end()
            anchor = match.group(0)
    if start is None:
        return {"advice_text": "", "advice_items": [], "anchor": None, "status": "not_found"}

    body = text[start:]
    closing = re.search(r"\n\s*(?:特此函复|此复[。.]?|专此函复)[。.]?", body)
    if closing:
        body = body[: closing.start()]
    body = body.strip()

    marker = re.compile(r"(?m)^\s*(?P<marker>(?:\d{1,2}[.、]|[一二三四五六七八九十]+[、.]))\s*")
    matches = list(marker.finditer(body))
    items: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        item = body[match.start():end].strip()
        if item:
            items.append(item)
    if not items and body:
        items = [body]
    return {
        "advice_text": body,
        "advice_items": items,
        "anchor": anchor,
        "status": "extracted" if body else "empty",
    }


def extract_attention_subsection(text: str) -> dict[str, object]:
    """Extract only the reusable attention items, excluding old project facts."""
    anchors = (
        r"(?:请[^。；\n]{0,50})?注意如下事项[：:]",
        r"注意事项(?:如下)?[：:]",
        r"按如下意见(?:修改完善|实施)[^：:\n]{0,30}[：:]",
    )
    match = next((found for pattern in anchors if (found := re.search(pattern, text))), None)
    if not match:
        return {"attention_text": "", "attention_items": [], "anchor": None, "status": "not_found"}

    tail = text[match.end():]
    next_top_level = re.search(r"(?m)^\s*\d{1,2}[.、]\s*", tail)
    if next_top_level:
        tail = tail[:next_top_level.start()]
    tail = tail.strip()

    marker = re.compile(r"(?m)^\s*(?:（\d{1,2}）|\(\d{1,2}\))\s*")
    markers = list(marker.finditer(tail))
    items: list[str] = []
    for index, item_match in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(tail)
        item = tail[item_match.start():end].strip()
        if item:
            items.append(item)
    if not items and tail:
        items = [tail]
    return {
        "attention_text": tail,
        "attention_items": items,
        "anchor": match.group(0),
        "status": "extracted" if tail else "empty",
    }


def infer_metadata(text: str, path_text: str = "") -> dict[str, object]:
    combined = f"{path_text}\n{text}"
    headline = next(
        (line for line in text.splitlines()[:20] if re.search(r"复函|回函|征求.*意见", line)),
        "",
    )
    methods = [method for method in ("明挖", "暗挖", "盾构", "高架") if method in combined]
    lines = sorted(set(re.findall(r"(?:地铁|轨道交通)?([0-9S号线+、～~至—-]{1,20}号线)", combined)))
    if re.search(r"穿越|下穿|上跨|交叉", combined):
        relationship = "交叉"
    elif re.search(r"两侧|双侧", combined):
        relationship = "双侧"
    elif re.search(r"东侧|西侧|南侧|北侧|一侧|单侧|邻近", combined):
        relationship = "单侧"
    else:
        relationship = None
    project_type = "基坑" if re.search(r"基坑|工作井|接收井|竖井", combined) else None

    def measurement(patterns: tuple[str, ...]) -> float | None:
        for pattern in patterns:
            match = re.search(pattern, combined, flags=re.S)
            if match:
                return float(match.group(1))
        return None

    return {
        # A reply often mentions later construction requirements regardless of its
        # current stage. Path/title therefore outrank the full opinion body.
        "stage": infer_stage(path_text) or infer_stage(headline) or infer_stage(text),
        "project_type": project_type,
        "relative_relationship": relationship,
        "structure_methods": methods,
        "metro_lines": lines,
        "pit_depth_m": measurement((
            r"基坑(?:开挖)?深(?:度)?[^\d]{0,12}(\d+(?:\.\d+)?)\s*(?:m|米)",
            r"开挖深度[^\d]{0,12}(\d+(?:\.\d+)?)\s*(?:m|米)",
        )),
        "minimum_horizontal_clearance_m": measurement((
            r"最小水平(?:投影)?(?:净距|距离)[^\d]{0,15}(\d+(?:\.\d+)?)\s*(?:m|米)",
            r"水平(?:净距|距离)[^\d]{0,15}(\d+(?:\.\d+)?)\s*(?:m|米)",
        )),
        "minimum_vertical_clearance_m": measurement((
            r"最小竖向(?:净距|距离)[^\d]{0,15}(\d+(?:\.\d+)?)\s*(?:m|米)",
            r"竖向(?:净距|距离)[^\d]{0,15}(\d+(?:\.\d+)?)\s*(?:m|米)",
        )),
    }
