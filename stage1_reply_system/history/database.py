"""Build and query the SQLite historical reply database."""

from __future__ import annotations

import json
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from .advice import extract_advice_section, extract_project_name, infer_metadata
from .scanner import cluster_replies, pair_incoming, scan_documents
from .text_extract import extract_document


SCHEMA = """
CREATE TABLE IF NOT EXISTS reply_cases (
    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT NOT NULL UNIQUE,
    project_name TEXT,
    project_root TEXT NOT NULL,
    stage TEXT,
    project_type TEXT,
    relative_relationship TEXT,
    structure_methods_json TEXT NOT NULL,
    metro_lines_json TEXT NOT NULL,
    pit_depth_m REAL,
    minimum_horizontal_clearance_m REAL,
    minimum_vertical_clearance_m REAL,
    incoming_file TEXT,
    incoming_text TEXT,
    primary_reply_file TEXT NOT NULL,
    editable_reply_file TEXT,
    official_reply_file TEXT,
    reply_files_json TEXT NOT NULL,
    reply_text TEXT NOT NULL,
    advice_text TEXT NOT NULL,
    advice_items_json TEXT NOT NULL,
    extraction_json TEXT NOT NULL,
    pair_score REAL,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reply_cases_stage ON reply_cases(stage);
CREATE INDEX IF NOT EXISTS idx_reply_cases_project_type ON reply_cases(project_type);
"""


def _read(path: str | None, allow_pdf_ocr: bool) -> dict[str, object]:
    if not path:
        return {"path": None, "text": "", "method": None, "error": None}
    try:
        return {**extract_document(path, allow_pdf_ocr=allow_pdf_ocr), "error": None}
    except Exception as exc:  # Preserve failures in the database build report.
        return {"path": path, "text": "", "method": None, "error": f"{type(exc).__name__}: {exc}"}


