from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from .agent import AgentService, SILICONFLOW_EMBEDDING_MODEL, SILICONFLOW_MODEL
from .config import KNOWLEDGE_ROOT
from .rag_audit import RISK_TOPICS, _paragraph_chunks, _risk_signal_score, _tokens, _walk_case
from .regulation_rules import RULE_FIELD_CATALOG, RegulationRepository


Progress = Callable[[str], None]
VECTOR_DB = KNOWLEDGE_ROOT / "rag_vectors.sqlite3"
AUDIT_CACHE_ROOT = KNOWLEDGE_ROOT / "rag_audit_cache"
AUDIT_CACHE_VERSION = "ima-rag-v7-fast-main-issues"
AUDIT_PACKET_BATCH_SIZE = 5
AUDIT_EVIDENCE_CHAR_LIMIT = 650
AUDIT_BATCH_TIMEOUT_SECONDS = 75
AUDIT_DIMENSION_TOTAL_TIMEOUT_SECONDS = 110
AUDIT_CORE_TOPIC_LIMIT = 4
AUDIT_CASE_HIT_LIMIT = 3
AUDIT_REGULATION_HIT_LIMIT = 2

USER_FIELD_LABELS = {
    **RULE_FIELD_CATALOG,
    "minimum_horizontal_clearance_m": "最小水平净距",
    "minimum_vertical_clearance_m": "最小竖向净距",
    "pit_depth_m": "基坑深度",
    "pit_length_m": "基坑长度",
    "buried_depth_m": "轨道结构埋深",
    "outer_diameter_or_width_m": "隧道外径或结构宽度",
    "structure_method": "轨道结构形式",
    "structure_condition": "轨道结构状态",
    "terrain_zone": "地段区域",
    "is_soft_soil": "是否存在软弱土层",
    "is_complex_geology_or_hydrology": "地质水文条件是否复杂",
    "protection_zone_location": "保护区位置",
}


def _humanize_user_text(value: Any) -> str:
    text = str(value or "")
    for field_name in sorted(USER_FIELD_LABELS, key=len, reverse=True):
        text = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(field_name)}(?![A-Za-z0-9_])",
            USER_FIELD_LABELS[field_name],
            text,
        )
    text = re.sub(r"(?<![A-Za-z])true(?![A-Za-z])", "是", text, flags=re.I)
    text = re.sub(r"(?<![A-Za-z])false(?![A-Za-z])", "否", text, flags=re.I)
    # Internal field paths are useful in JSON logs, but should never leak into the user report.
    text = re.sub(r"\s*[（(]\s*[A-Za-z][A-Za-z0-9_.]*(?:\s*[:=]\s*[^)）]+)?[)）]", "", text)
    text = re.sub(r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_.]+\b", "相关工程参数", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _regulation_reference(ref: dict[str, Any]) -> str:
    raw_title = str(ref.get("document_title") or "").strip()
    title = Path(raw_title).name if raw_title else ""
    if title.startswith("《") and title.endswith("》"):
        document = title
    elif title:
        document = f"《{title}》"
    else:
        document = "规程文件名缺失（旧索引）"
    section = str(ref.get("section") or "").strip()
    if section and section not in {"None", "未知", "相关内容"}:
        clause = f"第{section}条" if re.fullmatch(r"\d+(?:\.\d+)*", section) else section
        return f"{document} {clause}"
    return document


def _regulation_source_name(document: dict[str, Any]) -> str:
    """Return the exact uploaded file name used for user-facing traceability."""
    source_name = str(document.get("original_file_name") or document.get("title") or "").strip()
    return Path(source_name).name if source_name else "规程文件名缺失"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _history_context(case_data: dict[str, Any]) -> dict[str, Any]:
    value = case_data.get("project_archive_context") if isinstance(case_data, dict) else None
    return value if isinstance(value, dict) else {}


def _current_session_context(case_data: dict[str, Any]) -> dict[str, Any]:
    value = case_data.get("manual_context") if isinstance(case_data, dict) else None
    return value if isinstance(value, dict) else {}


def _audit_context_hash(case_data: dict[str, Any]) -> str:
    return _hash(json.dumps({
        "history": _history_context(case_data),
        "current_session": _current_session_context(case_data),
    }, ensure_ascii=False, sort_keys=True))


