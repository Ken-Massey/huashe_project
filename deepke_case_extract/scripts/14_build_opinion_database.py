import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

from common import ensure_dir, read_document_paragraphs, write_json


def safe_read_paragraphs(path):
    path = Path(path)
    if path.suffix.lower() != ".docx":
        return read_document_paragraphs(path)
    temp_path = None
    try:
        return read_document_paragraphs(path)
    except PermissionError:
        temp_dir = Path(tempfile.gettempdir())
        temp_path = temp_dir / f"opinion_db_{path.stem}_{id(path)}.docx"
        shutil.copy2(path, temp_path)
        return read_document_paragraphs(temp_path)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def is_section_title(text, section):
    return bool(re.match(rf"^{re.escape(section)}(?:\s|$)", text.strip()))


def is_opinion_section_title(text):
    text = text.strip()
    if not text:
        return False
    title_patterns = [
        r"^\d+(?:\.\d+)*\.?\s*(?:对.+的)?(?:评价与建议|结论与建议|分析结论和建议|实施的建议|建议)$",
        r"^\d+(?:\.\d+)*\.?\s*.*(?:安全控制建议|控制建议|实施建议)$",
        r"^\d+(?:\.\d+)*\.?\s*建议$",
        r"^\d+[、.．]\s*.*(?:评价与建议|结论与建议|建议)$",
        r"^第?[一二三四五六七八九十]+[章节]?\s*(?:评价与建议|结论与建议|实施的建议|建议)$",
    ]
    return any(re.match(pattern, text) for pattern in title_patterns)


def is_next_major_section(text, current_title):
    text = text.strip()
    if not text:
        return False
    if text == current_title:
        return False
    if is_opinion_section_title(text):
        return True
    return bool(re.match(r"^\d+(?:\.\d+)*\.?\s+\S+", text) and not re.match(r"^\d+[）、.．、]", text))


def extract_section(paragraphs, section="6.2"):
    start = None
    for idx, item in enumerate(paragraphs):
        text = item.get("text", "").strip()
        if is_section_title(text, section):
            start = idx
    if start is None:
        return None, []

    title = paragraphs[start]["text"].strip()
    collected = []
    for item in paragraphs[start + 1 :]:
        text = item.get("text", "").strip()
        if not text:
            continue
        if re.match(r"^\d+(?:\.\d+)?\s+", text) or re.match(r"^[一二三四五六七八九十]+[、.]", text):
            break
        collected.append(text)
    return title, collected


def extract_opinion_sections(paragraphs, section="auto"):
    if section != "auto":
        title, body = extract_section(paragraphs, section=section)
        return [{"section": section, "title": title, "paragraphs": body}] if body else []

    starts = []
    for idx, item in enumerate(paragraphs):
        text = item.get("text", "").strip()
        if is_opinion_section_title(text):
            starts.append(idx)

    sections = []
    for pos, start in enumerate(starts):
        title = paragraphs[start]["text"].strip()
        end = starts[pos + 1] if pos + 1 < len(starts) else len(paragraphs)
        collected = []
        for item in paragraphs[start + 1 : end]:
            text = item.get("text", "").strip()
            if not text:
                continue
            if collected and is_next_major_section(text, title):
                break
            collected.append(text)
        if "结论与建议" in title and any(re.match(r"^\d+(?:\.\d+)+\s+", text) for text in collected[:5]):
            continue
        if split_numbered_opinions(collected):
            section_id = re.match(r"^(\d+(?:\.\d+)*)", title)
            sections.append(
                {
                    "section": section_id.group(1) if section_id else "建议",
                    "title": title,
                    "paragraphs": collected,
                }
            )
    return sections


