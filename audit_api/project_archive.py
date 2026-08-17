from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .config import PROJECT_ARCHIVE_DB


PROJECT_STATUSES = {"active", "archived"}
STAGE_STATUSES = {"active", "archived"}
AUDIT_STATUSES = {"pending", "running", "success", "failed"}


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _text(value: Any, *, field: str, required: bool = False, maximum: int = 500) -> str:
    result = " ".join(str(value or "").split())
    if required and not result:
        raise ValueError(f"{field}不能为空。")
    if len(result) > maximum:
        raise ValueError(f"{field}不能超过{maximum}个字符。")
    return result


def _json_dump(value: Any, fallback: Any) -> str:
    return json.dumps(fallback if value is None else value, ensure_ascii=False)


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback


def _clip(value: Any, maximum: int) -> str:
    return " ".join(str(value or "").split())[:maximum]


def _history_findings(result_data: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    risk_report = (
        ((result_data.get("dynamic_regulation_audit") or {}).get("risk_report") or {})
        if isinstance(result_data, dict) else {}
    )
    candidates = risk_report.get("findings") or []
    if not candidates and isinstance(result_data, dict):
        candidates = (result_data.get("audit_details") or {}).get("non_compliant_items") or []
    findings = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        judgement = str(item.get("judgement") or item.get("status") or "risk")
        if judgement == "compliant":
            continue
        findings.append({
            "title": _clip(item.get("title") or item.get("name"), 160),
            "risk_level": _clip(item.get("risk_level") or item.get("severity"), 20),
            "judgement": _clip(judgement, 30),
            "analysis": _clip(item.get("analysis") or item.get("result"), 500),
            "recommendation": _clip(item.get("recommendation") or item.get("opinion"), 300),
        })
        if len(findings) >= limit:
            break
    return findings


class ProjectArchiveRepository:
    """Persistent project, custom stage and single-audit archive storage."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or PROJECT_ARCHIVE_DB).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS archive_schema (
                    schema_version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    code TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active'
                        CHECK(status IN ('active', 'archived')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS project_stages (
                    stage_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL COLLATE NOCASE,
                    stage_order INTEGER NOT NULL CHECK(stage_order >= 1),
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active'
                        CHECK(status IN ('active', 'archived')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE RESTRICT,
                    UNIQUE(project_id, name)
                );

                CREATE TABLE IF NOT EXISTS audit_records (
                    audit_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    stage_id TEXT NOT NULL UNIQUE,
                    source_task_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending', 'running', 'success', 'failed')),
                    attempt_count INTEGER NOT NULL DEFAULT 1 CHECK(attempt_count >= 1),
                    audit_date TEXT NOT NULL DEFAULT '',
                    result TEXT NOT NULL DEFAULT '',
                    risk_level TEXT NOT NULL DEFAULT '',
                    summary TEXT NOT NULL DEFAULT '',
                    result_json TEXT NOT NULL DEFAULT '{}',
                    history_context_json TEXT NOT NULL DEFAULT '[]',
                    source_files_json TEXT NOT NULL DEFAULT '[]',
                    artifacts_json TEXT NOT NULL DEFAULT '[]',
                    error_message TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE RESTRICT,
                    FOREIGN KEY(stage_id) REFERENCES project_stages(stage_id) ON DELETE RESTRICT
                );

                CREATE INDEX IF NOT EXISTS idx_projects_updated
                    ON projects(status, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_project_stages_order
                    ON project_stages(project_id, status, stage_order, created_at);
                CREATE INDEX IF NOT EXISTS idx_audit_records_project
                    ON audit_records(project_id, status, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_records_task
                    ON audit_records(source_task_id);
                """
            )
            row = connection.execute("SELECT schema_version FROM archive_schema LIMIT 1").fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO archive_schema(schema_version, updated_at) VALUES(1, ?)",
                    (_now(),),
                )

    @staticmethod
    def _project(row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    @staticmethod
    def _stage(row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    @staticmethod
    def _audit(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["result_data"] = _json_load(result.pop("result_json"), {})
        result["history_context"] = _json_load(result.pop("history_context_json"), [])
        result["source_files"] = _json_load(result.pop("source_files_json"), [])
        result["artifacts"] = _json_load(result.pop("artifacts_json"), [])
        return result

    @staticmethod
    def _integrity_error(exc: sqlite3.IntegrityError) -> ValueError:
        message = str(exc).lower()
        if "projects.name" in message:
            return ValueError("项目名称已存在。")
        if "project_stages.project_id, project_stages.name" in message:
            return ValueError("该项目下已存在同名阶段。")
        if "audit_records.stage_id" in message:
            return ValueError("该阶段已经存在审核记录。")
        return ValueError("项目档案数据不符合唯一性或关联约束。")

    def list_projects(self, search: str = "", status: str | None = "active") -> list[dict[str, Any]]:
        if status is not None and status not in PROJECT_STATUSES:
            raise ValueError("项目状态无效。")
        clauses, params = [], []
        if status is not None:
            clauses.append("p.status = ?")
            params.append(status)
        if search.strip():
            pattern = f"%{search.strip()}%"
            clauses.append("p.name LIKE ?")
            params.append(pattern)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT p.*,
                       COUNT(DISTINCT s.stage_id) AS stage_count,
                       COUNT(DISTINCT CASE WHEN a.status = 'success' THEN a.audit_id END)
                           AS completed_stage_count
                FROM projects p
                LEFT JOIN project_stages s
                    ON s.project_id = p.project_id AND s.status = 'active'
                LEFT JOIN audit_records a ON a.stage_id = s.stage_id
                {where}
                GROUP BY p.project_id
                ORDER BY p.updated_at DESC, p.name
                """,
                params,
            ).fetchall()
        return [self._project(row) for row in rows]

    def get_project(self, project_id: str, *, include_archived_stages: bool = False) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE project_id = ?", (project_id,)
            ).fetchone()
            if row is None:
                raise KeyError("项目不存在。")
            stage_sql = """
                SELECT s.*, a.audit_id, a.status AS audit_status,
                       a.risk_level, a.summary, a.audit_date, a.attempt_count
                FROM project_stages s
                LEFT JOIN audit_records a ON a.stage_id = s.stage_id
                WHERE s.project_id = ?
            """
            params: list[Any] = [project_id]
            if not include_archived_stages:
                stage_sql += " AND s.status = 'active'"
            stage_sql += " ORDER BY s.stage_order, s.created_at"
            stages = [self._stage(item) for item in connection.execute(stage_sql, params)]
        project = self._project(row)
        project["stages"] = stages
        project["stage_count"] = len(stages)
        project["completed_stage_count"] = sum(
            1 for stage in stages if stage.get("audit_status") == "success"
        )
        return project

    def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
        project_id, now = _id("prj"), _now()
        values = (
            project_id,
            _text(data.get("name"), field="项目名称", required=True, maximum=120),
            _text(data.get("code"), field="项目编号", maximum=80),
            _text(data.get("location"), field="项目地点", maximum=200),
            _text(data.get("description"), field="项目说明", maximum=2000),
            now,
            now,
        )
        try:
            with self._lock, self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO projects(
                        project_id, name, code, location, description, created_at, updated_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc
        return self.get_project(project_id)

    def update_project(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        current = self.get_project(project_id, include_archived_stages=True)
        name = _text(data.get("name", current["name"]), field="项目名称", required=True, maximum=120)
        code = _text(data.get("code", current["code"]), field="项目编号", maximum=80)
        location = _text(data.get("location", current["location"]), field="项目地点", maximum=200)
        description = _text(data.get("description", current["description"]), field="项目说明", maximum=2000)
        try:
            with self._lock, self._connect() as connection:
                connection.execute(
                    """
                    UPDATE projects SET name = ?, code = ?, location = ?, description = ?,
                        updated_at = ? WHERE project_id = ?
                    """,
                    (name, code, location, description, _now(), project_id),
                )
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc
        return self.get_project(project_id, include_archived_stages=True)

    def resolve_project_stage(self, project_name: str, stage_name: str) -> dict[str, Any]:
        """Atomically reuse or create an active project and stage by their names."""
        clean_project = _text(project_name, field="项目名称", required=True, maximum=120)
        clean_stage = _text(stage_name, field="阶段名称", required=True, maximum=120)
        project_created = False
        stage_created = False
        now = _now()
        with self._lock, self._connect() as connection:
            project = connection.execute(
                "SELECT * FROM projects WHERE name = ? COLLATE NOCASE",
                (clean_project,),
            ).fetchone()
            if project is None:
                project_id = _id("prj")
                connection.execute(
                    """
                    INSERT INTO projects(
                        project_id, name, code, location, description, created_at, updated_at
                    ) VALUES(?, ?, '', '', '', ?, ?)
                    """,
                    (project_id, clean_project, now, now),
                )
                project_created = True
            else:
                project_id = project["project_id"]
                if project["status"] != "active":
                    connection.execute(
                        "UPDATE projects SET status = 'active', updated_at = ? WHERE project_id = ?",
                        (now, project_id),
                    )

            stage = connection.execute(
                """
                SELECT * FROM project_stages
                WHERE project_id = ? AND name = ? COLLATE NOCASE
                """,
                (project_id, clean_stage),
            ).fetchone()
            if stage is None:
                stage_id = _id("stg")
                order = self._next_stage_order(connection, project_id)
                connection.execute(
                    """
                    INSERT INTO project_stages(
                        stage_id, project_id, name, stage_order, description,
                        created_at, updated_at
                    ) VALUES(?, ?, ?, ?, '', ?, ?)
                    """,
                    (stage_id, project_id, clean_stage, order, now, now),
                )
                stage_created = True
            else:
                stage_id = stage["stage_id"]
                if stage["status"] != "active":
                    connection.execute(
                        "UPDATE project_stages SET status = 'active', updated_at = ? WHERE stage_id = ?",
                        (now, stage_id),
                    )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                (now, project_id),
            )
        return {
            "project": self.get_project(project_id),
            "stage": self.get_stage(stage_id),
            "project_created": project_created,
            "stage_created": stage_created,
        }

    def delete_project(self, project_id: str) -> dict[str, Any]:
        """Permanently delete a project archive unless one of its audits is active."""
        with self._lock, self._connect() as connection:
            project = connection.execute(
                "SELECT project_id, name FROM projects WHERE project_id = ?", (project_id,)
            ).fetchone()
            if project is None:
                raise KeyError("项目不存在。")
            active_audits = int(connection.execute(
                """
                SELECT COUNT(*) FROM audit_records
                WHERE project_id = ? AND status IN ('pending', 'running')
                """,
                (project_id,),
            ).fetchone()[0])
            if active_audits:
                raise ValueError("项目存在正在排队或执行的审核任务，暂不能删除。")
            audit_count = int(connection.execute(
                "SELECT COUNT(*) FROM audit_records WHERE project_id = ?", (project_id,)
            ).fetchone()[0])
            stage_count = int(connection.execute(
                "SELECT COUNT(*) FROM project_stages WHERE project_id = ?", (project_id,)
            ).fetchone()[0])
            connection.execute("DELETE FROM audit_records WHERE project_id = ?", (project_id,))
            connection.execute("DELETE FROM project_stages WHERE project_id = ?", (project_id,))
            connection.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        return {
            "project_id": project_id,
            "name": project["name"],
            "deleted_stage_count": stage_count,
            "deleted_audit_count": audit_count,
        }

    def set_project_archived(self, project_id: str, archived: bool = True) -> dict[str, Any]:
        self.get_project(project_id, include_archived_stages=True)
        status = "archived" if archived else "active"
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE projects SET status = ?, updated_at = ? WHERE project_id = ?",
                (status, _now(), project_id),
            )
        return self.get_project(project_id, include_archived_stages=True)

    def _next_stage_order(self, connection: sqlite3.Connection, project_id: str) -> int:
        return int(connection.execute(
            "SELECT COALESCE(MAX(stage_order), 0) + 1 FROM project_stages WHERE project_id = ?",
            (project_id,),
        ).fetchone()[0])

    def create_stage(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        project = self.get_project(project_id, include_archived_stages=True)
        if project["status"] != "active":
            raise ValueError("已归档项目不能新增阶段。")
        stage_id, now = _id("stg"), _now()
        name = _text(data.get("name"), field="阶段名称", required=True, maximum=120)
        description = _text(data.get("description"), field="阶段说明", maximum=2000)
        try:
            with self._lock, self._connect() as connection:
                order = data.get("stage_order")
                order = self._next_stage_order(connection, project_id) if order is None else int(order)
                if order < 1:
                    raise ValueError("阶段顺序必须大于等于1。")
                connection.execute(
                    "UPDATE project_stages SET stage_order = stage_order + 1 WHERE project_id = ? AND stage_order >= ?",
                    (project_id, order),
                )
                connection.execute(
                    """
                    INSERT INTO project_stages(
                        stage_id, project_id, name, stage_order, description, created_at, updated_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?)
                    """,
                    (stage_id, project_id, name, order, description, now, now),
                )
                connection.execute(
                    "UPDATE projects SET updated_at = ? WHERE project_id = ?", (now, project_id)
                )
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc
        return self.get_stage(stage_id)

    def get_stage(self, stage_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT s.*, p.name AS project_name, p.status AS project_status,
                       a.audit_id, a.status AS audit_status, a.risk_level,
                       a.summary, a.audit_date, a.attempt_count
                FROM project_stages s
                JOIN projects p ON p.project_id = s.project_id
                LEFT JOIN audit_records a ON a.stage_id = s.stage_id
                WHERE s.stage_id = ?
                """,
                (stage_id,),
            ).fetchone()
        if row is None:
            raise KeyError("项目阶段不存在。")
        return self._stage(row)

    def update_stage(self, stage_id: str, data: dict[str, Any]) -> dict[str, Any]:
        current = self.get_stage(stage_id)
        name = _text(data.get("name", current["name"]), field="阶段名称", required=True, maximum=120)
        description = _text(data.get("description", current["description"]), field="阶段说明", maximum=2000)
        new_order = int(data.get("stage_order", current["stage_order"]))
        if new_order < 1:
            raise ValueError("阶段顺序必须大于等于1。")
        try:
            with self._lock, self._connect() as connection:
                old_order = int(current["stage_order"])
                if new_order < old_order:
                    connection.execute(
                        """
                        UPDATE project_stages SET stage_order = stage_order + 1
                        WHERE project_id = ? AND stage_id <> ? AND stage_order >= ? AND stage_order < ?
                        """,
                        (current["project_id"], stage_id, new_order, old_order),
                    )
                elif new_order > old_order:
                    connection.execute(
                        """
                        UPDATE project_stages SET stage_order = stage_order - 1
                        WHERE project_id = ? AND stage_id <> ? AND stage_order > ? AND stage_order <= ?
                        """,
                        (current["project_id"], stage_id, old_order, new_order),
                    )
                now = _now()
                connection.execute(
                    """
                    UPDATE project_stages SET name = ?, stage_order = ?, description = ?,
                        updated_at = ? WHERE stage_id = ?
                    """,
                    (name, new_order, description, now, stage_id),
                )
                connection.execute(
                    "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                    (now, current["project_id"]),
                )
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc
        return self.get_stage(stage_id)

    def set_stage_archived(self, stage_id: str, archived: bool = True) -> dict[str, Any]:
        current = self.get_stage(stage_id)
        status = "archived" if archived else "active"
        now = _now()
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE project_stages SET status = ?, updated_at = ? WHERE stage_id = ?",
                (status, now, stage_id),
            )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                (now, current["project_id"]),
            )
        return self.get_stage(stage_id)

    def begin_audit(
        self,
        stage_id: str,
        source_task_id: str,
        *,
        source_files: list[dict[str, Any]] | None = None,
        history_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        stage = self.get_stage(stage_id)
        if stage["project_status"] != "active" or stage["status"] != "active":
            raise ValueError("已归档的项目或阶段不能发起审核。")
        task_id = _text(source_task_id, field="来源任务ID", required=True, maximum=120)
        now = _now()
        with self._lock, self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM audit_records WHERE stage_id = ?", (stage_id,)
            ).fetchone()
            if existing and existing["status"] == "success":
                raise ValueError("该阶段已完成审核，一个阶段只能有一份审核记录。")
            if existing and existing["status"] in {"pending", "running"}:
                raise ValueError("该阶段已有审核任务正在进行。")
            if existing:
                audit_id = existing["audit_id"]
                connection.execute(
                    """
                    UPDATE audit_records SET source_task_id = ?, status = 'pending',
                        attempt_count = attempt_count + 1, audit_date = '', result = '',
                        risk_level = '', summary = '', result_json = '{}',
                        history_context_json = ?, source_files_json = ?, artifacts_json = '[]',
                        error_message = '', updated_at = ?, completed_at = ''
                    WHERE audit_id = ?
                    """,
                    (
                        task_id,
                        _json_dump(history_context, []),
                        _json_dump(source_files, []),
                        now,
                        audit_id,
                    ),
                )
            else:
                audit_id = _id("aud")
                connection.execute(
                    """
                    INSERT INTO audit_records(
                        audit_id, project_id, stage_id, source_task_id,
                        history_context_json, source_files_json, created_at, updated_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        stage["project_id"],
                        stage_id,
                        task_id,
                        _json_dump(history_context, []),
                        _json_dump(source_files, []),
                        now,
                        now,
                    ),
                )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                (now, stage["project_id"]),
            )
        return self.get_audit(audit_id)

    def incomplete_audits(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM audit_records
                WHERE status IN ('pending', 'running')
                ORDER BY updated_at
                """
            ).fetchall()
        return [self._audit(row) for row in rows]

    def mark_audit_running(self, audit_id: str) -> dict[str, Any]:
        current = self.get_audit(audit_id)
        if current["status"] != "pending":
            raise ValueError("只有等待中的审核记录可以开始执行。")
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE audit_records SET status = 'running', updated_at = ? WHERE audit_id = ?",
                (_now(), audit_id),
            )
        return self.get_audit(audit_id)

    def complete_audit(self, audit_id: str, data: dict[str, Any]) -> dict[str, Any]:
        current = self.get_audit(audit_id)
        if current["status"] not in {"pending", "running"}:
            raise ValueError("当前审核记录不能标记为成功。")
        now = _now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE audit_records SET status = 'success', audit_date = ?, result = ?,
                    risk_level = ?, summary = ?, result_json = ?, artifacts_json = ?,
                    error_message = '', updated_at = ?, completed_at = ?
                WHERE audit_id = ?
                """,
                (
                    _text(data.get("audit_date") or now, field="审核日期", maximum=40),
                    _text(data.get("result"), field="审核结论", maximum=120),
                    _text(data.get("risk_level"), field="风险等级", maximum=40),
                    _text(data.get("summary"), field="审核摘要", maximum=10000),
                    _json_dump(data.get("result_data"), {}),
                    _json_dump(data.get("artifacts"), []),
                    now,
                    now,
                    audit_id,
                ),
            )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                (now, current["project_id"]),
            )
        return self.get_audit(audit_id)

    def write_stage_audit(
        self,
        stage_id: str,
        data: dict[str, Any],
        *,
        source_task_id: str = "",
        overwrite: bool = False,
        source_files: list[dict[str, Any]] | None = None,
        history_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Manually write the latest reviewed result into a project stage."""
        stage = self.get_stage(stage_id)
        if stage["project_status"] != "active" or stage["status"] != "active":
            raise ValueError("已归档的项目或阶段不能写入审核记录。")
        now = _now()
        task_id = _text(source_task_id, field="来源任务ID", maximum=120)
        with self._lock, self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM audit_records WHERE stage_id = ?", (stage_id,)
            ).fetchone()
            if existing and existing["status"] in {"pending", "running"}:
                raise ValueError("该阶段已有审核任务正在进行，暂不能覆盖。")
            if existing and existing["status"] == "success" and not overwrite:
                raise ValueError("该阶段已经存在审核记录。")
            if existing:
                audit_id = existing["audit_id"]
                connection.execute(
                    """
                    UPDATE audit_records SET source_task_id = ?, status = 'success',
                        attempt_count = attempt_count + 1, audit_date = ?, result = ?,
                        risk_level = ?, summary = ?, result_json = ?,
                        history_context_json = ?, source_files_json = ?, artifacts_json = ?,
                        error_message = '', updated_at = ?, completed_at = ?
                    WHERE audit_id = ?
                    """,
                    (
                        task_id,
                        _text(data.get("audit_date") or now, field="审核日期", maximum=40),
                        _text(data.get("result"), field="审核结论", maximum=120),
                        _text(data.get("risk_level"), field="风险等级", maximum=40),
                        _text(data.get("summary"), field="审核摘要", maximum=10000),
                        _json_dump(data.get("result_data"), {}),
                        _json_dump(history_context, []),
                        _json_dump(source_files, []),
                        _json_dump(data.get("artifacts"), []),
                        now,
                        now,
                        audit_id,
                    ),
                )
            else:
                audit_id = _id("aud")
                connection.execute(
                    """
                    INSERT INTO audit_records(
                        audit_id, project_id, stage_id, source_task_id, status,
                        audit_date, result, risk_level, summary, result_json,
                        history_context_json, source_files_json, artifacts_json,
                        created_at, updated_at, completed_at
                    ) VALUES(?, ?, ?, ?, 'success', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        stage["project_id"],
                        stage_id,
                        task_id,
                        _text(data.get("audit_date") or now, field="审核日期", maximum=40),
                        _text(data.get("result"), field="审核结论", maximum=120),
                        _text(data.get("risk_level"), field="风险等级", maximum=40),
                        _text(data.get("summary"), field="审核摘要", maximum=10000),
                        _json_dump(data.get("result_data"), {}),
                        _json_dump(history_context, []),
                        _json_dump(source_files, []),
                        _json_dump(data.get("artifacts"), []),
                        now,
                        now,
                        now,
                    ),
                )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                (now, stage["project_id"]),
            )
        return self.get_audit(audit_id)

    def fail_audit(self, audit_id: str, error_message: str) -> dict[str, Any]:
        current = self.get_audit(audit_id)
        if current["status"] == "success":
            raise ValueError("已成功的审核记录不能改为失败。")
        message = _text(error_message, field="失败原因", required=True, maximum=4000)
        now = _now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE audit_records SET status = 'failed', error_message = ?,
                    updated_at = ?, completed_at = ? WHERE audit_id = ?
                """,
                (message, now, now, audit_id),
            )
        return self.get_audit(audit_id)

    def get_audit(self, audit_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM audit_records WHERE audit_id = ?", (audit_id,)
            ).fetchone()
        if row is None:
            raise KeyError("审核记录不存在。")
        return self._audit(row)

    def get_stage_audit(self, stage_id: str) -> dict[str, Any] | None:
        self.get_stage(stage_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM audit_records WHERE stage_id = ?", (stage_id,)
            ).fetchone()
        return self._audit(row) if row else None

    def previous_successful_audits(self, stage_id: str) -> list[dict[str, Any]]:
        current = self.get_stage(stage_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT a.*, s.name AS stage_name, s.stage_order
                FROM project_stages s
                JOIN audit_records a ON a.stage_id = s.stage_id AND a.status = 'success'
                WHERE s.project_id = ? AND s.status = 'active' AND s.stage_order < ?
                ORDER BY s.stage_order, s.created_at
                """,
                (current["project_id"], current["stage_order"]),
            ).fetchall()
        return [self._audit(row) for row in rows]

    def latest_successful_audit_for_project(self, project_id: str) -> dict[str, Any] | None:
        self.get_project(project_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT a.*, s.name AS stage_name, s.stage_order
                FROM project_stages s
                JOIN audit_records a ON a.stage_id = s.stage_id AND a.status = 'success'
                WHERE s.project_id = ? AND s.status = 'active'
                ORDER BY s.stage_order DESC, a.completed_at DESC, a.updated_at DESC
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()
        return self._audit(row) if row else None

    def history_context_for_stage(
        self,
        stage_id: str,
        *,
        max_stages: int = 12,
        max_findings_per_stage: int = 6,
    ) -> dict[str, Any]:
        if max_stages < 1 or max_findings_per_stage < 1:
            raise ValueError("历史阶段和问题数量限制必须大于0。")
        current = self.get_stage(stage_id)
        records = self.previous_successful_audits(stage_id)
        omitted = max(0, len(records) - max_stages)
        records = records[-max_stages:]
        previous_stages = []
        for record in records:
            result_data = record.get("result_data")
            result_data = result_data if isinstance(result_data, dict) else {}
            risk_report = (
                (result_data.get("dynamic_regulation_audit") or {}).get("risk_report") or {}
            )
            supplements = risk_report.get("required_supplements") or []
            previous_stages.append({
                "stage_id": record["stage_id"],
                "stage_name": record["stage_name"],
                "stage_order": record["stage_order"],
                "audit_date": record.get("audit_date") or record.get("completed_at"),
                "result": _clip(record.get("result"), 120),
                "risk_level": _clip(record.get("risk_level"), 20),
                "summary": _clip(record.get("summary"), 1200),
                "key_findings": _history_findings(
                    result_data, max_findings_per_stage
                ),
                "required_supplements": [
                    {
                        "field": _clip(item.get("field"), 120),
                        "reason": _clip(item.get("reason"), 300),
                    }
                    for item in supplements[:max_findings_per_stage]
                    if isinstance(item, dict)
                ],
            })
        return {
            "format_version": "project_archive_history_v1",
            "project": {
                "project_id": current["project_id"],
                "project_name": current["project_name"],
            },
            "current_stage": {
                "stage_id": current["stage_id"],
                "stage_name": current["name"],
                "stage_order": current["stage_order"],
            },
            "previous_stage_count": len(previous_stages),
            "omitted_stage_count": omitted,
            "previous_stages": previous_stages,
        }
