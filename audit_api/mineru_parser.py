from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

import requests
from pypdf import PdfReader, PdfWriter

from .config import (
    MINERU_API_BASE_URL,
    MINERU_API_TOKEN,
    MINERU_CACHE_ROOT,
    MINERU_MODEL_VERSION,
    MINERU_PARSER_MODE,
    MINERU_POLL_SECONDS,
    MINERU_TASK_TIMEOUT_SECONDS,
)


Progress = Callable[[str], None]
_CACHE_LOCKS: dict[str, threading.Lock] = {}
_CACHE_LOCKS_GUARD = threading.Lock()


class MinerUError(RuntimeError):
    pass


def _cache_lock(digest: str) -> threading.Lock:
    with _CACHE_LOCKS_GUARD:
        return _CACHE_LOCKS.setdefault(digest, threading.Lock())


def _write_json_atomic(path: Path, payload: Any, *, indent: int | None = None) -> None:
    temporary = path.with_name(f"{path.name}.{threading.get_ident()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )
    temporary.replace(path)


def _publish_extracted_best_effort(
    temporary: Path,
    extracted: Path,
    progress: Progress,
) -> bool:
    try:
        if extracted.exists():
            shutil.rmtree(extracted)
        temporary.replace(extracted)
        return True
    except OSError:
        progress("MinerU正文结果已保存；解析预览目录正被Windows占用，已跳过目录缓存发布")
        shutil.rmtree(temporary, ignore_errors=True)
        return False


def _current_private_settings() -> dict[str, str]:
    path = MINERU_CACHE_ROOT.parent / "secrets" / "mineru.env"
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip("\"'")
    return values


def _current_token() -> str:
    return _current_private_settings().get("MINERU_API_TOKEN") or MINERU_API_TOKEN


def mineru_cloud_available() -> bool:
    mode = _current_private_settings().get("MINERU_PARSER_MODE", MINERU_PARSER_MODE).lower()
    return mode in {"auto", "cloud"} and bool(_current_token())


def mineru_cache_available(source: Path) -> bool:
    source = Path(source).resolve()
    if not source.exists():
        return False
    cache = MINERU_CACHE_ROOT / _digest(source)
    return (cache / "complete.json").exists() and (cache / "rows.json").exists()


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _response_json(response: requests.Response, operation: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise MinerUError(f"MinerU{operation}返回了无法解析的响应（HTTP {response.status_code}）。") from exc
    if response.status_code != 200 or payload.get("code") != 0:
        message = payload.get("msg") or payload.get("message") or f"HTTP {response.status_code}"
        raise MinerUError(f"MinerU{operation}失败：{message}")
    return payload


def _safe_extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as package:
        for member in package.infolist():
            target = (destination / member.filename).resolve()
            if destination != target and destination not in target.parents:
                raise MinerUError("MinerU结果压缩包包含不安全路径，已拒绝解压。")
        package.extractall(destination)


def _download_with_retry(url: str, destination: Path, progress: Progress, label: str) -> None:
    temporary = destination.with_suffix(destination.suffix + ".download")
    last_error: Exception | None = None
    parsed = urlsplit(url)
    urls = [url]
    if parsed.hostname == "cdn-mineru.openxlab.org.cn":
        urls.append(urlunsplit((
            parsed.scheme,
            "mineru.oss-cn-shanghai.aliyuncs.com",
            parsed.path,
            parsed.query,
            parsed.fragment,
        )))
    for attempt in range(1, 7):
        candidate = urls[(attempt - 1) % len(urls)]
        try:
            with requests.get(candidate, stream=True, timeout=(30, 600)) as download:
                download.raise_for_status()
                with temporary.open("wb") as stream:
                    for block in download.iter_content(1024 * 1024):
                        if block:
                            stream.write(block)
            temporary.replace(destination)
            return
        except requests.RequestException as exc:
            last_error = exc
            if attempt >= 6:
                break
            delay = min(30, 2 ** attempt)
            route = "OSS源站" if urls[(attempt) % len(urls)] != url else "CDN"
            progress(f"{label}下载连接中断，{delay}秒后切换{route}重试")
            time.sleep(delay)
    raise MinerUError(f"{label}下载失败，已自动重试6次。") from last_error


def _content_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        item_type = str(item.get("type") or "")
        page = item.get("page_idx")
        page = page + 1 if isinstance(page, int) else None
        if item_type in {"header", "footer", "page_number", "aside_text", "page_footnote"}:
            continue
        if item_type == "table":
            caption = " ".join(_clean_text(value) for value in item.get("table_caption") or [] if _clean_text(value))
            table = str(item.get("table_body") or item.get("content") or "").strip()
            if caption:
                rows.append({"page": page, "text": caption, "content_type": "paragraph"})
            if table:
                rows.append({"page": page, "text": table, "content_type": "table"})
            continue
        if item_type == "list":
            for value in item.get("list_items") or []:
                text = _clean_text(value)
                if text:
                    rows.append({"page": page, "text": text, "content_type": "paragraph"})
            continue
        text = _clean_text(item.get("text"))
        if not text:
            continue
        level = item.get("text_level")
        if item_type == "text" and isinstance(level, int) and level > 0:
            text = f"{'#' * min(level, 6)} {text}"
        rows.append({
            "page": page,
            "text": text,
            "content_type": "equation" if item_type == "equation" else "paragraph",
        })
    return rows


def _rows_from_result(folder: Path) -> list[dict[str, Any]]:
    candidates = [
        path for path in folder.rglob("*_content_list.json")
        if not path.name.endswith("_content_list_v2.json")
    ]
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, list):
            rows = _content_rows(payload)
            if rows:
                return rows
    markdown_files = sorted(folder.rglob("full.md")) or sorted(folder.rglob("*.md"))
    for path in markdown_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rows = [
            {"page": None, "text": line.strip(), "content_type": "paragraph"}
            for line in text.splitlines() if line.strip()
        ]
        if rows:
            return rows
    raise MinerUError("MinerU结果中未找到可用的Markdown或content_list.json。")


def _pdf_parts(source: Path, cache: Path, pages_per_part: int = 180) -> list[dict[str, Any]]:
    try:
        reader = PdfReader(str(source), strict=False)
        page_count = len(reader.pages)
    except Exception as exc:
        raise MinerUError("无法读取PDF页数，不能提交MinerU解析。") from exc
    if page_count <= pages_per_part:
        return [{"path": source, "page_offset": 0, "page_count": page_count}]

    part_root = cache / "input_parts"
    part_root.mkdir(parents=True, exist_ok=True)
    parts = []
    for part_index, start in enumerate(range(0, page_count, pages_per_part), start=1):
        stop = min(start + pages_per_part, page_count)
        part_path = part_root / f"{source.stem}.part{part_index:03d}.pdf"
        if not part_path.exists():
            writer = PdfWriter()
            for page_index in range(start, stop):
                writer.add_page(reader.pages[page_index])
            with part_path.open("wb") as stream:
                writer.write(stream)
        parts.append({"path": part_path, "page_offset": start, "page_count": stop - start})
    return parts


def _recover_rows_from_temporary(
    source: Path,
    cache: Path,
    temporary: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    parts = _pdf_parts(source, cache)
    rows: list[dict[str, Any]] = []
    for index, part in enumerate(parts, start=1):
        part_output = temporary / f"part{index:03d}"
        if not part_output.exists():
            return None
        try:
            part_rows = _rows_from_result(part_output)
        except MinerUError:
            return None
        for row in part_rows:
            if isinstance(row.get("page"), int):
                row["page"] += part["page_offset"]
        rows.extend(part_rows)
    return rows, parts


class MinerUCloudParser:
    def __init__(self) -> None:
        if not mineru_cloud_available():
            raise MinerUError("未配置可用的MinerU云端解析密钥。")
        token = _current_token()
        self.base_url = MINERU_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def parse_pdf(self, source: Path, progress: Progress) -> list[dict[str, Any]]:
        source = Path(source).resolve()
        source_digest = _digest(source)
        with _cache_lock(source_digest):
            return self._parse_pdf_locked(source, progress, source_digest)

    def _parse_pdf_locked(
        self,
        source: Path,
        progress: Progress,
        source_digest: str,
    ) -> list[dict[str, Any]]:
        cache = MINERU_CACHE_ROOT / source_digest
        rows_file = cache / "rows.json"
        extracted = cache / "extracted"
        marker = cache / "complete.json"
        pending_file = cache / "pending_batch.json"
        if marker.exists() and rows_file.exists():
            try:
                rows = json.loads(rows_file.read_text(encoding="utf-8"))
                if isinstance(rows, list) and rows:
                    progress(f"已复用MinerU缓存结果，共识别{len(rows)}个内容块")
                    return rows
            except (OSError, json.JSONDecodeError):
                pass
        if marker.exists() and extracted.exists():
            try:
                rows = _rows_from_result(extracted)
                progress(f"已复用MinerU缓存结果，共识别{len(rows)}个内容块")
                return rows
            except MinerUError:
                pass

        cache.mkdir(parents=True, exist_ok=True)
        legacy_temporary = cache / "extracted.tmp"
        if legacy_temporary.exists():
            recovered = _recover_rows_from_temporary(source, cache, legacy_temporary)
            if recovered:
                rows, recovered_parts = recovered
                pending = {}
                if pending_file.exists():
                    try:
                        pending = json.loads(pending_file.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        pass
                _write_json_atomic(rows_file, rows)
                _write_json_atomic(
                    marker,
                    {
                        "source_name": source.name,
                        "batch_id": pending.get("batch_id"),
                        "model_version": MINERU_MODEL_VERSION,
                        "row_count": len(rows),
                        "page_count": sum(part["page_count"] for part in recovered_parts),
                        "part_count": len(recovered_parts),
                        "recovered_from_completed_download": True,
                    },
                    indent=2,
                )
                pending_file.unlink(missing_ok=True)
                _publish_extracted_best_effort(legacy_temporary, extracted, progress)
                progress(f"已恢复上次完成的MinerU结果，共提取{len(rows)}个内容块")
                return rows
        temporary = Path(tempfile.mkdtemp(prefix="extracted.", suffix=".tmp", dir=cache))

        parts = _pdf_parts(source, cache)
        if len(parts) > 1:
            progress(f"PDF共{sum(part['page_count'] for part in parts)}页，已自动拆分为{len(parts)}卷")
        files = []
        part_by_data_id = {}
        for index, part in enumerate(parts, start=1):
            data_id = f"audit_{source_digest[:18]}_{index:03d}"
            part["data_id"] = data_id
            part_by_data_id[data_id] = part
            files.append({"name": part["path"].name, "data_id": data_id, "is_ocr": True})
        batch_id = None
        if pending_file.exists():
            try:
                pending = json.loads(pending_file.read_text(encoding="utf-8"))
                if pending.get("source_digest") == source_digest:
                    batch_id = pending.get("batch_id")
                    progress("正在继续上次未完成的MinerU解析任务")
            except (OSError, json.JSONDecodeError):
                pass
        if not batch_id:
            request_body = {
                "files": files,
                "model_version": MINERU_MODEL_VERSION,
                "enable_table": True,
                "enable_formula": True,
                "language": "ch",
            }
            progress("正在向MinerU申请安全上传地址")
            response = requests.post(
                f"{self.base_url}/file-urls/batch",
                headers=self.headers,
                json=request_body,
                timeout=(15, 60),
            )
            payload = _response_json(response, "创建解析任务")
            data = payload.get("data") or {}
            batch_id = data.get("batch_id")
            upload_urls = data.get("file_urls") or []
            if not batch_id or len(upload_urls) != len(parts):
                raise MinerUError("MinerU未返回批次编号或上传地址。")

            upload_size = sum(part["path"].stat().st_size for part in parts) / 1024 / 1024
            for index, (part, upload_url) in enumerate(zip(parts, upload_urls), start=1):
                progress(f"正在上传PDF第{index}/{len(parts)}卷（总计{upload_size:.1f} MB）")
                with part["path"].open("rb") as stream:
                    upload = requests.put(upload_url, data=stream, timeout=(30, 600))
                if upload.status_code not in {200, 201, 204}:
                    raise MinerUError(f"MinerU第{index}卷上传失败（HTTP {upload.status_code}）。")
            pending_file.write_text(
                json.dumps({
                    "source_digest": source_digest,
                    "batch_id": batch_id,
                    "part_count": len(parts),
                }, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        result_url = f"{self.base_url}/extract-results/batch/{batch_id}"
        deadline = time.monotonic() + MINERU_TASK_TIMEOUT_SECONDS
        last_message = ""
        results: dict[str, dict[str, Any]] = {}
        total_pages = sum(part["page_count"] for part in parts)
        while time.monotonic() < deadline:
            response = requests.get(result_url, headers=self.headers, timeout=(15, 60))
            payload = _response_json(response, "查询解析进度")
            entries = (payload.get("data") or {}).get("extract_result") or []
            for entry in entries:
                data_id = entry.get("data_id")
                if data_id in part_by_data_id:
                    if entry.get("state") == "failed":
                        part_index = parts.index(part_by_data_id[data_id]) + 1
                        raise MinerUError(
                            f"MinerU第{part_index}卷解析失败：{entry.get('err_msg') or '未知原因'}"
                        )
                    if entry.get("state") == "done":
                        results[data_id] = entry
            if len(results) == len(parts):
                break
            if not entries:
                message = "MinerU已接收文件，正在创建解析任务"
            else:
                completed_pages = sum(
                    part_by_data_id[data_id]["page_count"] for data_id in results
                )
                for entry in entries:
                    if entry.get("data_id") in results:
                        continue
                    details = entry.get("extract_progress") or {}
                    done = details.get("extracted_pages")
                    if isinstance(done, int):
                        completed_pages += done
                message = (
                    f"MinerU正在识别PDF：约完成{min(completed_pages, total_pages)}/{total_pages}页，"
                    f"{len(results)}/{len(parts)}卷已完成"
                )
            if message != last_message:
                progress(message)
                last_message = message
            time.sleep(MINERU_POLL_SECONDS)
        if len(results) != len(parts):
            raise MinerUError(f"MinerU解析超过{MINERU_TASK_TIMEOUT_SECONDS // 60}分钟，已停止等待。")

        rows = []
        for index, part in enumerate(parts, start=1):
            result = results[part["data_id"]]
            zip_url = result.get("full_zip_url")
            if not zip_url:
                raise MinerUError(f"MinerU第{index}卷已完成，但未返回结果下载地址。")
            progress(f"正在下载并整理MinerU结果：第{index}/{len(parts)}卷")
            archive = cache / f"result.part{index:03d}.zip"
            part_output = temporary / f"part{index:03d}"
            part_output.mkdir(parents=True, exist_ok=True)
            _download_with_retry(zip_url, archive, progress, f"MinerU第{index}卷结果")
            _safe_extract(archive, part_output)
            part_rows = _rows_from_result(part_output)
            for row in part_rows:
                if isinstance(row.get("page"), int):
                    row["page"] += part["page_offset"]
            rows.extend(part_rows)
        _write_json_atomic(rows_file, rows)
        _write_json_atomic(
            marker,
            {
                "source_name": source.name,
                "batch_id": batch_id,
                "model_version": MINERU_MODEL_VERSION,
                "row_count": len(rows),
                "page_count": total_pages,
                "part_count": len(parts),
            },
            indent=2,
        )
        pending_file.unlink(missing_ok=True)
        _publish_extracted_best_effort(temporary, extracted, progress)
        progress(f"MinerU识别完成，共提取{len(rows)}个内容块")
        return rows


def extract_pdf_with_mineru(source: Path, progress: Progress | None = None) -> list[dict[str, Any]]:
    notify = progress or (lambda _message: None)
    return MinerUCloudParser().parse_pdf(source, notify)
