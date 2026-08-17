import re
from typing import Any, Callable


def _normalize(text: str) -> str:
    text = text.replace("\u3000", " ").replace("～", "~")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _join_wrapped_lines(text: str) -> str:
    return re.sub(r"\s*\n\s*", "", text).strip()


def _normalize_date(text: str) -> str:
    numbers = re.findall(r"\d+", text)
    if len(numbers) < 3:
        return text
    year, month, day = map(int, numbers[:3])
    return f"{year:04d}-{month:02d}-{day:02d}"


def _page_text(extraction: dict[str, Any], page: int) -> str:
    for item in extraction["pages"]:
        if item["page"] == page:
            footer = "\n".join(line["text"] for line in item.get("footer_lines", []))
            return item["text"] + ("\n" + footer if footer else "")
    return ""


def _find_page(extraction: dict[str, Any], evidence: str) -> int | None:
    compact = re.sub(r"\s+", "", evidence)
    for page in extraction["pages"]:
        searchable = _page_text(extraction, page["page"])
        if compact and compact in re.sub(r"\s+", "", searchable):
            return page["page"]
    return None


def _field(
    value: Any,
    confidence: float,
    page: int | None,
    source_text: str,
    method: str,
    status: str | None = None,
) -> dict[str, Any]:
    if value in (None, "", []):
        return {
            "value": None,
            "confidence": 0.0,
            "source_page": None,
            "source_text": "",
            "extraction_method": method,
            "status": "not_found",
        }
    return {
        "value": value,
        "confidence": round(confidence, 3),
        "source_page": page,
        "source_text": source_text.strip(),
        "extraction_method": method,
        "status": status or ("needs_review" if confidence < 0.75 else "extracted"),
    }


