import gc
import tempfile
import unittest
import sqlite3
from pathlib import Path

from audit_api.audit_knowledge_graph import build_audit_knowledge_graph, render_relationship_expansion
from audit_api.ima_rag import (
    CAG_FIXED_AUDIT_CONTEXT,
    SemanticIndex,
    _audit_context_hash,
    _audit_packet_batch,
    _bind_retrieved_regulation_evidence,
    _current_project_facts_context,
    _fast_dimensions,
    _history_context_text,
    _has_applicable_primary_regulation,
    _packet_context,
    _regulation_reference,
    _regulation_source_name,
    _top_rag_evidence_context,
    _top_rag_evidence_items,
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
        self.assertIn(
            "外部补充规范，已核验",
            _regulation_reference({"document_title": "外部规范.pdf", "section": "4.2.1", "source_tier": "external_supplement"}),
        )

    def test_primary_regulation_only_blocks_external_fallback_when_relevant(self):
        self.assertFalse(_has_applicable_primary_regulation([{"rerank_score": 0.33}]))
        self.assertTrue(_has_applicable_primary_regulation([{"rerank_score": 0.34}]))

    def test_retrieved_clause_is_bound_when_model_omits_regulation_chunk_id(self):
        evidence = {
            "case-1": {"corpus_type": "case"},
            "reg-1": {"corpus_type": "regulation"},
        }
        findings = [{"category": "监测方案", "title": "监测方案待补充", "regulation_evidence": []}]
        packets = [{
            "dimension": {"title": "监测方案"},
            "regulation_hits": [{
                "chunk_id": "reg-1", "document_title": "城市轨道交通保护技术规程.pdf",
                "section": "7.2.1", "chunk_text": "施工期间应实施保护监测。",
            }],
        }]
        bound = _bind_retrieved_regulation_evidence(findings, packets, evidence)
        self.assertEqual(bound[0]["regulation_evidence"][0]["chunk_id"], "reg-1")
        self.assertTrue(bound[0]["regulation_evidence"][0]["auto_bound"])

    def test_fast_dimensions_cover_numeric_and_general_audit_topics(self):
        dimensions = _fast_dimensions()
        titles = {item["title"] for item in dimensions}

        self.assertEqual(len(dimensions), 6)
        self.assertIn("关键控制指标与超限值", titles)
        self.assertIn("原方案与修改方案对比", titles)
        self.assertIn("工程与水文地质", titles)

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

    def test_cag_prompt_has_fixed_framework_facts_rules_and_global_top5_evidence(self):
        class FakeAgent:
            def complete_json(self, system, prompt, max_tokens):
                self.system = system
                self.prompt = prompt
                return {"findings": []}

        packets = [{
            "dimension": {"title": "基坑支护", "question": "支护是否适用？"},
            "case_hits": [{
                "chunk_id": "case-1", "corpus_type": "case", "source_page": 1,
                "chunk_text": "项目基坑深度18.5m。", "rerank_score": 0.91,
            }],
            "regulation_hits": [{
                "chunk_id": "reg-1", "corpus_type": "regulation", "document_title": "测试规程",
                "section": "6.2.1", "chunk_text": "深基坑应实施专项控制。", "rerank_score": 0.88,
            }],
        }]
        agent = FakeAgent()
        facts = _current_project_facts_context({"pit_depth_m": 18.5})
        top5 = _top_rag_evidence_context(packets)
        _audit_packet_batch(agent, packets, deterministic_rules='[{"rule_id":"R001"}]', project_facts=facts, top_rag_evidence=top5)

        self.assertTrue(agent.system.startswith(CAG_FIXED_AUDIT_CONTEXT))
        self.assertIn("基坑深度：18.5", agent.prompt)
        self.assertIn('"rule_id":"R001"', agent.prompt)
        self.assertIn("case-1", agent.prompt)
        self.assertIn("reg-1", agent.prompt)

    def test_global_top5_evidence_is_deduplicated_and_ranked(self):
        def hit(chunk_id, score):
            return {"chunk_id": chunk_id, "corpus_type": "case", "chunk_text": chunk_id, "rerank_score": score}

        packets = [{
            "case_hits": [hit("same", 0.2), hit("c1", 0.9), hit("c2", 0.8)],
            "regulation_hits": [hit("same", 0.95), hit("c3", 0.7), hit("c4", 0.6), hit("c5", 0.5)],
        }]
        selected = _top_rag_evidence_items(packets)

        self.assertEqual([item["chunk_id"] for item in selected], ["same", "c1", "c2", "c3", "c4"])

    def test_knowledge_graph_expands_only_from_current_audit_inputs(self):
        graph = build_audit_knowledge_graph(
            "当前项目事实：\n- 基坑深度：18.5\n- 降水方式：管井降水",
            [{
                "rule_id": "R001", "audit_status": "triggered",
                "input_values": {"pit_depth": 18.5},
            }],
            [{
                "chunk_id": "case-1", "corpus_type": "case",
                "chunk_text": "本项目采用地下连续墙并进行基坑开挖。",
            }],
        )
        expansion = render_relationship_expansion(graph)

        self.assertIn("基坑与支护", graph["activated_topics"])
        self.assertTrue(any(item["target"] == "地层变形与沉降" for item in graph["relationship_expansion"]))
        self.assertIn("仅辅助分析，不是项目事实或规程依据", expansion)
        self.assertIn("基坑与支护", expansion)

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

    def test_semantic_index_filters_metadata_and_returns_hybrid_rerank_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            index = SemanticIndex(Path(directory) / "vectors.sqlite3", FakeEmbeddingAgent())
            index.sync("regulation", "reg-a", "规程A", [
                {
                    "chunk_id": "table", "text": "基坑监测频率应根据风险等级调整。",
                    "content_type": "table",
                    "metadata": {"source_kind": "technical_regulation", "knowledge_type": "table"},
                },
                {
                    "chunk_id": "other", "text": "其他工程的一般管理要求。",
                    "content_type": "qualitative",
                    "metadata": {"source_kind": "other_source", "knowledge_type": "qualitative"},
                },
            ])

            hits = index.search(
                "基坑监测频率",
                "regulation",
                metadata_filters={"source_kind": "technical_regulation"},
                metadata_preferences={"table": 0.7},
            )

            self.assertEqual([item["chunk_id"] for item in hits], ["table"])
            self.assertGreater(hits[0]["bm25_score"], 0)
            self.assertIn("rerank_score", hits[0])
            self.assertEqual(hits[0]["metadata"]["knowledge_type"], "table")

    def test_semantic_index_migrates_existing_vector_store_for_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "vectors.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    """CREATE TABLE rag_chunk(
                        chunk_id TEXT PRIMARY KEY, corpus_type TEXT NOT NULL, document_id TEXT NOT NULL,
                        document_title TEXT, source_page INTEGER, section TEXT, content_type TEXT,
                        chunk_text TEXT NOT NULL, content_hash TEXT NOT NULL, vector_json TEXT NOT NULL,
                        embedding_model TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
                    )"""
                )
            connection.close()
            index = SemanticIndex(database, FakeEmbeddingAgent())
            del index
            gc.collect()
            with sqlite3.connect(database) as connection:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(rag_chunk)")}
            connection.close()
            self.assertIn("metadata_json", columns)

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
