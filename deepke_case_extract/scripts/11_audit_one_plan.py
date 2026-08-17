import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from common import ensure_dir, read_document_paragraphs, write_json


DEFAULT_PLAN_FILE = r"D:\桌面\1、基坑支护开挖专项施工方案（修改版）(1).docx"


def safe_name(text, max_len=80):
    text = re.sub(r'[<>:"/\\|?*\s]+', "_", text.strip())
    text = re.sub(r"_+", "_", text).strip("_")
    return (text or "case")[:max_len]


def run_step(command, cwd):
    print("RUN:", " ".join(str(part) for part in command), flush=True)
    subprocess.run(command, cwd=str(cwd), check=True)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_one(path, pattern):
    matches = list(Path(path).glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file matched {pattern} in {path}")
    if len(matches) > 1:
        print(f"WARNING: matched {len(matches)} files for {pattern}; using {matches[0].name}")
    return matches[0]


def read_original_paragraph(source_file, paragraph_id, cache):
    if not source_file or paragraph_id in (None, ""):
        return None
    path = Path(source_file)
    if not path.exists():
        return None
    cache_key = str(path.resolve())
    if cache_key not in cache:
        try:
            cache[cache_key] = read_document_paragraphs(path)
        except Exception as exc:
            cache[cache_key] = exc
    paragraphs = cache[cache_key]
    if isinstance(paragraphs, Exception):
        return None
    try:
        index = int(paragraph_id) - 1
    except (TypeError, ValueError):
        return None
    if 0 <= index < len(paragraphs):
        return paragraphs[index].get("text")
    return None


def field_sources(case_data):
    detail = case_data.get("field_detail", [])
    if isinstance(detail, dict):
        detail = [{"field_name": key, **value} for key, value in detail.items()]
    by_field = {}
    paragraph_cache = {}
    for item in detail:
        field = item.get("field_name")
        if not field or item.get("value") in (None, "", []):
            continue
        original_text = read_original_paragraph(
            item.get("source_file"),
            item.get("source_paragraph"),
            paragraph_cache,
        )
        by_field.setdefault(field, []).append(
            {
                "value": item.get("value"),
                "source_file": item.get("source_file"),
                "source_page": item.get("source_page"),
                "source_paragraph": item.get("source_paragraph"),
                "source_section": item.get("source_section"),
                "word_source_text": original_text,
                "source_text": item.get("source_text"),
                "confidence": item.get("confidence"),
                "extraction_method": item.get("extraction_method"),
            }
        )
    return by_field


def build_non_compliant_report(case_json_path, audit_json_path, output_dir):
    case_data = load_json(case_json_path)
    audit_data = load_json(audit_json_path)
    sources_by_field = field_sources(case_data)

    items = []
    clause_rows = (
        audit_data.get("non_compliant_results")
        or audit_data.get("clause_results")
        or audit_data.get("called_clause_results")
        or []
    )
    for clause in clause_rows:
        if clause.get("status") != "non_compliant":
            continue
        audit_evidence = (
            clause.get("audit_evidence")
            or clause.get("matched_field_values")
            or (clause.get("non_compliant_explanation") or {}).get("related_attributes")
            or {}
        )
        evidence_sources = {
            field: sources_by_field.get(field, [])
            for field in audit_evidence
        }
        items.append(
            {
                "clause": clause.get("clause"),
                "chapter": clause.get("chapter"),
                "section": clause.get("section"),
                "title": clause.get("title"),
                "status": clause.get("status"),
                "result": clause.get("result"),
                "audit_basis": clause.get("audit_basis") or (clause.get("source_truth_rule") or {}).get("source_rule_basis"),
                "audit_evidence": audit_evidence,
                "evidence_sources": evidence_sources,
                "basis": clause.get("basis") or clause.get("audit_basis") or (clause.get("source_truth_rule") or {}).get("source_rule_basis"),
                "module_file": clause.get("module_file"),
                "function": clause.get("function"),
                "judgement_source": clause.get("judgement_source"),
                "match_reason": clause.get("match_reason", []),
                "matched_fields": clause.get("matched_fields", []),
            }
        )

    report = {
        "format_version": "non_compliant_report_v1",
        "doc_id": audit_data.get("doc_id"),
        "source_case_json": str(case_json_path),
        "source_audit_json": str(audit_json_path),
        "summary": audit_data.get("summary", {}),
        "non_compliant_count": len(items),
        "non_compliant_items": items,
    }

    json_path = Path(output_dir) / "non_compliant_report.json"
    md_path = Path(output_dir) / "non_compliant_report.md"
    write_json(json_path, report)
    write_markdown_report(md_path, report)
    return json_path, md_path


def write_markdown_report(path, report):
    lines = [
        f"# 不符合操作规程条文清单",
        "",
        f"- 案例：{report.get('doc_id')}",
        f"- 不符合条文数：{report.get('non_compliant_count')}",
        f"- 审核汇总：{json.dumps(report.get('summary', {}), ensure_ascii=False)}",
        "",
    ]
    if not report.get("non_compliant_items"):
        lines.append("未发现自动判定的不符合条文。")
    for idx, item in enumerate(report.get("non_compliant_items", []), start=1):
        lines.extend(
            [
                f"## {idx}. 条文 {item.get('clause')}",
                "",
                f"- 状态：`{item.get('status')}`",
                f"- 判断：{item.get('result')}",
                f"- 规则文件：`{item.get('module_file')}`",
                f"- 审核函数：`{item.get('function')}`",
                f"- 判断来源：`{item.get('judgement_source')}`",
                f"- 自动判断依据：`{item.get('audit_basis')}`",
                "",
                "### 使用的案例属性",
                "",
            ]
        )
        evidence = item.get("audit_evidence") or {}
        if evidence:
            for field, value in evidence.items():
                lines.append(f"- `{field}`：{value}")
        else:
            lines.append("- 无")
        lines.extend(["", "### 原文来源", ""])
        sources = item.get("evidence_sources") or {}
        any_source = False
        for field, field_sources_ in sources.items():
            for source in field_sources_[:3]:
                any_source = True
                lines.append(
                    f"- `{field}`：页码 {source.get('source_page')}，段落 {source.get('source_paragraph')}，"
                    f"置信度 {source.get('confidence')}"
                )
                if source.get("word_source_text"):
                    lines.append(f"  - Word原文：{source.get('word_source_text')}")
                elif source.get("source_text"):
                    lines.append(f"  - 原文：{source.get('source_text')}")
        if not any_source:
            lines.append("- 暂无可追溯原文来源。")
        lines.extend(["", "### 规程依据", "", str(item.get("basis") or ""), ""])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Audit one safety assessment plan and output automatic rule-check results."
    )
    parser.add_argument(
        "plan_file",
        nargs="?",
        default=DEFAULT_PLAN_FILE,
        help="方案文件路径，支持 docx/pdf/txt；不填时使用脚本顶部的 DEFAULT_PLAN_FILE。",
    )
    parser.add_argument(
        "--schema-doc",
        default="../案例属性描述(1).docx",
        help="案例属性描述 docx 路径。",
    )
    parser.add_argument(
        "--chapter-dir",
        default="../chapter_1_functions",
        help="规程函数文件夹路径。",
    )
    parser.add_argument(
        "-o",
        "--output-root",
        default="outputs/one_click_audit",
        help="一键审核输出根目录。",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="本次运行的目录名称；不填则自动生成。",
    )
    parser.add_argument(
        "--opinion-db",
        default="data/opinion_database.json",
        help="人工审核意见库 JSON 路径；不存在时会从 --opinion-source 自动构建。",
    )
    parser.add_argument(
        "--opinion-source",
        default="../安全评估报告",
        help="用于构建人工审核意见库的 Word 文件或文件夹，默认使用安全评估报告文件夹。",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    plan_file = Path(args.plan_file).resolve()
    if not plan_file.exists():
        raise FileNotFoundError(plan_file)

    schema_doc = Path(args.schema_doc)
    if not schema_doc.is_absolute():
        schema_doc = (project_root / schema_doc).resolve()
    if not schema_doc.exists():
        raise FileNotFoundError(schema_doc)

    chapter_dir = Path(args.chapter_dir)
    if not chapter_dir.is_absolute():
        chapter_dir = (project_root / chapter_dir).resolve()
    if not chapter_dir.exists():
        raise FileNotFoundError(chapter_dir)

    opinion_db = Path(args.opinion_db)
    if not opinion_db.is_absolute():
        opinion_db = (project_root / opinion_db).resolve()
    opinion_source = Path(args.opinion_source)
    if not opinion_source.is_absolute():
        opinion_source = (project_root / opinion_source).resolve()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = args.run_id or f"{safe_name(plan_file.stem)}_{timestamp}"
    run_dir = (project_root / args.output_root / run_id).resolve()

    raw_docs = run_dir / "data" / "raw_docs"
    schema_dir = run_dir / "data" / "schema"
    texts_dir = run_dir / "data" / "texts"
    chunks_dir = run_dir / "data" / "chunks"
    deepke_inputs = run_dir / "outputs" / "deepke_inputs"
    oneke_inputs = run_dir / "outputs" / "oneke_inputs"
    raw_extract = run_dir / "outputs" / "raw_extract"
    normalized = run_dir / "outputs" / "normalized"
    final_json = run_dir / "outputs" / "final_json"
    rule_json = run_dir / "outputs" / "rule_json"
    auto_audit = run_dir / "outputs" / "auto_audit_results"
    matched_audit = run_dir / "outputs" / "matched_rule_audit"
    reports = run_dir / "reports"

    for folder in [raw_docs, schema_dir, texts_dir, chunks_dir, reports]:
        ensure_dir(folder)
    copied_plan = raw_docs / plan_file.name
    shutil.copy2(plan_file, copied_plan)

    schema_json = schema_dir / "case_schema.json"

    py = sys.executable
    print(f"Run directory: {run_dir}", flush=True)

    run_step([py, "scripts/00_build_schema.py", str(schema_doc), "-o", str(schema_json)], project_root)
    run_step([py, "scripts/01_doc_to_text.py", str(raw_docs), "-o", str(texts_dir)], project_root)
    run_step([py, "scripts/02_text_chunk.py", str(texts_dir), "-o", str(chunks_dir)], project_root)
    run_step([py, "scripts/03_build_deepke_inputs.py", str(chunks_dir), str(schema_json), "-o", str(deepke_inputs)], project_root)
    run_step([py, "scripts/07_prepare_oneke_input.py", str(deepke_inputs), "-o", str(oneke_inputs)], project_root)
    run_step([py, "scripts/04_rule_extract.py", str(chunks_dir), "-o", str(raw_extract)], project_root)
    run_step([py, "scripts/05_normalize.py", str(raw_extract), "-o", str(normalized)], project_root)
    run_step([py, "scripts/06_merge_result.py", str(normalized), "-o", str(final_json), "--schema", str(schema_json)], project_root)
    run_step([py, "scripts/08_build_rule_json.py", str(final_json), "-o", str(rule_json)], project_root)
    run_step([py, "scripts/10_auto_audit_from_full_json.py", str(final_json), "--chapter-dir", str(chapter_dir), "-o", str(auto_audit)], project_root)
    run_step([py, "scripts/13_build_rule_function_field_mapping.py", "--chapter-dir", str(chapter_dir)], project_root)
    if not opinion_db.exists():
        run_step([py, "scripts/14_build_opinion_database.py", str(opinion_source), "-o", str(opinion_db)], project_root)
    run_step(
        [
            py,
            "scripts/12_match_rule_audit.py",
            str(final_json),
            "--chapter-dir",
            str(chapter_dir),
            "-o",
            str(matched_audit),
            "--no-skipped",
        ],
        project_root,
    )

    case_json_path = find_one(final_json, "*.case.json")
    audit_json_path = find_one(auto_audit, "*.auto_audit.json")
    matched_audit_json_path = find_one(matched_audit, "*.matched_audit.json")
    non_json, non_md = build_non_compliant_report(case_json_path, matched_audit_json_path, reports)
    run_step(
        [
            py,
            "scripts/15_generate_review_opinion.py",
            str(case_json_path),
            str(matched_audit_json_path),
            "--opinion-db",
            str(opinion_db),
            "-o",
            str(reports / "generated_review_opinion"),
        ],
        project_root,
    )

    audit = load_json(audit_json_path)
    matched_audit_data = load_json(matched_audit_json_path)
    summary = {
        "run_dir": str(run_dir),
        "input_plan": str(plan_file),
        "case_json": str(case_json_path),
        "rule_json_dir": str(rule_json),
        "auto_audit_json": str(audit_json_path),
        "matched_rule_audit_json": str(matched_audit_json_path),
        "non_compliant_report_json": str(non_json),
        "non_compliant_report_md": str(non_md),
        "generated_review_opinion_json": str(reports / "generated_review_opinion" / "generated_review_opinion.json"),
        "generated_review_opinion_md": str(reports / "generated_review_opinion" / "generated_review_opinion.md"),
        "opinion_database": str(opinion_db),
        "audit_summary": audit.get("summary", {}),
        "matched_rule_audit_summary": matched_audit_data.get("summary", {}),
    }
    write_json(run_dir / "audit_summary.json", summary)

    print("\nDONE")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
