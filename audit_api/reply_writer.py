from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from .agent import AgentService
from .config import STAGE1_DATABASE


STAGE_TITLE = {
    "出让": "出让条件",
    "规划": "规划方案",
    "设计": "设计方案",
    "施工": "施工方案",
}


STAGE_STYLE_RULES = {
    "规划": {
        "name": "规划阶段",
        "lead": "我部原则同意该规划方案。为确保地铁结构、设施及运营安全，请贵司在后续工作中注意如下事项：",
        "focus": (
            "规划阶段第2点应以原则性、方向性意见为主：路径/线位/平纵断面优化、避让地铁用地红线和保护区、"
            "加大水平及竖向净距、明确交叉节点实施方式、开展现状调查及安全评估、为后续设计和施工预留条件。"
            "不要写成施工过程控制口径。"
        ),
        "second_point_tone": (
            "规划阶段第二点写法应偏“原则同意+后续深化”口径，不展开内部审核细节。"
            "通常概括说明需进一步优化规划线位、平纵断面和工程布置，尽量避让或加大与地铁结构安全净距，"
            "并要求后续阶段补充专项评估、保护措施和报审材料。"
        ),
        "closing": (
            "根据《南京市轨道交通条例》的规定，请贵司将该工程后续设计方案、施工图设计及施工方案按规定书面征求我部意见。"
            "项目实施期间，应由有资质的单位对地铁结构进行变形监测。"
        ),
    },
    "设计": {
        "name": "设计阶段",
        "lead": "请贵司按如下意见修改完善该设计方案，形成正式施工图后报我部备案：",
        "focus": (
            "设计阶段第2点应以设计技术审查为主：核实与地铁结构的空间关系、净距、埋深和交叉节点，"
            "完善基坑、支护、止水、降水、加固、顶管、盾构等设计参数，补充计算模型、工况设置、变形控制指标、"
            "现状调查、安全评估、专项保护设计和监测设计。不要泛泛写施工现场管理。"
        ),
        "second_point_tone": (
            "设计阶段第二点写法应偏“修改完善设计方案/施工图后备案或审查”口径。"
            "可概括要求复核设计参数、计算分析、专项保护设计、监测设计和安全控制指标，"
            "但不逐项照搬审核条目，不堆砌精确数值和规范条文。"
        ),
        "closing": (
            "根据《南京市轨道交通条例》的规定，该工程施工方案应报我部进行技术审查。"
            "施工期间，应由有资质的单位对地铁结构进行变形监测。"
        ),
    },
    "施工": {
        "name": "施工阶段",
        "lead": "为确保地铁结构、设施及运营安全，请贵司按如下意见对该施工方案进行修改完善并报我部备案：",
        "focus": (
            "施工阶段第2点应以施工实施控制为主：施工前技术交底、施工工序和时序、设备工法及参数控制、"
            "基坑开挖、支护、止水、降水、顶管、盾构、注浆、回填、荷载控制、监测巡视、信息化施工、"
            "异常停工报告、方案变化重新报审。不要只停留在规划深化或设计原则。"
        ),
        "second_point_tone": (
            "施工阶段第二点写法应偏“施工组织和现场控制”口径。"
            "可概括要求严格按方案实施、完善施工组织、监测预警、现场巡查、应急处置和信息报送，"
            "避免写成规划原则或设计计算审查，也不要将审核意见的风险项逐条原样写入。"
        ),
        "closing": (
            "根据《南京市轨道交通条例》的规定，施工期间地铁设施保护工作人员将进入施工现场进行查看与监督，请贵司予以配合。"
            "施工期间，应由有资质的单位对地铁结构进行变形监测。"
        ),
    },
    "出让": {
        "name": "出让阶段",
        "lead": "为确保地铁结构、设施及运营安全，请贵司在后续规划设计和实施过程中注意如下事项：",
        "focus": (
            "出让阶段按前置条件口径书写，重点说明地块或工程与地铁保护区、用地红线、既有或规划线路的关系，"
            "提出后续规划设计、专项论证、安全评估和报审要求。"
        ),
        "second_point_tone": (
            "出让阶段第二点写法应偏“前置条件和后续控制要求”口径，重点概括地块开发边界、保护区控制、"
            "规划设计深化、专项论证、安全评估和后续报审要求。"
        ),
        "closing": (
            "根据《南京市轨道交通条例》的规定，后续规划设计、施工图设计及施工方案应按规定书面征求我部意见。"
            "项目实施期间，应由有资质的单位对地铁结构进行变形监测。"
        ),
    },
}


