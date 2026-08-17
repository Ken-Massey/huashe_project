import argparse
import json
import re
from pathlib import Path

from common import ensure_dir, write_json


CLAUSE_TO_TOPIC = {
    "3.1.4": "控制保护区",
    "3.1.5": "特别保护区",
    "3.4.3": "结构变形控制",
    "4.1.1": "现状调查",
    "4.1.2": "安全评估监测应急",
    "5.1.2": "方案报审",
    "5.2.7": "基坑施工控制",
    "5.2.10": "基坑地下水控制",
    "5.2.11": "基坑底板与暴露控制",
    "5.5.1": "降水影响预估",
    "5.5.2": "降水结构安全验算",
    "5.5.6": "承压水降压方案",
    "7.1.1": "轨道结构安全监测",
    "7.1.2": "监测点与初始值",
    "7.1.3": "监测方法",
    "7.2.6": "地下水位监测",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def non_empty(value):
    return value not in (None, "", [], {})


def compact_text(text, max_len=180):
    text = re.sub(r"\s+", "", str(text or ""))
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def values_from_case(case_data):
    values = {}
    for key, value in (case_data.get("attributes") or {}).items():
        if non_empty(value):
            values[key] = value
    for key, value in (case_data.get("measured_values") or {}).items():
        if non_empty(value):
            values.setdefault(key, value)
    return values


def non_compliant_items(audit_data):
    rows = (
        audit_data.get("non_compliant_results")
        or [
            item
            for item in audit_data.get("called_clause_results", [])
            if item.get("status") == "non_compliant"
        ]
    )
    return rows


def collect_audit_keywords(items):
    words = []
    for item in items:
        parts = [
            item.get("clause"),
            item.get("title"),
            item.get("result"),
            item.get("audit_basis"),
            json.dumps(item.get("audit_evidence") or {}, ensure_ascii=False),
        ]
        text = "\n".join(str(part or "") for part in parts)
        for word in [
            "特别保护区",
            "控制保护区",
            "监测",
            "安全监测",
            "地下水位",
            "承压水",
            "降水",
            "结构安全",
            "变形",
            "沉降",
            "现状调查",
            "报审",
            "备案",
            "减震",
            "隔振",
            "振动",
            "围护",
            "回填",
            "停止降水",
        ]:
            if word in text:
                words.append(word)
    return sorted(set(words))


def score_record(record, item, keywords):
    score = 0
    clause = str(item.get("clause") or "")
    text = "\n".join(
        [
            str(item.get("result") or ""),
            str(item.get("audit_basis") or ""),
            json.dumps(item.get("audit_evidence") or {}, ensure_ascii=False),
        ]
    )
    if clause in record.get("related_clauses", []):
        score += 6
    if CLAUSE_TO_TOPIC.get(clause) in record.get("topics", []):
        score += 4
    for word in record.get("keywords", []):
        if word in text:
            score += 2
    for word in keywords:
        if word in record.get("opinion_text", ""):
            score += 1
    return score


def retrieve_examples(opinion_db, item, keywords, limit=2):
    scored = []
    for record in opinion_db.get("records", []):
        score = score_record(record, item, keywords)
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("source_doc", ""), pair[1].get("opinion_number", 0)))
    return [record for _, record in scored[:limit]]


def has_clause(items, clause):
    return any(str(item.get("clause")) == clause for item in items)


def item_by_clause(items, clause):
    for item in items:
        if str(item.get("clause")) == clause:
            return item
    return None


def build_opinion_sentence(item, values, examples):
    clause = str(item.get("clause") or "")
    result = str(item.get("result") or "")
    example_text = examples[0]["opinion_text"] if examples else ""

    if clause == "3.1.5":
        return "项目位于城市轨道交通控制保护区内时，应明确特别保护区范围及控制要求；特别保护区内不得实施影响轨道交通结构安全的工程活动，相关设计和施工边界应复核确认。"
    if clause == "3.4.3":
        return "计算结果显示外部作业引起的轨道交通结构附加变形存在不满足安全控制指标的情况，应优化建筑、基坑或施工方案，重新开展结构安全影响分析，直至满足结构安全控制要求。"
    if clause == "4.1.1":
        return "施工前应补充开展轨道交通既有结构现状调查，调查内容宜包括结构变形、沉降、裂缝、渗漏水、既有监测资料及周边环境条件，并将调查结论作为保护方案和施工控制措施的依据。"
    if clause == "5.5.1":
        return "基坑降水方案应补充降水施工影响预估，重点分析地下水位变化、地层沉降及其对既有轨道交通结构的影响，并提出防止流砂、管涌、坑底突涌和较大沉降的控制措施。"
    if clause == "5.5.2":
        return "当降水作业可能引起轨道交通结构周边地下水位变化时，应补充既有结构受力安全验算，并根据验算结果完善降水控制和保护措施。"
    if clause == "7.1.1":
        return "外部作业实施期间应对受影响的轨道交通结构开展安全监测，监测对象不应仅限于周边市政设施或建筑物，监测工作不得影响轨道交通正常运营。"
    if clause == "7.1.2":
        return "应在外部作业实施前完成轨道交通结构监测点布设和初始值采集，施工过程中开展动态监测，并及时反馈监测成果。"
    if clause == "7.2.6":
        return "外部降水作业期间，应对既有轨道交通结构附近地下水位进行监测；涉及抽降承压水时，还应同步监测承压水位，并根据监测结果及时调整降水措施。"

    if example_text:
        return example_text
    return f"针对条文{clause}自动审核发现的问题，应结合规程要求进行补充说明或方案调整：{result}"


