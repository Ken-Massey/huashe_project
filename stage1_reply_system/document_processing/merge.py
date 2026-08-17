import copy
from typing import Any


FIELD_MAPPING = {
    "project_name": "project.project_name",
    "applicant": "project.applicant",
    "project_stage": "project.project_stage",
    "project_location": "project.project_address",
    "construction_content": "project.construction_content",
}


def _get_path(data: dict[str, Any], path: str) -> Any:
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _set_path(data: dict[str, Any], path: str, value: Any) -> None:
    target = data
    parts = path.split(".")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def merge_extracted_with_manual(
    manual_input: dict[str, Any],
    extracted_fields: dict[str, Any],
    minimum_confidence: float = 0.75,
) -> dict[str, Any]:
    merged = copy.deepcopy(manual_input)
    applied: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    review_required: list[dict[str, Any]] = []

    for extracted_name, target_path in FIELD_MAPPING.items():
        field = extracted_fields["fields"].get(extracted_name, {})
        extracted_value = field.get("value")
        if extracted_value in (None, ""):
            continue
        manual_value = _get_path(merged, target_path)
        record = {
            "field": target_path,
            "manual_value": manual_value,
            "extracted_value": extracted_value,
            "confidence": field.get("confidence", 0.0),
            "source_page": field.get("source_page"),
            "source_text": field.get("source_text", ""),
        }
        if manual_value not in (None, ""):
            if str(manual_value).strip() != str(extracted_value).strip():
                record["resolution"] = "kept_manual"
                conflicts.append(record)
            continue
        if field.get("confidence", 0.0) >= minimum_confidence and field.get("status") == "extracted":
            _set_path(merged, target_path, extracted_value)
            record["resolution"] = "used_extracted"
            applied.append(record)
        else:
            record["resolution"] = "manual_confirmation_required"
            review_required.append(record)

    letter_date = extracted_fields["fields"].get("letter_date", {})
    incoming_document = next(
        (document for document in merged.get("source_documents", []) if document.get("role") == "incoming_letter"),
        None,
    )
    if incoming_document is not None and letter_date.get("value"):
        record = {
            "field": "source_documents[incoming_letter].document_date",
            "manual_value": incoming_document.get("document_date"),
            "extracted_value": letter_date["value"],
            "confidence": letter_date.get("confidence", 0.0),
            "source_page": letter_date.get("source_page"),
            "source_text": letter_date.get("source_text", ""),
        }
        if incoming_document.get("document_date"):
            if incoming_document["document_date"] != letter_date["value"]:
                record["resolution"] = "kept_manual"
                conflicts.append(record)
        elif letter_date.get("confidence", 0.0) >= minimum_confidence and letter_date.get("status") == "extracted":
            incoming_document["document_date"] = letter_date["value"]
            record["resolution"] = "used_extracted"
            applied.append(record)
        else:
            record["resolution"] = "manual_confirmation_required"
            review_required.append(record)

    for document in merged.get("source_documents", []):
        if document.get("role") == "incoming_letter":
            document["sha256"] = extracted_fields.get("source_sha256")
            document["text_extraction_method"] = next(
                (
                    field.get("extraction_method")
                    for field in extracted_fields["fields"].values()
                    if field.get("extraction_method")
                ),
                document.get("text_extraction_method", "not_extracted"),
            )

    return {
        "format_version": "manual_extraction_merge_v1",
        "merged_input": merged,
        "applied_fields": applied,
        "conflicts": conflicts,
        "review_required": review_required,
        "merge_policy": "人工值优先；空白人工字段仅接受置信度不低于阈值且状态为extracted的抽取值。",
    }