def _connect(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    existing = {row[1] for row in connection.execute("PRAGMA table_info(reply_cases)")}
    for name in ("pit_depth_m", "minimum_horizontal_clearance_m", "minimum_vertical_clearance_m"):
        if name not in existing:
            connection.execute(f"ALTER TABLE reply_cases ADD COLUMN {name} REAL")
    if "active" not in existing:
        connection.execute("ALTER TABLE reply_cases ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
    return connection


def build_history_database(
    roots: Iterable[str | Path],
    database_path: str | Path,
    *,
    rebuild: bool = True,
    allow_pdf_ocr: bool = True,
    progress: Callable[[int, int, str], None] | None = None,
) -> dict[str, object]:
    scan = scan_documents(roots)
    clusters = cluster_replies(scan)
    connection = _connect(database_path)
    if rebuild:
        connection.execute("DELETE FROM reply_cases")

    errors: list[dict[str, str]] = []
    stored = 0
    skipped = 0
    extraction_cache: dict[tuple[str, bool], dict[str, object]] = {}

    def read_cached(path: str | None, use_ocr: bool) -> dict[str, object]:
        key = (path or "", use_ocr)
        if key not in extraction_cache:
            extraction_cache[key] = _read(path, use_ocr)
        return extraction_cache[key]

    for index, cluster in enumerate(clusters, 1):
        primary = cluster["primary_reply"]
        if progress:
            progress(index, len(clusters), Path(str(primary["path"])).name)
        incoming = pair_incoming(cluster, scan["incoming"])
        text_source = primary
        reply_result = read_cached(str(text_source["path"]), allow_pdf_ocr)
        official = cluster.get("official_reply")
        if reply_result["error"] and official and official["path"] != text_source["path"]:
            errors.append({
                "path": str(text_source["path"]),
                "error": f"可编辑回函读取失败，已改用盖章PDF：{reply_result['error']}",
            })
            text_source = official
            reply_result = read_cached(str(text_source["path"]), allow_pdf_ocr)
        # The reply itself repeats the project facts needed for matching. For a
        # scanned historical incoming letter, avoid a second expensive OCR pass.
        incoming_result = read_cached(str(incoming["path"]) if incoming else None, False)
        if reply_result["error"]:
            errors.append({"path": str(text_source["path"]), "error": str(reply_result["error"])})
            skipped += 1
            continue
        reply_text = str(reply_result["text"])
        advice = extract_advice_section(reply_text)
        if not advice["advice_text"]:
            errors.append({"path": str(primary["path"]), "error": "未识别到审核意见正文"})
        metadata = infer_metadata(f"{incoming_result['text']}\n{reply_text}", str(text_source["path"]))
        project_name = extract_project_name(reply_text)
        if not project_name or len(project_name) < 4:
            project_name = extract_project_name(Path(str(text_source["path"])).stem)
        paths = [str(item["path"]) for item in cluster["reply_documents"]]
        identity = str(Path(str(text_source["path"])).resolve()).casefold()
        fingerprint = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        extraction = {
            "reply_method": reply_result["method"],
            "incoming_method": incoming_result["method"],
            "incoming_error": incoming_result["error"],
            "advice_anchor": advice["anchor"],
            "advice_status": advice["status"],
        }
        values = (
            fingerprint, project_name, cluster["project_root"], metadata["stage"] or cluster["stage"],
            metadata["project_type"], metadata["relative_relationship"],
            json.dumps(metadata["structure_methods"], ensure_ascii=False),
            json.dumps(metadata["metro_lines"], ensure_ascii=False),
            metadata["pit_depth_m"], metadata["minimum_horizontal_clearance_m"],
            metadata["minimum_vertical_clearance_m"],
            str(incoming["path"]) if incoming else None, str(incoming_result["text"]),
            str(text_source["path"]), str(cluster["editable_reply"]["path"]) if cluster["editable_reply"] else None,
            str(cluster["official_reply"]["path"]) if cluster["official_reply"] else None,
            json.dumps(paths, ensure_ascii=False), reply_text, str(advice["advice_text"]),
            json.dumps(advice["advice_items"], ensure_ascii=False), json.dumps(extraction, ensure_ascii=False),
            incoming.get("pair_score") if incoming else None, datetime.now().isoformat(timespec="seconds"),
        )
        connection.execute(
            """INSERT INTO reply_cases (
                fingerprint, project_name, project_root, stage, project_type, relative_relationship,
                structure_methods_json, metro_lines_json,
                pit_depth_m, minimum_horizontal_clearance_m, minimum_vertical_clearance_m,
                incoming_file, incoming_text,
                primary_reply_file, editable_reply_file, official_reply_file, reply_files_json,
                reply_text, advice_text, advice_items_json, extraction_json, pair_score, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
                project_name=excluded.project_name,
                project_root=excluded.project_root,
                stage=excluded.stage,
                project_type=excluded.project_type,
                relative_relationship=excluded.relative_relationship,
                structure_methods_json=excluded.structure_methods_json,
                metro_lines_json=excluded.metro_lines_json,
                pit_depth_m=excluded.pit_depth_m,
                minimum_horizontal_clearance_m=excluded.minimum_horizontal_clearance_m,
                minimum_vertical_clearance_m=excluded.minimum_vertical_clearance_m,
                incoming_file=excluded.incoming_file,
                incoming_text=excluded.incoming_text,
                primary_reply_file=excluded.primary_reply_file,
                editable_reply_file=excluded.editable_reply_file,
                official_reply_file=excluded.official_reply_file,
                reply_files_json=excluded.reply_files_json,
                reply_text=excluded.reply_text,
                advice_text=excluded.advice_text,
                advice_items_json=excluded.advice_items_json,
                extraction_json=excluded.extraction_json,
                pair_score=excluded.pair_score,
                updated_at=excluded.updated_at""",
            values,
        )
        stored += 1
    connection.commit()
    actual_stored = connection.execute("SELECT COUNT(*) FROM reply_cases").fetchone()[0]
    connection.close()
    return {
        "database_path": str(Path(database_path).resolve()),
        "incoming_count": len(scan["incoming"]),
        "reply_file_count": len(scan["replies"]),
        "reply_cluster_count": len(clusters),
        "processed_case_count": stored,
        "stored_case_count": actual_stored,
        "skipped_case_count": skipped,
        "warnings": errors,
    }


def _quality_status(case: dict[str, object]) -> tuple[str, list[str]]:
    issues: list[str] = []
    if not case.get("incoming_file"):
        issues.append("未配对来函")
    if not str(case.get("advice_text") or "").strip():
        issues.append("未提取到建议")
    pair_score = case.get("pair_score")
    if pair_score is not None and float(pair_score) < 0.55:
        issues.append("来函回函配对分偏低")
    extraction = case.get("extraction") or {}
    if isinstance(extraction, dict) and extraction.get("incoming_error"):
        issues.append("来函文字读取失败")
    return ("ready" if not issues else "review_required", issues)


def load_history_cases(
    database_path: str | Path,
    *,
    include_inactive: bool = False,
) -> list[dict[str, object]]:
    connection = _connect(database_path)
    where = "" if include_inactive else "WHERE active = 1"
    rows = connection.execute(f"SELECT * FROM reply_cases {where} ORDER BY case_id").fetchall()
    connection.close()
    cases: list[dict[str, object]] = []
    for row in rows:
        item = dict(row)
        for key in ("structure_methods_json", "metro_lines_json", "reply_files_json", "advice_items_json", "extraction_json"):
            item[key.removesuffix("_json")] = json.loads(item.pop(key))
        item["quality_status"], item["quality_issues"] = _quality_status(item)
        cases.append(item)
    return cases


def set_history_case_active(case_id: int, active: bool, database_path: str | Path) -> bool:
    connection = _connect(database_path)
    cursor = connection.execute(
        "UPDATE reply_cases SET active = ?, updated_at = ? WHERE case_id = ?",
        (1 if active else 0, datetime.now().isoformat(timespec="seconds"), int(case_id)),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount == 1


def history_database_stats(database_path: str | Path) -> dict[str, int]:
    cases = load_history_cases(database_path, include_inactive=True)
    return {
        "total": len(cases),
        "active": sum(bool(case["active"]) for case in cases),
        "inactive": sum(not bool(case["active"]) for case in cases),
        "ready": sum(bool(case["active"]) and case["quality_status"] == "ready" for case in cases),
        "review_required": sum(bool(case["active"]) and case["quality_status"] != "ready" for case in cases),
    }