def _stage_key(stage: Any) -> str:
    text = str(stage or "").strip()
    if "施工" in text or "勘察" in text:
        return "施工"
    if "设计" in text or "施工图" in text or "备案" in text:
        return "设计"
    if "出让" in text:
        return "出让"
    if "规划" in text or "方案" in text:
        return "规划"
    return "规划"


def _fact(package: dict[str, Any], label: str, default: str = "") -> str:
    for item in package.get("project_facts", []):
        if item.get("label") == label and item.get("value") not in (None, "", []):
            return str(item["value"]).strip()
    return default


def _measure(value: Any, suffix: str = "米") -> str:
    if value in (None, ""):
        return ""
    return f"{value}{suffix}"


def _has_positive_measure(value: Any) -> bool:
    if value in (None, ""):
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return True


def _project_description(data: dict[str, Any]) -> str:
    project = data.get("project", {})
    metro = data.get("metro_structure", {})
    pit = data.get("pit", {})
    pieces: list[str] = []

    if project.get("project_address"):
        pieces.append(f"项目位于{project['project_address']}")
    if project.get("construction_content"):
        pieces.append(str(project["construction_content"]).rstrip("。；"))
    if _has_positive_measure(pit.get("pit_depth_m")):
        pieces.append(f"基坑开挖深度约{_measure(pit['pit_depth_m'])}")
    if _has_positive_measure(pit.get("pit_length_m")):
        pieces.append(f"基坑长度约{_measure(pit['pit_length_m'])}")

    metro_name = "".join(
        str(value)
        for value in (metro.get("metro_line_name"), metro.get("metro_section_name"))
        if value
    )
    relation = project.get("relative_relationship")
    structure = metro.get("structure_method")
    relation_text = ""
    if metro_name:
        relation_text = f"项目与{metro_name}"
        if structure:
            relation_text += f"{structure}结构"
        if relation:
            relation_text += f"呈{relation}关系"
    distances: list[str] = []
    if _has_positive_measure(pit.get("minimum_horizontal_clearance_m")):
        distances.append(f"最小水平净距约{_measure(pit['minimum_horizontal_clearance_m'])}")
    if _has_positive_measure(pit.get("minimum_vertical_clearance_m")):
        distances.append(f"最小竖向净距约{_measure(pit['minimum_vertical_clearance_m'])}")
    if relation_text:
        if distances:
            relation_text += "，" + "，".join(distances)
        pieces.append(relation_text)

    if not pieces:
        pieces.append("项目建设内容及其与既有地铁结构的空间关系详见报审资料")
    return "，".join(pieces).rstrip("，；。") + "。"


def _join_cn(parts: list[str], sep: str = "，") -> str:
    return sep.join(str(part).strip("，；。 ") for part in parts if str(part or "").strip())


def _metro_relation_text(project: dict[str, Any], metro: dict[str, Any], pit: dict[str, Any]) -> str:
    metro_name = _join_cn([
        metro.get("metro_line_name"),
        metro.get("metro_section_name"),
    ], "")
    structure = str(metro.get("structure_method") or "").strip()
    relation = str(project.get("relative_relationship") or "").strip()
    pieces: list[str] = []
    if metro_name:
        text = f"与{metro_name}"
        if structure:
            text += f"{structure}结构"
        if relation:
            text += f"呈{relation}关系"
        pieces.append(text)
    distances: list[str] = []
    if _has_positive_measure(pit.get("minimum_horizontal_clearance_m")):
        distances.append(f"最小水平净距约{_measure(pit['minimum_horizontal_clearance_m'])}")
    if _has_positive_measure(pit.get("minimum_vertical_clearance_m")):
        distances.append(f"最小竖向净距约{_measure(pit['minimum_vertical_clearance_m'])}")
    if _has_positive_measure(metro.get("buried_depth_m")):
        distances.append(f"对应地铁结构埋深约{_measure(metro['buried_depth_m'])}")
    if distances:
        pieces.append("、".join(distances))
    return _join_cn(pieces)


