from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .agent import AgentService
from .regulation_rules import RegulationRepository


DOMAIN_TERMS = (
    "基坑", "盾构", "明挖", "暗挖", "矿山法", "高架", "隧道", "车站", "降水",
    "监测", "变形", "沉降", "倾斜", "振动", "净距", "保护区", "安全评估",
    "软土", "粉土", "粉砂", "地下水", "支护", "围护", "开挖", "病害", "裂缝",
    "承压水", "隔离桩", "注浆", "隆起", "收敛", "渗漏", "管涌", "流砂",
    "报警", "预警", "控制值", "管线", "建构筑物", "卸载", "超载", "偏压",
)

RISK_TOPICS = {
    "空间位置与结构安全": ("净距", "保护区", "上穿", "下穿", "侧穿", "盾构", "隧道", "车站"),
    "既有结构状态": ("病害", "裂缝", "渗漏", "收敛", "沉降", "倾斜", "现状调查", "检测"),
    "地层变形与沉降": ("沉降", "变形", "位移", "地层损失", "Peck", "叠层", "倾斜", "隆起"),
    "工程与水文地质": ("软土", "粉土", "粉砂", "地下水", "承压水", "流砂", "管涌", "降水", "回灌"),
    "施工工法与时序": ("施工顺序", "时序", "开挖", "支护", "围护", "注浆", "加固", "封顶", "拆撑"),
    "监测与风险控制": ("监测", "预警", "控制值", "报警", "测点", "巡视", "应急", "信息化施工"),
    "周边环境与运营": ("管线", "建筑", "道路", "振动", "噪声", "运营", "市政设施", "交通"),
    "计算分析与方案完整性": ("数值模拟", "计算", "工况", "参数", "边界条件", "敏感性", "验算", "模型"),
}

RISK_SIGNAL_TERMS = (
    "风险", "不利", "不满足", "不足", "超限", "超过", "异常", "较差", "病害",
    "最大", "最小", "控制值", "报警值", "预警值", "结论", "建议", "应", "不得",
)


def _walk_case(value: Any, path: str = "") -> tuple[list[str], list[str]]:
    facts: list[str] = []
    evidence: list[str] = []
    if isinstance(value, dict):
        if value.get("value") not in (None, ""):
            facts.append(f"{path or 'value'}={value['value']}")
        source = value.get("source_text")
        if isinstance(source, str) and len(source.strip()) >= 8:
            evidence.append(source.strip())
        for key, child in value.items():
            if key in {"source_text", "source_file", "managed_file", "text_file"}:
                continue
            child_path = f"{path}.{key}" if path else str(key)
            child_facts, child_evidence = _walk_case(child, child_path)
            facts.extend(child_facts)
            evidence.extend(child_evidence)
    elif isinstance(value, list):
        for child in value[:80]:
            child_facts, child_evidence = _walk_case(child, path)
            facts.extend(child_facts)
            evidence.extend(child_evidence)
    elif value not in (None, "") and not isinstance(value, (bytes, bytearray)):
        text = str(value).strip()
        if text and len(text) <= 500 and not re.match(r"^[A-Za-z]:[\\/]", text):
            facts.append(f"{path}={text}")
    return facts, evidence


def _tokens(text: str) -> set[str]:
    normalized = re.sub(r"\s+", "", text.lower())
    result = set(re.findall(r"[a-z_][a-z0-9_]{2,}|\d+(?:\.\d+)?", normalized))
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", normalized))
    result.update(chinese[index:index + 2] for index in range(max(0, len(chinese) - 1)))
    result.update(term for term in DOMAIN_TERMS if term in text)
    return {item for item in result if item}


def _make_chunk(rows: list[dict[str, Any]], chunk_id: int) -> dict[str, Any]:
    paragraph_ids = [row.get("paragraph_id") for row in rows if row.get("paragraph_id") is not None]
    pages = [row.get("source_page") for row in rows if row.get("source_page") is not None]
    return {
        "chunk_id": f"C{chunk_id:04d}",
        "text": "\n".join(row["text"] for row in rows),
        "paragraph_start": min(paragraph_ids) if paragraph_ids else None,
        "paragraph_end": max(paragraph_ids) if paragraph_ids else None,
        "source_page": pages[0] if pages and len(set(pages)) == 1 else None,
    }


