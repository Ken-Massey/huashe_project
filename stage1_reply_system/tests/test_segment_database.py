from pathlib import Path
import unittest

from stage1_reply_system.input_builder import build_input
from stage1_reply_system.segment_database import (
    build_autofill_suggestion,
    delete_segment,
    find_nearby_segments,
    haversine_distance_m,
    list_segments,
    save_segment,
)


def segment(**overrides):
    values = {
        "line_name": "1号线",
        "section_name": "甲站至乙站区间",
        "structure_method": "盾构",
        "structure_category": "地下装配式",
        "structure_condition": "较好",
        "buried_depth_m": 16.5,
        "longitude": 118.8000,
        "latitude": 32.0600,
        "source_project": "已核实资料",
        "source_file": None,
        "notes": None,
    }
    values.update(overrides)
    return values


class SegmentDatabaseTests(unittest.TestCase):
 def setUp(self):
    import tempfile
    self.tempdir = tempfile.TemporaryDirectory()
    self.database = Path(self.tempdir.name) / "segments.sqlite3"

 def tearDown(self):
    self.tempdir.cleanup()

 def test_segment_crud_and_soft_delete(self):
    database = self.database
    segment_id = save_segment(segment(), database)
    records = list_segments(database)
    assert records[0]["id"] == segment_id
    assert records[0]["buried_depth_m"] == 16.5

    save_segment(segment(buried_depth_m=18.0), database, segment_id=segment_id)
    assert list_segments(database)[0]["buried_depth_m"] == 18.0
    assert delete_segment(segment_id, database) is True
    assert list_segments(database) == []
    assert len(list_segments(database, include_inactive=True)) == 1


 def test_haversine_and_nearby_ranking(self):
    database = self.database
    near_other_line = save_segment(
        segment(line_name="2号线", section_name="近点", longitude=118.8001), database
    )
    matching_line = save_segment(
        segment(section_name="线路一致点", longitude=118.8004), database
    )
    distance = haversine_distance_m(32.06, 118.80, 32.06, 118.801)
    assert 90 < distance < 100

    matches = find_nearby_segments(
        32.06, 118.80, database, line_name="1号线", max_distance_m=1_000
    )
    assert matches[0]["id"] == matching_line
    assert matches[0]["line_match"] is True
    assert {item["id"] for item in matches} == {near_other_line, matching_line}


 def test_autofill_is_traceable_and_requires_confirmation(self):
    database = self.database
    save_segment(segment(), database)
    match = find_nearby_segments(32.06, 118.80, database, max_distance_m=500)[0]
    suggestion = build_autofill_suggestion(match)
    assert suggestion["metro_section_name"] == "甲站至乙站区间"
    assert suggestion["autofill_source"]["confirmed_by_user"] is False
    assert suggestion["autofill_source"]["source_type"] == "segment_database"


 def test_input_builder_preserves_confirmed_autofill_source(self):
    letter = Path(self.tempdir.name) / "letter.pdf"
    letter.write_bytes(b"pdf")
    source = {
        "source_type": "segment_database",
        "source_id": "7",
        "source_name": "1号线 / 甲站至乙站区间",
        "distance_m": 25.0,
        "confidence": 0.95,
        "confirmed_by_user": True,
    }
    result = build_input({"incoming_letter": letter, "case_id": "x", "autofill_source": source})
    assert result["metro_structure"]["autofill_source"] == source


 def test_invalid_coordinates_are_rejected(self):
    with self.assertRaises(ValueError):
        save_segment(segment(latitude=100), self.database)
