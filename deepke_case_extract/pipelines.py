"""Callable adapters for the two stage-two desktop workflows.

The existing numbered scripts are kept unchanged for PyCharm users.  These
adapters provide stable Python function entry points for the HTTP service and
run each heavy workflow in an isolated process.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable


Progress = Callable[[str], None]
PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
ADVICE_DATABASE_LOCK = threading.Lock()


def _run(command: list[str], *, cwd: Path, log_file: Path, progress: Progress, label: str) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    progress(label)
    with log_file.open("a", encoding="utf-8") as log:
        log.write("COMMAND: " + " ".join(command) + "\n")
        log.flush()
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"{label}失败，退出码 {completed.returncode}；日志：{log_file}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_extract_plan_text(
    plan_file: str | Path,
    *,
    run_id: str,
    output_root: str | Path,
    python_executable: str | Path | None = None,
    progress: Progress | None = None,
    preparsed_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Extract document text for pure RAG without executing rule functions."""
    notify = progress or (lambda message: None)
    plan = Path(plan_file).resolve()
    if not plan.exists():
        raise FileNotFoundError(plan)
    run_dir = Path(output_root).resolve() / run_id
    raw_docs = run_dir / "data" / "raw_docs"
    texts_dir = run_dir / "data" / "texts"
    raw_docs.mkdir(parents=True, exist_ok=True)
    texts_dir.mkdir(parents=True, exist_ok=True)
    copied = raw_docs / plan.name
    shutil.copy2(plan, copied)
    log_file = run_dir / "service_rag_extraction.log"
    if preparsed_rows is not None:
        notify("正在整理MinerU案例识别结果")
        rows = []
        for index, item in enumerate(preparsed_rows, start=1):
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            rows.append({
                "doc_id": plan.stem,
                "source_file": str(plan),
                "source_page": item.get("page"),
                "paragraph_id": index,
                "content_type": item.get("content_type") or "paragraph",
                "text": text,
            })
        paragraph_file = texts_dir / f"{plan.stem}.paragraphs.jsonl"
        with paragraph_file.open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        (texts_dir / f"{plan.stem}.txt").write_text(
            "\n".join(row["text"] for row in rows), encoding="utf-8"
        )
        log_file.write_text(
            f"MinerU preparsed rows: {len(rows)}\n", encoding="utf-8"
        )
    else:
        python = str(Path(python_executable).resolve()) if python_executable else sys.executable
        _run(
            [python, str(PROJECT_ROOT / "scripts" / "01_doc_to_text.py"), str(raw_docs), "-o", str(texts_dir)],
            cwd=PROJECT_ROOT,
            log_file=log_file,
            progress=notify,
            label="正在解析案例全文、页码、段落和表格",
        )
    paragraph_files = sorted(texts_dir.glob("*.paragraphs.jsonl"), key=lambda item: item.stat().st_size, reverse=True)
    if not paragraph_files:
        raise FileNotFoundError(f"案例解析完成但未生成段落索引：{texts_dir}")
    notify("案例全文解析完成")
    return {
        "run_dir": str(run_dir),
        "input_plan": str(plan),
        "paragraph_jsonl": str(paragraph_files[0]),
        "service_log": str(log_file),
    }


def run_extract_case_attributes(
    plan_file: str | Path,
    *,
    run_id: str,
    output_root: str | Path,
    schema_doc: str | Path | None = None,
    python_executable: str | Path | None = None,
    progress: Progress | None = None,
) -> dict[str, Any]:
    """Extract schema-aligned case attributes without executing audit functions."""
    notify = progress or (lambda message: None)
    plan = Path(plan_file).resolve()
    if not plan.exists():
        raise FileNotFoundError(plan)
    run_dir = Path(output_root).resolve() / run_id
    raw_docs = run_dir / "data" / "raw_docs"
    schema_dir = run_dir / "data" / "schema"
    texts_dir = run_dir / "data" / "texts"
    chunks_dir = run_dir / "data" / "chunks"
    deepke_inputs = run_dir / "outputs" / "deepke_inputs"
    oneke_inputs = run_dir / "outputs" / "oneke_inputs"
    raw_extract = run_dir / "outputs" / "raw_extract"
    normalized = run_dir / "outputs" / "normalized"
    final_json = run_dir / "outputs" / "final_json"
    for folder in (raw_docs, schema_dir, texts_dir, chunks_dir):
        folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan, raw_docs / plan.name)
    schema = Path(schema_doc or WORKSPACE_ROOT / "案例属性描述(1).docx").resolve()
    schema_json = schema_dir / "case_schema.json"
    python = str(Path(python_executable).resolve()) if python_executable else sys.executable
    log_file = run_dir / "service_attribute_extraction.log"
    steps = [
        ("正在读取案例属性模板", ["00_build_schema.py", str(schema), "-o", str(schema_json)]),
        ("正在解析案例全文、页码、段落和表格", ["01_doc_to_text.py", str(raw_docs), "-o", str(texts_dir)]),
        ("正在按章节切分案例全文", ["02_text_chunk.py", str(texts_dir), "-o", str(chunks_dir)]),
        ("正在准备属性抽取输入", ["03_build_deepke_inputs.py", str(chunks_dir), str(schema_json), "-o", str(deepke_inputs)]),
        ("正在准备语义抽取数据", ["07_prepare_oneke_input.py", str(deepke_inputs), "-o", str(oneke_inputs)]),
        ("正在从案例原文提取属性", ["04_rule_extract.py", str(chunks_dir), "-o", str(raw_extract)]),
        ("正在标准化案例属性", ["05_normalize.py", str(raw_extract), "-o", str(normalized)]),
        ("正在合并案例属性", ["06_merge_result.py", str(normalized), "-o", str(final_json), "--schema", str(schema_json)]),
    ]
    for label, arguments in steps:
        _run(
            [python, str(PROJECT_ROOT / "scripts" / arguments[0]), *arguments[1:]],
            cwd=PROJECT_ROOT,
            log_file=log_file,
            progress=notify,
            label=label,
        )
    case_files = sorted(final_json.glob("*.case.json"), key=lambda item: item.stat().st_size, reverse=True)
    paragraph_files = sorted(texts_dir.glob("*.paragraphs.jsonl"), key=lambda item: item.stat().st_size, reverse=True)
    if not case_files or not paragraph_files:
        raise FileNotFoundError(f"属性提取完成但结果不完整：{run_dir}")
    notify("案例属性与全文证据提取完成")
    return {
        "run_dir": str(run_dir),
        "input_plan": str(plan),
        "case_json": str(case_files[0]),
        "paragraph_jsonl": str(paragraph_files[0]),
        "service_log": str(log_file),
    }