def _paragraph_chunks(source: str | Path | None, target_size: int = 900) -> list[dict[str, Any]]:
    if not source:
        return []
    path = source if isinstance(source, Path) else Path(source)
    rows: list[dict[str, Any]] = []
    if path.exists() and path.suffix.lower() == ".jsonl":
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = str(row.get("text") or "").strip()
            if text:
                rows.append({
                    "text": text,
                    "paragraph_id": row.get("paragraph_id"),
                    "source_page": row.get("source_page"),
                })
    else:
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else str(source)
        rows = [
            {"text": item.strip(), "paragraph_id": index + 1, "source_page": None}
            for index, item in enumerate(re.split(r"\n+", text))
            if item.strip()
        ]
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_size = 0
    for row in rows:
        row_size = len(row["text"])
        if current and current_size + row_size > target_size:
            chunks.append(_make_chunk(current, len(chunks) + 1))
            current = current[-2:]
            current_size = sum(len(item["text"]) for item in current)
        current.append(row)
        current_size += row_size
        if row_size >= target_size:
            chunks.append(_make_chunk(current, len(chunks) + 1))
            current = []
            current_size = 0
    if current:
        chunks.append(_make_chunk(current, len(chunks) + 1))
    return chunks


def _risk_signal_score(text: str) -> float:
    score = sum(4.0 for term in RISK_SIGNAL_TERMS if term in text)
    score += min(12.0, len(re.findall(r"\d+(?:\.\d+)?\s*(?:mm|cm|m|dB|%|MPa|kPa)", text, re.I)) * 1.5)
    if re.search(r"(结论|建议|风险|影响评价|安全评估)", text):
        score += 8.0
    if re.search(r"(沉降|位移|净距|变形|水位|深度|长度).{0,20}\d", text):
        score += 8.0
    return score


def _rank_case_chunks(chunks: list[dict[str, Any]], queries: list[str], limit: int = 36) -> list[dict[str, Any]]:
    if not chunks:
        return []
    chunk_tokens = [_tokens(item["text"]) for item in chunks]
    frequencies = Counter(token for tokens in chunk_tokens for token in tokens)
    selected: dict[str, dict[str, Any]] = {}
    for query in queries:
        query_tokens = _tokens(query)
        if not query_tokens:
            continue
        ranked: list[tuple[float, int]] = []
        for index, tokens in enumerate(chunk_tokens):
            overlap = query_tokens & tokens
            score = sum(math.log((len(chunks) + 1) / (frequencies[token] + 1)) + 1 for token in overlap)
            score += 12 * sum(1 for term in DOMAIN_TERMS if term in query and term in chunks[index]["text"])
            if score > 0:
                ranked.append((score, index))
        # Keep several passages for every professional topic. This prevents
        # one dense chapter from crowding all other disciplines out.
        for score, index in sorted(ranked, reverse=True)[:4]:
            item = dict(chunks[index])
            item["relevance_score"] = round(score, 4)
            old = selected.get(item["chunk_id"])
            if old is None or item["relevance_score"] > old["relevance_score"]:
                selected[item["chunk_id"]] = item
    # Long reports often state decisive values only in conclusions, tables or
    # monitoring summaries. Include those passages even when wording differs
    # from the regulation clause.
    for signal_score, index in sorted(
        ((_risk_signal_score(item["text"]), index) for index, item in enumerate(chunks)),
        reverse=True,
    )[:12]:
        if signal_score <= 0:
            continue
        item = dict(chunks[index])
        item["relevance_score"] = round(max(float(item.get("relevance_score") or 0), signal_score), 4)
        selected.setdefault(item["chunk_id"], item)
    return sorted(selected.values(), key=lambda item: item["relevance_score"], reverse=True)[:limit]


