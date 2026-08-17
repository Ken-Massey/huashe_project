from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .config import CASE_ADVICE_DATABASE, DEEPKE_PYTHON, KNOWLEDGE_DB, KNOWLEDGE_FILE_ROOT, WORKSPACE_ROOT


Progress = Callable[[str], None]

DEFAULT_CASE_FOLDERS = (
    ("foundation_pit", "基坑类"),
    ("pipeline_open", "管线类（明挖）"),
    ("pipeline_trenchless", "管线类（非开挖）"),
    ("road_bridge", "道路桥梁类"),
    ("deep_fill", "高填、深挖类"),
    ("other", "其他类"),
)

CASE_CATEGORY_KEYS = {
    "基坑类": "foundation_pit",
    "管线类（明挖）": "pipeline_open",
    "管线类（非开挖）": "pipeline_trenchless",
    "道路桥梁类": "road_bridge",
    "高填、深挖类": "deep_fill",
    "其他类": "other",
}


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _text_values(value: Any):
    if isinstance(value, str) and value.strip():
        yield value.strip()
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _text_values(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _text_values(nested)


def normalize_case_category(value: str | None) -> str:
    text = re.sub(r"\s+", "", str(value or "")).strip()
    aliases = {
        "基坑": "基坑类",
        "管线": "管线类（明挖）",
        "管线类": "管线类（明挖）",
        "道路桥梁": "道路桥梁类",
        "高填深挖": "高填、深挖类",
        "高填深挖类": "高填、深挖类",
        "其他": "其他类",
        "未分类": "其他类",
    }
    return aliases.get(text, text)


def infer_case_category(
    case_name: str | None,
    original_file_name: str | None = None,
    features: dict[str, Any] | None = None,
) -> str:
    """Infer a stable project category from the case title and extracted features."""
    features = features or {}
    title = " ".join(
        str(value or "") for value in (case_name, original_file_name, features.get("case_name"))
    )
    compact = re.sub(r"\s+", "", title).lower()

    category = normalize_case_category(features.get("category"))
    if category:
        return category

    rules = (
        ("管线类（非开挖）", ("顶管", "非开挖", "定向钻", "牵引管", "拖拉管", "顶进管", "微型隧道")),
        ("管线类（明挖）", ("雨污水", "污水管", "给水管", "排水管", "燃气管", "电力管线", "综合管线", "管道", "管网", "沟槽", "泵站")),
        ("高填、深挖类", ("高填", "深挖", "场平", "土方工程", "环境整治", "边坡")),
        ("基坑类", ("基坑", "地下室", "地下车库", "地块项目", "产业园", "房建")),
        ("道路桥梁类", ("道路", "大道", "公路", "高速", "桥梁", "铁路", "城际", "上跨", "下穿", "路工程")),
    )
    for label, keywords in rules:
        if any(keyword in compact for keyword in keywords):
            return label

    work_types = features.get("work_types") or []
    if isinstance(work_types, str):
        work_types = [work_types]
    normalized = {str(value).strip() for value in work_types if str(value).strip()}
    fallback = (
        ("管线类（明挖）", {"管线"}),
        ("基坑类", {"基坑", "桩基"}),
        ("道路桥梁类", {"道路桥梁"}),
        ("高填、深挖类", {"高填深挖", "高填、深挖"}),
    )
    for label, values in fallback:
        if normalized & values:
            return label
    return "其他类"


class KnowledgeBase:
    def __init__(
        self,
        database: Path = KNOWLEDGE_DB,
        file_root: Path = KNOWLEDGE_FILE_ROOT,
        match_database: Path = CASE_ADVICE_DATABASE,
        python_executable: str | Path | None = DEEPKE_PYTHON,
    ) -> None:
        self.database = database
        self.file_root = Path(file_root).resolve()
        self.match_database = Path(match_database).resolve()
        self.python_executable = str(python_executable) if python_executable else sys.executable
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.file_root.mkdir(parents=True, exist_ok=True)
        self.match_database.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._initialize()
        self._import_legacy_database()
        self._backfill_categories()
        self._initialize_default_folders()
        self._backfill_case_folders()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS kb_case (
                    case_id TEXT PRIMARY KEY,
                    case_name TEXT NOT NULL,
                    category TEXT,
                    original_file_name TEXT,
                    stored_file TEXT,
                    source_file TEXT,
                    sha256 TEXT,
                    file_size INTEGER,
                    extraction_method TEXT,
                    paragraph_count INTEGER DEFAULT 0,
                    text_length INTEGER DEFAULT 0,
                    text_file TEXT,
                    features_json TEXT NOT NULL,
                    advices_json TEXT NOT NULL,
                    advice_count INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    managed_file INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    folder_id TEXT,
                    folder_assignment TEXT
                )
                """
            )
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS kb_case_folder (
                    folder_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    system_key TEXT UNIQUE,
                    parent_id TEXT,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS kb_setting (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(kb_case)")}
            if "folder_id" not in columns:
                connection.execute("ALTER TABLE kb_case ADD COLUMN folder_id TEXT")
            if "folder_assignment" not in columns:
                connection.execute("ALTER TABLE kb_case ADD COLUMN folder_assignment TEXT")
            folder_columns = {row["name"] for row in connection.execute("PRAGMA table_info(kb_case_folder)")}
            if "parent_id" not in folder_columns:
                connection.execute("ALTER TABLE kb_case_folder ADD COLUMN parent_id TEXT")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_kb_case_active ON kb_case(active, status)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_kb_case_sha256 ON kb_case(sha256)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_kb_case_folder ON kb_case(folder_id)")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_kb_case_folder_parent ON kb_case_folder(parent_id)"
            )

    def _initialize_default_folders(self) -> None:
        with self.lock, self._connect() as connection:
            seeded = connection.execute(
                "SELECT setting_value FROM kb_setting WHERE setting_key='default_case_folders_seeded'"
            ).fetchone()
            if seeded:
                return
            now = _now()
            for sort_order, (system_key, name) in enumerate(DEFAULT_CASE_FOLDERS):
                existing = connection.execute(
                    "SELECT folder_id FROM kb_case_folder WHERE name=? COLLATE NOCASE",
                    (name,),
                ).fetchone()
                if existing:
                    connection.execute(
                        "UPDATE kb_case_folder SET system_key=?, sort_order=?, updated_at=? WHERE folder_id=?",
                        (system_key, sort_order, now, existing["folder_id"]),
                    )
                else:
                    connection.execute(
                        """INSERT INTO kb_case_folder(
                            folder_id,name,system_key,sort_order,created_at,updated_at
                        ) VALUES(?,?,?,?,?,?)""",
                        ("CF-" + uuid.uuid4().hex[:12].upper(), name, system_key, sort_order, now, now),
                    )
            connection.execute(
                """INSERT OR REPLACE INTO kb_setting(setting_key,setting_value,updated_at)
                   VALUES('default_case_folders_seeded','1',?)""",
                (now,),
            )

    def _folder_id_for_category(self, category: str | None) -> str | None:
        system_key = CASE_CATEGORY_KEYS.get(normalize_case_category(category), "other")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT folder_id FROM kb_case_folder WHERE system_key=?",
                (system_key,),
            ).fetchone()
        return row["folder_id"] if row else None

    def _backfill_case_folders(self) -> None:
        with self.lock, self._connect() as connection:
            rows = connection.execute(
                """SELECT c.case_id,c.category
                   FROM kb_case c
                   LEFT JOIN kb_case_folder f ON f.folder_id=c.folder_id
                   WHERE c.folder_assignment='auto'
                      OR (c.folder_assignment IS NULL AND (c.folder_id IS NULL OR f.system_key IS NOT NULL))"""
            ).fetchall()
            now = _now()
            for row in rows:
                folder_id = self._folder_id_for_category(row["category"])
                if folder_id:
                    connection.execute(
                        """UPDATE kb_case
                           SET folder_id=?, folder_assignment='auto', updated_at=?
                           WHERE case_id=?""",
                        (folder_id, now, row["case_id"]),
                    )

    def list_folders(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT f.*,
                    (SELECT COUNT(*) FROM kb_case c WHERE c.folder_id=f.folder_id) case_count
                   FROM kb_case_folder f
                   ORDER BY f.sort_order,f.created_at,f.name"""
            ).fetchall()
        return [dict(row) for row in rows]

    def get_folder(self, folder_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT f.*,
                    (SELECT COUNT(*) FROM kb_case c WHERE c.folder_id=f.folder_id) case_count
                   FROM kb_case_folder f WHERE f.folder_id=?""",
                (folder_id,),
            ).fetchone()
        if not row:
            raise KeyError(folder_id)
        return dict(row)

    def create_folder(self, name: str, parent_id: str | None = None) -> dict[str, Any]:
        clean_name = re.sub(r"\s+", " ", name).strip()
        if not clean_name:
            raise ValueError("案例文件夹名称不能为空。")
        if len(clean_name) > 60:
            raise ValueError("案例文件夹名称不能超过60个字符。")
        folder_id = "CF-" + uuid.uuid4().hex[:12].upper()
        now = _now()
        if parent_id:
            self.get_folder(parent_id)
        try:
            with self.lock, self._connect() as connection:
                sort_order = connection.execute(
                    """SELECT COALESCE(MAX(sort_order),-1)+1 value
                       FROM kb_case_folder WHERE parent_id IS ?""",
                    (parent_id,),
                ).fetchone()["value"]
                connection.execute(
                    """INSERT INTO kb_case_folder(
                           folder_id,name,parent_id,sort_order,created_at,updated_at
                       ) VALUES(?,?,?,?,?,?)""",
                    (folder_id, clean_name, parent_id, sort_order, now, now),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("已存在同名案例文件夹。") from exc
        return self.get_folder(folder_id)

    def rename_folder(self, folder_id: str, name: str) -> dict[str, Any]:
        self.get_folder(folder_id)
        clean_name = re.sub(r"\s+", " ", name).strip()
        if not clean_name:
            raise ValueError("案例文件夹名称不能为空。")
        if len(clean_name) > 60:
            raise ValueError("案例文件夹名称不能超过60个字符。")
        try:
            with self.lock, self._connect() as connection:
                connection.execute(
                    "UPDATE kb_case_folder SET name=?,updated_at=? WHERE folder_id=?",
                    (clean_name, _now(), folder_id),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("已存在同名案例文件夹。") from exc
        return self.get_folder(folder_id)

    def delete_folder(self, folder_id: str) -> dict[str, Any]:
        item = self.get_folder(folder_id)
        parent_id = item.get("parent_id")
        with self.lock, self._connect() as connection:
            connection.execute(
                """UPDATE kb_case
                   SET folder_id=?,folder_assignment='manual',updated_at=?
                   WHERE folder_id=?""",
                (parent_id, _now(), folder_id),
            )
            connection.execute(
                "UPDATE kb_case_folder SET parent_id=?,updated_at=? WHERE parent_id=?",
                (parent_id, _now(), folder_id),
            )
            connection.execute("DELETE FROM kb_case_folder WHERE folder_id=?", (folder_id,))
        return item

    def set_case_folder(self, case_id: str, folder_id: str | None) -> dict[str, Any]:
        self.get_case(case_id)
        if folder_id:
            self.get_folder(folder_id)
        with self.lock, self._connect() as connection:
            connection.execute(
                """UPDATE kb_case
                   SET folder_id=?,folder_assignment='manual',updated_at=?
                   WHERE case_id=?""",
                (folder_id, _now(), case_id),
            )
        return self.get_case(case_id)

    def _import_legacy_database(self) -> None:
        with self.lock, self._connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM kb_case").fetchone()[0]
            if count or not self.match_database.exists():
                return
            legacy = json.loads(self.match_database.read_text(encoding="utf-8"))
            for index, record in enumerate(legacy.get("records", []), start=1):
                case_id = record.get("case_id") or f"legacy_{index:04d}"
                now = _now()
                connection.execute(
                    """
                    INSERT OR IGNORE INTO kb_case (
                        case_id, case_name, category, source_file, features_json, advices_json,
                        advice_count, status, active, managed_file, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ready', 1, 0, ?, ?)
                    """,
                    (
                        case_id,
                        record.get("case_name") or case_id,
                        record.get("category"),
                        record.get("report_file"),
                        _json(record.get("features") or {}),
                        _json(record.get("advices") or []),
                        len(record.get("advices") or []),
                        now,
                        now,
                    ),
                )

    def _backfill_categories(self) -> None:
        with self.lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT case_id, case_name, category, original_file_name, features_json FROM kb_case"
            ).fetchall()
            if not rows:
                return
            now = _now()
            for row in rows:
                features = json.loads(row["features_json"] or "{}")
                category = normalize_case_category(row["category"]) or infer_case_category(
                    row["case_name"], row["original_file_name"], features
                )
                if category == row["category"]:
                    continue
                connection.execute(
                    "UPDATE kb_case SET category = ?, updated_at = ? WHERE case_id = ?",
                    (category, now, row["case_id"]),
                )
            self._export_locked(connection)

    @staticmethod
    def _digest(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while block := stream.read(1024 * 1024):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["active"] = bool(item["active"])
        item["managed_file"] = bool(item["managed_file"])
        item["features"] = json.loads(item.pop("features_json") or "{}")
        item["advices"] = json.loads(item.pop("advices_json") or "[]")
        return item

    def list_cases(self, keyword: str | None = None, include_inactive: bool = False) -> list[dict[str, Any]]:
        clauses = [] if include_inactive else ["active = 1"]
        params: list[Any] = []
        if keyword:
            clauses.append("(case_name LIKE ? OR category LIKE ? OR original_file_name LIKE ?)")
            term = f"%{keyword}%"
            params.extend([term, term, term])
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"""SELECT c.*,f.name folder_name
                    FROM kb_case c
                    LEFT JOIN kb_case_folder f ON f.folder_id=c.folder_id
                    {where.replace('active', 'c.active').replace('case_name', 'c.case_name').replace('category', 'c.category').replace('original_file_name', 'c.original_file_name')}
                    ORDER BY c.updated_at DESC""",
                params,
            ).fetchall()
        return [self._row(row) for row in rows]

    def get_case(self, case_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT c.*,f.name folder_name
                   FROM kb_case c
                   LEFT JOIN kb_case_folder f ON f.folder_id=c.folder_id
                   WHERE c.case_id=?""",
                (case_id,),
            ).fetchone()
        if row is None:
            raise KeyError(case_id)
        return self._row(row)

    def rename_case(self, case_id: str, name: str) -> dict[str, Any]:
        self.get_case(case_id)
        clean_name = re.sub(r"\s+", " ", name).strip()
        if not clean_name:
            raise ValueError("案例名称不能为空。")
        if len(clean_name) > 180:
            raise ValueError("案例名称不能超过180个字符。")
        with self.lock, self._connect() as connection:
            connection.execute(
                "UPDATE kb_case SET case_name=?,updated_at=? WHERE case_id=?",
                (clean_name, _now(), case_id),
            )
        return self.get_case(case_id)

    def import_case(
        self,
        uploaded_file: Path,
        case_name: str | None,
        category: str | None,
        progress: Progress,
        folder_id: str | None = None,
    ) -> dict[str, Any]:
        if folder_id:
            self.get_folder(folder_id)
        source = uploaded_file.resolve()
        sha256 = self._digest(source)
        with self.lock, self._connect() as connection:
            duplicate = connection.execute("SELECT case_id FROM kb_case WHERE sha256 = ? AND active = 1", (sha256,)).fetchone()
            if duplicate:
                raise ValueError(f"该文件已经在知识库中，案例编号：{duplicate['case_id']}")

        case_id = f"kb_{uuid.uuid4().hex}"
        folder = self.file_root / case_id
        folder.mkdir(parents=True, exist_ok=False)
        stored = folder / source.name
        shutil.copy2(source, stored)
        text_file = folder / "extracted_text.txt"
        record_file = folder / "case_record.json"
        log_file = folder / "import.log"
        python = self.python_executable
        command = [
            python,
            str(WORKSPACE_ROOT / "deepke_case_extract" / "scripts" / "18_extract_knowledge_case.py"),
            str(stored),
            "--case-id",
            case_id,
            "--text-output",
            str(text_file),
            "-o",
            str(record_file),
        ]
        if case_name:
            command.extend(["--case-name", case_name])
        if category:
            command.extend(["--category", category])
        progress("正在读取案例正文并抽取属性和评审建议")
        with log_file.open("w", encoding="utf-8") as log:
            completed = subprocess.run(
                command,
                cwd=str(WORKSPACE_ROOT / "deepke_case_extract"),
                stdout=log,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        if completed.returncode != 0:
            raise RuntimeError(f"知识库文件解析失败，日志：{log_file}")
        record = json.loads(record_file.read_text(encoding="utf-8"))
        resolved_category = (
            normalize_case_category(category)
            or normalize_case_category(record.get("category"))
            or infer_case_category(record.get("case_name"), source.name, record.get("features") or {})
        )
        record["category"] = resolved_category
        assigned_folder_id = folder_id or self._folder_id_for_category(resolved_category)
        record_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        status = "ready" if record["advice_count"] else "review_required"
        now = _now()
        with self.lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO kb_case (
                    case_id, case_name, category, original_file_name, stored_file, source_file,
                    sha256, file_size, extraction_method, paragraph_count, text_length, text_file,
                    features_json, advices_json, advice_count, status, active, managed_file,
                    created_at, updated_at, folder_id, folder_assignment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    record["case_name"],
                    resolved_category,
                    source.name,
                    str(stored),
                    str(stored),
                    sha256,
                    stored.stat().st_size,
                    record.get("extraction_method"),
                    record.get("paragraph_count", 0),
                    record.get("text_length", 0),
                    str(text_file),
                    _json(record.get("features") or {}),
                    _json(record.get("advices") or []),
                    record.get("advice_count", 0),
                    status,
                    now,
                    now,
                    assigned_folder_id,
                    "manual" if folder_id else "auto",
                ),
            )
            self._export_locked(connection)
        progress("案例已加入知识库和匹配数据库")
        return self.get_case(case_id)

    def set_active(self, case_id: str, active: bool) -> dict[str, Any]:
        with self.lock, self._connect() as connection:
            cursor = connection.execute(
                "UPDATE kb_case SET active = ?, updated_at = ? WHERE case_id = ?",
                (1 if active else 0, _now(), case_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(case_id)
            self._export_locked(connection)
        return self.get_case(case_id)

    def delete_case(self, case_id: str) -> dict[str, Any]:
        """Permanently remove a case record and files managed by this knowledge base."""
        item = self.get_case(case_id)
        with self.lock, self._connect() as connection:
            cursor = connection.execute("DELETE FROM kb_case WHERE case_id = ?", (case_id,))
            if cursor.rowcount == 0:
                raise KeyError(case_id)
            self._export_locked(connection)

        source = item.get("stored_file")
        if item.get("managed_file") and source:
            folder = Path(source).resolve().parent
            root = self.file_root.resolve()
            if folder.parent == root and folder.exists():
                shutil.rmtree(folder)
        return item

    def _export_locked(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT * FROM kb_case WHERE active = 1 AND status = 'ready' AND advice_count > 0 ORDER BY created_at"
        ).fetchall()
        records = []
        for row in rows:
            item = self._row(row)
            source = item.get("stored_file") or item.get("source_file")
            records.append(
                {
                    "case_id": item["case_id"],
                    "case_name": item["case_name"],
                    "category": item.get("category"),
                    "case_folder": str(Path(source).parent) if source else None,
                    "report_file": source,
                    "features": item["features"],
                    "advice_count": item["advice_count"],
                    "advices": item["advices"],
                }
            )
        value = {
            "format_version": "case_advice_database_v1",
            "source_root": str(self.file_root),
            "case_count": len(records),
            "records": records,
        }
        temporary = self.match_database.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.match_database)

    def stats(self) -> dict[str, int]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) AS active,
                    SUM(CASE WHEN active = 1 AND status = 'ready' THEN 1 ELSE 0 END) AS matchable,
                    SUM(CASE WHEN active = 1 AND status = 'review_required' THEN 1 ELSE 0 END) AS review_required
                FROM kb_case
                """
            ).fetchone()
        return {key: int(row[key] or 0) for key in row.keys()}

    def search(self, question: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search active case text, attributes and advice while preserving source excerpts."""
        query = re.sub(r"\s+", "", question).lower()
        domain_terms = (
            "基坑", "盾构", "明挖", "暗挖", "高架", "退让距离", "净距", "安全评估",
            "保护监测", "结构监测", "变形监测", "降水", "支护", "控制保护区",
            "特别保护区", "影响等级", "专家意见", "施工", "规划", "设计", "出让",
        )
        terms = [term for term in domain_terms if term in query]
        terms.extend(re.findall(r"[a-z0-9.]+", query))
        if not terms:
            terms.extend(query[index:index + 2] for index in range(max(0, len(query) - 1)))
        terms = list(dict.fromkeys(term for term in terms if len(term) >= 2 or term.replace(".", "").isdigit()))
        if not terms:
            return []

        results: list[dict[str, Any]] = []
        for item in self.list_cases():
            text = ""
            text_file = item.get("text_file")
            if text_file and Path(text_file).exists():
                text = Path(text_file).read_text(encoding="utf-8", errors="replace")[:2_000_000]
            fallback = "\n".join([
                item.get("case_name") or "",
                item.get("category") or "",
                *_text_values(item.get("features") or {}),
                *_text_values(item.get("advices") or []),
            ])
            corpus = f"{text}\n{fallback}"
            corpus_lower = corpus.lower()
            title_lower = (item.get("case_name") or "").lower()
            matched_terms = sum(1 for term in terms if term in corpus_lower)
            score = matched_terms * 100 + sum(
                (corpus_lower.count(term) + 4 * title_lower.count(term)) * len(term) for term in terms
            )
            if score <= 0:
                continue
            paragraphs = [part.strip() for part in re.split(r"[\r\n]+", corpus) if part.strip()]
            ranked = sorted(
                paragraphs,
                key=lambda part: (
                    sum(1 for term in terms if term in part.lower()),
                    sum(part.lower().count(term) * len(term) for term in terms),
                ),
                reverse=True,
            )
            relevant = [part for part in ranked if any(term in part.lower() for term in terms)]
            excerpt = "；".join(relevant[:2])[:500]
            results.append({
                "case_id": item["case_id"],
                "case_name": item["case_name"],
                "category": item.get("category"),
                "score": score,
                "excerpt": excerpt,
                "original_file_name": item.get("original_file_name"),
            })
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]