def _regex_field(
    text: str,
    extraction: dict[str, Any],
    pattern: str,
    group: int | str = 1,
    confidence: float = 0.85,
    flags: int = re.S,
    transform: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    match = re.search(pattern, text, flags)
    if not match:
        return _field(None, 0.0, None, "", extraction["extraction_method"])
    raw_value = match.group(group).strip(" ，,。；;：:")
    value = transform(raw_value) if transform else raw_value
    evidence = match.group(0)
    return _field(value, confidence, _find_page(extraction, evidence), evidence, extraction["extraction_method"])


def _extract_title(extraction: dict[str, Any]) -> dict[str, Any]:
    lines = extraction["pages"][0]["lines"] if extraction["pages"] else []
    title_lines: list[dict[str, Any]] = []
    started = False
    for line in lines[:10]:
        if "关于" in line["text"]:
            started = True
        if started:
            title_lines.append(line)
        if started and "函" in line["text"]:
            break
    title = "".join(line["text"] for line in title_lines)
    confidence = sum(line["confidence"] for line in title_lines) / len(title_lines) if title_lines else 0.0
    return _field(title, confidence, 1 if title else None, title, extraction["extraction_method"])


def _extract_applicant(extraction: dict[str, Any]) -> dict[str, Any]:
    last_page = extraction["pages"][-1] if extraction["pages"] else {"lines": [], "page": None}
    all_lines = last_page["lines"] + last_page.get("footer_lines", [])
    candidates = [
        line for line in all_lines
        if re.search(r"(?:有限公司|集团|委员会|管理局|人民政府|指挥部)$", line["text"])
        and "联系人" not in line["text"]
    ]
    if not candidates:
        return _field(None, 0.0, None, "", extraction["extraction_method"])
    candidate = max(candidates, key=lambda item: (len(item["text"]), item["confidence"]))
    confidence = min(float(candidate["confidence"]), 0.68)
    return _field(
        candidate["text"],
        confidence,
        last_page["page"],
        candidate["text"],
        extraction["extraction_method"],
        "needs_review",
    )


def _extract_measurements(text: str, extraction: dict[str, Any]) -> dict[str, Any]:
    patterns = [
        r"(?:DN|dn|d)\s*\d{3,4}",
        r"(?:长约|约)\s*\d+(?:\.\d+)?\s*(?:千米|公里|m|米)",
        r"埋深约\s*\d+(?:\.\d+)?\s*(?:m|米)\s*[~至-]\s*\d+(?:\.\d+)?\s*(?:m|米)?",
        r"\d+(?:\.\d+)?\s*万\s*m[³3²2]?/d",
    ]
    values: list[str] = []
    for pattern in patterns:
        values.extend(match.group(0) for match in re.finditer(pattern, text, re.I))
    values = list(dict.fromkeys(value.strip() for value in values))
    evidence = "；".join(values)
    field = _field(values, 0.84, _find_page(extraction, values[0]) if values else None, evidence, extraction["extraction_method"])
    if extraction["extraction_method"] != "direct" and re.search(r"m[²2]/d", evidence, re.I):
        field["confidence"] = min(field["confidence"], 0.72)
        field["status"] = "needs_review"
        field["review_note"] = "OCR得到面积/时间单位m2/d，可能将体积流量单位m3/d识错，必须核对原图。"
    return field


def extract_letter_fields(extraction: dict[str, Any]) -> dict[str, Any]:
    text = _normalize("\n".join(page["text"] for page in extraction["pages"]))
    title = _extract_title(extraction)
    title_text = title["value"] or ""
    stage_value = next((stage for stage in ("出让", "规划", "设计", "施工") if stage in title_text), None)

    construction_content = _regex_field(
        text,
        extraction,
        r"建设规模[：:]\s*(.+?)(?=\n?本工程|\n?目前本项目|$)",
        confidence=0.88,
        transform=_join_wrapped_lines,
    )
    if extraction["extraction_method"] != "direct" and construction_content["value"] and re.search(r"m[²2]/d", construction_content["value"], re.I):
        construction_content["confidence"] = min(construction_content["confidence"], 0.72)
        construction_content["status"] = "needs_review"
        construction_content["review_note"] = "OCR得到面积/时间单位m2/d，可能将体积流量单位m3/d识错，必须核对原图。"

    fields = {
        "document_title": title,
        "project_name": _regex_field(
            title_text + "\n" + text,
            extraction,
            r"关于\s*(.+?工程)(?:规划|设计|施工|出让|条件|方案|征求)",
            confidence=0.92,
        ),
        "applicant": _extract_applicant(extraction),
        "recipient": _regex_field(
            text,
            extraction,
            r"^([^\n：:]{2,40}(?:指挥部|集团|公司|管理局|委员会))[：:]",
            confidence=0.9,
            flags=re.M,
        ),
        "project_stage": _field(stage_value, 0.95 if stage_value else 0.0, 1 if stage_value else None, title_text, extraction["extraction_method"]),
        "project_location": _regex_field(
            text,
            extraction,
            r"工程建设地点(?:位于|为)\s*(.+?)(?=建设规模[：:]|。\s*建设规模|\n\s*建设规模)",
            confidence=0.9,
            transform=_join_wrapped_lines,
        ),
        "construction_content": construction_content,
        "contact_name": _regex_field(
            text,
            extraction,
            r"联系人[：:]?\s*([\u4e00-\u9fff]{2,4})",
            confidence=0.82,
            flags=0,
        ),
        "contact_phone": _regex_field(
            text,
            extraction,
            r"(1[3-9]\d{9})",
            confidence=0.95,
            flags=0,
        ),
        "letter_date": _regex_field(
            _page_text(extraction, extraction["page_count"]),
            extraction,
            r"(20\d{2}\s*[./-]?\s*年?\s*\d{1,2}\s*[月./-]\s*\d{1,2}\s*日?)",
            confidence=0.65 if extraction["extraction_method"] != "direct" else 0.95,
            flags=0,
            transform=_normalize_date,
        ),
        "measurements": _extract_measurements(text, extraction),
    }
    return {
        "format_version": "incoming_letter_fields_v1",
        "source_file": extraction["source_file"],
        "source_sha256": extraction["sha256"],
        "fields": fields,
    }
