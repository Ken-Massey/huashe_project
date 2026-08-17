import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from stage1_reply_system.history.advice import extract_advice_section, infer_metadata, normalize_title
from stage1_reply_system.history.database import (
    SCHEMA,
    history_database_stats,
    load_history_cases,
    set_history_case_active,
)
from stage1_reply_system.history.matcher import match_similar_replies


REPLY_TEXT = """关于测试基坑工程规划方案征求地铁意见的复函
经研究，具体意见函复如下：
1. 项目位于地铁1号线盾构区间北侧，基坑深度8米，最小水平净距12米。
2. 原则同意，为确保安全，请注意如下事项：
（1）开展现状调查。
（2）开展安全评估。
3. 施工前应书面征求意见。
特此函复。
"""


class AdviceTests(unittest.TestCase):
    def test_extracts_complete_verbatim_opinion_body(self):
        result = extract_advice_section(REPLY_TEXT)
        self.assertEqual(result["status"], "extracted")
        self.assertTrue(result["advice_text"].startswith("1. 项目位于"))
        self.assertIn("3. 施工前", result["advice_text"])
        self.assertNotIn("特此函复", result["advice_text"])
        self.assertEqual(len(result["advice_items"]), 3)

    def test_title_normalization_unifies_editable_and_stamped_names(self):
        editable = "[BHQ]关于测试工程规划方案征求地铁意见的复函.doc"
        stamped = "宁地铁保护〔2024〕1002号 关于测试工程规划方案征求地铁意见的复函.pdf"
        self.assertEqual(normalize_title(editable), normalize_title(stamped))

    def test_infers_measured_values(self):
        metadata = infer_metadata(REPLY_TEXT)
        self.assertEqual(metadata["stage"], "规划")
        self.assertEqual(metadata["project_type"], "基坑")
        self.assertEqual(metadata["relative_relationship"], "单侧")
        self.assertEqual(metadata["pit_depth_m"], 8.0)
        self.assertEqual(metadata["minimum_horizontal_clearance_m"], 12.0)


class MatcherTests(unittest.TestCase):
    def test_matches_and_returns_verbatim_advice(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "history.sqlite3"
            connection = sqlite3.connect(database)
            connection.executescript(SCHEMA)
            connection.execute(
                """INSERT INTO reply_cases (
                    fingerprint, project_name, project_root, stage, project_type, relative_relationship,
                    structure_methods_json, metro_lines_json, pit_depth_m,
                    minimum_horizontal_clearance_m, minimum_vertical_clearance_m,
                    incoming_file, incoming_text, primary_reply_file, editable_reply_file,
                    official_reply_file, reply_files_json, reply_text, advice_text,
                    advice_items_json, extraction_json, pair_score, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("abc", "测试基坑工程", "x", "规划", "基坑", "单侧", '["盾构"]', '["1号线"]',
                 8.0, 12.0, None, "in.pdf", "测试基坑位于地铁北侧", "reply.doc", None, None,
                 '["reply.doc"]', REPLY_TEXT, "原样审核意见", '["原样审核意见"]', '{}', 1.0, "2026-07-20"),
            )
            connection.commit()
            connection.close()
            query = {
                "project": {"project_name": "测试基坑工程", "project_stage": "规划", "project_type": "基坑", "relative_relationship": "单侧"},
                "metro_structure": {"structure_method": "盾构", "metro_line_name": "1号线"},
                "pit": {"pit_depth_m": 8.0, "minimum_horizontal_clearance_m": 12.0, "minimum_vertical_clearance_m": None},
            }
            result = match_similar_replies(query, database, letter_text="测试基坑位于地铁北侧")
            self.assertEqual(result["match_status"], "matched")
            self.assertEqual(result["selected_match"]["advice_text"], "原样审核意见")
            self.assertTrue(result["selected_match"]["advice_is_verbatim"])

    def test_inactive_case_is_not_used_for_matching(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "history.sqlite3"
            connection = sqlite3.connect(database)
            connection.executescript(SCHEMA)
            connection.execute(
                """INSERT INTO reply_cases (
                    fingerprint, project_name, project_root, stage, project_type, relative_relationship,
                    structure_methods_json, metro_lines_json, incoming_file, incoming_text,
                    primary_reply_file, reply_files_json, reply_text, advice_text,
                    advice_items_json, extraction_json, pair_score, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("inactive", "停用案例", "x", "规划", "基坑", "单侧", '["盾构"]', '["1号线"]',
                 "in.pdf", "文字", "reply.doc", '["reply.doc"]', REPLY_TEXT, "停用意见",
                 '["停用意见"]', '{}', 1.0, "2026-07-20"),
            )
            connection.commit()
            connection.close()
            self.assertTrue(set_history_case_active(1, False, database))
            self.assertEqual(load_history_cases(database), [])
            self.assertEqual(len(load_history_cases(database, include_inactive=True)), 1)
            stats = history_database_stats(database)
            self.assertEqual(stats["inactive"], 1)
            query = {
                "project": {"project_name": "停用案例", "project_stage": "规划", "project_type": "基坑", "relative_relationship": "单侧"},
                "metro_structure": {"structure_method": "盾构", "metro_line_name": "1号线"},
                "pit": {},
            }
            result = match_similar_replies(query, database, letter_text="文字")
            self.assertIsNone(result["selected_match"])


if __name__ == "__main__":
    unittest.main()