def retrieve_relevant_clauses(
    case_data: dict[str, Any], repository: RegulationRepository, limit: int = 36,
    document_chunks: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    facts, evidence = _walk_case(case_data)
    full_text_signals = [
        chunk["text"][:1200] for chunk in document_chunks or []
        if any(term in chunk["text"] for term in DOMAIN_TERMS)
    ]
    query = "\n".join(facts[-500:] + evidence[-200:] + full_text_signals[:80])
    query_tokens = _tokens(query)
    active_domain_terms = {term for term in DOMAIN_TERMS if term in query}
    clauses: list[dict[str, Any]] = []
    for document in repository.list_documents():
        if not document.get("active"):
            continue
        for clause in repository.list_clauses(document["regulation_id"]):
            item = dict(clause)
            item["regulation_title"] = document["title"]
            item["tokens"] = _tokens(f"{clause.get('title') or ''}\n{clause['clause_text']}")
            clauses.append(item)
    if not clauses:
        return []
    frequencies = Counter(token for clause in clauses for token in clause["tokens"])
    total = len(clauses)
    for clause in clauses:
        overlap = query_tokens & clause["tokens"]
        score = sum(math.log((total + 1) / (frequencies[token] + 1)) + 1 for token in overlap)
        source = clause["clause_text"]
        matched_domain_terms = {term for term in active_domain_terms if term in source}
        score += 18 * len(matched_domain_terms)
        # Prevent very long table clauses from winning merely because they have
        # more generic character bigrams in common with a long report.
        score /= max(1.0, math.sqrt(len(clause["tokens"]) / 70))
        if "基坑" in active_domain_terms and "基坑" in source:
            score += 45
        if "盾构" in active_domain_terms and "盾构" in source:
            score += 28
        if "降水" in active_domain_terms and "降水" in source:
            score += 32
        clause["relevance_score"] = round(score, 4)
        clause.pop("tokens", None)
    ranked = [
        item for item in sorted(clauses, key=lambda item: item["relevance_score"], reverse=True)
        if item["relevance_score"] > 0
    ]
    # First reserve clauses for every professional topic. A single global rank
    # otherwise over-selects repeated generic words from one chapter.
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for _topic, terms in RISK_TOPICS.items():
        topic_items = [
            item for item in ranked
            if any(term in f"{item.get('title') or ''}{item.get('clause_text') or ''}" for term in terms)
        ][:3]
        for item in topic_items:
            if item["clause_id"] not in selected_ids:
                selected.append(item)
                selected_ids.add(item["clause_id"])
                if len(selected) >= limit:
                    return selected
    # Formula conversion must not crowd qualitative principles and tables out of RAG.
    for item in ranked:
        if item["clause_id"] in selected_ids:
            continue
        selected.append(item)
        selected_ids.add(item["clause_id"])
        if len(selected) >= max(1, limit - 10):
            break
    for knowledge_type, quota in (("qualitative", 6), ("table", 3), ("quantitative", 2)):
        added = 0
        for item in ranked:
            if item.get("knowledge_type") != knowledge_type or item["clause_id"] in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item["clause_id"])
            added += 1
            if added >= quota or len(selected) >= limit:
                break
    return selected[:limit]


def _fallback_report(audit: dict[str, Any], clauses: list[dict[str, Any]], error: str | None = None) -> dict[str, Any]:
    items = []
    for result in audit.get("results") or []:
        if result.get("audit_status") not in {"non_compliant", "triggered"}:
            continue
        execution = result.get("execution") or {}
        items.append({
            "name": result.get("rule_name") or "规程要求",
            "severity": "高" if result.get("audit_status") == "non_compliant" else "中",
            "analysis": execution.get("calculation") or execution.get("message") or "已触发相关规程要求。",
            "case_evidence": [],
            "clause_refs": [str(result.get("clause") or "")],
        })
    if not items:
        items = [{
            "name": "相关规程复核",
            "severity": "提示",
            "analysis": "已检索到与案例相关的技术规程，当前没有形成可直接计算的不符合结论。",
            "case_evidence": [],
            "clause_refs": [str(item.get("clause_no")) for item in clauses[:5]],
        }]
    return {
        "overview": (
            "本次专业风险分析未能完整生成；以下仅保留确定性规则结果，不能据此认定项目不存在风险。"
        ),
        "overall_risk_level": "待分析",
        "overall_conclusion": "需在大模型分析恢复后重新生成专业风险报告。",
        "compliance_sections": [{"title": "工程安全与合规风险", "items": items}],
        "engineering_risk_sections": [],
        "risk_sections": [{"title": "工程安全与合规风险", "items": items}],
        "qualitative_checks": [],
        "required_supplements": [{
            "field": "专业风险分析结果",
            "reason": "大模型结构化结果生成失败，当前结果只覆盖可执行规则，未覆盖全文工程风险。",
        }],
        "retrieved_clause_count": len(clauses),
        "retrieved_case_chunk_count": 0,
        "generation_mode": "deterministic_fallback",
        "generation_warning": error,
    }


