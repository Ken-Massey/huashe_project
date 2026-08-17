import json
import tempfile
import unittest
from pathlib import Path

from audit_api.rag_audit import (
    _fallback_report,
    _paragraph_chunks,
    _rank_case_chunks,
    _validate_layered_report,
)


class FullTextRetrievalTests(unittest.TestCase):
    def test_paragraph_jsonl_keeps_trace_coordinates(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "case.paragraphs.jsonl"
            rows = [
                {"paragraph_id": 10, "source_page": 3, "text": "基坑采用轻型井点降水。"},
                {"paragraph_id": 11, "source_page": 3, "text": "应监测盾构隧道附近地下水位。"},
            ]
            source.write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
                encoding="utf-8",
            )

            chunks = _paragraph_chunks(source, target_size=200)

            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0]["paragraph_start"], 10)
            self.assertEqual(chunks[0]["paragraph_end"], 11)
            self.assertEqual(chunks[0]["source_page"], 3)
            self.assertIn("轻型井点降水", chunks[0]["text"])

    def test_topic_retrieval_finds_relevant_full_text(self):
        chunks = [
            {"chunk_id": "C0001", "text": "项目名称与建设单位。"},
            {"chunk_id": "C0002", "text": "基坑采用轻型井点降水，应加强地下水位和沉降监测。"},
            {"chunk_id": "C0003", "text": "建筑面积及停车位数量。"},
        ]

        selected = _rank_case_chunks(chunks, ["工程与水文地质 降水 地下水 沉降"], limit=2)

        self.assertEqual(selected[0]["chunk_id"], "C0002")

    def test_numeric_risk_signal_is_kept_without_exact_query_wording(self):
        chunks = [
            {"chunk_id": "C0001", "text": "项目建设单位和总建筑面积。"},
            {"chunk_id": "C0002", "text": "监测结果显示既有结构最大沉降为12.6mm，接近报警值。"},
        ]

        selected = _rank_case_chunks(chunks, ["既有结构状态 病害 检测"], limit=2)

        self.assertIn("C0002", {item["chunk_id"] for item in selected})

    def test_fallback_does_not_claim_no_risk(self):
        result = _fallback_report({"results": []}, [], "AI输出失败")

        self.assertEqual(result["overall_risk_level"], "待分析")
        self.assertIn("不能据此认定项目不存在风险", result["overview"])
        self.assertTrue(result["required_supplements"])

    def test_quality_gate_drops_claim_conflicting_with_hard_rule(self):
        value = {
            "compliance_sections": [{
                "title": "空间关系",
                "items": [{
                    "name": "净距违规",
                    "analysis": "本项目违反规程要求，不符合最小净距。",
                    "clause_refs": ["3.1.5"],
                    "case_evidence": ["最小净距20m"],
                }],
            }],
            "engineering_risk_sections": [],
        }
        clauses = [{"clause_no": "3.1.5", "clause_text": "地下隧道结构外边线外侧不小于5m。"}]
        hard_findings = [{"clause": "3.1.5", "status": "compliant"}]

        result = _validate_layered_report(value, clauses, hard_findings)

        self.assertEqual(result["compliance_sections"], [])
        self.assertIn("确定性计算", result["quality_warnings"][0])


if __name__ == "__main__":
    unittest.main()
