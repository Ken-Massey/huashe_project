import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from stage1_reply_system.history.advice import extract_attention_subsection
from stage1_reply_system.history.database import SCHEMA
from stage1_reply_system.review_generation import build_review_package, render_reply_draft_markdown


ADVICE = """1. 历史项目位于地铁北侧，净距12米。
2. 为确保安全，请贵司注意如下事项：
（1）开展既有结构现状调查。
（2）施工期间开展变形监测。
3. 施工方案应另行报审。"""


def complete_input() -> dict:
    return {
        "case_id": "TEST-001",
        "project": {
            "project_name": "测试基坑工程", "applicant": "测试单位", "project_stage": "规划",
            "project_type": "基坑", "relative_relationship": "单侧", "project_address": "测试路",
            "construction_content": "新建基坑", "other_involvements": [],
        },
        "metro_structure": {
            "structure_method": "盾构", "structure_category": "地下装配式",
            "structure_condition": "较好", "metro_line_name": "1号线",
            "outer_diameter_or_width_m": 6.0, "is_cross_river_segment": False,
        },
        "geology": {"is_soft_soil": False},
        "pit": {
            "pit_depth_m": 8.0, "minimum_horizontal_clearance_m": 8.0,
            "minimum_vertical_clearance_m": None, "support_components": ["围护桩"],
        },
        "review_context": {"is_in_control_protection_zone": True},
    }


def create_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA)
    connection.execute(
        """INSERT INTO reply_cases (
            fingerprint, project_name, project_root, stage, project_type, relative_relationship,
            structure_methods_json, metro_lines_json, pit_depth_m, minimum_horizontal_clearance_m,
            minimum_vertical_clearance_m, incoming_file, incoming_text, primary_reply_file,
            editable_reply_file, official_reply_file, reply_files_json, reply_text, advice_text,
            advice_items_json, extraction_json, pair_score, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("review-test", "测试基坑工程", "x", "规划", "基坑", "单侧", '["盾构"]', '["1号线"]',
         8.0, 8.0, None, "in.pdf", "测试基坑工程", "reply.doc", None, None, '["reply.doc"]',
         ADVICE, ADVICE, '["1", "2", "3"]', '{}', 1.0, "2026-07-20"),
    )
    connection.commit()
    connection.close()


class AttentionTests(unittest.TestCase):
    def test_attention_excludes_old_project_facts_and_later_top_level_item(self):
        result = extract_attention_subsection(ADVICE)
        self.assertEqual(len(result["attention_items"]), 2)
        self.assertNotIn("净距12米", result["attention_text"])
        self.assertNotIn("另行报审", result["attention_text"])


class ReviewPackageTests(unittest.TestCase):
    def test_complete_package_keeps_function_trace_and_verbatim_attention(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "history.sqlite3"
            create_database(database)
            package = build_review_package(complete_input(), database, letter_text="测试基坑工程")
            self.assertEqual(package["overall_status"], "ready_for_human_review")
            self.assertEqual(package["audit_opinions"][0]["function"], "stage1_reply_system.rules.setback.evaluate_setback_distance")
            self.assertEqual(len(package["historical_advice"]["attention_items"]), 2)
            self.assertFalse(package["formal_issuance_allowed"])

    def test_missing_data_blocks_formal_conclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "history.sqlite3"
            create_database(database)
            data = complete_input()
            data["pit"]["support_components"] = []
            data["pit"]["minimum_horizontal_clearance_m"] = None
            data["metro_structure"]["outer_diameter_or_width_m"] = None
            data["review_context"]["is_in_control_protection_zone"] = None
            package = build_review_package(data, database)
            self.assertEqual(package["overall_status"], "blocked_by_missing_data")
            fields = {item["field"] for item in package["missing_required_inputs"]}
            self.assertIn("pit.support_components", fields)
            self.assertIn("pit.minimum_horizontal_clearance_m", fields)
            self.assertNotIn("pit.minimum_vertical_clearance_m", fields)
            self.assertIn("review_context.is_in_control_protection_zone", fields)
            draft = render_reply_draft_markdown(package)
            self.assertIn("关于测试基坑工程规划方案征求地铁意见的复函", draft)
            self.assertIn("测试单位：", draft)
            self.assertIn("（1）开展既有结构现状调查。", draft)

    def test_failed_setback_requires_special_study(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "history.sqlite3"
            create_database(database)
            data = complete_input()
            data["pit"]["minimum_horizontal_clearance_m"] = 2.0
            package = build_review_package(data, database)
            self.assertEqual(package["overall_status"], "requires_special_study")
            self.assertEqual(package["calculation"]["decisions"]["setback_distance"]["status"], "fail")
            self.assertEqual(package["audit_opinions"][0]["review_status"], "requires_revision")


if __name__ == "__main__":
    unittest.main()
