"""Metro segment reference database and location-based matching."""

from __future__ import annotations

import csv
import math
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_DATABASE_FILE = Path(__file__).resolve().parent / "data" / "metro_segments.sqlite3"

SEGMENT_FIELDS = (
    "line_name",
    "section_name",
    "structure_method",
    "structure_category",
    "structure_condition",
    "buried_depth_m",
    "longitude",
    "latitude",
    "source_project",
    "source_file",
    "notes",
)


@contextmanager
def _connect(database_file: str | Path):
    path = Path(database_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_segment_database(database_file: str | Path = DEFAULT_DATABASE_FILE) -> Path:
    """Create the segment table without inserting guessed reference records."""
    path = Path(database_file)
    with _connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metro_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_name TEXT NOT NULL,
                section_name TEXT NOT NULL,
                structure_method TEXT NOT NULL,
                structure_category TEXT NOT NULL,
                structure_condition TEXT NOT NULL,
                buried_depth_m REAL,
                longitude REAL NOT NULL CHECK(longitude BETWEEN -180 AND 180),
                latitude REAL NOT NULL CHECK(latitude BETWEEN -90 AND 90),
                source_project TEXT,
                source_file TEXT,
                notes TEXT,
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(line_name, section_name, longitude, latitude)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_metro_segments_line ON metro_segments(line_name)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_metro_segments_active ON metro_segments(active)"
        )
    return path


def _clean_segment(values: dict[str, Any]) -> dict[str, Any]:
    required_text = (
        "line_name",
        "section_name",
        "structure_method",
        "structure_category",
        "structure_condition",
    )
    cleaned: dict[str, Any] = {}
    for name in required_text:
        value = str(values.get(name) or "").strip()
        if not value:
            raise ValueError(f"{name} 不能为空。")
        cleaned[name] = value

    for name, lower, upper in (
        ("longitude", -180.0, 180.0),
        ("latitude", -90.0, 90.0),
    ):
        try:
            number = float(values.get(name))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} 必须是数字。") from exc
        if not lower <= number <= upper:
            raise ValueError(f"{name} 必须位于 {lower} 至 {upper} 之间。")
        cleaned[name] = number

    buried_depth = values.get("buried_depth_m")
    if buried_depth in (None, ""):
        cleaned["buried_depth_m"] = None
    else:
        try:
            cleaned["buried_depth_m"] = float(buried_depth)
        except (TypeError, ValueError) as exc:
            raise ValueError("buried_depth_m 必须是数字。") from exc
        if cleaned["buried_depth_m"] < 0:
            raise ValueError("buried_depth_m 不能小于 0。")

    for name in ("source_project", "source_file", "notes"):
        text = str(values.get(name) or "").strip()
        cleaned[name] = text or None
    return cleaned


def save_segment(
    values: dict[str, Any],
    database_file: str | Path = DEFAULT_DATABASE_FILE,
    *,
    segment_id: int | None = None,
) -> int:
    """Insert a segment or update the selected record."""
    initialize_segment_database(database_file)
    cleaned = _clean_segment(values)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(database_file) as connection:
        if segment_id is None:
            columns = ", ".join(SEGMENT_FIELDS)
            placeholders = ", ".join("?" for _ in SEGMENT_FIELDS)
            cursor = connection.execute(
                f"INSERT INTO metro_segments ({columns}, created_at, updated_at) "
                f"VALUES ({placeholders}, ?, ?)",
                [cleaned[name] for name in SEGMENT_FIELDS] + [now, now],
            )
            return int(cursor.lastrowid)

        assignments = ", ".join(f"{name} = ?" for name in SEGMENT_FIELDS)
        cursor = connection.execute(
            f"UPDATE metro_segments SET {assignments}, updated_at = ? WHERE id = ?",
            [cleaned[name] for name in SEGMENT_FIELDS] + [now, int(segment_id)],
        )
        if cursor.rowcount != 1:
            raise KeyError(f"未找到区段记录 {segment_id}。")
        return int(segment_id)