def _validate_layered_report(
    value: dict[str, Any], clauses: list[dict[str, Any]], hard_findings: list[dict[str, Any]]
) -> dict[str, Any]:
    clause_sources = {str(item.get("clause_no")): str(item.get("clause_text") or "") for item in clauses}
    hard_statuses: dict[str, set[str]] = {}
    for item in hard_findings:
        clause = str(item.get("clause") or "")
        if clause:
            hard_statuses.setdefault(clause, set()).add(str(item.get("status") or ""))
    negative_terms = ("不符合", "违反", "违规", "未满足", "严禁", "禁止", "不得实施")
    fabricated_obligation_terms = ("严禁", "禁止", "不得实施")
    quality_warnings: list[str] = []
    validated_sections: list[dict[str, Any]] = []
    for section in value.get("compliance_sections") or []:
        valid_items = []
        for item in section.get("items") or []:
            analysis = str(item.get("analysis") or "")
            refs = [str(ref) for ref in item.get("clause_refs") or [] if str(ref) in clause_sources]
            source = "\n".join(clause_sources[ref] for ref in refs)
            reason = ""
            if not refs:
                reason = "未引用本次检索到的有效规程条文"
            elif any(term in analysis for term in negative_terms) and all(
                hard_statuses.get(ref) == {"compliant"} for ref in refs if ref in hard_statuses
            ) and any(ref in hard_statuses for ref in refs):
                reason = "与同条款确定性计算的符合结论冲突"
            elif any(term in analysis and term not in source for term in fabricated_obligation_terms):
                reason = "使用了条文原文不存在的禁止性表述"
            else:
                source_domain = {term for term in DOMAIN_TERMS if term in source}
                analysis_domain = {term for term in DOMAIN_TERMS if term in analysis}
                if ("规程规定" in analysis or "规程要求" in analysis) and not (source_domain & analysis_domain):
                    reason = "风险主题与引用条文缺少直接语义关联"
                requirement_numbers = re.findall(
                    r"(?:规程规定|规程要求|条文规定)[^。；]{0,50}?(\d+(?:\.\d+)?)\s*(?:m|mm|dB|%)",
                    analysis,
                    flags=re.IGNORECASE,
                )
                source_numbers = set(re.findall(r"\d+(?:\.\d+)?", source))
                unsupported = [number for number in requirement_numbers if number not in source_numbers]
                if not reason and unsupported:
                    reason = f"规程限值{','.join(unsupported)}无法从引用条文原文核实"
            if reason:
                quality_warnings.append(f"{item.get('name') or '未命名结论'}：{reason}")
                continue
            item["clause_refs"] = refs
            item["basis_type"] = "regulation_requirement"
            valid_items.append(item)
        if valid_items:
            validated = dict(section)
            validated["items"] = valid_items
            validated_sections.append(validated)
    engineering_sections = []
    for section in value.get("engineering_risk_sections") or []:
        items = []
        for item in section.get("items") or []:
            if not item.get("case_evidence"):
                quality_warnings.append(f"{item.get('name') or '未命名风险'}：缺少案例证据，已剔除")
                continue
            item["basis_type"] = "case_inference"
            items.append(item)
        if items:
            validated = dict(section)
            validated["items"] = items
            engineering_sections.append(validated)
    value["compliance_sections"] = validated_sections
    value["engineering_risk_sections"] = engineering_sections
    value["risk_sections"] = validated_sections + engineering_sections
    value["quality_warnings"] = quality_warnings
    all_items = [
        item
        for section in value["risk_sections"]
        for item in section.get("items") or []
    ]
    severity_rank = {"提示": 0, "低": 1, "中": 2, "高": 3, "重大": 4}
    highest = max(
        (severity_rank.get(str(item.get("severity") or ""), 0) for item in all_items),
        default=0,
    )
    calculated_level = {0: "提示", 1: "低风险", 2: "中风险", 3: "高风险", 4: "重大风险"}[highest]
    declared_level = str(value.get("overall_risk_level") or "").strip()
    if declared_level not in {"提示", "低风险", "中风险", "高风险", "重大风险"}:
        value["overall_risk_level"] = calculated_level
    elif severity_rank.get(declared_level.replace("风险", ""), 0) < highest:
        value["overall_risk_level"] = calculated_level
    value["risk_item_count"] = len(all_items)
    value["high_risk_count"] = sum(
        1 for item in all_items if str(item.get("severity") or "") in {"高", "重大"}
    )
    value["compliance_finding_count"] = sum(
        len(section.get("items") or []) for section in validated_sections
    )
    value["engineering_risk_count"] = sum(
        len(section.get("items") or []) for section in engineering_sections
    )
    if not value.get("overall_conclusion"):
        if all_items:
            value["overall_conclusion"] = (
                f"确定性规则与全文专业分析共识别{len(all_items)}项需关注事项，"
                f"综合风险等级为{value['overall_risk_level']}。"
            )
        else:
            value["overall_conclusion"] = (
                "当前证据未形成明确不符合项，但这不等同于工程无风险，仍应结合完整资料持续复核。"
            )
    return value


