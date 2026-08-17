import tempfile
import unittest
from pathlib import Path

from audit_api.ima_rag import (
    SemanticIndex,
    _audit_context_hash,
    _audit_packet_batch,
    _fast_dimensions,
    _history_context_text,
    _packet_context,
    _regulation_reference,
    _regulation_source_name,
    _validate_report,
)


class FakeEmbeddingAgent:
    def embed(self, texts):
        vectors = []
        for text in texts:
            vectors.append([
                float("监测" in text),
                float("基坑" in text),
                float("净距" in text),
            ])
        return vectors


class ImaRagTests(unittest.TestCase):
    def test_project_history_changes_cache_context_and_enters_prompt(self):
        case_without_history = {"project": {"project_name": "测试项目"}}
        case_with_history = {
            **case_without_history,
            "project_archive_context": {
                "previous_stages": [{
                    "stage_name": "方案论证",
                    "stage_order": 1,
                    "result": "修改后通过",
                    "risk_level": "中",
                    "summary": "下一阶段应落实监测方案。",
                    "key_findings": [{
                        "title": "监测频率不足",
                        "analysis": "原监测频率偏低。",
                        "recommendation": "施工阶段提高监测频率。",
                    }],
                }]
            },
        }
        self.assertNotEqual(
            _audit_context_hash(case_without_history),
            _audit_context_hash(case_with_history),
        )
        history_text = _history_context_text(case_with_history)
        self.assertIn("方案论证", history_text)
        self.assertIn("监测频率不足", history_text)

        class FakeAgent:
            def __init__(self):
                self.prompt = ""

            def complete_json(self, system, prompt, max_tokens):
                self.prompt = prompt
                return {"findings": []}

        agent = FakeAgent()
        _audit_packet_batch(agent, [], history_text)
        self.assertIn("前序阶段审核记录", agent.prompt)
        self.assertIn("方案论证", agent.prompt)
        self.assertIn("不能替代本次案例原文", agent.prompt)

    def test_regulation_reference_contains_source_file_and_clause(self):
        source_file = r"D:\规程\城市轨道交通结构安全保护技术规程-DBT32-4351-2022.pdf"
        self.assertEqual(
            _regulation_source_name(
                {
                    "title": "城市轨道交通结构安全保护技术规程",
                    "original_file_name": source_file,
                }
            ),
            "城市轨道交通结构安全保护技术规程-DBT32-4351-2022.pdf",
        )
        self.assertEqual(
            _regulation_reference({"document_title": source_file, "section": "3.4.4"}),
            "《城市轨道交通结构安全保护技术规程-DBT32-4351-2022.pdf》 第3.4.4条",
        )

    def test_fast_dimensions_cover_numeric_and_general_audit_topics(self):
        dimensions = _fast_dimensions()
        titles = {item["title"] for item in dimensions}

        self.assertEqual(len(dimensions), 10)
        self.assertIn("关键控制指标与超限值", titles)
        self.assertIn("原方案与修改方案对比", titles)
        self.assertIn("工程与水文地质", titles)
        self.assertIn("监测与风险控制", titles)

    def test_packet_context_deduplicates_shared_evidence(self):
        case_hit = {
            "chunk_id": "case-1",
            "corpus_type": "case",
            "source_page": 1,
            "chunk_text": "同一段案例证据",
        }
        packets = [
            {
                "dimension": {"title": "空间关系", "question": "净距是否满足？"},
                "case_hits": [case_hit],
                "regulation_hits": [],
            },
            {
                "dimension": {"title": "施工风险", "question": "施工是否安全？"},
                "case_hits": [case_hit],
                "regulation_hits": [],
            },
        ]

        context = _packet_context(packets)

        self.assertEqual(context.count("同一段案例证据"), 1)
        self.assertIn("关联维度:空间关系、施工风险", context)

    def test_semantic_index_filters_current_case_and_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            index = SemanticIndex(Path(directory) / "vectors.sqlite3", FakeEmbeddingAgent())
            index.sync("case", "case-a", "案例A", [{"chunk_id": "a1", "text": "本案例设置了完整的基坑监测方案"}])
            index.sync("case", "case-b", "案例B", [{"chunk_id": "b1", "text": "另一个案例包含其他基坑工程资料"}])
            index.sync("regulation", "reg-a", "规程A", [{"chunk_id": "r1", "text": "规程要求监测范围应当覆盖基坑工程"}])

            case_hits = index.search("基坑监测", "case", document_id="case-a")
            regulation_hits = index.search("基坑监测", "regulation")

            self.assertEqual([item["chunk_id"] for item in case_hits], ["a1"])
            self.assertEqual([item["chunk_id"] for item in regulation_hits], ["r1"])

    def test_semantic_index_refreshes_source_name_without_reembedding(self):
        with tempfile.TemporaryDirectory() as directory:
            index = SemanticIndex(Path(directory) / "vectors.sqlite3", FakeEmbeddingAgent())
            chunks = [
                {
                    "chunk_id": "r1",
                    "text": "既有结构状态较差时，应动态调整控制指标。",
                    "page": 12,
                    "section": "3.4.4",
                    "content_type": "text",
                }
            ]
            index.sync("regulation", "reg-a", "规程简称", chunks)
            index.sync(
                "regulation",
                "reg-a",
                "城市轨道交通结构安全保护技术规程-DBT32-4351-2022.pdf",
                chunks,
            )

            hits = index.search("既有结构状态", "regulation")
            self.assertEqual(
                hits[0]["document_title"],
                "城市轨道交通结构安全保护技术规程-DBT32-4351-2022.pdf",
            )

    def test_report_validation_rejects_cross_corpus_evidence_and_sorts_risk(self):
        evidence = {
            "case-1": {"corpus_type": "case"},
            "reg-1": {
                "corpus_type": "regulation",
                "document_title": "城市轨道交通结构安全保护技术规程-DBT32-4351-2022.pdf",
                "section": "3.4.4",
                "source_page": 12,
            },
        }
        report = _validate_report(
            {
                "findings": [
                    {
                        "title": "已满足要求",
                        "risk_level": "高",
                        "judgement": "compliant",
                        "analysis": "案例满足规程要求。",
                        "case_evidence": [{"chunk_id": "case-1"}],
                        "regulation_evidence": [{"chunk_id": "reg-1"}],
                    },
                    {
                        "title": "明确超限",
                        "risk_level": "重大",
                        "judgement": "non_compliant",
                        "analysis": "案例值超过限值。",
                        "case_evidence": [{"chunk_id": "case-1"}],
                        "regulation_evidence": [
                            {"chunk_id": "case-1"},
                            {"chunk_id": "reg-1"},
                        ],
                    },
                    {
                        "title": "净距未满足",
                        "risk_level": "高",
                        "judgement": "non_compliant",
                        "analysis": "案例净距为15.6m，规程要求为5m。",
                        "comparison": "15.6m>5m，现状>要求，满足要求。",
                        "case_evidence": [{"chunk_id": "case-1"}],
                        "regulation_evidence": [{"chunk_id": "reg-1"}],
                    },
                ]
            },
            evidence,
        )

        self.assertEqual(report["findings"][0]["title"], "明确超限")
        self.assertEqual(
            report["findings"][0]["regulation_evidence"][0]["document_title"],
            "城市轨道交通结构安全保护技术规程-DBT32-4351-2022.pdf",
        )
        self.assertEqual(
            report["risk_sections"][0]["items"][0]["clause_refs"],
            ["《城市轨道交通结构安全保护技术规程-DBT32-4351-2022.pdf》 第3.4.4条"],
        )
        self.assertEqual(report["risk_sections"][0]["items"][0]["basis_label"], "规程依据")
        self.assertEqual(report["findings"][1]["judgement"], "risk")
        self.assertIn("适用性需核实", report["findings"][1]["title"])
        self.assertEqual(report["findings"][2]["risk_level"], "提示")


if __name__ == "__main__":
    unittest.main()