def group_items_for_opinions(items):
    priority = ["3.1.5", "4.1.1", "5.5.1", "5.5.2", "7.1.1", "7.1.2", "7.2.6", "3.4.3"]
    selected = []
    used = set()
    for clause in priority:
        item = item_by_clause(items, clause)
        if item:
            selected.append(item)
            used.add(clause)
    for item in items:
        clause = str(item.get("clause") or "")
        if clause not in used:
            selected.append(item)
    return selected


def generate_opinions(case_data, audit_data, opinion_db):
    values = values_from_case(case_data)
    items = non_compliant_items(audit_data)
    keywords = collect_audit_keywords(items)
    generated = []

    for idx, item in enumerate(group_items_for_opinions(items), start=1):
        examples = retrieve_examples(opinion_db, item, keywords)
        sentence = build_opinion_sentence(item, values, examples)
        generated.append(
            {
                "number": idx,
                "opinion": sentence,
                "source_clause": item.get("clause"),
                "source_function": item.get("function"),
                "source_result": item.get("result"),
                "matched_human_examples": [
                    {
                        "source_doc": record.get("source_doc"),
                        "section": record.get("section"),
                        "opinion_number": record.get("opinion_number"),
                        "opinion_text": record.get("opinion_text"),
                    }
                    for record in examples
                ],
            }
        )

    if not generated:
        generated.append(
            {
                "number": 1,
                "opinion": "自动审核未发现明确不符合条文，建议按既有报告结论继续落实设计、施工、监测和报审要求；若后续实施方案调整，应重新开展审核。",
                "source_clause": None,
                "source_function": None,
                "source_result": None,
                "matched_human_examples": [],
            }
        )

    return {
        "format_version": "generated_review_opinion_v1",
        "doc_id": case_data.get("doc_id") or audit_data.get("doc_id"),
        "source_case_json": case_data.get("source_file"),
        "audit_summary": audit_data.get("summary", {}),
        "opinion_database_record_count": opinion_db.get("record_count", 0),
        "generated_opinions": generated,
    }


def write_markdown(path, result):
    lines = [
        "# 自动生成审核意见",
        "",
        f"- 案例：{result.get('doc_id')}",
        f"- 审核汇总：{json.dumps(result.get('audit_summary', {}), ensure_ascii=False)}",
        f"- 使用人工意见库记录数：{result.get('opinion_database_record_count')}",
        "",
        "## 类6.2审核意见",
        "",
    ]
    for item in result.get("generated_opinions", []):
        lines.append(f"{item['number']}、{item['opinion']}")
        lines.append("")
    lines.append("## 生成依据")
    lines.append("")
    for item in result.get("generated_opinions", []):
        lines.append(f"- 意见{item['number']}：来源条文 `{item.get('source_clause')}`，审核函数 `{item.get('source_function')}`，自动判断：{compact_text(item.get('source_result'))}")
        for example in item.get("matched_human_examples", []):
            lines.append(f"  - 参考人工意见：{example.get('source_doc')} / {example.get('section')} / 第{example.get('opinion_number')}条：{example.get('opinion_text')}")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate section-6.2-like review opinions from audit results and a human opinion database.")
    parser.add_argument("case_json")
    parser.add_argument("audit_json")
    parser.add_argument("--opinion-db", default="data/opinion_database.json")
    parser.add_argument("-o", "--output", default="reports/generated_review_opinion")
    args = parser.parse_args()

    case_data = load_json(args.case_json)
    audit_data = load_json(args.audit_json)
    opinion_db = load_json(args.opinion_db) if Path(args.opinion_db).exists() else {"records": [], "record_count": 0}

    result = generate_opinions(case_data, audit_data, opinion_db)
    output = Path(args.output)
    if output.suffix:
        json_path = output.with_suffix(".json")
        md_path = output.with_suffix(".md")
    else:
        ensure_dir(output)
        json_path = output / "generated_review_opinion.json"
        md_path = output / "generated_review_opinion.md"
    write_json(json_path, result)
    write_markdown(md_path, result)
    print(f"generated review opinion: {md_path}")


if __name__ == "__main__":
    main()
