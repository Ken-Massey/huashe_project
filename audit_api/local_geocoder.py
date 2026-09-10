from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


NANJING_VIEWBOX = "118.33,32.63,119.92,30.23"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class LocalGeocoder:
    """Small cached client for an organisation-hosted Nominatim-compatible API."""

    def __init__(self, database: Path, endpoint: str, timeout_seconds: float = 8.0):
        self.database = database
        self.endpoint = endpoint.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._lock = threading.RLock()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._session() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS geocode_cache (
                    query TEXT PRIMARY KEY,
                    response_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def status(self) -> dict[str, Any]:
        with self._session() as connection:
            cached_count = int(connection.execute("SELECT COUNT(*) FROM geocode_cache").fetchone()[0])
        return {
            "provider": "local_nominatim",
            "configured": bool(self.endpoint),
            "endpoint": self.endpoint,
            "coverage": "南京市行政区域",
            "coordinate_system": "WGS84",
            "cached_queries": cached_count,
        }

    def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        normalized = " ".join(str(query or "").split())
        if not normalized:
            return []
        limit = max(1, min(int(limit or 8), 12))
        cache_key = normalized.casefold()
        with self._session() as connection:
            cached = connection.execute(
                "SELECT response_json FROM geocode_cache WHERE query = ?", (cache_key,)
            ).fetchone()
        if cached:
            cached_rows = json.loads(cached["response_json"])
            # An empty response may have been produced while the local Nominatim
            # container was restarting. Do not make that transient failure a
            # permanent "not found" result.
            if cached_rows:
                return cached_rows[:limit]
        if not self.endpoint:
            raise RuntimeError("本地南京地理编码服务尚未配置。")
        params = {
            "q": normalized,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": limit,
            "countrycodes": "cn",
            "viewbox": NANJING_VIEWBOX,
            "bounded": 1,
        }
        url = f"{self.endpoint}/search?{urlencode(params)}"
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "HuasheRailAudit/1.0"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network failures depend on deployment
            raise RuntimeError("本地南京地理编码服务不可用。") from exc
        rows: list[dict[str, Any]] = []
        for item in payload if isinstance(payload, list) else []:
            try:
                longitude, latitude = float(item["lon"]), float(item["lat"])
            except (KeyError, TypeError, ValueError):
                continue
            address = item.get("address") if isinstance(item.get("address"), dict) else {}
            name = str(item.get("name") or address.get("road") or item.get("display_name") or normalized).strip()
            display_name = str(item.get("display_name") or name).strip()
            rows.append({
                "name": name,
                "address": display_name,
                "value": f"{name}（{display_name}）" if display_name != name else name,
                "longitude": longitude,
                "latitude": latitude,
                "coordinate_system": "WGS84",
            })
        with self._lock, self._session() as connection:
            if rows:
                connection.execute(
                    "INSERT OR REPLACE INTO geocode_cache(query, response_json, updated_at) VALUES(?, ?, ?)",
                    (cache_key, json.dumps(rows, ensure_ascii=False), _now()),
                )
            else:
                # Keep the cache useful for positive results only. A later OSM
                # data refresh may add this POI, so empty results must be retried.
                connection.execute("DELETE FROM geocode_cache WHERE query = ?", (cache_key,))
        return rows