def _current_session_context_text(case_data: dict[str, Any]) -> str:
    context = _current_session_context(case_data)
    if not context:
        return ""
    latest_items = context.get("latest_review_items") or []
    documents = context.get("uploaded_documents") or []
    rerun_context = context.get("rerun_context") or {}
    lines = [
        "以下是当前审核会话的连续复核上下文。若本轮新增附件或用户要求重新审核，应结合已有文件、新增附件、当前确认数据和上一版审核意见重新形成综合判断："
    ]
    if rerun_context:
        lines.append(f"复核方式：{rerun_context.get('mode') or '补充附件后综合复核'}")
        if rerun_context.get("latest_instruction"):
            lines.append(f"最新用户意见：{rerun_context.get('latest_instruction')}")
        if rerun_context.get("attachment_policy"):
            lines.append(f"附件处理要求：{rerun_context.get('attachment_policy')}")
    overall = context.get("latest_overall_opinion") or {}
    if isinstance(overall, dict) and (overall.get("conclusion") or overall.get("recommendation")):
        lines.append(f"上一版综合评价：{overall.get('conclusion') or overall.get('recommendation')}")
    if latest_items:
        lines.append("上一版主要审核意见：")
        for item in latest_items[:8]:
            if not isinstance(item, dict):
                continue
            lines.append(
                "{order}. {title}；风险等级：{risk}；意见：{opinion}".format(
                    order=item.get("order_no") or "",
                    title=item.get("title") or "未命名意见",
                    risk=item.get("risk_level") or "未填写",
                    opinion=item.get("opinion") or item.get("conclusion") or item.get("recommendation") or "无",
                )
            )
    if documents:
        lines.append("当前会话已上传资料清单：")
        for doc in documents[:20]:
            if not isinstance(doc, dict):
                continue
            excerpt = str(doc.get("text_excerpt") or doc.get("textPreview") or "")[:600]
            lines.append(
                f"- {doc.get('name') or '未命名文件'}；角色：{doc.get('role') or '未标注'}；摘要：{excerpt or '无'}"
            )
    return "\n".join(lines)[:18000]


def _history_context_text(case_data: dict[str, Any]) -> str:
    context = _history_context(case_data)
    stages = context.get("previous_stages") or []
    if not stages:
        return ""
    lines = [
        "以下是同一项目前序阶段已经形成的审核记录，仅用于检查风险延续、资料补充和整改闭环："
    ]
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        lines.append(
            f"\n### {stage.get('stage_order')}. {stage.get('stage_name') or '历史阶段'}"
        )
        lines.append(
            f"审核结论：{stage.get('result') or '未填写'}；风险等级：{stage.get('risk_level') or '未填写'}"
        )
        if stage.get("summary"):
            lines.append(f"阶段摘要：{stage['summary']}")
        for finding in stage.get("key_findings") or []:
            if not isinstance(finding, dict):
                continue
            lines.append(
                "- 历史问题：{title}；分析：{analysis}；建议：{recommendation}".format(
                    title=finding.get("title") or "未命名问题",
                    analysis=finding.get("analysis") or "无",
                    recommendation=finding.get("recommendation") or "无",
                )
            )
        for supplement in stage.get("required_supplements") or []:
            if isinstance(supplement, dict):
                lines.append(
                    f"- 待补资料：{supplement.get('field') or '未命名资料'}；原因：{supplement.get('reason') or '无'}"
                )
    return "\n".join(lines)[:16000]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    denominator = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return numerator / denominator if denominator else 0.0