def _works_text(project: dict[str, Any], pit: dict[str, Any]) -> str:
    pieces: list[str] = []
    content = str(project.get("construction_content") or "").strip()
    project_type = str(project.get("project_type") or "").strip()
    if content:
        pieces.append(content)
    elif project_type:
        pieces.append(f"拟实施{project_type}工程")
    if _has_positive_measure(pit.get("pit_depth_m")):
        pieces.append(f"基坑开挖深度约{_measure(pit['pit_depth_m'])}")
    if _has_positive_measure(pit.get("pit_length_m")):
        pieces.append(f"基坑长度约{_measure(pit['pit_length_m'])}")
    if pit.get("support_components"):
        support = pit["support_components"]
        if isinstance(support, list):
            support_text = "、".join(str(item) for item in support if item)
        else:
            support_text = str(support)
        if support_text:
            pieces.append(f"采用{support_text}等支护形式")
    if pit.get("dewatering_method"):
        pieces.append(f"降水方式为{pit['dewatering_method']}")
    return _join_cn(pieces)


def _stage_project_description(data: dict[str, Any], stage_key: str) -> str:
    """生成复函正文第1点：按规划、设计、施工阶段分别书写项目情况和涉铁关系。"""
    project = data.get("project", {})
    metro = data.get("metro_structure", {})
    pit = data.get("pit", {})
    project_name = str(project.get("project_name") or "").strip()
    address = str(project.get("project_address") or "").strip()
    works = _works_text(project, pit)
    relation = _metro_relation_text(project, metro, pit)

    if stage_key == "施工":
        pieces: list[str] = []
        subject = project_name or "该工程"
        if address:
            pieces.append(f"{subject}位于{address}")
        else:
            pieces.append(subject)
        if works:
            pieces.append(f"本次施工内容为{works}")
        if relation:
            pieces.append(relation)
        if not pieces:
            return "该工程施工内容、施工方法及其与既有地铁结构的空间关系详见报审资料。"
        return _join_cn(pieces).rstrip("，；。") + "。"

    if stage_key == "设计":
        pieces = []
        subject = project_name or "该工程"
        if address:
            pieces.append(f"{subject}位于{address}")
        else:
            pieces.append(subject)
        if works:
            pieces.append(f"本次设计方案主要内容为{works}")
        if relation:
            pieces.append(relation)
        if not pieces:
            return "该工程设计方案内容及其与既有地铁结构的空间关系详见报审资料。"
        return _join_cn(pieces).rstrip("，；。") + "。"

    if stage_key == "出让":
        pieces = []
        subject = project_name or "该地块"
        if address:
            pieces.append(f"{subject}位于{address}")
        else:
            pieces.append(subject)
        if relation:
            pieces.append(relation)
        if works:
            pieces.append(f"后续拟实施内容为{works}")
        if not pieces:
            return "该地块出让条件及其与既有或规划地铁结构的空间关系详见报审资料。"
        return _join_cn(pieces).rstrip("，；。") + "。"

    pieces = []
    subject = project_name or "该工程"
    if works:
        pieces.append(f"{subject}主要建设内容为{works}")
    else:
        pieces.append(subject)
    if relation:
        pieces.append(f"其与地铁相对关系为：{relation}")
    elif address:
        pieces.append(f"项目位于{address}，与地铁相对关系详见报审资料")
    else:
        pieces.append("其与地铁相对关系详见报审资料")
    return _join_cn(pieces).rstrip("，；。") + "。"