def generate_risk_report(
    case_data: dict[str, Any], audit: dict[str, Any], repository: RegulationRepository | None = None,
    agent: AgentService | None = None, case_document: str | Path | None = None,
) -> dict[str, Any]:
    repository = repository or RegulationRepository()
    document_chunks = _paragraph_chunks(case_document)
    clauses = retrieve_relevant_clauses(case_data, repository, document_chunks=document_chunks)
    facts, evidence = _walk_case(case_data)
    topic_queries = [f"{title} {' '.join(terms)}" for title, terms in RISK_TOPICS.items()]
    clause_queries = [f"{item.get('title') or ''} {item['clause_text'][:700]}" for item in clauses]
    selected_chunks = _rank_case_chunks(document_chunks, topic_queries + clause_queries)
    full_text_context = "\n\n".join(
        f"[{item['chunk_id']}|页码{item.get('source_page')}|段落{item.get('paragraph_start')}-{item.get('paragraph_end')}]\n"
        f"{item['text'][:1400]}"
        for item in selected_chunks
    )
    case_context = "\n".join((facts[-260:] + [f"属性来源：{item}" for item in evidence[-80:]]))[:18000]
    if full_text_context:
        case_context = f"{case_context}\n\n案例全文召回片段：\n{full_text_context}"[:40000]
    clause_context = "\n\n".join(
        f"[{item['clause_no']}|{item.get('knowledge_type') or 'knowledge'}]《{item['regulation_title']}》\n{item['clause_text'][:1400]}"
        for item in clauses
    )[:26000]
    hard_findings = [
        {
            "status": item.get("audit_status"),
            "rule": item.get("rule_name"),
            "clause": item.get("clause"),
            "result": (item.get("execution") or {}).get("calculation") or (item.get("execution") or {}).get("message"),
        }
        for item in audit.get("results") or []
        if item.get("audit_status") in {"non_compliant", "triggered", "compliant"}
    ]
    if not clauses:
        return _fallback_report(audit, clauses, "未检索到相关规程条文。")
    system = (
        "你是城市轨道交通结构安全保护审查专家。请像专业评估报告一样，结合案例证据和检索到的规程条文，"
        "分别完成规程合规审查和开放式工程风险识别。不得逐条罗列全部规程，不得把不相关条文或普通缺字段写成待复审。"
        "只在缺失信息会直接影响重要结论时列入required_supplements。硬规则计算结果不得被改写或推翻。"
        "对于qualitative条文，先提取条文意图，再形成检查问题，并在案例中查找分析、计算或措施作为证据；"
        "证据充分记为satisfied，存在冲突记为risk，相关但报告未论证记为not_demonstrated，无关记为not_applicable。"
        "开放式工程风险可以根据案例事实和成熟工程机理进行专业推断，但必须标为case_inference，不得伪造规程条款、"
        "标准名称、限值或计算结果；只有给定规程原文明确支持时才可标为regulation_requirement。"
        "每项结论都要引用案例全文片段编号或属性原文。表达应专业、具体、克制，区分已确认事实、风险推断和待补充论证。"
        "若确定性规则显示某条款compliant，禁止再依据同一条款判定不符合。"
        "不得仅因没有同名字段就判定缺失。风险等级按后果严重性、发生可能性和证据充分度综合确定；"
        "“未发现确定性不符合”不等于“无风险”。只返回JSON。"
    )
    prompt = f"""请输出以下结构：
{{
  "overview": "3至5句项目总体判断，先说空间关系和主要工程特征，再概括主要风险与审核结论",
  "overall_risk_level": "提示|低风险|中风险|高风险|重大风险",
  "overall_conclusion": "明确区分确定性规则结论与全文专业风险判断的综合结论",
  "compliance_sections": [
    {{"title": "规程合规风险类别", "items": [
      {{"name": "风险名称", "severity": "高|中|低|提示", "basis_type": "regulation_requirement",
        "analysis": "条文要求、案例现状和差距", "case_evidence": ["C0001：案例原文或属性数值"],
        "clause_refs": ["5.2.3"], "recommendation": "针对性处置建议"}}
    ]}}
  ],
  "engineering_risk_sections": [
    {{"title": "开放式工程风险类别", "items": [
      {{"name": "风险名称", "severity": "高|中|低|提示", "basis_type": "case_inference",
        "analysis": "基于工程机理和案例事实的风险分析，不伪造限值", "case_evidence": ["C0002：案例原文或属性数值"],
        "clause_refs": [], "recommendation": "建议核查或控制措施"}}
    ]}}
  ],
  "qualitative_checks": [
    {{"clause_ref": "4.1.1", "intent": "条文意图", "check_question": "针对本案例形成的检查问题", "status": "satisfied|risk|not_demonstrated|not_applicable", "finding": "结合案例证据的判断", "case_evidence": ["案例原文"]}}
  ],
  "required_supplements": [{{"field": "中文资料名", "reason": "为何会影响重要结论"}}]
}}

请执行完整而非关键词式的专业审查：
1. 先识别项目对象、空间关系、既有结构状态、施工阶段、地层和地下水条件。
2. 再核查计算模型、关键工况、变形控制、降水、施工时序、监测预警、应急措施及周边环境。
3. 对报告给出的预测值、实测值、控制值和规程限值进行同单位比较；不能比较时说明原因，不得臆造阈值。
4. 合规风险只写规程原文能够支持的差距；工程风险可依据成熟机理推断，但必须有案例证据。
5. 通常归纳6至12项最重要风险，重复事项合并；没有证据的类别不要凑数。
6. 若既有结构已有较大变形、预测值接近或超过控制值、多项目影响叠加、软弱地层降水或关键论证缺失，
   应在证据支持的前提下提高风险等级并说明传递路径。

案例资料：
{case_context}

确定性规则结果：
{json.dumps(hard_findings, ensure_ascii=False)}

检索到的规程条文：
{clause_context}
    """
    try:
        service = agent or AgentService()
        try:
            value = service.complete_json(system, prompt, max_tokens=4500)
        except RuntimeError as exc:
            if "合法JSON" not in str(exc):
                raise
            retry_system = (
                system
                + " 上一次输出存在JSON语法错误。本次必须保证JSON完整闭合，适当减少条目和文字长度，"
                  "不要输出Markdown代码块或JSON之外的任何字符。"
            )
            value = service.complete_json(retry_system, prompt, max_tokens=4200)
        if not isinstance(value, dict):
            raise RuntimeError("大模型未返回风险分组结构。")
        compliance = value.get("compliance_sections")
        engineering = value.get("engineering_risk_sections")
        if not isinstance(compliance, list) or not isinstance(engineering, list):
            raise RuntimeError("大模型未返回分层风险结构。")
        value = _validate_layered_report(value, clauses, hard_findings)
        value["retrieved_clause_count"] = len(clauses)
        value["retrieved_case_chunk_count"] = len(selected_chunks)
        value["generation_mode"] = "llm_rag"
        value["report_method"] = "deterministic_rules+fulltext_rag+professional_inference"
        value["evidence_chunks"] = [
            {key: item.get(key) for key in ("chunk_id", "source_page", "paragraph_start", "paragraph_end")}
            for item in selected_chunks
        ]
        value["retrieved_clauses"] = [
            {"clause": item["clause_no"], "title": item.get("title"), "regulation": item["regulation_title"],
             "knowledge_type": item.get("knowledge_type")}
            for item in clauses
        ]
        return value
    except RuntimeError as exc:
        return _fallback_report(audit, clauses, str(exc))