class SemanticIndex:
    def __init__(self, database: Path = VECTOR_DB, agent: AgentService | None = None) -> None:
        self.database = database
        self.agent = agent or AgentService()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS rag_chunk(
                    chunk_id TEXT PRIMARY KEY,
                    corpus_type TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    document_title TEXT,
                    source_page INTEGER,
                    section TEXT,
                    content_type TEXT,
                    chunk_text TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS idx_rag_corpus ON rag_chunk(corpus_type, active);
                CREATE INDEX IF NOT EXISTS idx_rag_document ON rag_chunk(document_id, active);
                """
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def sync(self, corpus_type: str, document_id: str, title: str, chunks: list[dict[str, Any]]) -> int:
        prepared = []
        for index, chunk in enumerate(chunks, 1):
            text = str(chunk.get("text") or "").strip()
            if len(text) < 12:
                continue
            prepared.append({
                **chunk,
                "chunk_id": str(chunk.get("chunk_id") or f"{document_id}:{index:04d}"),
                "text": text,
                "content_hash": _hash(text),
            })
        with self._connect() as connection:
            existing = {
                row["chunk_id"]: dict(row)
                for row in connection.execute(
                    "SELECT chunk_id,content_hash,embedding_model FROM rag_chunk WHERE document_id=?",
                    (document_id,),
                )
            }
        missing = [
            item for item in prepared
            if item["chunk_id"] not in existing
            or existing[item["chunk_id"]]["content_hash"] != item["content_hash"]
            or existing[item["chunk_id"]]["embedding_model"] != SILICONFLOW_EMBEDDING_MODEL
        ]
        vectors = self.agent.embed([item["text"] for item in missing]) if missing else []
        active_ids = {item["chunk_id"] for item in prepared}
        with self._connect() as connection:
            connection.execute("UPDATE rag_chunk SET active=0 WHERE document_id=?", (document_id,))
            for item, vector in zip(missing, vectors):
                connection.execute(
                    """
                    INSERT INTO rag_chunk(
                        chunk_id,corpus_type,document_id,document_title,source_page,section,
                        content_type,chunk_text,content_hash,vector_json,embedding_model,active
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,1)
                    ON CONFLICT(chunk_id) DO UPDATE SET
                        corpus_type=excluded.corpus_type, document_id=excluded.document_id,
                        document_title=excluded.document_title, source_page=excluded.source_page,
                        section=excluded.section, content_type=excluded.content_type,
                        chunk_text=excluded.chunk_text, content_hash=excluded.content_hash,
                        vector_json=excluded.vector_json, embedding_model=excluded.embedding_model, active=1
                    """,
                    (
                        item["chunk_id"], corpus_type, document_id, title, item.get("source_page"),
                        item.get("section"), item.get("content_type") or "text", item["text"],
                        item["content_hash"], json.dumps(vector), SILICONFLOW_EMBEDDING_MODEL,
                    ),
                )
            missing_ids = {item["chunk_id"] for item in missing}
            for item in prepared:
                if item["chunk_id"] in missing_ids:
                    continue
                # Refresh metadata even when the text embedding can be reused. This keeps
                # renamed or legacy documents traceable to their current source file.
                connection.execute(
                    """
                    UPDATE rag_chunk SET
                        corpus_type=?, document_id=?, document_title=?, source_page=?,
                        section=?, content_type=?, chunk_text=?, content_hash=?, active=1
                    WHERE chunk_id=?
                    """,
                    (
                        corpus_type, document_id, title, item.get("source_page"),
                        item.get("section"), item.get("content_type") or "text",
                        item["text"], item["content_hash"], item["chunk_id"],
                    ),
                )
        return len(prepared)

    def delete_document(self, document_id: str) -> int:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM rag_chunk WHERE document_id=?", (document_id,))
        return cursor.rowcount

    def search(
        self, query: str, corpus_type: str, limit: int = 5, document_id: str | None = None
    ) -> list[dict[str, Any]]:
        vector = self.agent.embed([query])[0]
        return self.search_with_vector(query, vector, corpus_type, limit, document_id)

    def search_with_vector(
        self,
        query: str,
        vector: list[float],
        corpus_type: str,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query_tokens = _tokens(query)
        sql = "SELECT * FROM rag_chunk WHERE corpus_type=? AND active=1"
        params: list[Any] = [corpus_type]
        if document_id:
            sql += " AND document_id=?"
            params.append(document_id)
        with self._connect() as connection:
            rows = [dict(row) for row in connection.execute(sql, params)]
        ranked = []
        for row in rows:
            semantic = _cosine(vector, json.loads(row.pop("vector_json")))
            overlap = len(query_tokens & _tokens(row["chunk_text"])) / max(1, len(query_tokens))
            row["semantic_score"] = round(semantic, 6)
            row["hybrid_score"] = round(0.86 * semantic + 0.14 * overlap, 6)
            ranked.append(row)
        return sorted(ranked, key=lambda item: item["hybrid_score"], reverse=True)[:limit]


def purge_rag_document(document_id: str) -> dict[str, int]:
    """Remove a document's vectors and invalidate cached audits."""
    removed_vectors = SemanticIndex().delete_document(document_id)
    removed_cache_files = 0
    if AUDIT_CACHE_ROOT.exists():
        for path in AUDIT_CACHE_ROOT.glob("*.json"):
            path.unlink(missing_ok=True)
            removed_cache_files += 1
    return {"removed_vectors": removed_vectors, "removed_cache_files": removed_cache_files}


def _regulation_chunks(repository: RegulationRepository) -> list[tuple[str, str, list[dict[str, Any]]]]:
    result = []
    for document in repository.list_documents():
        if not document.get("active"):
            continue
        clauses = repository.list_clauses(document["regulation_id"])
        if clauses:
            chunks = [{
                "chunk_id": f"REG:{item['clause_id']}",
                "text": item["clause_text"],
                "source_page": item.get("source_page"),
                "section": item.get("clause_no"),
                "content_type": item.get("knowledge_type") or "clause",
            } for item in clauses]
        else:
            rows = json.loads(
                (Path(document["text_file"]).parent / "paragraphs.json").read_text(encoding="utf-8")
            )
            chunks, current, size = [], [], 0
            for row in rows:
                text = str(row.get("text") or "").strip()
                if not text:
                    continue
                if current and size + len(text) > 900:
                    chunks.append({
                        "chunk_id": f"REG:{document['regulation_id']}:{len(chunks) + 1:04d}",
                        "text": "\n".join(item["text"] for item in current),
                        "source_page": current[0].get("page"),
                        "content_type": "document_chunk",
                    })
                    current, size = current[-1:], len(current[-1]["text"])
                current.append({"text": text, "page": row.get("page")})
                size += len(text)
            if current:
                chunks.append({
                    "chunk_id": f"REG:{document['regulation_id']}:{len(chunks) + 1:04d}",
                    "text": "\n".join(item["text"] for item in current),
                    "source_page": current[0].get("page"),
                    "content_type": "document_chunk",
                })
        result.append((document["regulation_id"], _regulation_source_name(document), chunks))
    return result


def _default_dimensions() -> list[dict[str, str]]:
    return [
        {
            "title": title,
            "question": f"案例在{title}方面是否符合规程并存在哪些风险？",
            "case_query": " ".join(terms),
            "regulation_query": f"{title} {' '.join(terms)} 要求 限值 监测 控制",
        }
        for title, terms in RISK_TOPICS.items()
    ]


def _fast_dimensions() -> list[dict[str, str]]:
    """Build a complete audit plan locally so audit startup never waits on an LLM."""
    required = [
        {
            "title": "关键控制指标与超限值",
            "question": "案例中的位移、沉降、倾斜、净距、水位等关键数值是否超过规程或报告采用的控制值？",
            "case_query": "超过 超限 不满足 控制值 最大值 位移 沉降 倾斜 净距 水位 mm",
            "regulation_query": "安全控制指标 控制值 限值 位移 沉降 倾斜 净距 地下水 不得超过",
        },
        {
            "title": "原方案与修改方案对比",
            "question": "报告是否存在原方案超限、修改方案改善的情形，最终采用方案是否明确并落实？",
            "case_query": "原方案 修改方案 优化方案 推荐方案 超过 满足 计算结果",
            "regulation_query": "方案调整 优化措施 安全控制指标 计算分析 施工方案 落实",
        },
    ]
    return required + _default_dimensions()[:AUDIT_CORE_TOPIC_LIMIT]


def _plan_dimensions(agent: AgentService, case_scout: str) -> list[dict[str, str]]:
    value = agent.complete_json(
        (
            "你是轨道交通结构保护审查专家。根据案例初步原文制定审核检索计划。"
            "计划要覆盖空间关系、既有结构、工程地质、水文、施工、计算、监测和周边环境，"
            "并根据案例对象增加专属问题。只输出JSON。"
        ),
        f"""案例初步资料：
{case_scout[:18000]}

输出：
{{"dimensions":[{{"title":"审核维度","question":"需要回答的审核问题","case_query":"检索案例全文的查询","regulation_query":"检索规程知识库的查询"}}]}}
生成8至12个互不重复的审核维度。查询词应包含对象、风险机理、数值或要求的同义表达。""",
        max_tokens=1800,
    )
    dimensions = value.get("dimensions") if isinstance(value, dict) else None
    if not isinstance(dimensions, list):
        return _default_dimensions()
    required = [
        {
            "title": "关键控制指标与超限值",
            "question": "案例中的位移、沉降、倾斜、净距、水位等关键数值是否超过规程或报告采用的控制值？",
            "case_query": "超过 超限 不满足 控制值 最大值 位移 沉降 倾斜 净距 水位 mm",
            "regulation_query": "安全控制指标 控制值 限值 位移 沉降 倾斜 净距 地下水 不得超过",
        },
        {
            "title": "原方案与修改方案对比",
            "question": "报告是否存在原方案超限、修改方案改善的情形，最终采用方案是否明确并落实？",
            "case_query": "原方案 修改方案 优化方案 推荐方案 超过 满足 计算结果",
            "regulation_query": "方案调整 优化措施 安全控制指标 计算分析 施工方案 落实",
        },
    ]
    cleaned = list(required)
    for item in dimensions[:12]:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        title = str(item["title"])
        if any(title == existing["title"] for existing in cleaned):
            continue
        cleaned.append({
            "title": title,
            "question": str(item.get("question") or item["title"]),
            "case_query": str(item.get("case_query") or item["title"]),
            "regulation_query": str(item.get("regulation_query") or item["title"]),
        })
    return cleaned[:12] or _default_dimensions()


def _validate_report(value: dict[str, Any], evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    findings = []
    seen_titles: set[str] = set()
    for item in value.get("findings") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title or title in seen_titles:
            continue
        case_refs = [
            ref for ref in item.get("case_evidence") or []
            if isinstance(ref, dict)
            and str(ref.get("chunk_id") or "") in evidence
            and evidence[str(ref.get("chunk_id"))]["corpus_type"] == "case"
        ]
        regulation_refs = []
        for ref in item.get("regulation_evidence") or []:
            if not isinstance(ref, dict):
                continue
            chunk_id = str(ref.get("chunk_id") or "")
            source = evidence.get(chunk_id)
            if not source or source["corpus_type"] != "regulation":
                continue
            enriched = dict(ref)
            enriched["document_title"] = (
                source.get("document_title") or enriched.get("document_title") or ""
            )
            enriched["section"] = (
                enriched.get("section") or source.get("section") or "相关内容"
            )
            enriched["source_page"] = source.get("source_page")
            regulation_refs.append(enriched)
        if not case_refs:
            continue
        judgement = str(item.get("judgement") or "risk")
        if judgement in {"non_compliant", "compliant"} and not regulation_refs:
            item["judgement"] = "risk"
            item["verification_note"] = "缺少可追溯规程证据，已降为工程风险判断。"
        analysis = str(item.get("analysis") or "")
        comparison = str(item.get("comparison") or "")
        if judgement == "non_compliant" and any(
            phrase in analysis[-180:] for phrase in ("判定为合规", "故判定为合规", "结论：满足")
        ):
            item["judgement"] = "risk"
            item["verification_note"] = "模型标题与分析结论不一致，已降为风险提示。"
        if (
            judgement == "non_compliant"
            and any(phrase in comparison for phrase in ("满足要求", "现状>要求，满足", "现状≥要求，满足"))
            and not any(phrase in comparison for phrase in ("不满足", "不合规", "超过限值", "超限"))
        ):
            item["judgement"] = "risk"
            item["title"] = title.replace("未满足", "适用性需核实")
            item["verification_note"] = "数值比较显示满足但文字判定相反，已降为适用性核实项。"
        if item.get("judgement") == "compliant":
            item["risk_level"] = "提示"
        item["case_evidence"] = case_refs
        item["regulation_evidence"] = regulation_refs
        item["title"] = _humanize_user_text(item.get("title"))[:200]
        item["analysis"] = _humanize_user_text(analysis)[:900]
        item["comparison"] = _humanize_user_text(comparison)[:500]
        item["recommendation"] = _humanize_user_text(item.get("recommendation"))[:500]
        seen_titles.add(title)
        findings.append(item)
    risk_rank = {"重大": 0, "高": 1, "中": 2, "低": 3, "提示": 4}
    judgement_rank = {"non_compliant": 0, "risk": 1, "insufficient": 2, "compliant": 3}
    findings.sort(key=lambda item: (
        judgement_rank.get(str(item.get("judgement")), 2),
        risk_rank.get(str(item.get("risk_level")), 4),
    ))
    value["findings"] = findings
    value["risk_item_count"] = len(findings)
    value["high_risk_count"] = sum(
        1 for item in findings if str(item.get("risk_level") or "") in {"重大", "高"}
    )
    value["compliance_finding_count"] = sum(
        1 for item in findings if item.get("judgement") in {"non_compliant", "compliant"}
    )
    value["engineering_risk_count"] = sum(
        1 for item in findings if item.get("judgement") in {"risk", "insufficient"}
    )
    compliance_items, risk_items = [], []
    for item in findings:
        clause_refs = [
            _regulation_reference(ref) for ref in item.get("regulation_evidence") or []
        ]
        has_regulation_evidence = bool(clause_refs)
        rendered = {
            "name": item.get("title"),
            "severity": item.get("risk_level"),
            "analysis": item.get("analysis"),
            "case_evidence": [
                f"{ref.get('chunk_id')}：{ref.get('quote') or ''}" for ref in item.get("case_evidence") or []
            ],
            "clause_refs": clause_refs,
            "recommendation": item.get("recommendation"),
            "basis_type": "regulation" if has_regulation_evidence else "engineering_analysis",
            "basis_label": "规程依据" if has_regulation_evidence else "工程分析依据",
            "basis_note": "" if has_regulation_evidence else (
                "基于案例原文和工程风险分析，未检索到可直接引用的具体规程条款。"
            ),
            "judgement": item.get("judgement"),
        }
        if item.get("judgement") in {"non_compliant", "compliant"}:
            compliance_items.append(rendered)
        else:
            risk_items.append(rendered)
    value["compliance_sections"] = (
        [{"title": "规程符合性与差距", "items": compliance_items}] if compliance_items else []
    )
    value["engineering_risk_sections"] = (
        [{"title": "综合工程风险", "items": risk_items}] if risk_items else []
    )
    value["risk_sections"] = value["compliance_sections"] + value["engineering_risk_sections"]
    value["overview"] = _humanize_user_text(value.get("overview"))[:1200]
    value["overall_conclusion"] = _humanize_user_text(value.get("overall_conclusion"))[:1200]
    value.setdefault("required_supplements", [])
    value.setdefault("qualitative_checks", [])
    return value


def _packet_context(packets: list[dict[str, Any]]) -> str:
    parts = ["## 审核维度"]
    for packet in packets:
        dimension = packet["dimension"]
        parts.append(f"- {dimension['title']}：{dimension['question']}")

    unique_hits: dict[str, dict[str, Any]] = {}
    for packet in packets:
        title = packet["dimension"]["title"]
        for item in packet["case_hits"] + packet["regulation_hits"]:
            chunk_id = item["chunk_id"]
            if chunk_id not in unique_hits:
                unique_hits[chunk_id] = {"item": item, "dimensions": []}
            unique_hits[chunk_id]["dimensions"].append(title)

    parts.append("\n## 去重后的检索证据")
    for entry in unique_hits.values():
        item = entry["item"]
        related = "、".join(dict.fromkeys(entry["dimensions"]))
        if item["corpus_type"] == "case":
            heading = f"[案例|{item['chunk_id']}|页{item.get('source_page')}|关联维度:{related}]"
        else:
            heading = (
                f"[规程|{item['chunk_id']}|《{item.get('document_title')}》|"
                f"{item.get('section') or '相关内容'}|页{item.get('source_page')}|关联维度:{related}]"
            )
        parts.append(f"{heading}\n{item['chunk_text'][:AUDIT_EVIDENCE_CHAR_LIMIT]}")
    return "\n".join(parts)


def _audit_packet_batch(
    agent: AgentService,
    packets: list[dict[str, Any]],
    history_text: str = "",
) -> list[dict[str, Any]]:
    value = agent.complete_json(
        (
            "你是资深城市轨道交通结构安全保护评审专家。只采用LLM+RAG审核，不调用规则函数。"
            "直接阅读案例和规程证据，完成数值比较、表格查表、多条件判断和工程风险推理。"
            "不得虚构事实、条款、数值或页码。所有面向用户的文字必须使用自然中文，"
            "严禁输出snake_case英文内部字段名、JSON路径、true或false。只输出紧凑合法JSON。"
        ),
        f"""审核以下检索证据：
{_packet_context(packets)}

同一项目前序阶段审核记录（辅助信息，不是本次材料或规程证据）：
{history_text or '无前序阶段审核记录'}

输出：
{{"findings":[{{
  "category":"风险类别",
  "title":"具体问题",
  "risk_level":"重大|高|中|低|提示",
  "judgement":"compliant|non_compliant|risk|insufficient",
  "analysis":"规程要求、案例现状以及判断理由",
  "comparison":"有数值时写明数据、单位和比较过程，否则为空",
  "case_evidence":[{{"chunk_id":"案例块ID","quote":"原文短引","page":1}}],
  "regulation_evidence":[{{"chunk_id":"规程块ID","document_title":"规程文件名","section":"条款号或标题","quote":"规程原文短引"}}],
  "recommendation":"可执行建议"
}}]}}

要求：
1. 每个审核维度只输出1项最重要结论，不重复凑数。
2. 符合或不符合必须同时有案例和规程证据；仅有案例证据时标记risk或insufficient。
3. 不要因缺少同名字段判资料不足，应先按全文语义判断。
4. 表格必须按表头、行名、列名和单元格共同解释。
5. analysis不超过220个汉字，recommendation不超过120个汉字，不输出检索过程说明。
6. 案例参数必须写成用户能理解的中文工程术语，例如“最小水平净距为12m”，
不得写“minimum_horizontal_clearance_m: 12”一类内部表示。
7. 若有前序阶段记录，应检查历史风险、待补资料和整改要求在本次材料中是否得到响应；
历史结论只能作为连续性辅助信息，不能替代本次案例原文和现行规程证据。""",
        max_tokens=1500,
    )
    return value.get("findings", []) if isinstance(value, dict) else []


def _synthesize_report(agent: AgentService, findings: list[dict[str, Any]], case_scout: str) -> dict[str, Any]:
    compact = [{
        "title": item.get("title"),
        "risk_level": item.get("risk_level"),
        "judgement": item.get("judgement"),
        "analysis": str(item.get("analysis") or "")[:500],
        "recommendation": str(item.get("recommendation") or "")[:300],
    } for item in findings]
    value = agent.complete_json(
        (
            "你是城市轨道交通结构安全保护评审负责人。根据已经完成的分项审查，"
            "形成专业、审慎、可执行的总体结论。不得增加分项审查中没有依据的新事实。只输出JSON。"
        ),
        f"""案例概况材料：
{case_scout[:7000]}

分项审查：
{json.dumps(compact, ensure_ascii=False)}

输出：
{{
  "overview":"项目对象、空间关系、工程特征和主要矛盾的专业概述",
  "overall_risk_level":"重大|高|中|低|提示",
  "overall_conclusion":"综合审核结论",
  "required_supplements":[{{"field":"真正影响结论的资料","reason":"缺少该资料的影响"}}]
}}
总体风险等级应与分项风险一致；若有重大或高风险，不得写成“未发现风险”。""",
        max_tokens=1500,
    )
    return value if isinstance(value, dict) else {}


def _raw_case_hits(
    chunks: list[dict[str, Any]], document_id: str, title: str
) -> list[dict[str, Any]]:
    return [{
        "chunk_id": item["chunk_id"],
        "corpus_type": "case",
        "document_id": document_id,
        "document_title": title,
        "source_page": item.get("source_page"),
        "section": None,
        "content_type": "full_text_recall",
        "chunk_text": item["text"],
        "semantic_score": None,
        "hybrid_score": None,
    } for item in chunks]


def run_ima_rag_audit(
    case_data: dict[str, Any],
    case_document: str | Path,
    *,
    repository: RegulationRepository | None = None,
    agent: AgentService | None = None,
    progress: Progress | None = None,
) -> dict[str, Any]:
    notify = progress or (lambda _message: None)
    repository = repository or RegulationRepository()
    agent = agent or AgentService()
    index = SemanticIndex(agent=agent)
    started = time.perf_counter()
    case_chunks = _paragraph_chunks(case_document, target_size=850)
    case_content_hash = _hash("\n".join(item["text"] for item in case_chunks))
    history_hash = _audit_context_hash(case_data)
    history_text = _history_context_text(case_data)
    session_text = _current_session_context_text(case_data)
    case_id = "CASE:" + case_content_hash[:16]
    case_chunks = [
        {**item, "chunk_id": f"{case_id}:{item['chunk_id']}"}
        for item in case_chunks
    ]
    regulations = _regulation_chunks(repository)
    regulation_hash = _hash("\n".join(
        f"{document_id}|{title}|{item.get('chunk_id')}|{item.get('text')}"
        for document_id, title, chunks in regulations
        for item in chunks
    ))
    cache_key = _hash("|".join((
        AUDIT_CACHE_VERSION,
        SILICONFLOW_MODEL,
        SILICONFLOW_EMBEDDING_MODEL,
        case_content_hash,
        regulation_hash,
        history_hash,
    )))
    cache_file = AUDIT_CACHE_ROOT / f"{cache_key}.json"
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            cached["risk_report"]["cache_hit"] = True
            cached["risk_report"]["timings_seconds"] = {
                "total": round(time.perf_counter() - started, 3),
                "cache_reused": True,
            }
            notify("案例与知识库未变化，已复用上次完整审核结果")
            return cached
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            pass

    timings: dict[str, float | bool] = {"cache_reused": False}
    stage_started = time.perf_counter()
    notify("正在建立案例全文向量索引")
    index.sync("case", case_id, Path(case_document).stem, case_chunks)
    notify("正在同步技术规程向量知识库")
    regulation_count = 0
    for document_id, title, chunks in regulations:
        regulation_count += index.sync("regulation", document_id, title, chunks)
    timings["vector_index"] = round(time.perf_counter() - stage_started, 3)

    facts, source_evidence = _walk_case(case_data)
    scouts = sorted(case_chunks, key=lambda item: _risk_signal_score(item["text"]), reverse=True)[:18]
    case_scout = "\n".join(facts[-120:] + source_evidence[-30:] + [item["text"] for item in scouts])
    if history_text:
        notify("已加载项目前序阶段审核记录，正在检查风险和整改延续性")
        case_scout = f"{case_scout}\n\n{history_text}"
    if session_text:
        notify("已加载当前会话既有审核意见和附件记录，正在执行综合复核")
        case_scout = f"{case_scout}\n\n{session_text}"
    notify("正在生成多维审核检索计划")
    stage_started = time.perf_counter()
    dimensions = _fast_dimensions()
    timings["audit_plan"] = round(time.perf_counter() - stage_started, 3)

    notify("正在从案例全文和规程知识库进行语义检索")
    stage_started = time.perf_counter()
    packets, evidence = [], {}
    queries = [
        query
        for dimension in dimensions
        for query in (dimension["case_query"], dimension["regulation_query"])
    ]
    query_vectors = agent.embed(queries)
    for offset, dimension in enumerate(dimensions):
        case_hits = index.search_with_vector(
            dimension["case_query"], query_vectors[offset * 2],
            "case", limit=AUDIT_CASE_HIT_LIMIT, document_id=case_id,
        )
        if dimension["title"] == "关键控制指标与超限值":
            candidates = [
                item for item in case_chunks
                if re.search(r"(?:超过|超限|不满足|大于|小于|≥|≤|>|<)", item["text"])
            ]
            candidates.sort(key=lambda item: _risk_signal_score(item["text"]), reverse=True)
            case_hits.extend(_raw_case_hits(candidates[:3], case_id, Path(case_document).stem))
        elif dimension["title"] == "原方案与修改方案对比":
            candidates = [
                item for item in case_chunks
                if re.search(r"(?:原设计方案|原方案|修改方案|优化方案|推荐方案|比选方案)", item["text"])
            ]
            candidates.sort(key=lambda item: _risk_signal_score(item["text"]), reverse=True)
            case_hits.extend(_raw_case_hits(candidates[:3], case_id, Path(case_document).stem))
        case_hits = list({item["chunk_id"]: item for item in case_hits}.values())
        regulation_hits = index.search_with_vector(
            dimension["regulation_query"], query_vectors[offset * 2 + 1],
            "regulation", limit=AUDIT_REGULATION_HIT_LIMIT,
        )
        for hit in case_hits + regulation_hits:
            evidence[hit["chunk_id"]] = hit
        packets.append({
            "dimension": dimension,
            "case_hits": case_hits,
            "regulation_hits": regulation_hits,
        })
    timings["retrieval"] = round(time.perf_counter() - stage_started, 3)
    notify("正在由大模型分维度并行审查案例与规程证据")
    stage_started = time.perf_counter()
    batches = [
        packets[index:index + AUDIT_PACKET_BATCH_SIZE]
        for index in range(0, len(packets), AUDIT_PACKET_BATCH_SIZE)
    ]
    findings: list[dict[str, Any]] = []
    completed_batches = 0
    def add_degraded_batch(batch: list[dict[str, Any]], reason: str) -> None:
        for packet in batch:
            dimension = packet["dimension"]
            findings.append({
                "category": dimension["title"],
                "title": f"{dimension['title']}审核服务暂时超时",
                "risk_level": "提示",
                "judgement": "insufficient",
                "analysis": reason,
                "comparison": "",
                "case_evidence": [],
                "regulation_evidence": [],
                "recommendation": "稍后可重新审核该维度；本次结果不应据此判定资料完全满足要求。",
                "service_degraded": True,
            })

    executor = ThreadPoolExecutor(max_workers=min(3, len(batches)))
    try:
        futures = {
            executor.submit(_audit_packet_batch, agent, batch, "\n\n".join([item for item in [history_text, session_text] if item])): (batch, time.perf_counter())
            for batch in batches
        }
        deadline = time.perf_counter() + AUDIT_DIMENSION_TOTAL_TIMEOUT_SECONDS
        while futures:
            remaining = max(0.1, min(2.0, deadline - time.perf_counter()))
            done, _pending = wait(futures.keys(), timeout=remaining, return_when=FIRST_COMPLETED)
            if not done:
                now = time.perf_counter()
                timed_out = [
                    future for future, (_batch, submitted_at) in futures.items()
                    if now - submitted_at >= AUDIT_BATCH_TIMEOUT_SECONDS or now >= deadline
                ]
                for future in timed_out:
                    batch, _submitted_at = futures.pop(future)
                    future.cancel()
                    add_degraded_batch(
                        batch,
                        "该批大模型审核请求等待超时，系统已跳过该批并继续生成其余审核意见，避免任务长时间停留。",
                    )
                    completed_batches += 1
                    notify(f"大模型分维度审查已完成{completed_batches}/{len(batches)}批")
                continue
            for future in done:
                batch, _submitted_at = futures.pop(future)
                try:
                    findings.extend(future.result())
                except (TimeoutError, OSError, RuntimeError):
                    add_degraded_batch(
                        batch,
                        "该批请求已完成三次网络重试但仍然超时，其他维度已继续审核。",
                    )
                completed_batches += 1
                notify(f"大模型分维度审查已完成{completed_batches}/{len(batches)}批")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
    timings["dimension_audit"] = round(time.perf_counter() - stage_started, 3)
    notify("正在汇总总体风险等级和专业审核结论")
    stage_started = time.perf_counter()
    try:
        value = _synthesize_report(agent, findings, case_scout)
    except (TimeoutError, OSError, RuntimeError):
        risk_order = ["重大", "高", "中", "低", "提示"]
        present = {str(item.get("risk_level") or "提示") for item in findings}
        overall = next((level for level in risk_order if level in present), "提示")
        issues = [
            str(item.get("title") or "")
            for item in findings
            if item.get("judgement") in {"non_compliant", "risk"}
        ]
        value = {
            "overview": "已完成案例全文与知识库技术规程的分项检索审核。",
            "overall_risk_level": overall,
            "overall_conclusion": (
                "经分项审核，主要关注事项包括：" + "、".join(issues[:5]) + "。"
                if issues
                else "经分项审核，暂未形成有证据支持的明确不符合项。"
            ),
            "required_supplements": [],
            "synthesis_degraded": True,
        }
    timings["synthesis"] = round(time.perf_counter() - stage_started, 3)
    value["findings"] = findings
    value = _validate_report(value, evidence)
    value.update({
        "format_version": "ima_rag_audit_v1",
        "generation_mode": "pure_llm_rag",
        "report_method": "semantic_vector_rag+llm_reasoning",
        "embedding_model": SILICONFLOW_EMBEDDING_MODEL,
        "audit_dimensions": dimensions,
        "retrieved_case_chunk_count": len({
            item["chunk_id"] for packet in packets for item in packet["case_hits"]
        }),
        "retrieved_clause_count": len({
            item["chunk_id"] for packet in packets for item in packet["regulation_hits"]
        }),
        "indexed_case_chunk_count": len(case_chunks),
        "indexed_regulation_chunk_count": regulation_count,
        "cache_hit": False,
        "history_context_used": bool(history_text),
        "historical_stage_count": len((_history_context(case_data).get("previous_stages") or [])),
        "current_session_context_used": bool(session_text),
        "history_context_hash": history_hash,
    })
    timings["total"] = round(time.perf_counter() - started, 3)
    value["timings_seconds"] = timings
    result = {
        "format_version": "pure_llm_rag_audit_v1",
        "published_rule_count": 0,
        "summary": {
            "compliant": sum(1 for item in value["findings"] if item.get("judgement") == "compliant"),
            "non_compliant": sum(1 for item in value["findings"] if item.get("judgement") == "non_compliant"),
            "risk": sum(1 for item in value["findings"] if item.get("judgement") == "risk"),
            "insufficient_data": sum(1 for item in value["findings"] if item.get("judgement") == "insufficient"),
        },
        "results": [],
        "risk_report": value,
    }
    AUDIT_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    temporary = cache_file.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    temporary.replace(cache_file)
    return result