def _compact_audit(package: dict[str, Any], dynamic_audit: dict[str, Any]) -> dict[str, Any]:
    risk_report = dynamic_audit.get("risk_report", {})
    findings = []
    for item in risk_report.get("findings", []):
        if item.get("judgement") not in {"non_compliant", "risk", "insufficient"}:
            continue
        findings.append({
            "title": item.get("title"),
            "risk_level": item.get("risk_level"),
            "judgement": item.get("judgement"),
            "analysis": str(item.get("analysis") or "")[:500],
            "recommendation": str(item.get("recommendation") or "")[:300],
            "regulation_evidence": [
                {
                    "document_title": Path(str(evidence.get("document_title") or "")).name,
                    "clause": evidence.get("section") or evidence.get("clause"),
                    "text": str(evidence.get("chunk_text") or evidence.get("text") or "")[:350],
                }
                for evidence in (item.get("regulation_evidence") or [])[:3]
            ],
        })

    deterministic = [
        {
            "topic": item.get("topic"),
            "result": item.get("result"),
            "conclusion": item.get("conclusion"),
            "clauses": item.get("regulation_clauses"),
        }
        for item in package.get("audit_opinions", [])[:10]
    ]
    return {
        "overall_risk_level": risk_report.get("overall_risk_level"),
        "overall_conclusion": risk_report.get("overall_conclusion"),
        "required_supplements": risk_report.get("required_supplements", []),
        "findings": findings[:12],
        "deterministic_decisions": deterministic,
    }


def _extract_second_point(text: str) -> str:
    """从历史复函正文中提取第2点，用于学习同阶段第二点的详略和句式。"""
    source = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not source.strip():
        return ""

    start_pattern = re.compile(r"(?:^|\n)\s*(?:2[\.．、]|（二）|二[、\.．])\s*", re.MULTILINE)
    end_pattern = re.compile(r"(?:^|\n)\s*(?:3[\.．、]|（三）|三[、\.．])\s*", re.MULTILINE)
    start_match = start_pattern.search(source)
    if not start_match:
        return ""
    end_match = end_pattern.search(source, start_match.end())
    body = source[start_match.end(): end_match.start() if end_match else len(source)]
    body = re.sub(r"\n{2,}", "\n", body).strip()
    body = re.sub(r"[ \t]+", " ", body)
    return body[:1800]


