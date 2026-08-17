import unittest

from audit_api.knowledge_base import infer_case_category, normalize_case_category


class KnowledgeCategoryTests(unittest.TestCase):
    def test_title_categories_take_priority(self):
        self.assertEqual(
            infer_case_category("某污水管定向钻穿越工程"),
            "管线类（非开挖）",
        )
        self.assertEqual(
            infer_case_category("燃气管沟槽开挖工程"),
            "管线类（明挖）",
        )
        self.assertEqual(
            infer_case_category("丰子河路道路及排水工程"),
            "道路桥梁类",
        )
        self.assertEqual(
            infer_case_category("产业园地下车库基坑工程"),
            "基坑类",
        )

    def test_extracted_features_are_used_as_fallback(self):
        self.assertEqual(
            infer_case_category("安全影响评估报告", features={"work_types": ["道路桥梁"]}),
            "道路桥梁类",
        )
        self.assertEqual(
            infer_case_category("安全影响评估报告", features={}),
            "其他类",
        )

    def test_manual_aliases_are_normalized(self):
        self.assertEqual(normalize_case_category("基坑"), "基坑类")
        self.assertEqual(normalize_case_category("道路桥梁"), "道路桥梁类")
        self.assertEqual(normalize_case_category("管线类（非开挖）"), "管线类（非开挖）")


if __name__ == "__main__":
    unittest.main()
