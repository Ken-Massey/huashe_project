from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .config import AUDIT_SESSION_DB


SESSION_STATUSES = {"draft", "reviewing", "finalized", "archived"}
MESSAGE_ROLES = {"system", "user", "assistant"}


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _json_dump(value: Any, fallback: Any) -> str:
    return json.dumps(fallback if value is None else value, ensure_ascii=False)


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback


def _text(value: Any, *, field: str, required: bool = False, maximum: int = 4000) -> str:
    result = " ".join(str(value or "").split())
    if required and not result:
        raise ValueError(f"{field}不能为空。")
    if len(result) > maximum:
        raise ValueError(f"{field}不能超过{maximum}个字符。")
    return result


class AuditSessionRepository:
    """Stores editable audit result sessions, item versions and chat messages."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or AUDIT_SESSION_DB).resolve()
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
                CREATE TABLE IF NOT EXISTS audit_session_schema (
                    schema_version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_sessions (
                    session_id TEXT PRIMARY KEY,
                    source_task_id TEXT NOT NULL DEFAULT '',
                    project_id TEXT NOT NULL DEFAULT '',
                    stage_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'draft'
                        CHECK(status IN ('draft', 'reviewing', 'finalized', 'archived')),
                    current_version INTEGER NOT NULL DEFAULT 1 CHECK(current_version >= 1),
                    latest_result_json TEXT NOT NULL DEFAULT '{}',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_review_items (
                    item_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    order_no INTEGER NOT NULL CHECK(order_no >= 1),
                    title TEXT NOT NULL DEFAULT '',
                    conclusion TEXT NOT NULL DEFAULT '',
                    risk_level TEXT NOT NULL DEFAULT '',
                    basis_json TEXT NOT NULL DEFAULT '[]',
                    recommendation TEXT NOT NULL DEFAULT '',
                    source_json TEXT NOT NULL DEFAULT '{}',
                    manual_modified INTEGER NOT NULL DEFAULT 0 CHECK(manual_modified IN (0, 1)),
                    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0, 1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES audit_sessions(session_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_audit_review_items_session
                    ON audit_review_items(session_id, is_deleted, order_no, created_at);

                CREATE TABLE IF NOT EXISTS audit_chat_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant')),
                    content TEXT NOT NULL,
                    version_no INTEGER NOT NULL DEFAULT 1 CHECK(version_no >= 1),
                    result_snapshot_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES audit_sessions(session_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_audit_chat_messages_session
                    ON audit_chat_messages(session_id, created_at);
                """
            )
            row = connection.execute("SELECT schema_version FROM audit_session_schema LIMIT 1").fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO audit_session_schema(schema_version, updated_at) VALUES(1, ?)",
                    (_now(),),
                )

    @staticmethod
    def _session(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["latest_result"] = _json_load(result.pop("latest_result_json"), {})
        result["metadata"] = _json_load(result.pop("metadata_json"), {})
        return result

    @staticmethod
    def _item(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["basis"] = _json_load(result.pop("basis_json"), [])
        result["source"] = _json_load(result.pop("source_json"), {})
        result["manual_modified"] = bool(result["manual_modified"])
        result["is_deleted"] = bool(result["is_deleted"])
        return result

    @staticmethod
    def _message(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["result_snapshot"] = _json_load(result.pop("result_snapshot_json"), {})
        return result

    def _require_session(self, connection: sqlite3.Connection, session_id: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM audit_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise KeyError("审核会话不存在。")
        return row

    def _active_items(self, connection: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT * FROM audit_review_items
            WHERE session_id = ? AND is_deleted = 0
            ORDER BY order_no, created_at
            """,
            (session_id,),
        ).fetchall()
        return [self._item(row) for row in rows]

    def _next_order(self, connection: sqlite3.Connection, session_id: str) -> int:
        value = connection.execute(
            """
            SELECT COALESCE(MAX(order_no), 0) + 1
            FROM audit_review_items
            WHERE session_id = ? AND is_deleted = 0
            """,
            (session_id,),
        ).fetchone()[0]
        return int(value or 1)

    def _renumber_items(self, connection: sqlite3.Connection, session_id: str) -> None:
        rows = connection.execute(
            """
            SELECT item_id FROM audit_review_items
            WHERE session_id = ? AND is_deleted = 0
            ORDER BY order_no, created_at
            """,
            (session_id,),
        ).fetchall()
        for index, row in enumerate(rows, start=1):
            connection.execute(
                "UPDATE audit_review_items SET order_no = ?, updated_at = ? WHERE item_id = ?",
                (index, _now(), row["item_id"]),
            )

    def _touch_session(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        *,
        increment_version: bool = True,
    ) -> dict[str, Any]:
        session = self._session(self._require_session(connection, session_id))
        version = int(session["current_version"]) + 1 if increment_version else int(session["current_version"])
        items = self._active_items(connection, session_id)
        latest = {
            "format_version": "editable_audit_result_v1",
            "version_no": version,
            "items": items,
            "overall_opinion": (session.get("metadata") or {}).get("overall_opinion") or {},
        }
        connection.execute(
            """
            UPDATE audit_sessions
            SET current_version = ?, latest_result_json = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (version, _json_dump(latest, {}), _now(), session_id),
        )
        return self.get_session(session_id, connection=connection)

    def create_session(self, data: dict[str, Any] | None = None) -> dict[str, Any]:
        data = data or {}
        status = str(data.get("status") or "draft")
        if status not in SESSION_STATUSES:
            raise ValueError("审核会话状态无效。")
        now = _now()
        session_id = _id("ses")
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_sessions(
                    session_id, source_task_id, project_id, stage_id, status,
                    current_version, latest_result_json, metadata_json,
                    created_at, updated_at
                ) VALUES(?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    _text(data.get("source_task_id"), field="任务编号", maximum=80),
                    _text(data.get("project_id"), field="项目编号", maximum=80),
                    _text(data.get("stage_id"), field="阶段编号", maximum=80),
                    status,
                    _json_dump({"format_version": "editable_audit_result_v1", "version_no": 1, "items": []}, {}),
                    _json_dump(data.get("metadata"), {}),
                    now,
                    now,
                ),
            )
            for item in data.get("items") or []:
                self._insert_item(connection, session_id, item, increment_session=False)
            session = self._touch_session(connection, session_id, increment_version=False)
            initial_message = str(data.get("initial_message") or "").strip()
            if initial_message:
                self._insert_message(
                    connection,
                    session_id,
                    {"role": "assistant", "content": initial_message},
                    increment_session=False,
                )
                session = self.get_session(session_id, connection=connection)
            return session

    def get_session(
        self,
        session_id: str,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        if connection is not None:
            session = self._session(self._require_session(connection, session_id))
            session["items"] = self._active_items(connection, session_id)
            session["messages"] = [
                self._message(row)
                for row in connection.execute(
                    """
                    SELECT * FROM audit_chat_messages
                    WHERE session_id = ?
                    ORDER BY created_at
                    """,
                    (session_id,),
                )
            ]
            return session
        with self._connect() as local:
            return self.get_session(session_id, connection=local)

    def list_items(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            self._require_session(connection, session_id)
            return self._active_items(connection, session_id)

    def _insert_item(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        data: dict[str, Any],
        *,
        increment_session: bool = True,
    ) -> dict[str, Any]:
        item_id = _id("itm")
        now = _now()
        order_no = data.get("order_no")
        if order_no in (None, ""):
            order_no = self._next_order(connection, session_id)
        connection.execute(
            """
            INSERT INTO audit_review_items(
                item_id, session_id, order_no, title, conclusion, risk_level,
                basis_json, recommendation, source_json, manual_modified,
                is_deleted, created_at, updated_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                item_id,
                session_id,
                int(order_no),
                _text(data.get("title"), field="审核主题", required=True, maximum=200),
                _text(data.get("conclusion"), field="审核结论", maximum=8000),
                _text(data.get("risk_level"), field="风险等级", maximum=40),
                _json_dump(data.get("basis"), []),
                _text(data.get("recommendation"), field="审核建议", maximum=8000),
                _json_dump(data.get("source"), {}),
                1 if data.get("manual_modified") else 0,
                now,
                now,
            ),
        )
        self._renumber_items(connection, session_id)
        if increment_session:
            self._touch_session(connection, session_id)
        return self.get_item(item_id, connection=connection)

    def create_item(self, session_id: str, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            self._require_session(connection, session_id)
            return self._insert_item(connection, session_id, data)

    def get_item(
        self,
        item_id: str,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        def select(conn: sqlite3.Connection) -> dict[str, Any]:
            row = conn.execute(
                "SELECT * FROM audit_review_items WHERE item_id = ? AND is_deleted = 0",
                (item_id,),
            ).fetchone()
            if row is None:
                raise KeyError("审核条目不存在。")
            return self._item(row)

        if connection is not None:
            return select(connection)
        with self._connect() as local:
            return select(local)

    def update_item(self, item_id: str, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            item = self.get_item(item_id, connection=connection)
            updates: dict[str, Any] = {}
            mapping = {
                "order_no": "order_no",
                "title": "title",
                "conclusion": "conclusion",
                "risk_level": "risk_level",
                "recommendation": "recommendation",
            }
            for source, column in mapping.items():
                if source in data and data[source] is not None:
                    updates[column] = data[source]
            if "basis" in data:
                updates["basis_json"] = _json_dump(data.get("basis"), [])
            if "source" in data:
                updates["source_json"] = _json_dump(data.get("source"), {})
            if not updates:
                return item
            updates["manual_modified"] = 1
            updates["updated_at"] = _now()
            assignments = ", ".join(f"{column} = ?" for column in updates)
            params = list(updates.values()) + [item_id]
            connection.execute(
                f"UPDATE audit_review_items SET {assignments} WHERE item_id = ?",
                params,
            )
            self._renumber_items(connection, item["session_id"])
            self._touch_session(connection, item["session_id"])
            return self.get_item(item_id, connection=connection)

    def delete_item(self, item_id: str) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            item = self.get_item(item_id, connection=connection)
            connection.execute(
                """
                UPDATE audit_review_items
                SET is_deleted = 1, manual_modified = 1, updated_at = ?
                WHERE item_id = ?
                """,
                (_now(), item_id),
            )
            self._renumber_items(connection, item["session_id"])
            session = self._touch_session(connection, item["session_id"])
            return {"item_id": item_id, "deleted": True, "session": session}

    def replace_items(
        self,
        session_id: str,
        items: list[dict[str, Any]],
        *,
        manual_modified: bool = True,
        overall_opinion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not items:
            raise ValueError("审核结果至少需要保留一条。")
        with self._lock, self._connect() as connection:
            self._require_session(connection, session_id)
            connection.execute(
                """
                UPDATE audit_review_items
                SET is_deleted = 1, manual_modified = 1, updated_at = ?
                WHERE session_id = ? AND is_deleted = 0
                """,
                (_now(), session_id),
            )
            for index, item in enumerate(items, start=1):
                data = dict(item)
                data["order_no"] = index
                data["manual_modified"] = manual_modified
                self._insert_item(connection, session_id, data, increment_session=False)
            if overall_opinion is not None:
                session = self._session(self._require_session(connection, session_id))
                metadata = dict(session.get("metadata") or {})
                metadata["overall_opinion"] = overall_opinion
                connection.execute(
                    """
                    UPDATE audit_sessions
                    SET metadata_json = ?, updated_at = ?
                    WHERE session_id = ?
                    """,
                    (_json_dump(metadata, {}), _now(), session_id),
                )
            self._renumber_items(connection, session_id)
            return self._touch_session(connection, session_id)

    def _insert_message(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        data: dict[str, Any],
        *,
        increment_session: bool = False,
    ) -> dict[str, Any]:
        role = str(data.get("role") or "")
        if role not in MESSAGE_ROLES:
            raise ValueError("消息角色无效。")
        session = self._session(self._require_session(connection, session_id))
        message_id = _id("msg")
        snapshot = data.get("result_snapshot")
        if snapshot is None:
            snapshot = session.get("latest_result", {})
        connection.execute(
            """
            INSERT INTO audit_chat_messages(
                message_id, session_id, role, content, version_no,
                result_snapshot_json, created_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                session_id,
                role,
                _text(data.get("content"), field="消息内容", required=True, maximum=12000),
                int(data.get("version_no") or session["current_version"]),
                _json_dump(snapshot, {}),
                _now(),
            ),
        )
        if increment_session:
            self._touch_session(connection, session_id, increment_version=False)
        return self.get_message(message_id, connection=connection)

    def add_message(self, session_id: str, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            self._require_session(connection, session_id)
            return self._insert_message(connection, session_id, data)

    def get_message(
        self,
        message_id: str,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        def select(conn: sqlite3.Connection) -> dict[str, Any]:
            row = conn.execute(
                "SELECT * FROM audit_chat_messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()
            if row is None:
                raise KeyError("消息不存在。")
            return self._message(row)

        if connection is not None:
            return select(connection)
        with self._connect() as local:
            return select(local)

    def list_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            self._require_session(connection, session_id)
            return [
                self._message(row)
                for row in connection.execute(
                    """
                    SELECT * FROM audit_chat_messages
                    WHERE session_id = ?
                    ORDER BY created_at
                    """,
                    (session_id,),
                )
            ]
