"""Upgrade persisted audit-session overall opinions to the current template.

This maintenance command changes only ``metadata.overall_opinion`` and the
derived latest-result snapshot.  It never rewrites review items or historical
chat messages.

Run from the repository root:
    .venv\\Scripts\\python.exe -m audit_api.migrate_overall_opinions
"""

from __future__ import annotations

from .main import _refresh_session_overall_opinion, audit_sessions


def migrate(limit: int = 100000) -> tuple[int, int]:
    """Return ``(scanned, upgraded)`` for all persisted audit sessions."""
    scanned = 0
    upgraded = 0
    for session_id in audit_sessions.list_session_ids(limit=limit):
        session = audit_sessions.get_session(session_id)
        version_before = int(session.get("current_version") or 0)
        refreshed = _refresh_session_overall_opinion(session)
        scanned += 1
        if int(refreshed.get("current_version") or 0) > version_before:
            upgraded += 1
    return scanned, upgraded


if __name__ == "__main__":
    scanned_count, upgraded_count = migrate()
    print(f"审核会话综合评价迁移完成：检查 {scanned_count} 条，升级 {upgraded_count} 条。")
