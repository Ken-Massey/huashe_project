from __future__ import annotations

import os
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(os.getenv("AUDIT_API_RUNTIME", Path(__file__).resolve().parent / "runtime")).resolve()


def _load_private_environment(path: Path) -> None:
    """Load local secrets without adding another runtime dependency."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


_load_private_environment(RUNTIME_ROOT / "secrets" / "mineru.env")

UPLOAD_ROOT = RUNTIME_ROOT / "uploads"
RESULT_ROOT = RUNTIME_ROOT / "results"
TASK_ROOT = RUNTIME_ROOT / "tasks"
KNOWLEDGE_ROOT = RUNTIME_ROOT / "knowledge"
KNOWLEDGE_FILE_ROOT = KNOWLEDGE_ROOT / "files"
KNOWLEDGE_DB = KNOWLEDGE_ROOT / "knowledge.sqlite3"
REGULATION_DB = KNOWLEDGE_ROOT / "regulations.sqlite3"
REGULATION_FILE_ROOT = KNOWLEDGE_ROOT / "regulations"
PROJECT_ARCHIVE_ROOT = RUNTIME_ROOT / "project_archive"
PROJECT_ARCHIVE_DB = PROJECT_ARCHIVE_ROOT / "project_archive.sqlite3"
AUDIT_SESSION_ROOT = RUNTIME_ROOT / "audit_sessions"
AUDIT_SESSION_DB = AUDIT_SESSION_ROOT / "audit_sessions.sqlite3"
CASE_ADVICE_DATABASE = Path(
    os.getenv("CASE_ADVICE_DATABASE", WORKSPACE_ROOT / "deepke_case_extract" / "data" / "case_advice_database.json")
).resolve()
STAGE1_DATABASE = Path(
    os.getenv("STAGE1_HISTORY_DATABASE", WORKSPACE_ROOT / "stage1_reply_system" / "data" / "history_replies.sqlite3")
).resolve()
DEEPKE_PYTHON = os.getenv("DEEPKE_PYTHON") or None
SERVICE_TOKEN = os.getenv("AUDIT_API_TOKEN", "")
MAX_UPLOAD_BYTES = int(os.getenv("AUDIT_API_MAX_UPLOAD_BYTES", str(200 * 1024 * 1024)))
MAX_WORKERS = max(1, int(os.getenv("AUDIT_API_MAX_WORKERS", "2")))
MINERU_API_TOKEN = os.getenv("MINERU_API_TOKEN", "")
MINERU_API_BASE_URL = os.getenv("MINERU_API_BASE_URL", "https://mineru.net/api/v4").rstrip("/")
MINERU_PARSER_MODE = os.getenv("MINERU_PARSER_MODE", "auto").strip().lower()
MINERU_MODEL_VERSION = os.getenv("MINERU_MODEL_VERSION", "vlm").strip()
MINERU_POLL_SECONDS = max(1.0, float(os.getenv("MINERU_POLL_SECONDS", "3")))
MINERU_TASK_TIMEOUT_SECONDS = max(60, int(os.getenv("MINERU_TASK_TIMEOUT_SECONDS", "1800")))
MINERU_CACHE_ROOT = Path(os.getenv("MINERU_CACHE_ROOT", RUNTIME_ROOT / "mineru_cache")).resolve()
MINERU_ALLOW_LEGACY_OCR = os.getenv("MINERU_ALLOW_LEGACY_OCR", "false").strip().lower() in {"1", "true", "yes"}

for folder in (
    RUNTIME_ROOT, UPLOAD_ROOT, RESULT_ROOT, TASK_ROOT, KNOWLEDGE_ROOT,
    KNOWLEDGE_FILE_ROOT, REGULATION_FILE_ROOT, PROJECT_ARCHIVE_ROOT, AUDIT_SESSION_ROOT,
    MINERU_CACHE_ROOT,
):
    folder.mkdir(parents=True, exist_ok=True)
