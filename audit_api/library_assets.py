from __future__ import annotations

import mimetypes
import re
import shutil
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from .config import KNOWLEDGE_ROOT


LibraryType = Literal["regulation", "case", "reply"]


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _clean_name(value: str, fallback: str) -> str:
    name = re.sub(r"\s+", " ", (value or "").strip()) or fallback
    if len(name) > 180:
        raise ValueError("文件名称不能超过180个字符。")
    return name


def _file_kind(suffix: str) -> str:
    groups = {
        "pdf": {".pdf"},
        "word": {".doc", ".docx"},
        "cad": {".dwg", ".dxf", ".dwt"},
        "bim": {".rvt", ".ifc"},
        "spreadsheet": {".xls", ".xlsx", ".csv"},
        "presentation": {".ppt", ".pptx"},
        "image": {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"},
        "archive": {".zip", ".rar", ".7z"},
        "text": {".txt", ".md"},
    }
    for kind, suffixes in groups.items():
        if suffix in suffixes:
            return kind
    return "other"


class LibraryAssetRepository:
    """Stores ordinary knowledge-library files that are not parsed knowledge records."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or KNOWLEDGE_ROOT / "assets").resolve()
        self.db_path = KNOWLEDGE_ROOT / "library_assets.sqlite3"
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS library_asset (
                    asset_id TEXT PRIMARY KEY,
                    library_type TEXT NOT NULL CHECK(library_type IN ('regulation','case','reply')),
                    folder_id TEXT,
                    display_name TEXT NOT NULL,
                    original_file_name TEXT NOT NULL,
                    stored_file TEXT NOT NULL,
                    suffix TEXT NOT NULL,
                    file_kind TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_library_asset_type_folder
                    ON library_asset(library_type, folder_id);
                CREATE INDEX IF NOT EXISTS idx_library_asset_name
                    ON library_asset(display_name);
                """
            )

    def _ensure_reply_type_supported(self) -> None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='library_asset'"
            ).fetchone()
            sql = str(row["sql"] if row else "")
            if "'reply'" in sql:
                return
            connection.executescript(
                """
                PRAGMA foreign_keys=OFF;
                CREATE TABLE IF NOT EXISTS library_asset_new (
                    asset_id TEXT PRIMARY KEY,
                    library_type TEXT NOT NULL CHECK(library_type IN ('regulation','case','reply')),
                    folder_id TEXT,
                    display_name TEXT NOT NULL,
                    original_file_name TEXT NOT NULL,
                    stored_file TEXT NOT NULL,
                    suffix TEXT NOT NULL,
                    file_kind TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                INSERT INTO library_asset_new SELECT * FROM library_asset;
                DROP TABLE library_asset;
                ALTER TABLE library_asset_new RENAME TO library_asset;
                CREATE INDEX IF NOT EXISTS idx_library_asset_type_folder
                    ON library_asset(library_type, folder_id);
                CREATE INDEX IF NOT EXISTS idx_library_asset_name
                    ON library_asset(display_name);
                PRAGMA foreign_keys=ON;
                """
            )

    def _validate_type(self, library_type: str) -> LibraryType:
        if library_type not in {"regulation", "case", "reply"}:
            raise ValueError("library_type必须是regulation、case或reply。")
        if library_type == "reply":
            self._ensure_reply_type_supported()
        return library_type  # type: ignore[return-value]

    def add(
        self,
        source: Path,
        library_type: str,
        folder_id: str | None = None,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        library_type = self._validate_type(library_type)
        if not source.is_file():
            raise FileNotFoundError(source)
        original_name = source.name
        clean_name = _clean_name(display_name or "", original_name)
        suffix = source.suffix.lower()
        asset_id = "KA-" + uuid.uuid4().hex[:16].upper()
        destination_dir = self.root / library_type / asset_id
        destination_dir.mkdir(parents=True, exist_ok=False)
        destination = destination_dir / original_name
        try:
            shutil.copy2(source, destination)
            now = _now()
            with self.lock, self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO library_asset(
                        asset_id,library_type,folder_id,display_name,original_file_name,
                        stored_file,suffix,file_kind,media_type,file_size,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        asset_id,
                        library_type,
                        folder_id or None,
                        clean_name,
                        original_name,
                        str(destination),
                        suffix,
                        _file_kind(suffix),
                        mimetypes.guess_type(original_name)[0] or "application/octet-stream",
                        destination.stat().st_size,
                        now,
                        now,
                    ),
                )
        except Exception:
            shutil.rmtree(destination_dir, ignore_errors=True)
            raise
        return self.get(asset_id)

    def get(self, asset_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM library_asset WHERE asset_id=?", (asset_id,)
            ).fetchone()
        if not row:
            raise KeyError(asset_id)
        return dict(row)

    def list(
        self,
        library_type: str,
        folder_id: str | None = None,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        library_type = self._validate_type(library_type)
        sql = "SELECT * FROM library_asset WHERE library_type=?"
        params: list[Any] = [library_type]
        if folder_id == "__uncategorized__":
            sql += " AND folder_id IS NULL"
        elif folder_id:
            sql += " AND folder_id=?"
            params.append(folder_id)
        if keyword:
            sql += " AND (display_name LIKE ? OR original_file_name LIKE ?)"
            pattern = f"%{keyword.strip()}%"
            params.extend([pattern, pattern])
        sql += " ORDER BY updated_at DESC, display_name"
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(sql, params)]

    def rename(self, asset_id: str, display_name: str) -> dict[str, Any]:
        item = self.get(asset_id)
        clean_name = _clean_name(display_name, item["original_file_name"])
        with self.lock, self._connect() as connection:
            connection.execute(
                "UPDATE library_asset SET display_name=?,updated_at=? WHERE asset_id=?",
                (clean_name, _now(), asset_id),
            )
        return self.get(asset_id)

    def move(self, asset_id: str, folder_id: str | None) -> dict[str, Any]:
        self.get(asset_id)
        with self.lock, self._connect() as connection:
            connection.execute(
                "UPDATE library_asset SET folder_id=?,updated_at=? WHERE asset_id=?",
                (folder_id or None, _now(), asset_id),
            )
        return self.get(asset_id)

    def detach_folder(
        self,
        library_type: str,
        folder_id: str,
        target_folder_id: str | None = None,
    ) -> int:
        library_type = self._validate_type(library_type)
        with self.lock, self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE library_asset SET folder_id=?,updated_at=?
                WHERE library_type=? AND folder_id=?
                """,
                (target_folder_id, _now(), library_type, folder_id),
            )
            return int(cursor.rowcount or 0)

    def folder_counts(self, library_type: str) -> dict[str, int]:
        library_type = self._validate_type(library_type)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT folder_id,COUNT(*) count FROM library_asset
                WHERE library_type=? AND folder_id IS NOT NULL GROUP BY folder_id
                """,
                (library_type,),
            )
        return {str(row["folder_id"]): int(row["count"]) for row in rows}

    def delete(self, asset_id: str) -> dict[str, Any]:
        item = self.get(asset_id)
        with self.lock, self._connect() as connection:
            connection.execute("DELETE FROM library_asset WHERE asset_id=?", (asset_id,))
        stored = Path(item["stored_file"]).resolve()
        asset_dir = stored.parent
        try:
            asset_dir.relative_to(self.root)
        except ValueError:
            return item
        shutil.rmtree(asset_dir, ignore_errors=True)
        return item