def _stage_history_samples(stage_key: str, limit: int = 3) -> str:
    if not STAGE1_DATABASE.exists():
        return ""
    db_stage = {"规划": "规划", "设计": "设计", "施工": "施工", "出让": "规划"}.get(stage_key, "规划")
    try:
        with sqlite3.connect(STAGE1_DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT reply_text, advice_text
                FROM reply_cases
                WHERE active = 1 AND stage = ?
                ORDER BY updated_at DESC, case_id DESC
                LIMIT ?
                """,
                (db_stage, limit),
            ).fetchall()
    except sqlite3.Error:
        return ""
    samples: list[str] = []
    for row in rows:
        text = str(row["reply_text"] or row["advice_text"] or "").strip()
        if text:
            second_point = _extract_second_point(text) or text
            samples.append(second_point[:1600])
    return "\n\n---同阶段历史复函第2点样例---\n".join(samples)


def _historical_style_sample(package: dict[str, Any], stage_key: str) -> str:
    history = package.get("historical_advice", {})
    text = str(history.get("attention_text") or "").strip()
    if text:
        text = _extract_second_point(text) or text
    selected = package.get("history_match", {}).get("selected_match") or {}
    selected_text = str(selected.get("advice_text") or "").strip()
    if selected_text:
        selected_text = _extract_second_point(selected_text) or selected_text
    stage_samples = _stage_history_samples(stage_key)
    return "\n\n".join(part for part in (text, selected_text, stage_samples) if part)[:9000]


def _normalize_items(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    cleaned: list[str] = []
    for value in items:
        text = re.sub(r"^\s*(?:[（(]\d+[）)]|\d+[.、．])\s*", "", str(value or "")).strip()
        if text:
            cleaned.append(text.rstrip("。") + "。")
    return cleaned[:6]


def _fallback_items(package: dict[str, Any], audit: dict[str, Any], stage_key: str) -> list[str]:
    items = []
    if stage_key == "施工":
        items = [
            "施工前应进一步完善施工组织、技术交底、现场管控和应急处置措施，严格按经审查或备案的方案组织实施。",
            "施工期间应加强地铁结构监测、现场巡视和信息反馈，发现异常情况或方案发生变化时，应及时报我部并按规定履行相关手续。",
        ]
    elif stage_key == "设计":
        items = [
            "应结合项目与地铁结构的空间关系、地质条件和既有结构现状，进一步复核设计参数、计算分析和安全控制指标。",
            "应完善专项保护设计、监测设计及后续施工控制要求，确保项目实施满足地铁结构安全保护要求。",
        ]
    elif stage_key == "出让":
        items = [
            "后续规划设计应充分考虑地铁保护区、用地红线及既有或规划地铁结构控制要求，优化建设边界和工程布置。",
            "后续实施前应按规定开展专项论证、安全评估和保护方案编制，并将相关方案书面征求我部意见。",
        ]
    else:
        items = [
            "应结合项目与地铁结构的空间关系、现场条件和后续实施需要，进一步深化规划方案并优化工程布置。",
            "后续设计和施工前应按规定开展地铁结构现状调查、安全评估、专项保护方案编制及报审工作。",
        ]
    return _normalize_items(items)


def _contains_hard_rejection(audit: dict[str, Any]) -> bool:
    text = json.dumps(audit, ensure_ascii=False)
    return any(
        phrase in text
        for phrase in (
            "不予通过",
            "不同意",
            "不得实施",
            "严禁实施",
            "禁止实施",
            "退回",
        )
    )


def _approval_lead(stage_key: str, hard_rejection: bool) -> str:
    if hard_rejection:
        return "经研究，该方案尚需进一步修改完善，请贵司按如下要求补充后重新报我部审查："
    return STAGE_STYLE_RULES.get(stage_key, STAGE_STYLE_RULES["规划"])["lead"]


def _sanitize_lead(lead: str, stage_key: str, hard_rejection: bool) -> str:
    text = str(lead or "").strip()
    if not text:
        return _approval_lead(stage_key, hard_rejection)
    if not hard_rejection:
        text = re.sub(r"(当前方案)?不予通过|不同意|重大安全风险|重大风险|高风险|需重点复核", "", text).strip("，。；： ")
        formal_tokens = ("原则同意", "备案", "修改完善", "注意如下事项", "开展下一步工作")
        if not any(token in text for token in formal_tokens):
            return _approval_lead(stage_key, False)
    return text.rstrip("。；：") + "："


def generate_formal_reply_content(
    package: dict[str, Any],
    data: dict[str, Any],
    dynamic_audit: dict[str, Any],
    *,
    agent: AgentService | None = None,
) -> dict[str, Any]:
    project = data.get("project", {})
    project_name = str(project.get("project_name") or _fact(package, "项目名称", "项目名称待补充")).strip()
    applicant = str(project.get("applicant") or _fact(package, "报审单位", "收函单位待补充")).strip()
    stage = str(project.get("project_stage") or _fact(package, "项目阶段") or "规划阶段").strip()
    stage_key = _stage_key(stage)
    stage_title = STAGE_TITLE.get(stage_key, f"{stage_key}方案")
    stage_rule = STAGE_STYLE_RULES.get(stage_key, STAGE_STYLE_RULES["规划"])

    audit = _compact_audit(package, dynamic_audit)
    history_sample = _historical_style_sample(package, stage_key)
    fallback = _fallback_items(package, audit, stage_key)
    generated_items: list[str] = []
    generation_error = None
    hard_rejection = _contains_hard_rejection(audit)

    system = (
        "你是南京城市轨道交通保护区正式复函的专业拟稿人员。"
        "复函正文固定为三点：第1点介绍项目情况及与地铁相对关系；第2点写本阶段的实质性意见；第3点写后续报审、备案、监测或监管要求。"
        f"当前项目阶段为“{stage_rule['name']}”，必须严格采用该阶段写作模式：{stage_rule['focus']}"
        f"第二点必须按阶段单独书写：{stage_rule['second_point_tone']}"
        "历史复函只用于学习同阶段语言风格，不得把历史项目名称、位置、距离或工程规模写入新复函。"
        "第2点不是审核意见清单，不得逐条照搬本次审核意见；应把精准审核结论转化为复函中更概括、笼统、正式的原则性要求。"
        "除第1点已客观列明的工程相对关系外，第2点应少写精确数值、少写条文号，避免堆砌技术细节；确需表达时用概括说法。"
        "语言应审慎、正式、简洁、可执行，使用“应、须、请贵司、予以配合、报我部备案/审查”等公文表达。"
        "除非审核结论明确写有“不予通过、不同意、不得实施、退回”等硬性否定，不得输出“不予通过”“重大安全风险”等内部审核式或否定式表述。"
        "不得编造工程数值、规范名称或条文号；没有依据的数值不要写。只输出JSON。"
    )
    project_description = _stage_project_description(data, stage_key)

    prompt = f"""当前项目：
{json.dumps({"project_name": project_name, "applicant": applicant, "stage": stage, "description": project_description}, ensure_ascii=False)}

本次审核结论（仅用于判断需要表达的审查方向，不得逐句照搬到复函第2点）：
{json.dumps(audit, ensure_ascii=False)}

同阶段历史复函第2点样例（重点学习该阶段第2点的句式、详略和模糊程度）：
{history_sample or "暂无可用同阶段历史复函样例。"}

请只拟写正式复函正文第2点的开头句和分项意见，严格贴合“{stage_rule['name']}”口径。
要求：
1. 第2点要比审核意见更概括，偏正式复函口吻，不写成内部审核报告。
2. 分项意见控制在2至4条，优先表达原则性要求、后续补充完善方向和程序性要求。
3. 不直接罗列“高风险、中风险、缺失依据”等审核标签，不主动写“不予通过”。
4. 规划、设计、施工阶段的措辞必须明显不同，不能混用阶段口径。
输出格式：
{{
  "lead": "第2点开头句",
  "items": ["2至4条分项意见，每条为正式复函中的概括性要求"]
}}
"""

    try:
        value = (agent or AgentService()).complete_json(system, prompt, max_tokens=1800)
        if isinstance(value, dict):
            generated_items = _normalize_items(value.get("items"))
            lead = str(value.get("lead") or "").strip()
        else:
            lead = ""
    except (OSError, RuntimeError, ValueError) as exc:
        generation_error = str(exc)
        lead = ""

    lead = _sanitize_lead(lead, stage_key, hard_rejection)
    if not generated_items:
        generated_items = fallback

    issuing_organization = os.getenv(
        "REPLY_ISSUING_ORGANIZATION",
        "南京市地下铁道工程建设指挥部",
    )
    today = date.today()
    return {
        "format_version": "formal_reply_content_v2_stage_aware",
        "document_number": os.getenv("REPLY_DOCUMENT_NUMBER", f"宁地铁保护〔{today.year}〕    号"),
        "title": f"关于{project_name}{stage_title}征求地铁意见的复函",
        "recipient": applicant,
        "introduction": f"贵司关于{project_name}{stage_title}的函件及相关资料已收悉。经研究，具体意见函复如下：",
        "project_description": project_description,
        "attention_lead": lead,
        "attention_items": generated_items,
        "closing_requirement": stage_rule["closing"],
        "closing": "特此函复。",
        "attachment": None,
        "issuing_organization": issuing_organization,
        "issue_date": f"{today.year}年{today.month}月{today.day}日",
        "generation_method": "llm_stage_aware_reply_style_transfer" if not generation_error else "stage_aware_fallback",
        "generation_error": generation_error,
        "reply_stage_key": stage_key,
        "history_style_source": package.get("historical_advice", {}).get("source_project"),
        "history_style_similarity": package.get("historical_advice", {}).get("source_similarity"),
    }