def list_segments(
    database_file: str | Path = DEFAULT_DATABASE_FILE,
    *,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    initialize_segment_database(database_file)
    where = "" if include_inactive else "WHERE active = 1"
    with _connect(database_file) as connection:
        rows = connection.execute(
            f"SELECT * FROM metro_segments {where} ORDER BY line_name, section_name, id"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_segment(segment_id: int, database_file: str | Path = DEFAULT_DATABASE_FILE) -> bool:
    """Soft-delete a record so prior audit provenance remains meaningful."""
    initialize_segment_database(database_file)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(database_file) as connection:
        cursor = connection.execute(
            "UPDATE metro_segments SET active = 0, updated_at = ? WHERE id = ? AND active = 1",
            (now, int(segment_id)),
        )
    return cursor.rowcount == 1


def haversine_distance_m(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return great-circle distance in metres between two WGS84 coordinates."""
    radius_m = 6_371_008.8
    lat1, lat2 = math.radians(latitude_a), math.radians(latitude_b)
    delta_lat = math.radians(latitude_b - latitude_a)
    delta_lon = math.radians(longitude_b - longitude_a)
    hav = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * radius_m * math.asin(math.sqrt(hav))


def find_nearby_segments(
    latitude: float,
    longitude: float,
    database_file: str | Path = DEFAULT_DATABASE_FILE,
    *,
    line_name: str | None = None,
    max_distance_m: float = 2_000.0,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Rank active reference points by line agreement and geographic distance."""
    if not -90 <= float(latitude) <= 90 or not -180 <= float(longitude) <= 180:
        raise ValueError("经纬度超出有效范围。")
    if max_distance_m <= 0 or limit <= 0:
        raise ValueError("搜索半径和返回数量必须大于 0。")

    expected_line = (line_name or "").strip().casefold()
    candidates: list[dict[str, Any]] = []
    for segment in list_segments(database_file):
        distance = haversine_distance_m(
            float(latitude),
            float(longitude),
            float(segment["latitude"]),
            float(segment["longitude"]),
        )
        if distance > max_distance_m:
            continue
        line_match = bool(expected_line) and str(segment["line_name"]).strip().casefold() == expected_line
        distance_score = max(0.0, 1.0 - distance / max_distance_m)
        # Location dominates. An explicitly matching line resolves close alternatives.
        match_score = 0.85 * distance_score + 0.15 * (1.0 if line_match else 0.0)
        item = dict(segment)
        item.update({
            "distance_m": round(distance, 2),
            "line_match": line_match,
            "match_score": round(match_score, 4),
        })
        candidates.append(item)
    candidates.sort(key=lambda item: (-item["match_score"], item["distance_m"], item["id"]))
    return candidates[:limit]


def build_autofill_suggestion(segment: dict[str, Any]) -> dict[str, Any]:
    """Build traceable values that still require explicit user confirmation."""
    return {
        "metro_line_name": segment["line_name"],
        "metro_section_name": segment["section_name"],
        "structure_method": segment["structure_method"],
        "structure_category": segment["structure_category"],
        "structure_condition": segment["structure_condition"],
        "buried_depth_m": segment.get("buried_depth_m"),
        "autofill_source": {
            "source_type": "segment_database",
            "source_id": str(segment["id"]),
            "source_name": f"{segment['line_name']} / {segment['section_name']}",
            "distance_m": segment.get("distance_m"),
            "confidence": segment.get("match_score"),
            "confirmed_by_user": False,
        },
    }


def import_segments_csv(
    csv_file: str | Path,
    database_file: str | Path = DEFAULT_DATABASE_FILE,
) -> dict[str, Any]:
    """Import UTF-8 CSV records and report failures without hiding bad rows."""
    imported_ids: list[int] = []
    errors: list[dict[str, Any]] = []
    with Path(csv_file).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in SEGMENT_FIELDS[:8] if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("CSV 缺少必需列：" + "、".join(missing))
        for row_number, row in enumerate(reader, start=2):
            try:
                imported_ids.append(save_segment(row, database_file))
            except Exception as exc:
                errors.append({"row": row_number, "error": str(exc)})
    return {"imported_count": len(imported_ids), "imported_ids": imported_ids, "errors": errors}


def export_segments_csv(
    csv_file: str | Path,
    segments: Iterable[dict[str, Any]],
) -> Path:
    path = Path(csv_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SEGMENT_FIELDS), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(segments)
    return path
