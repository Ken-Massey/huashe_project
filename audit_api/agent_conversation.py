from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from .config import AGENT_CHAT_DB


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


class AgentConversationRepository:
    """Persistent chat sessions for the AI assistant page."""

    def __init__(self, database: Path = AGENT_CHAT_DB) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_chat_session (
                    session_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'general',
                    message_count INTEGER NOT NULL DEFAULT 0,
                    archived INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_message_at TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_chat_message (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model TEXT NOT NULL DEFAULT '',
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    usage_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES agent_chat_session(session_id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_session_owner_time ON agent_chat_session(owner_id, archived, updated_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_message_session_time ON agent_chat_message(session_id, created_at)"
            )

    def create(self, owner_id: str, title: str = "", mode: str = "general") -> dict[str, Any]:
        session_id = "chat_" + uuid.uuid4().hex[:20]
        now = _now()
        clean_title = (title or "").strip() or "新对话"
        clean_mode = mode if mode in {"general", "knowledge"} else "general"
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_chat_session (
                    session_id, owner_id, title, mode, message_count, archived,
                    created_at, updated_at, last_message_at
                ) VALUES (?, ?, ?, ?, 0, 0, ?, ?, NULL)
                """,
                (session_id, owner_id or "anonymous", clean_title, clean_mode, now, now),
            )
        value = self.get(owner_id, session_id)
        value["messages"] = []
        return value

    def list(self, owner_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM agent_chat_session
                WHERE owner_id = ? AND archived = 0
                ORDER BY COALESCE(last_message_at, updated_at) DESC, created_at DESC
                LIMIT ?
                """,
                (owner_id or "anonymous", int(limit)),
            ).fetchall()
        return [self._session(row) for row in rows]

    def get(self, owner_id: str, session_id: str, include_messages: bool = True) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM agent_chat_session
                WHERE owner_id = ? AND session_id = ? AND archived = 0
                """,
                (owner_id or "anonymous", session_id),
            ).fetchone()
            if row is None:
                raise KeyError(session_id)
            session = self._session(row)
            if include_messages:
                rows = connection.execute(
                    """
                    SELECT * FROM agent_chat_message
                    WHERE session_id = ?
                    ORDER BY created_at ASC, rowid ASC
                    """,
                    (session_id,),
                ).fetchall()
                session["messages"] = [self._message(item) for item in rows]
        return session

    def add_message(
        self,
        owner_id: str,
        session_id: str,
        role: str,
        content: str,
        *,
        model: str = "",
        sources: list[dict[str, Any]] | None = None,
        usage: dict[str, Any] | None = None,
        mode: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        if role not in {"user", "assistant"}:
            raise ValueError("消息角色不正确。")
        now = _now()
        message_id = "msg_" + uuid.uuid4().hex[:24]
        with self._connect() as connection:
            session = connection.execute(
                """
                SELECT * FROM agent_chat_session
                WHERE owner_id = ? AND session_id = ? AND archived = 0
                """,
                (owner_id or "anonymous", session_id),
            ).fetchone()
            if session is None:
                raise KeyError(session_id)
            session_title = session["title"]
            if title:
                session_title = " ".join(title.strip().split())[:80] or session_title
            clean_mode = mode if mode in {"general", "knowledge"} else session["mode"]
            connection.execute(
                """
                INSERT INTO agent_chat_message (
                    message_id, session_id, role, content, model, sources_json, usage_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    model or "",
                    json.dumps(sources or [], ensure_ascii=False),
                    json.dumps(usage or {}, ensure_ascii=False),
                    now,
                ),
            )
            connection.execute(
                """
                UPDATE agent_chat_session
                SET title = ?, mode = ?, message_count = message_count + 1,
                    updated_at = ?, last_message_at = ?
                WHERE session_id = ?
                """,
                (session_title, clean_mode, now, now, session_id),
            )
        return self.get(owner_id, session_id)

    def rename(self, owner_id: str, session_id: str, title: str) -> dict[str, Any]:
        clean_title = (title or "").strip()
        if not clean_title:
            raise ValueError("会话名称不能为空。")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE agent_chat_session
                SET title = ?, updated_at = ?
                WHERE owner_id = ? AND session_id = ? AND archived = 0
                """,
                (clean_title[:80], _now(), owner_id or "anonymous", session_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(session_id)
        return self.get(owner_id, session_id, include_messages=False)

    def archive(self, owner_id: str, session_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE agent_chat_session
                SET archived = 1, updated_at = ?
                WHERE owner_id = ? AND session_id = ? AND archived = 0
                """,
                (_now(), owner_id or "anonymous", session_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(session_id)
        return {"session_id": session_id, "deleted": True}

    def _session(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "session_id": row["session_id"],
            "title": row["title"],
            "mode": row["mode"],
            "message_count": row["message_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_message_at": row["last_message_at"],
        }

    def _message(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "message_id": row["message_id"],
            "role": row["role"],
            "content": row["content"],
            "model": row["model"],
            "sources": _json_load(row["sources_json"], []),
            "usage": _json_load(row["usage_json"], {}),
            "created_at": row["created_at"],
        }
