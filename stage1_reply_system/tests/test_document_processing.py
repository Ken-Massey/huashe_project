import copy
import unittest

from stage1_reply_system.document_processing.letter_fields import extract_letter_fields
from stage1_reply_system.document_processing.merge import merge_extracted_with_manual


def direct_extraction_fixture() -> dict:
    page_1 = (
        "关于测试基坑工程规划方案征求地铁意见的函\n"
        "南京市地下铁道工程建设指挥部：\n"
        "工程建设地点位于南京市测试区测试路。建设规模：新建基坑一座，基坑深度约8m。\n"
        "联系人：张三 13800138000"
    )
    page_2 = "测试建设有限公司\n2026年7月20日"
    return {
        "source_file": "test.pdf",
        "sha256": "abc",
        "page_count": 2,
        "extraction_method": "direct",
        "pages": [
            {
                "page": 1,
                "method": "direct",
                "text": page_1,
                "lines": [{"text": line, "confidence": 1.0, "bbox_pixels": None} for line in page_1.splitlines()],
            },
            {
                "page": 2,
                "method": "direct",
                "text": page_2,
                "lines": [{"text": line, "confidence": 1.0, "bbox_pixels": None} for line in page_2.splitlines()],
            },
        ],
    }


def manual_fixture() -> dict:
    return {
        "source_documents": [{"role": "incoming_letter", "path": "test.pdf", "sha256": None, "text_extraction_method": "not_extracted"}],
        "project": {
            "project_name": None,
            "applicant": None,
            "project_stage": "规划",
            "project_address": None,
            "construction_content": None,
        },
    }


class LetterFieldTests(unittest.TestCase):
    def test_extracts_core_fields_with_evidence(self):
        fields = extract_letter_fields(direct_extraction_fixture())["fields"]
        self.assertEqual(fields["project_name"]["value"], "测试基坑工程")
        self.assertEqual(fields["project_stage"]["value"], "规划")
        self.assertIn("南京市测试区", fields["project_location"]["value"])
        self.assertIn("新建基坑", fields["construction_content"]["value"])
        self.assertEqual(fields["contact_phone"]["value"], "13800138000")
        self.assertEqual(fields["project_location"]["source_page"], 1)

    def test_signature_is_capped_for_manual_review(self):
        fields = extract_letter_fields(direct_extraction_fixture())["fields"]
        self.assertEqual(fields["applicant"]["status"], "needs_review")
        self.assertLess(fields["applicant"]["confidence"], 0.75)

    def test_impossible_ocr_flow_unit_requires_review(self):
        fixture = direct_extraction_fixture()
        fixture["extraction_method"] = "ocr"
        fixture["pages"][0]["text"] = fixture["pages"][0]["text"].replace("基坑深度约8m", "规模16.5万m²/d")
        fixture["pages"][0]["lines"] = [
            {"text": line, "confidence": 0.9, "bbox_pixels": [[0, 0], [1, 0], [1, 1], [0, 1]]}
            for line in fixture["pages"][0]["text"].splitlines()
        ]
        fields = extract_letter_fields(fixture)["fields"]
        self.assertEqual(fields["construction_content"]["status"], "needs_review")
        self.assertIn("m3/d", fields["construction_content"]["review_note"])


class MergeTests(unittest.TestCase):
    def test_empty_manual_fields_are_filled(self):
        fields = extract_letter_fields(direct_extraction_fixture())
        result = merge_extracted_with_manual(manual_fixture(), fields)
        self.assertEqual(result["merged_input"]["project"]["project_name"], "测试基坑工程")
        self.assertTrue(any(item["field"] == "project.project_name" for item in result["applied_fields"]))
        self.assertTrue(any(item["field"] == "project.applicant" for item in result["review_required"]))

    def test_manual_value_wins_and_conflict_is_recorded(self):
        manual = copy.deepcopy(manual_fixture())
        manual["project"]["project_name"] = "人工确认名称"
        fields = extract_letter_fields(direct_extraction_fixture())
        result = merge_extracted_with_manual(manual, fields)
        self.assertEqual(result["merged_input"]["project"]["project_name"], "人工确认名称")
        self.assertTrue(any(item["field"] == "project.project_name" for item in result["conflicts"]))


if __name__ == "__main__":
    unittest.main()