def split_numbered_opinions(paragraphs):
    opinions = []
    current = None
    for text in paragraphs:
        text = text.strip()
        main_match = re.match(r"^([0-9]+)[、.．]\s*(.+)", text)
        sub_match = re.match(r"^[（(]([0-9]+)[)）、]\s*(.+)", text)
        if main_match:
            if current:
                opinions.append(current)
            current = {"number": int(main_match.group(1)), "text": main_match.group(2).strip()}
        elif sub_match and current:
            current["text"] += f"（{sub_match.group(1)}）{sub_match.group(2).strip()}"
        elif sub_match:
            current = {"number": int(sub_match.group(1)), "text": sub_match.group(2).strip()}
        elif current:
            current["text"] += text
    if current:
        opinions.append(current)
    return opinions


def classify_opinion(text):
    topics = []
    clauses = []
    fields = []
    keyword_map = [
        ("特别保护区", ["特别保护区", "保护区", "用地红线"], ["3.1.5"], ["is_in_special_protection_zone", "special_zone_intrusion_length"]),
        ("管线与周边设施", ["管线", "管综", "市政设施"], ["4.1.1"], ["main_external_work_type", "monitoring_object"]),
        ("围护结构和基础质量", ["围护结构", "建筑基础", "设计方案", "质量控制", "设计强度"], ["5.1.2", "5.2.7"], ["support_method", "foundation_type", "measure_for_support"]),
        ("回填与降水控制", ["回填", "停止降水", "降水"], ["5.5.1", "7.2.6"], ["measure_for_dewatering", "dewatering_type", "groundwater_monitoring_required"]),
        ("减震隔振", ["振动", "减震", "隔振", "环境振动"], ["3.4.3"], ["vibration_compliance", "measure_for_vibration"]),
        ("报审备案", ["上报", "审核备案", "重新报审", "施工图"], ["5.1.2"], ["approval_required", "review_stage"]),
        ("安全监测", ["安全监测", "监测", "变形监测"], ["7.1.1", "7.1.2", "7.1.3"], ["monitoring_required", "monitoring_items", "monitoring_requirements"]),
        ("现状调查", ["现状调查", "工前调查", "既有结构"], ["4.1.1"], ["pre_construction_investigation_done", "existing_condition_summary"]),
    ]
    for topic, words, related_clauses, related_fields in keyword_map:
        if any(word in text for word in words):
            topics.append(topic)
            clauses.extend(related_clauses)
            fields.extend(related_fields)
    return {
        "topics": sorted(set(topics)),
        "related_clauses": sorted(set(clauses)),
        "related_fields": sorted(set(fields)),
        "keywords": sorted({word for _, words, _, _ in keyword_map for word in words if word in text}),
    }


def build_database(input_path, output_path, section="6.2"):
    input_path = Path(input_path)
    files = [input_path] if input_path.is_file() else sorted(input_path.glob("*.docx")) + sorted(input_path.glob("*.pdf"))
    files = [path for path in files if not path.name.startswith("~$")]
    records = []
    for path in files:
        try:
            paragraphs = safe_read_paragraphs(path)
        except Exception as exc:
            print(f"skip {path.name}: {exc}")
            continue
        for found_section in extract_opinion_sections(paragraphs, section=section):
            for item in split_numbered_opinions(found_section["paragraphs"]):
                meta = classify_opinion(item["text"])
                records.append(
                    {
                        "source_file": str(path),
                        "source_doc": path.stem,
                        "section": found_section["section"],
                        "section_title": found_section["title"],
                        "opinion_number": item["number"],
                        "opinion_text": item["text"],
                        **meta,
                    }
                )

    database = {
        "format_version": "human_review_opinion_db_v1",
        "section": section,
        "record_count": len(records),
        "records": records,
    }
    write_json(output_path, database)
    print(f"opinion database: {output_path}, records={len(records)}")
    return database


def main():
    parser = argparse.ArgumentParser(description="Build a reusable database from manually written review opinions such as section 6.2.")
    parser.add_argument("input", help="Word file or folder containing Word files.")
    parser.add_argument("-o", "--output", default="data/opinion_database.json")
    parser.add_argument("--section", default="auto", help="默认 auto：自动识别 6.2、5.2、7.建议等人工意见章节。")
    args = parser.parse_args()
    ensure_dir(Path(args.output).parent)
    build_database(args.input, args.output, section=args.section)


if __name__ == "__main__":
    main()