def run_audit_one_plan(
    plan_file: str | Path,
    *,
    run_id: str,
    output_root: str | Path,
    schema_doc: str | Path | None = None,
    chapter_dir: str | Path | None = None,
    opinion_database: str | Path | None = None,
    opinion_source: str | Path | None = None,
    python_executable: str | Path | None = None,
    progress: Progress | None = None,
) -> dict[str, Any]:
    """Run extraction, rule audit and generated-opinion workflow for one plan."""
    notify = progress or (lambda message: None)
    plan = Path(plan_file).resolve()
    if not plan.exists():
        raise FileNotFoundError(plan)

    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=True)
    schema = Path(schema_doc or WORKSPACE_ROOT / "案例属性描述(1).docx").resolve()
    chapters = Path(chapter_dir or WORKSPACE_ROOT / "chapter_1_functions").resolve()
    opinion_db = Path(opinion_database or PROJECT_ROOT / "data" / "opinion_database.json").resolve()
    opinions = Path(opinion_source or WORKSPACE_ROOT / "安全评估报告").resolve()
    python = str(Path(python_executable).resolve()) if python_executable else sys.executable
    log_file = output / run_id / "service_stage2_audit.log"

    command = [
        python,
        str(PROJECT_ROOT / "scripts" / "00_audit_one_plan.py"),
        str(plan),
        "--schema-doc",
        str(schema),
        "--chapter-dir",
        str(chapters),
        "--output-root",
        str(output),
        "--run-id",
        run_id,
        "--opinion-db",
        str(opinion_db),
        "--opinion-source",
        str(opinions),
    ]
    _run(command, cwd=PROJECT_ROOT, log_file=log_file, progress=notify, label="正在执行方案属性提取和规程审核")

    summary_path = output / run_id / "audit_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"审核完成但未生成摘要：{summary_path}")
    summary = _load_json(summary_path)
    summary["service_log"] = str(log_file)
    notify("方案审核完成")
    return summary


def run_match_new_case_advice(
    new_case_file: str | Path,
    *,
    output_dir: str | Path,
    database_file: str | Path | None = None,
    historical_case_root: str | Path | None = None,
    rebuild_database: bool = False,
    top_k: int = 5,
    python_executable: str | Path | None = None,
    progress: Progress | None = None,
) -> dict[str, Any]:
    """Match a new case and return the complete advice text from the best case."""
    notify = progress or (lambda message: None)
    source = Path(new_case_file).resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    if top_k < 1 or top_k > 50:
        raise ValueError("top_k必须在1到50之间。")

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    database = Path(database_file or PROJECT_ROOT / "data" / "case_advice_database.json").resolve()
    history_root = Path(historical_case_root or WORKSPACE_ROOT / "项目安全评估").resolve()
    python = str(Path(python_executable).resolve()) if python_executable else sys.executable
    log_file = output / "service_advice_match.log"

    if rebuild_database or not database.exists():
        with ADVICE_DATABASE_LOCK:
            if rebuild_database or not database.exists():
                database.parent.mkdir(parents=True, exist_ok=True)
                _run(
                    [python, str(PROJECT_ROOT / "scripts" / "16_build_case_advice_database.py"), str(history_root), "-o", str(database)],
                    cwd=PROJECT_ROOT,
                    log_file=log_file,
                    progress=notify,
                    label="正在重建历史案例建议数据库",
                )

    _run(
        [
            python,
            str(PROJECT_ROOT / "scripts" / "17_match_case_advice.py"),
            str(source),
            "--database",
            str(database),
            "--top-k",
            str(top_k),
            "-o",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        log_file=log_file,
        progress=notify,
        label="正在匹配最相似案例并复制评审建议",
    )
    result_path = output / "case_advice_match.json"
    if not result_path.exists():
        raise FileNotFoundError(f"匹配完成但未生成结果：{result_path}")
    result = _load_json(result_path)
    result["output_dir"] = str(output)
    result["service_log"] = str(log_file)
    notify("案例建议匹配完成")
    return result
