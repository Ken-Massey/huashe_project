"""Render review packages as readable Markdown documents."""

from __future__ import annotations

import re
from typing import Any


STATUS_LABELS = {
    "blocked_by_missing_data": "关键资料待补充",
    "requires_special_study": "需专题专项论证",
    "ready_for_human_review": "计算完成，待人工复核",
}


def _without_list_marker(value: object) -> str:
    return re.sub(r"^\s*(?:[（(]\d+[）)]|\d+[.、])\s*", "", str(value)).strip()


def render_review_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 第一阶段辅助审核意见",
        "",
        f"- 案例编号：`{package['case_id']}`",
        f"- 总体状态：**{STATUS_LABELS.get(package['overall_status'], package['overall_status'])}**",
        f"- 正式出具：**不允许直接出具**",
        f"- 说明：{package['formal_issuance_note']}",
        "",
        "## 项目信息",
        "",
    ]
    lines.extend(f"- {fact['label']}：{fact['value']}" for fact in package["project_facts"])
    lines.extend(["", "## 规程审核判断", ""])
    for index, opinion in enumerate(package["audit_opinions"], 1):
        clauses = "、".join(opinion["regulation_clauses"])
        lines.extend([
            f"### {index}. {opinion['topic']}",
            "",
            f"- 结论：**{opinion['result']}**",
            f"- 审核意见：{opinion['conclusion']}",
            f"- 依据条文：{clauses}",
            f"- 计算函数：`{opinion['function']}`",
        ])
        if opinion["calculation_steps"]:
            lines.append("- 计算过程：" + "；".join(opinion["calculation_steps"]))
        lines.append("")

    lines.extend(["## 待补充资料", ""])
    if package["missing_required_inputs"]:
        lines.extend(f"- {item['label']}（`{item['field']}`）" for item in package["missing_required_inputs"])
    else:
        lines.append("- 无确定性计算所需的缺失字段。")

    history = package["historical_advice"]
    lines.extend(["", "## 历史回函注意事项", ""])
    if history["attention_items"]:
        lines.extend([
            f"- 来源项目：{history['source_project']}",
            f"- 相似度：{history['source_similarity']}",
            f"- 来源文件：`{history['source_reply_file']}`",
            "- 使用方式：以下内容为历史回函注意事项原文，未改写。",
            "",
        ])
        lines.extend(history["attention_items"])
    else:
        lines.append("未找到达到阈值且可精确截取注意事项的历史回函，需人工选择。")
    return "\n".join(lines).rstrip() + "\n"


def render_reply_draft_markdown(package: dict[str, Any]) -> str:
    facts = {fact["label"]: fact["value"] for fact in package["project_facts"]}
    name = facts.get("项目名称", "项目名称待补充")
    stage = facts.get("项目阶段", "当前阶段")
    applicant = facts.get("报审单位", "收函单位待补充")
    reply = package.get("formal_reply") or {}
    items = reply.get("attention_items") or package.get("historical_advice", {}).get("attention_items") or []
    lines = [
        f"# {reply.get('title') or f'关于{name}{stage}方案征求地铁意见的复函'}",
        "",
        f"{reply.get('recipient') or applicant}：",
        "",
        reply.get("introduction") or f"贵司关于{name}{stage}方案的函件及相关资料已收悉。经研究，具体意见函复如下：",
        "",
        f"1. {reply.get('project_description') or '项目建设内容及其与既有地铁结构的空间关系详见报审资料。'}",
        "",
        f"2. {reply.get('attention_lead') or '为确保地铁结构及运营安全，请贵司在后续工作中注意如下事项：'}",
    ]
    lines.extend(f"（{index}）{_without_list_marker(item)}" for index, item in enumerate(items, 1))
    lines.extend([
        "",
        f"3. {reply.get('closing_requirement') or ''}",
        "",
        reply.get("closing") or "特此函复。",
    ])
    attachment = str(reply.get("attachment") or "").strip()
    if attachment:
        lines.extend(["", f"附件：{attachment}"])
    lines.extend([
        "",
        reply.get("issuing_organization") or "南京市地下铁道工程建设指挥部",
        "",
        reply.get("issue_date") or "",
    ])
    return "\n".join(lines).rstrip() + "\n"
