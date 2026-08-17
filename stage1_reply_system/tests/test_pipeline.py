import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stage1_reply_system.history.database import SCHEMA
from stage1_reply_system.input_builder import build_input
from stage1_reply_system.pipeline import run_stage1_pipeline
from stage1_reply_system.validation import validate_input


def form_values(pdf: Path) -> dict:
    return {
        "incoming_letter": str(pdf),
        "case_id": "PIPELINE-001",
        "project_name": "流水线测试基坑",
        "project_type": "基坑",
        "project_stage": "规划",
        "relative_relationship": "单侧",
        "structure_method": "盾构",
        "structure_condition": "较好",
        "terrain_zone": "非漫滩",
        "pit_depth_m": 8.0,
        "minimum_horizontal_clearance_m": 8.0,
        "support_components": ["围护桩"],
        "outer_diameter_or_width_m": 6.0,
        "is_soft_soil": False,
        "is_cross_river_segment": False,
        "is_in_control_protection_zone": True,
    }


def create_database(path: Path) -> None:
    advice = "2. 请注意如下事项：\n（1）施工前开展现状调查。\n3. 后续方案另行报审。"
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
        ("pipeline", "流水线测试基坑", "x", "规划", "基坑", "单侧", '["盾构"]', '[]',
         8.0, 8.0, None, "in.pdf", "流水线测试基坑", "reply.doc", None, None,
         '["reply.doc"]', advice, advice, '["注意事项"]', '{}', 1.0, "2026-07-20"),
    )
    connection.commit()
    connection.close()


class InputBuilderTests(unittest.TestCase):
    def test_builds_schema_valid_input_and_method_category_default(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "letter.pdf"
            pdf.write_bytes(b"pdf")
            data = build_input(form_values(pdf))
            self.assertEqual(validate_input(data), [])
            self.assertEqual(data["metro_structure"]["structure_category"], "地下装配式")


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_all_traceable_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "letter.pdf"
            pdf.write_bytes(b"pdf")
            database = root / "history.sqlite3"
            create_database(database)
            data = build_input(form_values(pdf))
            extraction = {
                "source_file": str(pdf), "sha256": "abc", "page_count": 1,
                "source_page_count": 1, "extraction_method": "direct", "is_scanned": False,
                "full_text": "流水线测试基坑规划方案征求意见的函",
                "pages": [{"page": 1, "method": "direct", "text": "流水线测试基坑规划方案征求意见的函", "lines": []}],
            }
            fields = {"source_sha256": "abc", "fields": {}}
            with patch("stage1_reply_system.pipeline.extract_pdf", return_value=extraction), patch(
                "stage1_reply_system.pipeline.extract_letter_fields", return_value=fields
            ):
                result = run_stage1_pipeline(pdf, data, database, root / "outputs", run_name="test")
            output = Path(result["output_dir"])
            expected = {
                "00_manual_input.json", "01_pdf_text.json", "02_extracted_fields.json",
                "03_merge_report.json", "04_merged_input.json", "05_calculation.json",
                "06_history_match.json", "07_review_package.json", "函件全文.txt",
                "审核意见.md", "回函草稿.md", "最终版复函.docx",
                "内部自动审核记录.docx", "run_summary.json",
            }
            self.assertTrue(expected.issubset({path.name for path in output.iterdir()}))
            self.assertEqual(result["summary"]["overall_status"], "ready_for_human_review")


if __name__ == "__main__":
    unittest.main()
