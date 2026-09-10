"""Deterministic audit knowledge graph and non-normative LLM Wiki.

The graph expands relationships already signalled by the current project,
rule-engine results and RAG evidence.  It is deliberately not a replacement
for regulations: neither graph edges nor Wiki text may be cited as a clause.
"""
from __future__ import annotations

import re
from typing import Any


AUDIT_KNOWLEDGE_GRAPH_VERSION = "audit-knowledge-graph-v1"
LLM_WIKI_VERSION = "audit-llm-wiki-v1"

TOPICS: dict[str, dict[str, Any]] = {
    "空间位置与结构安全": {
        "terms": ("净距", "保护区", "上穿", "下穿", "侧穿", "交叉", "邻近", "隧道", "车站"),
        "wiki": "空间关系用于识别保护对象和可能的受力、变形传递路径；应结合实际净距、结构位置和施工范围核查。",
        "focus": "核查空间关系、最小净距、保护区范围及结构边界的对应关系。",
    },
    "基坑与支护": {
        "terms": ("基坑", "开挖", "支护", "围护", "地下连续墙", "地连墙", "锚杆", "锚索", "内支撑", "止水帷幕"),
        "wiki": "基坑开挖、围护和支撑体系会共同影响变形控制与施工工况，需与实际工序、设计参数和监测安排交叉核查。",
        "focus": "核查开挖深度、支护体系、分层分区工况、止水与支撑转换条件。",
    },
    "既有结构状态": {
        "terms": ("病害", "裂缝", "渗漏", "收敛", "沉降", "倾斜", "现状调查", "检测"),
        "wiki": "既有结构的初始状态决定风险判读的基线；发现病害或缺少现状资料时，应关注复测、基线建档和保护措施衔接。",
        "focus": "核查既有结构调查、检测基线、病害处置与施工期间复核安排。",
    },
    "地层变形与沉降": {
        "terms": ("沉降", "变形", "位移", "地层损失", "倾斜", "隆起", "收敛"),
        "wiki": "地层与结构变形通常与开挖、降水、支护刚度和施工时序相关；应按项目材料和规程证据判断控制与预警要求。",
        "focus": "核查变形控制指标、计算工况、监测点布置和预警后的处置闭环。",
    },
    "工程与水文地质": {
        "terms": ("软土", "粉土", "粉砂", "地下水", "承压水", "流砂", "管涌", "降水", "回灌", "水位"),
        "wiki": "水文地质条件会影响开挖稳定、渗流和变形响应；应核对勘察资料、降排水方案及其对周边结构的影响控制。",
        "focus": "核查地层参数、地下水条件、降排水/回灌方案及止水有效性验证。",
    },
    "施工工法与时序": {
        "terms": ("施工顺序", "时序", "开挖", "支护", "围护", "注浆", "加固", "封顶", "拆撑"),
        "wiki": "同一方案在不同施工阶段的风险并不相同，关系扩展用于提示工序转换、支撑转换和关键节点的专项核查。",
        "focus": "核查施工顺序、关键工序条件、支撑转换、应急措施和责任分工。",
    },
    "监测与风险控制": {
        "terms": ("监测", "预警", "控制值", "报警", "测点", "巡视", "应急", "信息化施工"),
        "wiki": "监测是风险控制的反馈环节；应核查对象、点位、频率、控制值、预警响应与信息报送，而非仅确认是否有监测章节。",
        "focus": "核查监测对象、点位、频率、控制值、预警分级及响应闭环。",
    },
}

# Directed, review-oriented relations.  These are generic causal/check links,
# not engineering thresholds or regulatory requirements.
RELATIONS: tuple[tuple[str, str, str], ...] = (
    ("空间位置与结构安全", "关联核查", "既有结构状态"),
    ("空间位置与结构安全", "影响路径", "地层变形与沉降"),
    ("基坑与支护", "影响路径", "地层变形与沉降"),
    ("基坑与支护", "关联工况", "施工工法与时序"),
    ("基坑与支护", "关联条件", "工程与水文地质"),
    ("工程与水文地质", "影响路径", "地层变形与沉降"),
    ("工程与水文地质", "控制反馈", "监测与风险控制"),
    ("既有结构状态", "控制反馈", "监测与风险控制"),
    ("施工工法与时序", "控制反馈", "监测与风险控制"),
    ("地层变形与沉降", "控制反馈", "监测与风险控制"),
)

