"""Build a complete stage-one Schema object from form values."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PROTECTION_ZONE_FLAGS = {
    "特别保护区": (True, True),
    "控制保护区（非特别保护区）": (True, False),
    "保护区外": (False, False),
    "待判断": (None, None),
}


METHOD_CATEGORY_DEFAULTS = {
    "明挖": "地下现浇",
    "暗挖（矿山法）": "地下现浇",
    "盾构": "地下装配式",
    "高架": "高架结构",
}


def build_input(values: dict[str, Any]) -> dict[str, Any]:
    zone_location = values.get("protection_zone_location")
    zone_flags = PROTECTION_ZONE_FLAGS.get(zone_location, (None, None))
    in_control_zone = values.get("is_in_control_protection_zone", zone_flags[0])
    in_special_zone = values.get("is_in_special_protection_zone", zone_flags[1])
    pdf_path = str(Path(values["incoming_letter"]).resolve())
    method = values.get("structure_method")
    category = values.get("structure_category") or (METHOD_CATEGORY_DEFAULTS.get(method) if method else None)
    source_documents = [{
        "role": "incoming_letter",
        "path": pdf_path,
        "sha256": None,
        "text_extraction_method": "not_extracted",
        "document_date": None,
        "page_count": None,
    }]
    for role, key in (("scheme", "scheme_file"), ("expert_opinion", "expert_opinion_file")):
        if values.get(key):
            source_documents.append({
                "role": role,
                "path": str(Path(values[key]).resolve()),
                "sha256": None,
                "text_extraction_method": "not_extracted",
                "document_date": None,
                "page_count": None,
            })
    return {
        "schema_version": "stage1_reply_input_v1",
        "case_id": values["case_id"],
        "source_documents": source_documents,
        "project": {
            "project_name": values.get("project_name"),
            "applicant": values.get("applicant"),
            "project_type": values.get("project_type"),
            "project_stage": values.get("project_stage"),
            "relative_relationship": values.get("relative_relationship"),
            "land_use_type": values.get("land_use_type"),
            "project_address": values.get("project_address"),
            "construction_content": values.get("construction_content"),
            "other_involvements": values.get("other_involvements", []),
            "location": {
                "longitude": values.get("longitude"),
                "latitude": values.get("latitude"),
                "map_label": values.get("map_label"),
            },
        },
        "metro_structure": {
            "metro_line_name": values.get("metro_line_name"),
            "metro_section_name": values.get("metro_section_name"),
            "structure_method": method,
            "structure_category": category,
            "structure_condition": values.get("structure_condition"),
            "buried_depth_m": values.get("buried_depth_m"),
            "original_excavation_depth_m": values.get("original_excavation_depth_m"),
            "outer_diameter_or_width_m": values.get("outer_diameter_or_width_m"),
            "mined_tunnel_span_m": values.get("mined_tunnel_span_m"),
            "elevated_pile_diameter_m": values.get("elevated_pile_diameter_m"),
            "is_special_section": values.get("is_special_section"),
            "disease_severity": values.get("disease_severity") or "未知",
            "is_cross_river_segment": values.get("is_cross_river_segment"),
            "autofill_source": values.get("autofill_source") or {
                "source_type": "manual",
                "source_id": None,
                "source_name": None,
                "distance_m": None,
                "confidence": None,
                "confirmed_by_user": True,
            },
        },
        "geology": {
            "terrain_zone": values.get("terrain_zone"),
            "is_soft_soil": values.get("is_soft_soil"),
            "is_complex_geology_or_hydrology": values.get("is_complex_geology_or_hydrology"),
            "has_geological_hazard": values.get("has_geological_hazard"),
            "geology_description": values.get("geology_description"),
        },
        "pit": {
            "pit_depth_m": values.get("pit_depth_m"),
            "pit_length_m": values.get("pit_length_m"),
            "pit_width_m": values.get("pit_width_m"),
            "pit_area_m2": values.get("pit_area_m2"),
            "minimum_horizontal_clearance_m": values.get("minimum_horizontal_clearance_m"),
            "minimum_vertical_clearance_m": values.get("minimum_vertical_clearance_m"),
            "support_components": values.get("support_components", []),
            "retaining_structure_type": values.get("retaining_structure_type"),
            "dewatering_method": values.get("dewatering_method"),
            "dewatering_involved": values.get("dewatering_involved"),
            "confined_water_drawdown": values.get("confined_water_drawdown"),
            "expert_opinion_text": values.get("expert_opinion_text"),
            "expert_opinion_file": values.get("expert_opinion_file"),
            "scheme_file": values.get("scheme_file"),
        },
        "review_context": {
            "protection_zone_location": zone_location or "待判断",
            "is_in_control_protection_zone": in_control_zone,
            "is_in_special_protection_zone": in_special_zone,
            "manual_notes": values.get("manual_notes"),
        },
    }