RULE_FIELD_TOPIC = {
    "pit_depth": "基坑与支护",
    "pit_depth_m": "基坑与支护",
    "support_components": "基坑与支护",
    "support_form": "基坑与支护",
    "minimum_horizontal_clearance": "空间位置与结构安全",
    "minimum_horizontal_clearance_m": "空间位置与结构安全",
    "minimum_vertical_clearance": "空间位置与结构安全",
    "minimum_vertical_clearance_m": "空间位置与结构安全",
    "buried_depth": "空间位置与结构安全",
    "buried_depth_m": "空间位置与结构安全",
    "dewatering_method": "工程与水文地质",
    "is_complex_geology_or_hydrology": "工程与水文地质",
    "is_soft_soil": "工程与水文地质",
    "structure_condition": "既有结构状态",
    "monitoring": "监测与风险控制",
}


def _contains_topic_term(text: str, terms: tuple[str, ...]) -> bool:
    normalized = re.sub(r"\s+", "", text)
    return any(term in normalized for term in terms)


def build_audit_knowledge_graph(
    project_facts: str,
    deterministic_results: list[dict[str, Any]],
    top_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a compact, inspectable graph from this audit's actual inputs."""
    nodes: list[dict[str, Any]] = [{
        "id": "project:current", "type": "project", "label": "当前项目事实",
    }]
    edges: list[dict[str, str]] = []
    activated: set[str] = set()

    fact_text = str(project_facts or "")
    for topic, definition in TOPICS.items():
        if _contains_topic_term(fact_text, definition["terms"]):
            activated.add(topic)
            edges.append({"from": "project:current", "relation": "涉及", "to": f"topic:{topic}"})

    for index, evidence in enumerate(top_evidence, start=1):
        evidence_id = str(evidence.get("chunk_id") or f"evidence-{index}")
        nodes.append({
            "id": f"evidence:{evidence_id}", "type": "rag_evidence", "label": evidence_id,
            "corpus_type": str(evidence.get("corpus_type") or "unknown"),
        })
        evidence_text = str(evidence.get("chunk_text") or "")
        for topic, definition in TOPICS.items():
            if _contains_topic_term(evidence_text, definition["terms"]):
                activated.add(topic)
                edges.append({"from": f"evidence:{evidence_id}", "relation": "关联", "to": f"topic:{topic}"})

    for result in deterministic_results:
        if str(result.get("audit_status") or "") not in {"triggered", "non_compliant", "compliant"}:
            continue
        rule_id = str(result.get("rule_id") or "unknown-rule")
        nodes.append({"id": f"rule:{rule_id}", "type": "rule_result", "label": rule_id})
        input_fields = (result.get("input_values") or {}).keys()
        for field in input_fields:
            topic = RULE_FIELD_TOPIC.get(str(field))
            if not topic:
                continue
            activated.add(topic)
            edges.append({"from": f"rule:{rule_id}", "relation": "判定关联", "to": f"topic:{topic}"})

    for topic in sorted(activated):
        nodes.append({"id": f"topic:{topic}", "type": "audit_topic", "label": topic})

    expansions: list[dict[str, str]] = []
    for source, relation, target in RELATIONS:
        if source not in activated or target in activated:
            continue
        expansions.append({
            "source": source,
            "relation": relation,
            "target": target,
            "review_focus": TOPICS[target]["focus"],
            "wiki": TOPICS[target]["wiki"],
        })
        edges.append({"from": f"topic:{source}", "relation": relation, "to": f"topic:{target}"})
    return {
        "version": AUDIT_KNOWLEDGE_GRAPH_VERSION,
        "llm_wiki_version": LLM_WIKI_VERSION,
        "nodes": nodes[:80],
        "edges": edges[:160],
        "activated_topics": sorted(activated),
        "relationship_expansion": expansions[:12],
    }


def render_relationship_expansion(graph: dict[str, Any]) -> str:
    """Produce an LLM-safe Wiki context. It is intentionally non-citable."""
    expansions = graph.get("relationship_expansion") or []
    if not expansions:
        return "本轮知识图谱未形成额外关系扩展；不得据此补造审核意见。"
    lines = [
        "知识图谱关系扩展与 LLM Wiki（仅辅助分析，不是项目事实或规程依据，不能单独引用或下符合性结论）："
    ]
    for item in expansions:
        lines.append(
            "- {source} —{relation}→ {target}：{focus} Wiki说明：{wiki}".format(
                source=item["source"], relation=item["relation"], target=item["target"],
                focus=item["review_focus"], wiki=item["wiki"],
            )
        )
    return "\n".join(lines)
