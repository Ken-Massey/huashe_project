from __future__ import annotations

import hashlib
import hmac
import json
import logging
import mimetypes
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Literal

try:
    from typing import Annotated
except ImportError:  # Python 3.8 compatibility
    from typing_extensions import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .agent import AgentService
from .audit_session import AuditSessionRepository
from .config import MAX_UPLOAD_BYTES, MAX_WORKERS, RESULT_ROOT, SERVICE_TOKEN, TASK_ROOT, UPLOAD_ROOT
from .ima_rag import purge_rag_document
from .knowledge_base import KnowledgeBase
from .library_assets import LibraryAssetRepository
from .project_archive import ProjectArchiveRepository
from .patrol import router as patrol_router
from .regulation_rules import RegulationRepository, RuleEngine
from .reply_writer import STAGE_STYLE_RULES, generate_formal_reply_content
from .services import advice_worker, recognize_letter, stage1_worker, stage2_audit_worker, stage2_full_worker
from .task_manager import TaskManager
from stage1_reply_system.review_generation import render_reply_draft_docx


LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="杞ㄩ亾浜ら€氫繚鎶ゅ尯鏅鸿兘瀹℃牳Python鏈嶅姟",
    version="1.0.0",
    description="为 RuoYi-Vue 提供智能审核、知识库、项目档案和回函管理接口。",
)
app.include_router(patrol_router)
tasks = TaskManager(TASK_ROOT, max_workers=MAX_WORKERS)
knowledge = KnowledgeBase()
agent = AgentService()
regulations = RegulationRepository()
library_assets = LibraryAssetRepository()
project_archives = ProjectArchiveRepository()
audit_sessions = AuditSessionRepository()
for interrupted_audit in project_archives.incomplete_audits():
    interrupted_task_id = str(interrupted_audit.get("source_task_id") or "")
    try:
        interrupted_task = tasks.get(interrupted_task_id)
    except KeyError:
        interrupted_task = None
    if interrupted_task is None or interrupted_task.get("status") == "failed":
        reason = (
            (interrupted_task or {}).get("error_message")
            or (interrupted_task or {}).get("message")
            or "Python 服务重启，原审核任务已中断，请重新提交。"
        )
        project_archives.fail_audit(interrupted_audit["audit_id"], str(reason)[:4000])


class AgentMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class AgentQuestion(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)
    mode: Literal["general", "knowledge"] = "general"
    history: list[AgentMessage] = Field(default_factory=list)


class AgentConfigRequest(BaseModel):
    api_key: str | None = Field(default=None, max_length=500)


class RulePayload(BaseModel):
    rule: dict[str, Any]


class RuleTestPayload(BaseModel):
    data: dict[str, Any]


class RegulationFolderPayload(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    parent_id: str | None = Field(default=None, max_length=40)


class RegulationMovePayload(BaseModel):
    folder_id: str | None = Field(default=None, max_length=40)


class CaseFolderPayload(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    parent_id: str | None = Field(default=None, max_length=40)


class CaseMovePayload(BaseModel):
    folder_id: str | None = Field(default=None, max_length=40)


class LibraryAssetRenamePayload(BaseModel):
    name: str = Field(min_length=1, max_length=180)


class LibraryAssetMovePayload(BaseModel):
    folder_id: str | None = Field(default=None, max_length=40)


class ArchiveProjectCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(default="", max_length=80)
    location: str = Field(default="", max_length=200)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    description: str = Field(default="", max_length=2000)


class ArchiveProjectUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    code: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=200)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    description: str | None = Field(default=None, max_length=2000)


class ArchiveResolvePayload(BaseModel):
    project_name: str = Field(min_length=1, max_length=120)
    stage_name: str = Field(min_length=1, max_length=120)


class ArchiveStageCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    stage_order: int | None = Field(default=None, ge=1)
    description: str = Field(default="", max_length=2000)


class ArchiveStageUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    stage_order: int | None = Field(default=None, ge=1)
    description: str | None = Field(default=None, max_length=2000)


class AuditReviewItemPayload(BaseModel):
    order_no: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=200)
    conclusion: str = Field(default="", max_length=8000)
    risk_level: str = Field(default="", max_length=40)
    basis: list[Any] = Field(default_factory=list)
    recommendation: str = Field(default="", max_length=8000)
    source: dict[str, Any] = Field(default_factory=dict)
    manual_modified: bool = False


class AuditReviewItemUpdatePayload(BaseModel):
    order_no: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    conclusion: str | None = Field(default=None, max_length=8000)
    risk_level: str | None = Field(default=None, max_length=40)
    basis: list[Any] | None = None
    recommendation: str | None = Field(default=None, max_length=8000)
    source: dict[str, Any] | None = None


class AuditSessionCreatePayload(BaseModel):
    source_task_id: str = Field(default="", max_length=80)
    project_id: str = Field(default="", max_length=80)
    stage_id: str = Field(default="", max_length=80)
    status: Literal["draft", "reviewing", "finalized", "archived"] = "draft"
    metadata: dict[str, Any] = Field(default_factory=dict)
    items: list[AuditReviewItemPayload] = Field(default_factory=list)
    initial_message: str = Field(default="", max_length=12000)


class AuditChatMessagePayload(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)
    result_snapshot: dict[str, Any] | None = None


class AuditSessionChatPayload(BaseModel):
    instruction: str = Field(min_length=1, max_length=4000)


class AuditSessionArchivePayload(BaseModel):
    project_name: str = Field(min_length=1, max_length=120)
    stage_name: str = Field(min_length=1, max_length=120)
    project_id: str = Field(default="", max_length=80)
    stage_id: str = Field(default="", max_length=80)
    overwrite: bool = False
    form_data: dict[str, Any] = Field(default_factory=dict)


class AuditSessionReplyPayload(BaseModel):
    project_name: str = Field(default="", max_length=120)
    applicant: str = Field(default="", max_length=200)
    project_stage: str = Field(default="", max_length=120)
    form_data: dict[str, Any] = Field(default_factory=dict)
    save_to_reply_library: bool = True

STAGE1_SUFFIXES = {".pdf"}
LETTER_RECOGNITION_SUFFIXES = {".pdf", ".docx", ".txt"}
STAGE2_SUFFIXES = {".pdf", ".docx", ".txt"}
ADVICE_SUFFIXES = STAGE2_SUFFIXES | {".json"}
ATTACHMENT_SUFFIXES = {".pdf", ".doc", ".docx"}
KNOWLEDGE_SUFFIXES = {".pdf", ".doc", ".docx"}
REGULATION_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}
LIBRARY_ASSET_SUFFIXES = {
    ".pdf", ".doc", ".docx", ".txt", ".md",
    ".xls", ".xlsx", ".csv", ".ppt", ".pptx",
    ".dwg", ".dxf", ".dwt", ".rvt", ".ifc",
    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp",
    ".zip", ".rar", ".7z",
}


def _folder_tree_counts(
    rows: list[dict[str, Any]],
    asset_counts: dict[str, int],
    item_count_key: str,
) -> list[dict[str, Any]]:
    """Attach direct and recursive counts while tolerating legacy or orphan rows."""
    by_id = {row["folder_id"]: row for row in rows}
    children: dict[str | None, list[dict[str, Any]]] = {}
    for row in rows:
        parent_id = row.get("parent_id")
        if parent_id not in by_id:
            parent_id = None
            row["parent_id"] = None
        row["asset_count"] = asset_counts.get(row["folder_id"], 0)
        row["direct_count"] = int(row.get(item_count_key) or 0) + row["asset_count"]
        children.setdefault(parent_id, []).append(row)

    def recursive_total(folder_id: str, trail: set[str]) -> int:
        row = by_id[folder_id]
        if folder_id in trail:
            return int(row["direct_count"])
        descendants = children.get(folder_id, [])
        row["child_folder_count"] = len(descendants)
        total = int(row["direct_count"])
        next_trail = trail | {folder_id}
        for child in descendants:
            total += recursive_total(child["folder_id"], next_trail)
        row["total_count"] = total
        return total

    for row in rows:
        if "total_count" not in row:
            recursive_total(row["folder_id"], set())
    return rows


def verify_service_token(x_service_token: Annotated[str | None, Header()] = None) -> None:
    if SERVICE_TOKEN and not hmac.compare_digest(x_service_token or "", SERVICE_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="服务令牌无效。")


def _parse_json(value: str | None, label: str) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"{label}不是合法JSON：{exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=422, detail=f"{label}必须是JSON对象。")
    return parsed


def _model_values(payload: BaseModel) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=True)
    return payload.dict(exclude_unset=True)


def _resolve_archive_context(binding: Any) -> dict[str, Any] | None:
    if binding in (None, ""):
        return None
    if not isinstance(binding, dict):
        raise HTTPException(status_code=422, detail="archive_binding必须是JSON对象。")
    project_id = str(binding.get("project_id") or "").strip()
    stage_id = str(binding.get("stage_id") or "").strip()
    stage_name = str(binding.get("stage_name") or "").strip()
    selected_nearby = binding.get("selected_nearby_projects") or []
    selected_nearby = selected_nearby if isinstance(selected_nearby, list) else []
    if not project_id:
        return None
    try:
        if not stage_id:
            project = project_archives.get_project(project_id, include_archived_stages=False)
            if project.get("status") != "active":
                raise HTTPException(status_code=409, detail="已归档的项目不能发起审核。")
            latest_record = project_archives.latest_successful_audit_for_project(project_id)
            previous_stages = []
            if latest_record:
                previous_stages.append({
                    "stage_id": latest_record.get("stage_id"),
                    "stage_name": latest_record.get("stage_name"),
                    "stage_order": latest_record.get("stage_order"),
                    "audit_date": latest_record.get("audit_date") or latest_record.get("completed_at"),
                    "result": latest_record.get("result"),
                    "risk_level": latest_record.get("risk_level"),
                    "summary": latest_record.get("summary"),
                })
            return {
                "format_version": "project_archive_history_v1",
                "project": {
                    "project_id": project_id,
                    "project_name": project.get("name") or project.get("project_name"),
                },
                "current_stage": {
                    "stage_id": "",
                    "stage_name": stage_name,
                    "stage_order": None,
                },
                "previous_stage_count": len(previous_stages),
                "omitted_stage_count": 0,
                "previous_stages": previous_stages,
                "latest_previous_audit": latest_record or {},
                "selected_nearby_projects": selected_nearby,
            }
        stage = project_archives.get_stage(stage_id)
        if stage["project_id"] != project_id:
            raise HTTPException(status_code=422, detail="所选阶段不属于指定项目。")
        if stage["project_status"] != "active" or stage["status"] != "active":
            raise HTTPException(status_code=409, detail="已归档的项目或阶段不能发起审核。")
        if stage.get("audit_status") in {"pending", "running"}:
            raise HTTPException(status_code=409, detail="该阶段已有审核任务正在进行。")
        context = project_archives.history_context_for_stage(stage_id)
        context["selected_nearby_projects"] = selected_nearby
        return context
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目或阶段不存在。") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _save_upload(upload: UploadFile, task_type: str, allowed: set[str]) -> Path:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=415, detail=f"{task_type}涓嶆敮鎸佹枃浠剁被鍨嬶細{suffix or '鏃犳墿灞曞悕'}")
    upload_id = hashlib.sha256(f"{task_type}:{upload.filename}:{id(upload)}".encode()).hexdigest()[:20]
    folder = UPLOAD_ROOT / upload_id
    folder.mkdir(parents=True, exist_ok=False)
    destination = folder / (Path(upload.filename or f"source{suffix}").name)
    total = 0
    try:
        with destination.open("wb") as target:
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="???????")
                target.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        folder.rmdir()
        raise
    finally:
        await upload.close()
    return destination


def _task_or_404(task_id: str) -> dict[str, Any]:
    try:
        return tasks.get(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


def _public_knowledge_case(item: dict[str, Any], *, detail: bool = False) -> dict[str, Any]:
    fields = (
        "case_id", "case_name", "category", "original_file_name", "file_size", "status",
        "active", "managed_file", "advice_count", "paragraph_count", "text_length",
        "extraction_method", "error_message", "folder_id", "folder_name", "created_at", "updated_at",
    )
    value = {key: item.get(key) for key in fields}
    value["has_source_file"] = bool(item.get("stored_file") or item.get("source_file"))
    value["has_extracted_text"] = bool(item.get("text_file"))
    if detail:
        value["features"] = item.get("features") or {}
        value["advices"] = item.get("advices") or []
    return value


def _public_regulation(item: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "regulation_id", "title", "version", "original_file_name", "extraction_method",
        "text_length", "paragraph_count", "clause_count", "status", "active", "rule_count",
        "published_count", "folder_id", "folder_name", "created_at", "updated_at",
    )
    return {key: item.get(key) for key in fields}


def _artifact_files(task: dict[str, Any]) -> list[dict[str, Any]]:
    result = task.get("result") or {}
    explicit_files = result.get("artifact_files")
    if not isinstance(explicit_files, list) and result.get("stage") == "stage1":
        public_files: list[str] = []
        for root_value in result.get("artifact_roots") or []:
            root = Path(root_value).resolve()
            opinion = root / "瀹℃牳鎰忚.md"
            if opinion.is_file():
                public_files.append(str(opinion))
            for name in ("鏈€缁堢増澶嶅嚱.docx", "澶嶅嚱鑽夌.docx", "鍥炲嚱杈呭姪鑽夌.docx"):
                reply = root / name
                if reply.is_file():
                    public_files.append(str(reply))
                    break
        explicit_files = public_files
    if isinstance(explicit_files, list):
        files: list[dict[str, Any]] = []
        for path_value in explicit_files:
            path = Path(path_value).resolve()
            if not path.exists() or not path.is_file():
                continue
            file_id = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:24]
            files.append({
                "file_id": file_id,
                "name": path.name,
                "relative_path": path.name,
                "size": path.stat().st_size,
                "root_index": 0,
                "path": str(path),
            })
        return files
    roots = result.get("artifact_roots") or []
    files: list[dict[str, Any]] = []
    for root_index, root_value in enumerate(roots):
        root = Path(root_value).resolve()
        if not root.exists() or not root.is_dir():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            file_id = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:24]
            files.append({
                "file_id": file_id,
                "name": path.name,
                "relative_path": str(path.relative_to(root)),
                "size": path.stat().st_size,
                "root_index": root_index,
                "path": str(path),
            })
    return files


def _source_file_records(
    source_file: Path,
    attachments: dict[str, Path] | None = None,
) -> list[dict[str, Any]]:
    roles = {"scheme_file": "scheme", "expert_opinion_file": "expert_opinion"}
    records = [{
        "role": "primary",
        "name": source_file.name,
        "size": source_file.stat().st_size if source_file.exists() else 0,
        "stored_file": str(source_file),
    }]
    for key, path in (attachments or {}).items():
        records.append({
            "role": roles.get(key, key),
            "name": path.name,
            "size": path.stat().st_size if path.exists() else 0,
            "stored_file": str(path),
        })
    return records


def _archive_completion_data(result: dict[str, Any]) -> dict[str, Any]:
    report = (result.get("dynamic_regulation_audit") or {}).get("risk_report") or {}
    findings = report.get("findings") or []
    judgements = {str(item.get("judgement") or "") for item in findings if isinstance(item, dict)}
    risk_level = str(report.get("overall_risk_level") or "").strip()
    if "non_compliant" in judgements:
        conclusion = "闇€淇敼"
    elif risk_level in {"重大", "高"}:
        conclusion = "闇€閲嶇偣澶嶆牳"
    elif report.get("required_supplements"):
        conclusion = "闇€琛ュ厖璧勬枡"
    else:
        conclusion = "瀹℃牳瀹屾垚"
    summary: Any = report.get("overall_conclusion") or report.get("overview")
    if not summary:
        summary = result.get("summary") or result.get("audit_summary") or conclusion
    if not isinstance(summary, str):
        summary = json.dumps(summary, ensure_ascii=False)
    artifacts = [
        {key: item[key] for key in ("file_id", "name", "relative_path", "size", "root_index")}
        for item in _artifact_files({"result": result})
    ]
    return {
        "result": conclusion,
        "risk_level": risk_level or "待判断",
        "summary": summary[:10000],
        "result_data": result,
        "artifacts": artifacts,
    }


def _archive_record_form_data(record: dict[str, Any]) -> dict[str, Any]:
    result_data = record.get("result_data") if isinstance(record, dict) else {}
    result_data = result_data if isinstance(result_data, dict) else {}
    candidates = [
        result_data.get("form_data"),
        (result_data.get("latest_result") or {}).get("form_data") if isinstance(result_data.get("latest_result"), dict) else None,
        (result_data.get("project_data") or {}).get("form_data") if isinstance(result_data.get("project_data"), dict) else None,
    ]
    for value in candidates:
        if isinstance(value, dict) and value:
            return value
    return {}


CONSISTENCY_FIELD_LABELS: dict[str, str] = {
    "relative_relationship": "相对关系",
    "structure_method": "结构形式",
    "structure_condition": "结构状态",
    "buried_depth_m": "结构埋深",
    "outer_diameter_or_width_m": "结构宽度",
    "disease_severity": "结构病害",
    "land_use_type": "用地性质",
    "pit_depth_m": "基坑深度",
    "pit_length_m": "基坑长度",
    "minimum_horizontal_clearance_m": "水平净距",
    "minimum_vertical_clearance_m": "竖向净距",
    "dewatering_method": "降水方式",
    "terrain_zone": "地段区域",
    "is_soft_soil": "软弱土",
    "is_complex_geology_or_hydrology": "复杂地质水文",
    "support_components": "支护构件",
    "protection_zone_location": "保护区位置",
}

CONSISTENCY_NUMERIC_FIELDS = {
    "buried_depth_m",
    "outer_diameter_or_width_m",
    "pit_depth_m",
    "pit_length_m",
    "minimum_horizontal_clearance_m",
    "minimum_vertical_clearance_m",
}


def _clean_compare_value(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text or text in {"未知", "待判断", "未填写", "无", "暂无"}:
            return None
        return text
    if isinstance(value, list):
        cleaned = [_clean_compare_value(item) for item in value]
        cleaned = [item for item in cleaned if item not in (None, "", [])]
        return sorted(str(item) for item in cleaned) if cleaned else None
    return value


def _format_compare_value(value: Any) -> str:
    value = _clean_compare_value(value)
    if value is None:
        return "未填写"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _compare_numeric_values(values: list[float]) -> bool:
    if len(values) < 2:
        return False
    maximum = max(values)
    minimum = min(values)
    diff = abs(maximum - minimum)
    scale = max(abs(maximum), abs(minimum), 1.0)
    return diff >= 0.2 and diff / scale >= 0.08


def _field_values_differ(key: str, values: list[Any]) -> bool:
    cleaned = [_clean_compare_value(value) for value in values]
    cleaned = [value for value in cleaned if value is not None]
    if len(cleaned) < 2:
        return False
    if key in CONSISTENCY_NUMERIC_FIELDS:
        numbers = []
        for value in cleaned:
            try:
                numbers.append(float(value))
            except (TypeError, ValueError):
                return len({str(item) for item in cleaned}) > 1
        return _compare_numeric_values(numbers)
    normalized = {
        json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (list, dict)) else str(value)
        for value in cleaned
    }
    return len(normalized) > 1


def _extract_manual_context(result: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        result.get("manual_context_for_consistency"),
        result.get("manual_context"),
        (result.get("project_data") or {}).get("form_data") if isinstance(result.get("project_data"), dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate:
            return candidate
    return {}


def _same_upload_data_consistency_item(context: dict[str, Any]) -> dict[str, Any] | None:
    documents = context.get("uploaded_documents") if isinstance(context, dict) else []
    if not isinstance(documents, list) or len(documents) < 2:
        return None
    differences: list[str] = []
    for key, label in CONSISTENCY_FIELD_LABELS.items():
        sources: list[tuple[str, Any]] = []
        for document in documents:
            if not isinstance(document, dict):
                continue
            fields = document.get("fields") if isinstance(document.get("fields"), dict) else {}
            value = fields.get(key)
            if _clean_compare_value(value) is not None:
                sources.append((str(document.get("name") or "未命名文件"), value))
        if _field_values_differ(key, [value for _, value in sources]):
            detail = "；".join(f"{name}为{_format_compare_value(value)}" for name, value in sources[:4])
            differences.append(f"{label}不一致（{detail}）")
        if len(differences) >= 4:
            break
    if not differences:
        return None
    return {
        "order_no": 1,
        "title": "多文件关键数据存在不一致",
        "conclusion": "本次上传的多份项目资料中，部分必要审核数据存在不一致：" + "；".join(differences) + "。相关差异会影响保护区关系、净距、工程规模或风险等级判断，需以正式有效文件核准后再作为审核依据。",
        "risk_level": "中",
        "basis": [],
        "recommendation": "请核对函件、安评报告、方案及附件中的关键参数，明确采用的最终数据来源；对不一致数据应补充说明或更正后，再形成最终审核结论。",
        "source": {"kind": "same_upload_data_consistency"},
        "manual_modified": False,
    }


def _previous_stage_form_data(archive_context: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    stage_id = str(((archive_context or {}).get("current_stage") or {}).get("stage_id") or "")
    if not stage_id:
        record = (archive_context or {}).get("latest_previous_audit") or {}
        form_data = _archive_record_form_data(record) if isinstance(record, dict) else {}
        if form_data:
            return form_data, record
        return {}, {}
    if not stage_id:
        return {}, {}
    try:
        records = project_archives.previous_successful_audits(stage_id)
    except Exception:
        return {}, {}
    for record in reversed(records):
        form_data = _archive_record_form_data(record)
        if form_data:
            return form_data, record
    return {}, {}


def _previous_stage_delta_item(context: dict[str, Any], archive_context: dict[str, Any] | None) -> dict[str, Any] | None:
    previous_form, previous_record = _previous_stage_form_data(archive_context)
    if not previous_form:
        return None
    differences: list[str] = []
    for key, label in CONSISTENCY_FIELD_LABELS.items():
        current_value = context.get(key)
        previous_value = previous_form.get(key)
        if _field_values_differ(key, [current_value, previous_value]):
            differences.append(
                f"{label}由上一阶段的{_format_compare_value(previous_value)}变为本阶段的{_format_compare_value(current_value)}"
            )
        if len(differences) >= 5:
            break
    if not differences:
        return None
    stage_name = str(previous_record.get("stage_name") or "上一阶段")
    return {
        "order_no": 1,
        "title": "本阶段数据与上一阶段档案存在明显差异",
        "conclusion": f"与项目档案中“{stage_name}”审核记录相比，本阶段关键参数存在明显变化：" + "；".join(differences) + "。这些变化可能导致保护区位置、工程影响范围或安全控制要求发生调整，需在本阶段审核中专项核实。",
        "risk_level": "中",
        "basis": [],
        "recommendation": "请说明本阶段参数变化原因，并提交对应版本的图纸、计算书或正式函件；如差异涉及净距、基坑规模、结构关系或保护区位置，应重新复核风险等级和控制措施。",
        "source": {
            "kind": "previous_stage_delta",
            "stage_id": previous_record.get("stage_id"),
            "stage_name": stage_name,
            "audit_id": previous_record.get("audit_id"),
        },
        "manual_modified": False,
    }


def _consistency_review_items(
    result: dict[str, Any],
    archive_context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    context = _extract_manual_context(result)
    items = [
        _same_upload_data_consistency_item(context),
        _previous_stage_delta_item(context, archive_context),
    ]
    return [item for item in items if item]


def _short_text(value: Any, maximum: int = 8000) -> str:
    return " ".join(str(value or "").split())[:maximum]


def _review_item_basis_from_finding(item: dict[str, Any]) -> list[dict[str, Any]]:
    basis = []
    for evidence in item.get("regulation_evidence") or []:
        if not isinstance(evidence, dict):
            continue
        basis.append({
            "document": Path(str(evidence.get("document_title") or "")).name,
            "clause": evidence.get("section") or evidence.get("clause"),
            "quote": _short_text(evidence.get("quote") or evidence.get("chunk_text") or evidence.get("text"), 800),
        })
    return basis


def _looks_like_source_title(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    return (
        "自动审核意见" in text
        or ((text.lower().endswith(".pdf") or "pdf" in text.lower()) and ("第" in text and "条" in text))
        or (("规程" in text or "规范" in text or "标准" in text) and "第" in text and "条" in text)
    )


def _derive_review_title(text: Any, fallback: str = "审核事项") -> str:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    if not raw:
        return fallback
    first = re.split(r"[。；;.!，,？?]", raw, maxsplit=1)[0].strip()
    first = re.sub(r"^(建议|审核意见|结论|意见)[:：\s]*", "", first).strip()
    if not first:
        first = raw
    if len(first) > 34:
        first = first[:34].rstrip("，、；;：: ") + "…"
    return first or fallback


_ACTION_OPINION_KEYWORDS = (
    "应", "需", "须", "请", "建议", "不得", "严禁", "禁止",
    "补充", "完善", "明确", "复核", "核查", "落实", "制定",
    "加强", "监测", "报审", "提交", "开展", "优化", "控制",
    "采取", "重新", "论证", "验算", "评估", "修正", "调整",
)


_POSITIVE_EVALUATION_KEYWORDS = (
    "符合安全要求", "符合要求", "满足安全要求", "满足要求", "风险可控",
    "可控范围", "已落实", "已制定", "严于规程", "严于规范", "严于标准",
    "低于规程", "低于规范", "低于标准", "有效减少", "不构成重大风险",
    "判定为", "属于", "位于", "根据规程", "根据规范", "显示",
)


_NEGATIVE_OR_REQUIREMENT_KEYWORDS = (
    "不足", "缺失", "缺少", "未明确", "未提供", "不满足", "不符合",
    "超标", "风险", "隐患", "应", "需", "须", "请", "建议",
    "补充", "完善", "明确", "复核", "核查", "落实", "制定",
    "加强", "监测", "报审", "提交", "开展", "优化", "控制",
    "采取", "重新", "论证", "验算", "评估", "修正", "调整",
)


def _looks_like_action_opinion(text: Any) -> bool:
    value = str(text or "").strip()
    return bool(value) and any(keyword in value for keyword in _ACTION_OPINION_KEYWORDS)


def _looks_like_positive_evaluation_text(text: Any) -> bool:
    value = str(text or "").strip()
    return bool(value) and any(keyword in value for keyword in _POSITIVE_EVALUATION_KEYWORDS)


def _looks_like_pure_evaluation_text(text: Any) -> bool:
    value = str(text or "").strip()
    return (
        bool(value)
        and _looks_like_positive_evaluation_text(value)
        and not any(keyword in value for keyword in _NEGATIVE_OR_REQUIREMENT_KEYWORDS)
    )


def _looks_like_evaluation_title(text: Any) -> bool:
    value = str(text or "").strip()
    return bool(value) and any(keyword in value for keyword in ("满足", "符合", "可控", "已落实", "严于", "低于"))


def _looks_like_positive_evaluation_item(item: dict[str, Any]) -> bool:
    """Filter out entries that are mainly positive evaluations instead of actionable opinions."""
    title = str(item.get("title") or "")
    conclusion = str(item.get("conclusion") or "")
    recommendation = str(item.get("recommendation") or "")
    combined = " ".join([title, conclusion, recommendation])
    if not combined:
        return False
    positive = any(keyword in combined for keyword in _POSITIVE_EVALUATION_KEYWORDS)
    low_risk = str(item.get("risk_level") or "") in {"低", "低风险", "提示"}
    title_is_positive = any(keyword in title for keyword in ("满足", "符合", "可控", "已落实", "严于"))
    return positive and (low_risk or title_is_positive) and not any(
        keyword in combined for keyword in ("不足", "缺失", "缺少", "未明确", "未提供", "不满足", "不符合", "超标")
    )


def _extract_action_opinion(value: dict[str, Any]) -> tuple[str, str]:
    """Return (opinion, recommendation) where opinion is a concrete requirement, not a pure evaluation."""
    recommendation = _short_text(value.get("recommendation"), 8000)
    conclusion = _short_text(value.get("conclusion") or value.get("opinion"), 8000)
    analysis = _short_text(value.get("analysis"), 8000)

    # 优先保留已经展开的正式审核意见。此前只取“建议”字段，容易把意见压缩成一句待办。
    if _looks_like_action_opinion(conclusion) and not _looks_like_pure_evaluation_text(conclusion):
        return conclusion, recommendation if recommendation != conclusion else ""
    if _looks_like_action_opinion(analysis) and not _looks_like_pure_evaluation_text(analysis):
        return analysis, recommendation if recommendation != analysis else ""
    if _looks_like_action_opinion(recommendation) and not _looks_like_pure_evaluation_text(recommendation):
        return recommendation, ""
    if recommendation and not _looks_like_pure_evaluation_text(recommendation):
        return recommendation, ""
    return "", ""


REVIEW_ITEM_TARGET_COUNT = 5
REVIEW_ITEM_MAX_COUNT = 6


def _review_item_risk_score(value: Any) -> int:
    text = str(value or "")
    if any(token in text for token in ("重大", "极高", "高")):
        return 50
    if "中" in text:
        return 30
    if "低" in text:
        return 12
    if "提示" in text:
        return 8
    return 16


def _review_item_importance(item: dict[str, Any]) -> int:
    title = str(item.get("title") or "")
    text = " ".join([
        title,
        str(item.get("conclusion") or ""),
        str(item.get("recommendation") or ""),
    ])
    source_kind = str((item.get("source") or {}).get("kind") or "")
    score = _review_item_risk_score(item.get("risk_level"))
    if source_kind == "dynamic_regulation_finding":
        score += 24
    elif source_kind == "dynamic_regulation_opinion":
        score += 12
    elif source_kind == "generated_opinion":
        score += 4
    keyword_weights = (
        ("不满足", 14), ("不符合", 14), ("超标", 14), ("不足", 12),
        ("缺少", 12), ("未提供", 12), ("未明确", 10), ("侵入", 16),
        ("特别保护区", 16), ("净距", 12), ("振动", 12), ("沉降", 10),
        ("施工监测", 10), ("计算", 8), ("模型", 8), ("方案", 8),
        ("补充", 6), ("严禁", 14), ("必须", 8),
    )
    for keyword, weight in keyword_weights:
        if keyword in text:
            score += weight
    if _looks_like_source_title(title):
        score -= 8
    return score


def _review_item_topic_key(item: dict[str, Any]) -> str:
    text = " ".join([
        str(item.get("title") or ""),
        str(item.get("conclusion") or ""),
        str(item.get("recommendation") or ""),
    ])
    for keyword in (
        "特别保护区", "红线", "净距", "振动", "沉降", "施工监测",
        "数值模拟", "模型", "降水", "地质", "支护", "应急", "报审",
        "合规", "计算", "资料",
    ):
        if keyword in text:
            return keyword
    normalized = re.sub(r"\W+", "", str(item.get("title") or text))
    return normalized[:18]


def _renumber_review_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        copied = dict(item)
        copied["order_no"] = index
        normalized.append(copied)
    return normalized


def _is_overall_review_item(item: dict[str, Any]) -> bool:
    source_kind = str((item.get("source") or {}).get("kind") or "")
    title = str(item.get("title") or "").strip()
    return source_kind == "overall_summary" or title in {"缁煎悎鎰忚", "缁煎悎瀹℃牳缁撹"}


def _select_key_review_items(
    items: list[dict[str, Any]],
    limit: int = REVIEW_ITEM_TARGET_COUNT,
) -> list[dict[str, Any]]:
    actionable_items = [
        item for item in items
        if not _looks_like_positive_evaluation_item(item)
    ]
    if actionable_items:
        items = actionable_items
    if len(items) <= limit:
        return _renumber_review_items(items)

    ranked = sorted(
        enumerate(items),
        key=lambda pair: (_review_item_importance(pair[1]), -pair[0]),
        reverse=True,
    )
    selected: list[tuple[int, dict[str, Any]]] = []
    used_topics: set[str] = set()
    for original_index, item in ranked:
        topic = _review_item_topic_key(item)
        if topic and topic in used_topics:
            continue
        selected.append((original_index, item))
        if topic:
            used_topics.add(topic)
        if len(selected) >= limit:
            break

    if len(selected) < limit:
        selected_indexes = {index for index, _ in selected}
        for original_index, item in ranked:
            if original_index in selected_indexes:
                continue
            selected.append((original_index, item))
            if len(selected) >= limit:
                break

    selected_items = [item for _, item in sorted(selected, key=lambda pair: pair[0])]
    return _renumber_review_items(selected_items)


def _build_overall_review_item(result: dict[str, Any], selected_items: list[dict[str, Any]]) -> dict[str, Any]:
    report = ((result.get("dynamic_regulation_audit") or {}).get("risk_report") or {})
    risk_level = _short_text(
        report.get("overall_risk_level")
        or result.get("risk_level")
        or "",
        40,
    )
    raw_summary = (
        report.get("overall_conclusion")
        or report.get("overview")
        or result.get("audit_summary")
        or result.get("summary")
    )
    if not isinstance(raw_summary, str):
        raw_summary = json.dumps(raw_summary, ensure_ascii=False) if raw_summary else ""
    summary = _formal_overall_review_text(result, selected_items, _short_text(raw_summary, 1600))
    return {
        "order_no": 0,
        "title": "综合评价",
        "conclusion": summary,
        "risk_level": risk_level,
        "basis": [],
        "recommendation": "",
        "source": {"kind": "overall_summary"},
    }


def _audit_result_to_review_items(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize current audit output into editable review items."""
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def append_item(value: dict[str, Any]) -> None:
        title = _short_text(value.get("title") or value.get("topic") or "审核事项", 200)
        conclusion, recommendation = _extract_action_opinion(value)
        if not conclusion and not recommendation:
            return
        if _looks_like_source_title(title) or _looks_like_evaluation_title(title):
            title = _derive_review_title(conclusion or recommendation, fallback="审核事项")
        key = (title, conclusion or recommendation)
        if not title or key in seen:
            return
        seen.add(key)
        items.append({
            "order_no": len(items) + 1,
            "title": title,
            "conclusion": conclusion,
            "risk_level": _short_text(value.get("risk_level") or value.get("severity"), 40),
            "basis": value.get("basis") or [],
            "recommendation": recommendation,
            "source": value.get("source") or {},
        })

    report = ((result.get("dynamic_regulation_audit") or {}).get("risk_report") or {})
    for finding in report.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        if finding.get("judgement") == "compliant":
            continue
        append_item({
            "title": finding.get("title") or finding.get("name"),
            "analysis": finding.get("analysis"),
            "recommendation": finding.get("recommendation"),
            "risk_level": finding.get("risk_level") or finding.get("severity"),
            "basis": _review_item_basis_from_finding(finding),
            "source": {
                "kind": "dynamic_regulation_finding",
                "judgement": finding.get("judgement"),
                "comparison": finding.get("comparison"),
            },
        })

    for opinion in result.get("dynamic_regulation_opinions") or []:
        if not isinstance(opinion, dict):
            continue
        append_item({
            "title": opinion.get("topic"),
            "conclusion": opinion.get("conclusion"),
            "risk_level": opinion.get("risk_level") or "",
            "basis": opinion.get("regulation_clauses") or [],
            "source": {
                "kind": "dynamic_regulation_opinion",
                "review_status": opinion.get("review_status"),
                "result": opinion.get("result"),
            },
        })

    details = result.get("audit_details") or {}
    for opinion in details.get("generated_opinions") or []:
        if not isinstance(opinion, dict):
            continue
        append_item({
            "title": opinion.get("source_clause") or f"自动审核意见{opinion.get('number') or ''}",
            "conclusion": opinion.get("opinion") or opinion.get("conclusion"),
            "basis": [opinion.get("source_clause")] if opinion.get("source_clause") else [],
            "source": {
                "kind": "generated_opinion",
                "source_function": opinion.get("source_function"),
                "source_result": opinion.get("source_result"),
            },
        })

    return _select_key_review_items(items, REVIEW_ITEM_TARGET_COUNT)


def _ai_expand_review_items(result: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use the LLM to turn selected findings into formal, regulation-based review opinions."""
    if not items:
        return items
    context = {
        "project_name": ((result.get("archive_binding") or {}).get("project_name") or result.get("project_name") or ""),
        "stage_name": ((result.get("archive_binding") or {}).get("stage_name") or result.get("project_stage") or ""),
        "audit_summary": result.get("audit_summary") or result.get("summary") or "",
        "risk_level": result.get("risk_level") or "",
        "items": [_public_review_item(item) for item in items],
    }
    system = (
        "你是轨道交通保护区工程审核专家，负责把机器识别出的风险点整理成正式审核意见。"
        "输出必须严格基于已有资料、识别结果和技术规程，不得编造未提供的数值、距离、地质条件、线路名称或规范条文。"
        "综合评价只写在overall_opinion中；items中的分条内容只写审核意见、补充资料要求、复核要求、控制措施或报审管理要求，"
        "不要写“符合要求、满足要求、风险可控、已落实、低于限值、严于规范”等评价性结论。"
        "每条意见应按技术规程审核逻辑展开，约100至200个汉字，避免一句话过短；应说明缺少/需明确的资料、对应安全控制或复核要求。"
        "只保留5至6条最主要意见，优先保留高风险、资料缺失、净距/保护区、地下水/地质、变形控制、监测和报审要求。"
        "只输出JSON，不要输出Markdown。"
    )
    prompt = (
        f"当前审核上下文：{json.dumps(context, ensure_ascii=False)}\n\n"
        "请返回JSON：{\"items\":[{\"order_no\":1,\"title\":\"8至20字的意见主题，不要写规程名称\",\"conclusion\":\"100至200字的正式审核意见，只写意见和要求，不写评价性结论\",\"risk_level\":\"高/中/低/提示/可为空\",\"basis\":[\"可为空\"],\"recommendation\":\"可为空\"}]}\n"
        "要求：items必须是完整最新版审核意见列表，数量5至6条；如果候选不足5条，可在不编造数值的前提下，根据资料缺失、规范复核、监测控制、报审要求等方向补足。"
    )
    try:
        value = agent.complete_json(system, prompt, max_tokens=5200)
        expanded = _sanitize_review_items(value, items)
        if len(expanded) >= min(len(items), REVIEW_ITEM_TARGET_COUNT):
            return _select_key_review_items(expanded, REVIEW_ITEM_MAX_COUNT)
    except Exception as exc:
        LOGGER.warning("AI failed to expand review items: %s", exc)
    return _select_key_review_items(items, REVIEW_ITEM_MAX_COUNT)


def _attach_audit_session(
    result: dict[str, Any],
    *,
    task_id: str,
    archive_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if result.get("audit_session"):
        return result
    project = (archive_context or {}).get("project") or {}
    stage = (archive_context or {}).get("current_stage") or {}
    items = _audit_result_to_review_items(result)
    consistency_items = _consistency_review_items(result, archive_context)
    if consistency_items:
        items = _select_key_review_items(consistency_items + items, REVIEW_ITEM_MAX_COUNT)
    items = _ai_expand_review_items(result, items)
    overall_opinion = _build_overall_review_item(result, items)
    session = audit_sessions.create_session({
        "source_task_id": task_id,
        "project_id": project.get("project_id") or "",
        "stage_id": stage.get("stage_id") or "",
        "status": "reviewing",
        "metadata": {
            "task_type": result.get("stage"),
            "project_name": project.get("project_name") or "",
            "stage_name": stage.get("stage_name") or "",
            "archive_binding": result.get("archive_binding") or {},
            "overall_opinion": overall_opinion,
        },
        "items": items,
        "initial_message": "已完成第一版审核结果，可以继续增删改每一条审核意见。",
    })
    result["audit_session_id"] = session["session_id"]
    result["audit_session"] = session
    result["review_items"] = session["items"]
    result["overall_opinion"] = overall_opinion
    return result


_CHINESE_ORDINALS = {
    "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


def _instruction_order_no(text: str) -> int | None:
    match = re.search(r"第\s*(\d+|[一二两三四五六七八九十])\s*(?:条|点|项|个)", text)
    if not match:
        return None
    value = match.group(1)
    if value.isdigit():
        return int(value)
    return _CHINESE_ORDINALS.get(value)


def _public_review_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_no": item.get("order_no"),
        "title": item.get("title") or "",
        "conclusion": item.get("conclusion") or "",
        "risk_level": item.get("risk_level") or "",
        "basis": item.get("basis") or [],
        "recommendation": item.get("recommendation") or "",
        "source": item.get("source") or {},
    }


def _sanitize_review_items(value: Any, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        candidates = value.get("items")
    else:
        candidates = value
    if not isinstance(candidates, list):
        raise ValueError("AI did not return a valid review item list.")
    items: list[dict[str, Any]] = []
    for index, item in enumerate(candidates[:50], start=1):
        if not isinstance(item, dict):
            continue
        title = _short_text(_clean_assistant_plain_text(item.get("title") or item.get("topic")), 200)
        conclusion, recommendation = _extract_action_opinion(item)
        conclusion = _clean_assistant_plain_text(conclusion)
        recommendation = _clean_assistant_plain_text(recommendation)
        if not conclusion and recommendation:
            conclusion = recommendation
        if not title:
            title = f"????{index}"
        if not conclusion and not recommendation:
            continue
        items.append({
            "order_no": index,
            "title": title,
            "conclusion": conclusion,
            "risk_level": _short_text(item.get("risk_level"), 40),
            "basis": item.get("basis") if isinstance(item.get("basis"), list) else [],
            "recommendation": recommendation,
            "source": {
                **(item.get("source") if isinstance(item.get("source"), dict) else {}),
                "modified_by": "ai_instruction",
            },
        })
    if not items:
        raise ValueError("No review item remains after AI modification.")
    return _select_key_review_items(items, REVIEW_ITEM_MAX_COUNT)


def _merge_partial_review_items(
    instruction: str,
    current_items: list[dict[str, Any]],
    incoming_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not current_items or not incoming_items:
        return incoming_items
    if len(incoming_items) >= min(len(current_items), REVIEW_ITEM_TARGET_COUNT):
        return incoming_items

    merged = [_public_review_item(item) for item in current_items]
    target_order = _instruction_order_no(instruction)
    incoming_by_order = {
        int(item.get("order_no") or 0): item
        for item in incoming_items
        if int(item.get("order_no") or 0) > 0
    }

    if target_order and incoming_items:
        replacement = dict(incoming_items[0])
        replacement["order_no"] = target_order
        incoming_by_order[target_order] = replacement

    for index, item in enumerate(merged):
        order_no = int(item.get("order_no") or index + 1)
        replacement = incoming_by_order.get(order_no)
        if replacement:
            merged[index] = {
                **item,
                **replacement,
                "order_no": order_no,
            }

    if not target_order:
        existing_orders = {int(item.get("order_no") or 0) for item in merged}
        for item in incoming_items:
            order_no = int(item.get("order_no") or 0)
            if order_no not in existing_orders and len(merged) < REVIEW_ITEM_MAX_COUNT:
                appended = dict(item)
                appended["order_no"] = len(merged) + 1
                merged.append(appended)

    for index, item in enumerate(merged, start=1):
        item["order_no"] = index
    return _select_key_review_items(merged, REVIEW_ITEM_MAX_COUNT)


def _looks_like_detail_instruction(instruction: str) -> bool:
    return bool(re.search(r"(详细|细化|展开|扩写|丰富|完善|具体|深化)", str(instruction or "")))


def _item_changed_enough(before: dict[str, Any] | None, after: dict[str, Any] | None) -> bool:
    if not before or not after:
        return True
    before_text = _clean_assistant_plain_text(
        " ".join(str(before.get(key) or "") for key in ("title", "conclusion", "recommendation"))
    )
    after_text = _clean_assistant_plain_text(
        " ".join(str(after.get(key) or "") for key in ("title", "conclusion", "recommendation"))
    )
    if not before_text:
        return bool(after_text)
    if len(after_text) >= len(before_text) + 60:
        return True
    return before_text != after_text and len(after_text) >= int(len(before_text) * 1.25)


def _expand_review_item_by_instruction(item: dict[str, Any], instruction: str) -> dict[str, Any]:
    expanded = dict(item)
    title = _short_text(expanded.get("title") or "审核意见细化", 80)
    base = _clean_assistant_plain_text(expanded.get("conclusion") or expanded.get("recommendation") or "")
    if not base:
        base = f"应围绕“{title}”补充完善相关资料、计算复核和实施控制要求。"
    detail = (
        f"{base}\n\n"
        "1. 资料补充要求：应进一步说明该事项涉及的工程条件、控制目标、计算参数和已有资料依据，明确缺失资料由设计单位或勘察单位补充完善。\n\n"
        "2. 技术复核要求：应结合基坑开挖、地下水控制、既有结构保护及现场实施条件，对相关计算、验算或专项方案进行复核，确保控制指标具备可核查依据。\n\n"
        "3. 实施管理要求：应在正式报审或施工前形成闭环文件，明确责任单位、复核结论、监测或应急控制措施，并经相关专业人员确认后纳入后续方案。"
    )
    expanded["title"] = title
    expanded["conclusion"] = _clean_assistant_plain_text(detail)
    expanded["recommendation"] = ""
    source = expanded.get("source") if isinstance(expanded.get("source"), dict) else {}
    expanded["source"] = {**source, "modified_by": "detail_instruction_fallback"}
    return expanded


def _ensure_detail_instruction_applied(
    instruction: str,
    current_items: list[dict[str, Any]],
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    order_no = _instruction_order_no(instruction)
    if not order_no or not _looks_like_detail_instruction(instruction):
        return items
    before = next((item for item in current_items if int(item.get("order_no") or 0) == order_no), None)
    after_index = next((index for index, item in enumerate(items) if int(item.get("order_no") or 0) == order_no), -1)
    if after_index < 0:
        return items
    if _item_changed_enough(before, items[after_index]):
        return items
    updated = [dict(item) for item in items]
    updated[after_index] = _expand_review_item_by_instruction(updated[after_index], instruction)
    return updated


def _sanitize_overall_opinion(value: Any, fallback: dict[str, Any] | None, items: list[dict[str, Any]]) -> dict[str, Any]:
    source = value.get("overall_opinion") if isinstance(value, dict) else None
    if not isinstance(source, dict):
        source = fallback if isinstance(fallback, dict) else {}
    conclusion = _short_text(source.get("conclusion") or source.get("recommendation") or "", 1600)
    risk_level = _short_text(source.get("risk_level") or "", 40)
    if not conclusion:
        conclusion = _build_overall_review_item({"risk_level": risk_level}, items).get("conclusion") or ""
    elif _overall_text_needs_formal_tone(conclusion):
        conclusion = _formal_overall_review_text({"risk_level": risk_level}, items, conclusion)
    return {
        "order_no": 0,
        "title": "综合评价",
        "conclusion": conclusion,
        "risk_level": risk_level,
        "basis": [],
        "recommendation": "",
        "source": {"kind": "overall_summary"},
    }


def _stage_key_for_overall(stage: Any) -> str:
    text = str(stage or "")
    for key in STAGE_STYLE_RULES:
        if key and key in text:
            return key
    return "规划"


def _contains_hard_rejection_text(*parts: Any) -> bool:
    text = " ".join(str(part or "") for part in parts)
    return bool(re.search(r"(不予通过|不同意|不得(?:实施|施工|推进|进入)|不可(?:实施|施工)|退回|否决)", text))


def _formal_overall_review_text(
    result: dict[str, Any],
    selected_items: list[dict[str, Any]],
    raw_summary: str = "",
) -> str:
    archive_binding = result.get("archive_binding") or {}
    stage = (
        archive_binding.get("stage_name")
        or result.get("project_stage")
        or result.get("stage_name")
        or ""
    )
    stage_key = _stage_key_for_overall(stage)
    has_items = bool(selected_items)
    hard_rejection = _contains_hard_rejection_text(
        raw_summary,
        *[
            " ".join([
                str(item.get("title") or ""),
                str(item.get("conclusion") or ""),
                str(item.get("recommendation") or ""),
            ])
            for item in selected_items
        ],
    )

    if hard_rejection:
        return (
            "经审查，本次报审资料已按基坑项目涉铁保护区审查流程完成阶段性核查，资料组织和审查程序总体符合本阶段合规审查要求。"
            "后续在落实下列审核意见、完成方案修改、资料补充和专项复核，并确认保护区安全控制措施完善后，可按程序推进后续工作。"
        )
    if not has_items:
        return (
            "经审查，本次报审资料与本阶段地铁保护区管理要求总体相符，资料内容和审查程序总体符合基坑项目合规审查要求，未发现需单独列出的主要风险事项。"
            "后续仍应按规范落实保护区管理、施工控制、监测和报审要求。"
        )
    if stage_key == "规划":
        return (
            "经审查，本次规划资料总体符合基坑项目涉铁保护区审查流程要求，已具备开展规划阶段合规审查和方案深化的基础。"
            "后续在落实下列审核意见、完善线位布置、净距控制、专项评估及报审材料后，可按程序推进后续工作。"
        )
    if stage_key == "设计":
        return (
            "经审查，本次设计资料总体符合基坑项目涉铁保护区审查流程要求，已具备开展设计阶段合规审查和方案完善的基础。"
            "后续在落实下列审核意见、补充完善相关资料及安全控制措施后，可按程序推进施工图深化及备案审查工作。"
        )
    if stage_key == "施工":
        return (
            "经审查，本次施工资料总体符合基坑项目涉铁保护区审查流程要求，已具备开展施工阶段合规审查和现场保护控制的基础。"
            "后续在落实下列审核意见、完善施工组织及监测应急措施后，可按程序推进后续施工管理工作。"
        )
    if stage_key == "出让":
        return (
            "经审查，本次资料总体符合基坑项目涉铁保护区前期审查流程要求，已基本具备作为后续规划设计深化依据的合规基础。"
            "后续在落实下列审核意见、明确保护区控制条件及报审衔接要求后，可按程序推进后续工作。"
        )
    return (
        "经审查，本次资料总体符合基坑项目涉铁保护区审查流程要求，已具备开展本阶段合规审查和方案深化的基础。"
        "后续在落实下列审核意见、补充完善相关资料及安全控制措施后，可按程序推进后续工作。"
    )


def _overall_text_needs_formal_tone(text: str) -> bool:
    return bool(re.search(
        r"(不予通过|不同意|不可实施|不得进入|不得实施|多项高风险|高风险及不合规|总体结论为|"
        r"缺乏|不足|超限|缺陷|缺失|不满足|不符合|严禁|必须严格)",
        str(text or ""),
    ))


def _deterministic_instruction_items(
    instruction: str,
    current_items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str] | None:
    order_no = _instruction_order_no(instruction)
    if order_no and re.search(r"(不要|删除|去掉|移除|删掉)", instruction):
        remaining = [
            _public_review_item(item)
            for item in current_items
            if int(item.get("order_no") or 0) != order_no
        ]
        if len(remaining) == len(current_items):
            raise ValueError(f"未找到第{order_no}条审核结果。")
        if not remaining:
            raise ValueError("至少需要保留一条审核结果。")
        for index, item in enumerate(remaining, start=1):
            item["order_no"] = index
        return remaining, f"已删除第{order_no}条审核结果，并重新编号。"
    return None


def _looks_like_review_edit_instruction(instruction: str) -> bool:
    text = str(instruction or "").strip()
    if not text:
        return False
    if re.search(r"(是什么|为什么|依据|来源|哪[里儿]|怎么理解|解释|说明一下|含义|什么意思|是否|能否|可以吗|吗[？?]?)", text):
        return False
    edit_verbs = (
        "添加", "新增", "补充", "增加", "加入",
        "删除", "删掉", "去掉", "不要", "移除",
        "修改", "调整", "改成", "改为", "替换", "恢复",
        "详细", "细化", "展开", "扩写", "丰富", "完善", "优化",
        "上一版", "刚才一版", "回到", "撤销",
    )
    review_words = ("审核", "意见", "结果", "条目", "条", "结论", "建议", "风险", "依据")
    if any(verb in text for verb in edit_verbs) and any(word in text for word in review_words):
        return True
    if re.search(r"第\s*(\d+|[一二三四五六七八九十]+)\s*(?:条|点|项|个)", text) and any(verb in text for verb in edit_verbs):
        return True
    return False


def _format_basis_text(value: Any) -> str:
    if not value:
        return ""
    values = value if isinstance(value, list) else [value]
    parts: list[str] = []
    for item in values:
        if item is None:
            continue
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = " ".join(str(item.get(key) or "").strip() for key in ("document", "document_title", "clause", "section", "quote", "text"))
        else:
            text = str(item).strip()
        if text:
            parts.append(text)
    return "；".join(parts)


def _deterministic_review_question_answer(
    instruction: str,
    session: dict[str, Any],
) -> str | None:
    order_no = _instruction_order_no(instruction)
    if not order_no:
        return None
    if not re.search(r"(依据|来源|为什么|是什么|哪[里儿]|怎么理解|说明|解释)", instruction):
        return None
    target = None
    for item in session.get("items") or []:
        if int(item.get("order_no") or 0) == order_no:
            target = _public_review_item(item)
            break
    if not target:
        return f"1. 我没有找到第{order_no}条审核意见。\n\n2. 你可以先确认当前结果中是否存在该编号，或让我按现有条目重新编号后再查询。"

    basis = _format_basis_text(target.get("basis"))
    title = target.get("title") or f"第{order_no}条审核意见"
    opinion = target.get("conclusion") or target.get("recommendation") or ""
    lines = [
        f"1. 第{order_no}条意见的主题是：{title}。",
    ]
    if basis:
        lines.append(f"2. 直接依据是：{basis}。")
        lines.append("3. 这条意见是结合上述依据与当前资料中的风险点形成的，主要用于明确需要补充、复核或落实的控制要求。")
    else:
        lines.append("2. 当前条目没有单独保存明确的规程条款依据。")
        lines.append("3. 从意见正文看，它主要依据当前资料暴露出的风险点和保护区安全控制要求形成。")
    if opinion:
        lines.append(f"4. 对应意见正文是：{opinion}")
    return _clean_assistant_plain_text("\n\n".join(lines))


def _clean_assistant_plain_text(value: Any) -> str:
    text = _short_text(value or "", 12000)
    if not text:
        return ""
    text = re.sub(r"\$+\s*K\s*\$+\s*值", "渗透系数K值", text, flags=re.IGNORECASE)
    text = re.sub(r"\$+\s*K\s*\$+", "渗透系数K", text, flags=re.IGNORECASE)
    text = re.sub(r"\$+\s*F\s*_\s*s\s*\\?geq\s*([0-9.]+)\s*\$+", r"抗突涌安全系数Fs不小于\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\$+\s*F\s*_\s*s\s*\$+", "抗突涌安全系数Fs", text, flags=re.IGNORECASE)
    text = re.sub(r"\(\s*抗突涌安全系数Fs\s*\)", "抗突涌安全系数Fs", text)
    text = re.sub(r"（\s*抗突涌安全系数Fs\s*）", "抗突涌安全系数Fs", text)
    text = re.sub(r"\(\s*渗透系数K值\s*\)", "渗透系数K值", text)
    text = re.sub(r"（\s*渗透系数K值\s*）", "渗透系数K值", text)
    text = re.sub(r"\\geq", "不小于", text)
    text = re.sub(r"\\leq", "不大于", text)
    text = re.sub(r"\\times", "乘以", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"\$+", "", text)
    text = re.sub(r"\bF\s*_\s*s\b", "抗突涌安全系数Fs", text, flags=re.IGNORECASE)
    text = re.sub(r"\bK\s*_\s*([a-zA-Z])\b", r"K\1", text)
    text = re.sub(r"```(?:json|markdown|md)?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*(?!\*)", r"\1", text)
    text = re.sub(r"[*#]+", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r'["\']?(order_no|title|conclusion|risk_level|basis|recommendation|reply|items|overall_opinion)["\']?\s*:\s*', "", text)
    text = re.sub(r"[{}\[\]]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ，,。；;：:")


def _ai_free_chat(instruction: str, session: dict[str, Any]) -> str:
    current_items = [_public_review_item(item) for item in session.get("items") or []]
    messages = session.get("messages") or []
    history = [
        {"role": item.get("role"), "content": item.get("content")}
        for item in messages[-12:]
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]
    question = (
        "你正在案例审核模块中与用户自由对话。当前最新版审核意见如下，仅作为上下文参考；"
        "如果用户不是明确要求增删改查审核意见，请只回答问题，不要改动审核意见。\n\n"
        "回复要求：使用简洁正式中文，内容较长时按1、2、3分段说明，每段只讲一个要点；"
        "公式和变量必须写成中文工程表达，例如“渗透系数K值”“抗突涌安全系数Fs不小于1.05”；"
        "不要输出Markdown、JSON、代码块、星号、井号、字段名或内部结构。\n\n"
        f"当前审核意见：{json.dumps(current_items, ensure_ascii=False)}\n\n"
        f"用户问题：{instruction}"
    )
    result = agent.chat(question, history, [], False)
    return _clean_assistant_plain_text(result.get("answer") or "")


def _ai_rewrite_review_items(
    instruction: str,
    session: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    current_items = [_public_review_item(item) for item in session.get("items") or []]
    current_overall = (session.get("metadata") or {}).get("overall_opinion") or {}
    system = (
        "你是轨道交通保护区审核结果编辑助手。你的任务是根据用户指令，对上一版审核结果逐条进行增删改。"
        "必须严格基于现有审核条目和用户明确指令，不得编造工程数值、距离、地质条件、规范名称或事实。"
        "用户要求删除时只删除指定条目并重新编号；用户要求添加时，如缺少必要判断数据，应新增一条需补充资料/需核实的审核要求，"
        "不得擅自填写具体数值。未被用户要求修改的条目必须尽量原样保留。"
        "审核意见默认控制在5至6条核心条目，最多6条；合并重复或次要条目，优先保留高风险、关键合规、资料缺失和后续报审要求。"
        "每条审核意见应按技术规程审核逻辑展开，约100至200个汉字，避免只给一句简短建议；"
        "需要说明该项需补充、复核、明确或落实的内容，以及对应的安全控制/报审管理要求。"
        "overall_opinion/综合评价必须与正式复函口径保持一致，采用正向、概括、公文式表达：先说明资料已收悉/已完成审查/具备审查基础，"
        "再说明可在落实下列意见后按程序推进；不得在综合评价中集中罗列高风险、不合规、不可实施、不予通过等负面判断。"
        "items中的每一条只写具体处理意见、补充要求或管理要求，不写“符合要求、风险可控、已满足、已落实、低于限值、严于规范”等评价性判断；"
        "风险、缺陷、资料缺失、超限、需修改等负面内容统一放入分条意见，不得堆在综合评价中。"
        "不要把综合评价或综合意见作为items中的一条审核意见；items只保留逐条具体意见。"
        "公式和变量必须写成中文工程表达，例如“渗透系数K值”“抗突涌安全系数Fs不小于1.05”，不得输出$、\\geq、下标或LaTeX格式。"
        "只输出JSON，不要输出Markdown。"
    )
    ctx = json.dumps({
        "version_no": session.get("current_version"),
        "overall_opinion": current_overall,
        "items": current_items,
    }, ensure_ascii=False)
    prompt = (
        f"当前审核结果版本：{ctx}\n\n"
        f"用户修改指令：{instruction}\n\n"
        "请返回JSON：{\"reply\":\"用1至3个短句说明本次改动，不要输出Markdown\",\"overall_opinion\":{\"title\":\"综合评价\",\"conclusion\":\"与复函评价一致的正向概括文字，不集中罗列负面问题\",\"risk_level\":\"高/中/低/提示/可为空\"},\"items\":[{\"order_no\":1,\"title\":\"8至20字的意见主题\",\"conclusion\":\"100至200字的正式审核意见，只写意见和要求，不写评价性判断；如内容较长可按1、2、3组织要点\",\"risk_level\":\"高/中/低/提示/可为空\",\"basis\":[],\"recommendation\":\"可为空；如填写也必须是具体要求\"}]}\n"
        "要求：items 必须是修改后的完整最新版审核结果列表，不是增量补丁；数量保持5至6条，最多6条；不要输出依据块或建议块。"
    )
    value = agent.complete_json(system, prompt, max_tokens=5200)
    items = _sanitize_review_items(value, current_items)
    items = _merge_partial_review_items(instruction, current_items, items)
    items = _ensure_detail_instruction_applied(instruction, current_items, items)
    overall = _sanitize_overall_opinion(value, current_overall, items)
    reply = "已根据你的指令更新审核结果。"
    if isinstance(value, dict) and value.get("reply"):
        reply = _clean_assistant_plain_text(value.get("reply"))[:1000] or reply
    return items, overall, reply


def _apply_audit_chat_instruction(session_id: str, instruction: str) -> dict[str, Any]:
    session = audit_sessions.get_session(session_id)
    current_items = session.get("items") or []
    if not current_items:
        raise ValueError("当前会话还没有可修改的审核结果。")
    audit_sessions.add_message(session_id, {"role": "user", "content": instruction})
    deterministic = _deterministic_instruction_items(instruction, current_items)
    if deterministic is not None:
        items, reply = deterministic
        overall = _sanitize_overall_opinion({}, (session.get("metadata") or {}).get("overall_opinion") or {}, items)
    elif _looks_like_review_edit_instruction(instruction):
        items, overall, reply = _ai_rewrite_review_items(instruction, session)
    else:
        updated = audit_sessions.get_session(session_id)
        reply = _deterministic_review_question_answer(instruction, updated)
        if not reply:
            reply = _clean_assistant_plain_text(_ai_free_chat(instruction, updated)) or "1. 我已收到你的问题。\n\n2. 当前没有检索到足够上下文，请换一种问法或指出具体第几条意见。"
        assistant_message = audit_sessions.add_message(session_id, {
            "role": "assistant",
            "content": reply,
            "result_snapshot": {},
        })
        updated = audit_sessions.get_session(session_id)
        return {
            "session": updated,
            "message": assistant_message,
            "review_items": updated["items"],
            "updated_review": False,
        }
    updated = audit_sessions.replace_items(session_id, items, manual_modified=True, overall_opinion=overall)
    assistant_message = audit_sessions.add_message(session_id, {
        "role": "assistant",
        "content": reply,
        "version_no": updated.get("current_version"),
        "result_snapshot": updated.get("latest_result") or {},
    })
    updated = audit_sessions.get_session(session_id)
    return {
        "session": updated,
        "message": assistant_message,
        "review_items": updated["items"],
        "updated_review": True,
    }


def _risk_rank(value: str) -> int:
    text = str(value or "")
    if any(token in text for token in ("重大", "极高", "高")):
        return 3
    if "中" in text:
        return 2
    if "低" in text:
        return 1
    return 0


def _session_archive_data(
    session: dict[str, Any],
    form_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    items = [item for item in (session.get("items") or []) if not _is_overall_review_item(item)]
    overall_opinion = (session.get("metadata") or {}).get("overall_opinion") or {}
    risk_level = ""
    if items:
        risk_level = max(
            (str(item.get("risk_level") or "") for item in items),
            key=_risk_rank,
            default="",
        )
    summary_lines = []
    for item in items[:20]:
        text = _short_text(item.get("conclusion") or item.get("recommendation"), 800)
        if text:
            summary_lines.append(f"{item.get('order_no')}. {item.get('title') or '审核事项'}：{text}")
    if overall_opinion.get("conclusion"):
        summary_lines.append(f"综合意见：{_short_text(overall_opinion.get('conclusion'), 1000)}")
    summary = "\n".join(summary_lines) or "最新版审核结果已写入档案。"
    result_data = {
        "stage": "editable_audit_session",
        "audit_session_id": session["session_id"],
        "version_no": session.get("current_version"),
        "review_items": items,
        "overall_opinion": overall_opinion,
        "form_data": form_data or {},
        "latest_result": session.get("latest_result") or {},
    }
    return {
        "result": "审核完成",
        "risk_level": risk_level or "待判断",
        "summary": summary[:10000],
        "result_data": result_data,
        "artifacts": [],
    }


def _session_project_data(session: dict[str, Any], payload: AuditSessionReplyPayload) -> dict[str, Any]:
    form = dict(payload.form_data or {})
    project_name = (
        payload.project_name
        or form.get("project_name")
        or (session.get("metadata") or {}).get("project_name")
        or "项目名称待补充"
    )
    applicant = payload.applicant or form.get("applicant") or "收函单位待补充"
    stage = (
        payload.project_stage
        or form.get("project_stage")
        or (session.get("metadata") or {}).get("stage_name")
        or "规划阶段"
    )
    return {
        "project": {
            "project_name": project_name,
            "applicant": applicant,
            "project_stage": stage,
            "project_type": form.get("project_type", ""),
            "project_address": form.get("project_address", ""),
            "construction_content": form.get("construction_content", ""),
            "relative_relationship": form.get("relative_relationship", ""),
        },
        "metro_structure": {
            "metro_line_name": form.get("metro_line_name", ""),
            "metro_section_name": form.get("metro_section_name", ""),
            "structure_method": form.get("structure_method", ""),
            "buried_depth_m": form.get("buried_depth_m"),
        },
        "pit": {
            "pit_depth_m": form.get("pit_depth_m"),
            "pit_length_m": form.get("pit_length_m"),
            "minimum_horizontal_clearance_m": form.get("minimum_horizontal_clearance_m"),
            "minimum_vertical_clearance_m": form.get("minimum_vertical_clearance_m"),
            "dewatering_method": form.get("dewatering_method", ""),
            "support_components": form.get("support_components") or [],
        },
    }


def _session_reply_package(
    session: dict[str, Any],
    payload: AuditSessionReplyPayload,
) -> dict[str, Any]:
    data = _session_project_data(session, payload)
    project = data["project"]
    items = [item for item in (session.get("items") or []) if not _is_overall_review_item(item)]
    overall_opinion = (session.get("metadata") or {}).get("overall_opinion") or {}
    overall_conclusion = _short_text(overall_opinion.get("conclusion") or overall_opinion.get("recommendation") or "", 1600)
    if not overall_conclusion or _overall_text_needs_formal_tone(overall_conclusion):
        overall_conclusion = _formal_overall_review_text(
            {
                "project_stage": project.get("project_stage") or "",
                "risk_level": _session_archive_data(session)["risk_level"],
            },
            items,
            overall_conclusion,
        )
    findings = []
    audit_opinions = []
    for item in items:
        basis = item.get("basis") or []
        clauses = [
            str(value if isinstance(value, str) else value.get("clause") or value.get("quote") or value)
            for value in basis
            if value
        ]
        findings.append({
            "title": item.get("title"),
            "risk_level": item.get("risk_level") or "鎻愮ず",
            "judgement": "risk",
            "analysis": item.get("conclusion") or item.get("recommendation"),
            "recommendation": item.get("recommendation") or item.get("conclusion"),
            "regulation_evidence": [
                {
                    "document_title": value.get("document") if isinstance(value, dict) else "",
                    "section": value.get("clause") if isinstance(value, dict) else "",
                    "quote": value.get("quote") if isinstance(value, dict) else str(value),
                }
                for value in basis
            ],
        })
        audit_opinions.append({
            "topic": item.get("title"),
            "result": "人工确认",
            "conclusion": item.get("recommendation") or item.get("conclusion"),
            "regulation_clauses": clauses,
        })
    dynamic_audit = {
        "risk_report": {
            "overall_risk_level": _session_archive_data(session)["risk_level"],
            "overall_conclusion": overall_conclusion or "已按最新版审核结果形成本次复函意见。",
            "required_supplements": [],
            "findings": findings,
        }
    }
    package = {
        "format_version": "editable_session_reply_package_v1",
        "case_id": session["session_id"],
        "project_facts": [
            {"label": "项目名称", "value": project["project_name"]},
            {"label": "项目阶段", "value": project["project_stage"]},
            {"label": "报审单位", "value": project["applicant"]},
        ],
        "audit_opinions": audit_opinions,
        "historical_advice": {},
        "history_match": {},
        "dynamic_regulation_audit": dynamic_audit,
    }
    package["formal_reply"] = generate_formal_reply_content(
        package,
        data,
        dynamic_audit,
        agent=agent,
    )
    return package


REPLY_LIBRARY_STAGES = ("规划阶段", "设计阶段", "施工阶段")


def _normalize_reply_library_stage(stage: Any) -> str:
    text = str(stage or "").strip()
    if text in REPLY_LIBRARY_STAGES:
        return text
    if "规划" in text:
        return "规划阶段"
    if "施工" in text:
        return "施工阶段"
    if "设计" in text or "方案" in text or "施工图" in text:
        return "设计阶段"
    return "设计阶段"


def _save_generated_reply_to_library(
    session: dict[str, Any],
    payload: AuditSessionReplyPayload,
    target: Path,
) -> dict[str, Any] | None:
    if not payload.save_to_reply_library:
        return None
    data = _session_project_data(session, payload)
    project = data["project"]
    project_name = str(project.get("project_name") or "").strip()
    if not project_name:
        return None
    stage_name = _normalize_reply_library_stage(project.get("project_stage"))
    version = session.get("current_version") or 1
    display_name = f"{project_name}{stage_name}复函（第{version}版）"
    return library_assets.add(
        target,
        "case",
        None,
        display_name,
    )


def _generate_audit_session_reply_file(
    session_id: str,
    payload: AuditSessionReplyPayload,
) -> Path:
    session = audit_sessions.get_session(session_id)
    if not session.get("items"):
        raise ValueError("当前会话没有可用于生成复函的审核结果。")
    package = _session_reply_package(session, payload)
    output_dir = RESULT_ROOT / "audit_sessions" / session_id / f"reply_v{session.get('current_version')}"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "review_package.json").write_text(
        json.dumps(package, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    target = output_dir / "最终版复函.docx"
    render_reply_draft_docx(package, target)
    _save_generated_reply_to_library(session, payload, target)
    return target


def _write_audit_session_to_archive(
    session_id: str,
    payload: AuditSessionArchivePayload,
) -> dict[str, Any]:
    session = audit_sessions.get_session(session_id)
    if not session.get("items"):
        raise ValueError("当前会话没有可写入档案的审核结果。")
    if payload.stage_id:
        stage = project_archives.get_stage(payload.stage_id)
        if payload.project_id and stage["project_id"] != payload.project_id:
            raise ValueError("项目与阶段不匹配。")
        project = project_archives.get_project(stage["project_id"])
        stage_id = stage["stage_id"]
        resolved = {"project": project, "stage": stage, "project_created": False, "stage_created": False}
    else:
        resolved = project_archives.resolve_project_stage(payload.project_name, payload.stage_name)
        stage_id = resolved["stage"]["stage_id"]
    form_data = payload.form_data or {}
    location_patch = {
        key: form_data.get(key)
        for key in ("location", "longitude", "latitude")
        if form_data.get(key) not in (None, "")
    }
    if location_patch:
        try:
            project_archives.update_project(resolved["project"]["project_id"], location_patch)
            resolved["project"] = project_archives.get_project(resolved["project"]["project_id"])
        except ValueError:
            pass
    history_context = project_archives.history_context_for_stage(stage_id)
    existing = project_archives.get_stage_audit(stage_id)
    if existing and existing.get("status") == "success" and not payload.overwrite:
        raise ValueError("该阶段已经存在审核记录。")
    record = project_archives.write_stage_audit(
        stage_id,
        _session_archive_data(session, payload.form_data),
        source_task_id=session.get("source_task_id") or "",
        overwrite=payload.overwrite,
        history_context=history_context,
    )
    return {
        "archive_record": record,
        "project": resolved["project"],
        "stage": project_archives.get_stage(stage_id),
        "overwritten": bool(existing and payload.overwrite),
        "project_created": bool(resolved.get("project_created")),
        "stage_created": bool(resolved.get("stage_created")),
    }


def _ensure_archive_record_session(record: dict[str, Any]) -> dict[str, Any]:
    if not record or record.get("status") != "success":
        return record
    result_data = record.get("result_data") if isinstance(record.get("result_data"), dict) else {}
    session_id = str(result_data.get("audit_session_id") or "")
    if session_id:
        try:
            audit_sessions.get_session(session_id)
            record["audit_session_id"] = session_id
            return record
        except KeyError:
            pass

    latest = result_data.get("latest_result") if isinstance(result_data.get("latest_result"), dict) else {}
    raw_items = result_data.get("review_items") or result_data.get("items") or latest.get("items") or latest.get("review_items") or []
    try:
        items = _sanitize_review_items({"items": raw_items}, [])
    except ValueError:
        LOGGER.warning(
            "Archive audit %s has no valid review items; restoring it as an empty editable session.",
            record.get("audit_id"),
        )
        items = []
    if not items:
        items = _audit_result_to_review_items(result_data)
    overall = _sanitize_overall_opinion(
        {"overall_opinion": result_data.get("overall_opinion") or latest.get("overall_opinion") or {}},
        {},
        items,
    )
    project_id = str(record.get("project_id") or "")
    stage_id = str(record.get("stage_id") or "")
    stage: dict[str, Any] = {}
    project: dict[str, Any] = {}
    try:
        stage = project_archives.get_stage(stage_id)
        project = project_archives.get_project(project_id)
    except Exception:
        pass
    session = audit_sessions.create_session({
        "source_task_id": record.get("source_task_id") or record.get("audit_id") or "",
        "project_id": project_id,
        "stage_id": stage_id,
        "status": "reviewing",
        "metadata": {
            "task_type": "archive_restored_session",
            "project_name": project.get("name") or stage.get("project_name") or "",
            "stage_name": stage.get("name") or "",
            "overall_opinion": overall,
            "restored_from_archive_audit_id": record.get("audit_id"),
        },
        "items": items,
        "initial_message": "已从项目档案恢复上一版审核结果，可以继续提问或修改。",
    })
    patched = dict(result_data)
    patched["audit_session_id"] = session["session_id"]
    patched["review_items"] = session.get("items") or items
    patched["overall_opinion"] = overall
    patched["latest_result"] = session.get("latest_result") or patched.get("latest_result") or {}
    updated = project_archives.update_audit_result_data(record["audit_id"], patched)
    updated["audit_session_id"] = session["session_id"]
    return updated


def _create_audit_task(
    task_type: str,
    source_file: Path,
    worker,
    archive_context: dict[str, Any] | None,
    *,
    attachments: dict[str, Path] | None = None,
    auto_archive: bool = True,
    manual_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not archive_context or not auto_archive:
        def session_worker(task_id: str, progress):
            result = worker(task_id, progress)
            if manual_context:
                result["manual_context_for_consistency"] = manual_context
            return _attach_audit_session(
                result,
                task_id=task_id,
                archive_context=archive_context,
            )

        return tasks.create(task_type, source_file, session_worker)
    stage_id = str((archive_context.get("current_stage") or {}).get("stage_id") or "")
    audit_holder: dict[str, Any] = {}

    def reserve(task_id: str) -> None:
        try:
            audit_holder.update(project_archives.begin_audit(
                stage_id,
                task_id,
                source_files=_source_file_records(source_file, attachments),
                history_context=archive_context,
            ))
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    def archive_worker(task_id: str, progress):
        audit_id = str(audit_holder["audit_id"])
        project_archives.mark_audit_running(audit_id)
        try:
            result = worker(task_id, progress)
            if manual_context:
                result["manual_context_for_consistency"] = manual_context
            result = _attach_audit_session(
                result,
                task_id=task_id,
                archive_context=archive_context,
            )
            archived = project_archives.complete_audit(
                audit_id, _archive_completion_data(result)
            )
        except Exception as exc:
            try:
                project_archives.fail_audit(
                    audit_id, (str(exc) or type(exc).__name__)[:4000]
                )
            except ValueError:
                pass
            raise
        result["archive_record"] = {
            key: archived.get(key)
            for key in (
                "audit_id", "project_id", "stage_id", "source_task_id", "status",
                "attempt_count", "audit_date", "result", "risk_level", "summary",
                "completed_at",
            )
        }
        return result

    return tasks.create(
        task_type,
        source_file,
        archive_worker,
        before_submit=reserve,
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "audit-api", "version": app.version, "knowledge": knowledge.stats()}


@app.get(
    "/api/v1/project-archives/projects",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def list_archive_projects(
    keyword: str = "",
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    return project_archives.list_projects(
        search=keyword,
        status=None if include_archived else "active",
    )


@app.get(
    "/api/v1/project-archives/projects/nearby",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def list_nearby_archive_projects(
    longitude: Annotated[float, Query(ge=-180, le=180)],
    latitude: Annotated[float, Query(ge=-90, le=90)],
    radius_m: Annotated[int, Query(ge=1, le=10000)] = 1000,
    exclude_project_id: str = "",
    limit: Annotated[int, Query(ge=1, le=50)] = 12,
) -> list[dict[str, Any]]:
    try:
        return project_archives.nearby_projects(
            longitude,
            latitude,
            radius_m=radius_m,
            exclude_project_id=exclude_project_id,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post(
    "/api/v1/project-archives/projects",
    status_code=201,
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def create_archive_project(payload: ArchiveProjectCreatePayload) -> dict[str, Any]:
    try:
        return project_archives.create_project(_model_values(payload))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post(
    "/api/v1/project-archives/resolve",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def resolve_archive_project_stage(payload: ArchiveResolvePayload) -> dict[str, Any]:
    try:
        return project_archives.resolve_project_stage(payload.project_name, payload.stage_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get(
    "/api/v1/project-archives/projects/{project_id}",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def get_archive_project(
    project_id: str,
    include_archived_stages: bool = False,
) -> dict[str, Any]:
    try:
        return project_archives.get_project(
            project_id,
            include_archived_stages=include_archived_stages,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post(
    "/api/v1/project-archives/projects/{project_id}",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def update_archive_project(
    project_id: str,
    payload: ArchiveProjectUpdatePayload,
) -> dict[str, Any]:
    try:
        return project_archives.update_project(project_id, _model_values(payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete(
    "/api/v1/project-archives/projects/{project_id}",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def delete_archive_project(project_id: str) -> dict[str, Any]:
    try:
        return project_archives.delete_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post(
    "/api/v1/project-archives/projects/{project_id}/archive",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def archive_project(project_id: str) -> dict[str, Any]:
    try:
        return project_archives.set_project_archived(project_id, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post(
    "/api/v1/project-archives/projects/{project_id}/restore",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def restore_project(project_id: str) -> dict[str, Any]:
    try:
        return project_archives.set_project_archived(project_id, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get(
    "/api/v1/project-archives/projects/{project_id}/latest-audit-form",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def get_latest_project_audit_form(project_id: str) -> dict[str, Any]:
    try:
        record = project_archives.latest_successful_audit_for_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    form_data = _archive_record_form_data(record) if record else {}
    return {
        "project_id": project_id,
        "has_record": bool(record),
        "source_stage_id": record.get("stage_id") if record else "",
        "source_stage_name": record.get("stage_name") if record else "",
        "source_audit_id": record.get("audit_id") if record else "",
        "form_data": form_data,
    }


@app.post(
    "/api/v1/project-archives/projects/{project_id}/stages",
    status_code=201,
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def create_archive_stage(
    project_id: str,
    payload: ArchiveStageCreatePayload,
) -> dict[str, Any]:
    try:
        return project_archives.create_stage(project_id, _model_values(payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get(
    "/api/v1/project-archives/stages/{stage_id}",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def get_archive_stage(stage_id: str) -> dict[str, Any]:
    try:
        return project_archives.get_stage(stage_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post(
    "/api/v1/project-archives/stages/{stage_id}",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def update_archive_stage(
    stage_id: str,
    payload: ArchiveStageUpdatePayload,
) -> dict[str, Any]:
    try:
        return project_archives.update_stage(stage_id, _model_values(payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post(
    "/api/v1/project-archives/stages/{stage_id}/archive",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def archive_stage(stage_id: str) -> dict[str, Any]:
    try:
        return project_archives.set_stage_archived(stage_id, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post(
    "/api/v1/project-archives/stages/{stage_id}/restore",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def restore_stage(stage_id: str) -> dict[str, Any]:
    try:
        return project_archives.set_stage_archived(stage_id, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get(
    "/api/v1/project-archives/stages/{stage_id}/audit",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def get_archive_stage_audit(stage_id: str) -> dict[str, Any] | None:
    try:
        record = project_archives.get_stage_audit(stage_id)
        return _ensure_archive_record_session(record) if record else None
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get(
    "/api/v1/project-archives/stages/{stage_id}/previous-audits",
    dependencies=[Depends(verify_service_token)],
    tags=["project-archives"],
)
def get_previous_stage_audits(stage_id: str) -> dict[str, Any]:
    try:
        stage = project_archives.get_stage(stage_id)
        records = project_archives.previous_successful_audits(stage_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    inherited_record = next(
        (record for record in reversed(records) if _archive_record_form_data(record)),
        None,
    )
    return {
        "project_id": stage["project_id"],
        "stage_id": stage_id,
        "stage_name": stage["name"],
        "record_count": len(records),
        "records": records,
        "inherited_form": {
            "source_stage_id": inherited_record.get("stage_id") if inherited_record else "",
            "source_stage_name": inherited_record.get("stage_name") if inherited_record else "",
            "source_audit_id": inherited_record.get("audit_id") if inherited_record else "",
            "form_data": _archive_record_form_data(inherited_record) if inherited_record else {},
        },
    }


@app.post(
    "/api/v1/audit-sessions",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def create_audit_session(payload: AuditSessionCreatePayload) -> dict[str, Any]:
    try:
        return audit_sessions.create_session(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get(
    "/api/v1/audit-sessions/{session_id}",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def get_audit_session(session_id: str) -> dict[str, Any]:
    try:
        return audit_sessions.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get(
    "/api/v1/audit-sessions/{session_id}/items",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def list_audit_session_items(session_id: str) -> list[dict[str, Any]]:
    try:
        return audit_sessions.list_items(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post(
    "/api/v1/audit-sessions/{session_id}/items",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def create_audit_session_item(
    session_id: str,
    payload: AuditReviewItemPayload,
) -> dict[str, Any]:
    try:
        return audit_sessions.create_item(session_id, payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post(
    "/api/v1/audit-sessions/{session_id}/items/{item_id}",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def update_audit_session_item(
    session_id: str,
    item_id: str,
    payload: AuditReviewItemUpdatePayload,
) -> dict[str, Any]:
    try:
        item = audit_sessions.get_item(item_id)
        if item["session_id"] != session_id:
            raise KeyError("审核条目不存在。")
        return audit_sessions.update_item(item_id, payload.model_dump(exclude_unset=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete(
    "/api/v1/audit-sessions/{session_id}/items/{item_id}",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def delete_audit_session_item(session_id: str, item_id: str) -> dict[str, Any]:
    try:
        item = audit_sessions.get_item(item_id)
        if item["session_id"] != session_id:
            raise KeyError("审核条目不存在。")
        return audit_sessions.delete_item(item_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get(
    "/api/v1/audit-sessions/{session_id}/messages",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def list_audit_session_messages(session_id: str) -> list[dict[str, Any]]:
    try:
        return audit_sessions.list_messages(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post(
    "/api/v1/audit-sessions/{session_id}/messages",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def create_audit_session_message(
    session_id: str,
    payload: AuditChatMessagePayload,
) -> dict[str, Any]:
    try:
        return audit_sessions.add_message(session_id, payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post(
    "/api/v1/audit-sessions/{session_id}/chat",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def revise_audit_session_by_chat(
    session_id: str,
    payload: AuditSessionChatPayload,
) -> dict[str, Any]:
    try:
        return _apply_audit_chat_instruction(session_id, payload.instruction)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post(
    "/api/v1/audit-sessions/{session_id}/archive",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def write_audit_session_to_archive(
    session_id: str,
    payload: AuditSessionArchivePayload,
) -> dict[str, Any]:
    try:
        return _write_audit_session_to_archive(session_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "审核会话或项目阶段不存在。") from exc
    except ValueError as exc:
        message = str(exc)
        status_code = 409 if "已经存在审核记录" in message else 422
        raise HTTPException(status_code=status_code, detail=message) from exc


@app.post(
    "/api/v1/audit-sessions/{session_id}/reply",
    dependencies=[Depends(verify_service_token)],
    tags=["audit-sessions"],
)
def generate_audit_session_reply(
    session_id: str,
    payload: AuditSessionReplyPayload,
) -> FileResponse:
    try:
        target = _generate_audit_session_reply_file(session_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return FileResponse(
        target,
        filename=target.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.post("/api/v1/knowledge/cases", status_code=202, dependencies=[Depends(verify_service_token)], tags=["knowledge"])
async def import_knowledge_case(
    file: Annotated[UploadFile, File(description="需要加入知识库的 PDF 或 Word 案例")],
    case_name: Annotated[str | None, Form(description="可选案例名称；不填则使用文件名")] = None,
    category: Annotated[str | None, Form(description="可选案例类别，例如基坑、管线、道路桥梁")] = None,
    folder_id: Annotated[str | None, Form(description="可选案例文件夹编号")] = None,
) -> dict[str, Any]:
    source = await _save_upload(file, "案例知识库", KNOWLEDGE_SUFFIXES)

    def worker(task_id: str, progress):
        item = knowledge.import_case(source, case_name, category, progress, folder_id)
        return {
            "stage": "knowledge_case_import",
            "case": _public_knowledge_case(item, detail=True),
            "artifact_roots": [str(Path(item["stored_file"]).parent)] if item.get("stored_file") else [],
        }

    task = tasks.create("knowledge_case_import", source, worker)
    return {key: task[key] for key in ("task_id", "task_type", "status", "progress", "message")}


@app.get("/api/v1/knowledge/case-folders", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def list_case_folders() -> list[dict[str, Any]]:
    counts = library_assets.folder_counts("case")
    rows = knowledge.list_folders()
    return _folder_tree_counts(rows, counts, "case_count")


@app.post("/api/v1/knowledge/case-folders", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def create_case_folder(payload: CaseFolderPayload) -> dict[str, Any]:
    try:
        return knowledge.create_folder(payload.name, payload.parent_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/knowledge/case-folders/{folder_id}/rename", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def rename_case_folder(folder_id: str, payload: CaseFolderPayload) -> dict[str, Any]:
    try:
        return knowledge.rename_folder(folder_id, payload.name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/v1/knowledge/case-folders/{folder_id}", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def delete_case_folder(folder_id: str) -> dict[str, Any]:
    try:
        item = knowledge.delete_folder(folder_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    detached_assets = library_assets.detach_folder("case", folder_id, item.get("parent_id"))
    return {
        "folder_id": folder_id,
        "deleted": True,
        "detached_case_count": item["case_count"],
        "detached_asset_count": detached_assets,
    }


@app.post("/api/v1/knowledge/cases/{case_id}/folder", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def move_case(case_id: str, payload: CaseMovePayload) -> dict[str, Any]:
    try:
        return _public_knowledge_case(knowledge.set_case_folder(case_id, payload.folder_id), detail=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post("/api/v1/knowledge/cases/{case_id}/rename", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def rename_case(case_id: str, payload: LibraryAssetRenamePayload) -> dict[str, Any]:
    try:
        return _public_knowledge_case(knowledge.rename_case(case_id, payload.name), detail=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/knowledge/cases", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def list_knowledge_cases(
    keyword: str | None = None,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    rows = knowledge.list_cases(keyword=keyword, include_inactive=include_inactive)
    return [_public_knowledge_case(row) for row in rows]


@app.get("/api/v1/knowledge/cases/{case_id}", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def get_knowledge_case(case_id: str) -> dict[str, Any]:
    try:
        return _public_knowledge_case(knowledge.get_case(case_id), detail=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get("/api/v1/knowledge/cases/{case_id}/content", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def get_knowledge_case_content(
    case_id: str,
    limit: Annotated[int, Query(ge=1000, le=500000)] = 50000,
) -> dict[str, Any]:
    try:
        item = knowledge.get_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    text_file = item.get("text_file")
    if not text_file or not Path(text_file).exists():
        raise HTTPException(status_code=404, detail="???????")
    text = Path(text_file).read_text(encoding="utf-8", errors="replace")
    return {
        "case_id": case_id,
        "content": text[:limit],
        "text_length": len(text),
        "truncated": len(text) > limit,
    }


@app.delete("/api/v1/knowledge/cases/{case_id}", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def disable_knowledge_case(case_id: str) -> dict[str, Any]:
    try:
        item = knowledge.set_active(case_id, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    return {"case_id": case_id, "active": item["active"], "message": "案例已停用，不再参与匹配。"}


@app.post("/api/v1/knowledge/cases/{case_id}/restore", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def restore_knowledge_case(case_id: str) -> dict[str, Any]:
    try:
        item = knowledge.set_active(case_id, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    return {"case_id": case_id, "active": item["active"], "message": "案例已恢复。"}


@app.delete("/api/v1/knowledge/cases/{case_id}/permanent", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def delete_knowledge_case(case_id: str) -> dict[str, Any]:
    try:
        item = knowledge.delete_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    cleanup = purge_rag_document(case_id)
    return {
        "case_id": case_id,
        "deleted": True,
        "case_name": item.get("case_name"),
        "cleanup": cleanup,
        "message": "案例及其知识库数据已彻底删除。",
    }


@app.get("/api/v1/knowledge/cases/{case_id}/file", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def download_knowledge_case(case_id: str) -> FileResponse:
    try:
        item = knowledge.get_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    source = item.get("stored_file") or item.get("source_file")
    if not source or not Path(source).exists():
        raise HTTPException(status_code=404, detail="???????")
    path = Path(source)
    return FileResponse(path, filename=item.get("original_file_name") or path.name, media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream")


def _validate_asset_folder(library_type: str, folder_id: str | None) -> None:
    if not folder_id:
        return
    if library_type == "reply":
        return
    try:
        if library_type == "regulation":
            regulations.get_folder(folder_id)
        else:
            knowledge.get_folder(folder_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get("/api/v1/knowledge/assets", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def list_library_assets(
    library_type: Literal["regulation", "case", "reply"],
    folder_id: str | None = None,
    keyword: str | None = None,
) -> list[dict[str, Any]]:
    if library_type == "case":
        case_assets = library_assets.list("case", folder_id, keyword)
        if folder_id:
            return case_assets
        reply_assets = library_assets.list("reply", None, keyword)
        return sorted(
            case_assets + reply_assets,
            key=lambda item: (item.get("updated_at") or "", item.get("display_name") or ""),
            reverse=True,
        )
    return library_assets.list(library_type, folder_id, keyword)


@app.post("/api/v1/knowledge/assets", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
async def upload_library_asset(
    file: Annotated[UploadFile, File(description="知识库普通资料文件")],
    library_type: Annotated[Literal["regulation", "case", "reply"], Form()],
    folder_id: Annotated[str | None, Form()] = None,
    display_name: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    _validate_asset_folder(library_type, folder_id)
    source = await _save_upload(file, "知识库资料", LIBRARY_ASSET_SUFFIXES)
    try:
        return library_assets.add(source, library_type, folder_id, display_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/knowledge/assets/{asset_id}/rename", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def rename_library_asset(asset_id: str, payload: LibraryAssetRenamePayload) -> dict[str, Any]:
    try:
        return library_assets.rename(asset_id, payload.name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/knowledge/assets/{asset_id}/folder", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def move_library_asset(asset_id: str, payload: LibraryAssetMovePayload) -> dict[str, Any]:
    try:
        item = library_assets.get(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    _validate_asset_folder(item["library_type"], payload.folder_id)
    return library_assets.move(asset_id, payload.folder_id)


@app.get("/api/v1/knowledge/assets/{asset_id}/file", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def download_library_asset(asset_id: str) -> FileResponse:
    try:
        item = library_assets.get(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    source = Path(item["stored_file"])
    if not source.exists():
        raise HTTPException(status_code=404, detail="???????")
    return FileResponse(
        source,
        filename=item["original_file_name"],
        media_type=item["media_type"],
    )


@app.delete("/api/v1/knowledge/assets/{asset_id}", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def delete_library_asset(asset_id: str) -> dict[str, Any]:
    try:
        item = library_assets.delete(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    return {"asset_id": asset_id, "deleted": True, "display_name": item["display_name"]}


@app.get("/api/v1/knowledge/stats", dependencies=[Depends(verify_service_token)], tags=["knowledge"])
def knowledge_stats() -> dict[str, int]:
    return knowledge.stats()


@app.post("/api/v1/knowledge/regulations", status_code=202, dependencies=[Depends(verify_service_token)], tags=["regulations"])
async def import_regulation(
    file: Annotated[UploadFile, File(description="需要加入知识库的技术规程 PDF、DOCX 或 TXT")],
    title: Annotated[str | None, Form(description="可选规程名称；不填则使用文件名")] = None,
    version: Annotated[str | None, Form(description="可选版本或发布年份")] = None,
    folder_id: Annotated[str | None, Form(description="可选技术规程文件夹编号")] = None,
) -> dict[str, Any]:
    source = await _save_upload(file, "技术规程知识库", REGULATION_SUFFIXES)

    def worker(task_id: str, progress):
        item = regulations.import_document(source, title, version, progress, folder_id)
        return {
            "stage": "regulation_import",
            "regulation": _public_regulation(item),
            "artifact_roots": [str(Path(item["stored_file"]).parent)],
        }

    task = tasks.create("regulation_import", source, worker)
    return {key: task[key] for key in ("task_id", "task_type", "status", "progress", "message")}


@app.get("/api/v1/knowledge/regulations", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def list_regulations(
    keyword: str | None = None,
    include_inactive: bool = False,
    folder_id: str | None = None,
) -> list[dict[str, Any]]:
    return [
        _public_regulation(item)
        for item in regulations.list_documents(keyword, include_inactive, folder_id)
    ]


@app.get("/api/v1/knowledge/regulation-folders", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def list_regulation_folders() -> list[dict[str, Any]]:
    counts = library_assets.folder_counts("regulation")
    rows = regulations.list_folders()
    return _folder_tree_counts(rows, counts, "regulation_count")


@app.post("/api/v1/knowledge/regulation-folders", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def create_regulation_folder(payload: RegulationFolderPayload) -> dict[str, Any]:
    try:
        return regulations.create_folder(payload.name, payload.parent_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/v1/knowledge/regulation-folders/{folder_id}/rename", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def rename_regulation_folder(folder_id: str, payload: RegulationFolderPayload) -> dict[str, Any]:
    try:
        return regulations.rename_folder(folder_id, payload.name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.delete("/api/v1/knowledge/regulation-folders/{folder_id}", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def delete_regulation_folder(folder_id: str) -> dict[str, Any]:
    try:
        item = regulations.delete_folder(folder_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    detached_assets = library_assets.detach_folder("regulation", folder_id, item.get("parent_id"))
    return {
        "folder_id": folder_id,
        "deleted": True,
        "moved_to_uncategorized": int(item.get("regulation_count") or 0),
        "detached_asset_count": detached_assets,
    }


@app.post("/api/v1/knowledge/regulations/{regulation_id}/folder", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def move_regulation(regulation_id: str, payload: RegulationMovePayload) -> dict[str, Any]:
    try:
        return _public_regulation(regulations.set_document_folder(regulation_id, payload.folder_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post("/api/v1/knowledge/regulations/{regulation_id}/rename", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def rename_regulation(regulation_id: str, payload: LibraryAssetRenamePayload) -> dict[str, Any]:
    try:
        return _public_regulation(regulations.rename_document(regulation_id, payload.name))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/knowledge/regulations/stats", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def regulation_stats() -> dict[str, int]:
    return regulations.stats()


@app.get("/api/v1/knowledge/regulations/{regulation_id}", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def get_regulation(regulation_id: str) -> dict[str, Any]:
    try:
        return _public_regulation(regulations.get_document(regulation_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get("/api/v1/knowledge/regulations/{regulation_id}/content", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def get_regulation_content(regulation_id: str, limit: Annotated[int, Query(ge=1000, le=500000)] = 100000) -> dict[str, Any]:
    try:
        return regulations.document_content(regulation_id, limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get("/api/v1/knowledge/regulations/{regulation_id}/clauses", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def get_regulation_clauses(regulation_id: str, keyword: str | None = None) -> list[dict[str, Any]]:
    try:
        return regulations.list_clauses(regulation_id, keyword)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.get("/api/v1/knowledge/regulations/{regulation_id}/file", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def download_regulation(regulation_id: str) -> FileResponse:
    try:
        item = regulations.get_document(regulation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    path = Path(item["stored_file"])
    return FileResponse(path, filename=item.get("original_file_name") or path.name, media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream")


@app.delete("/api/v1/knowledge/regulations/{regulation_id}", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def disable_regulation(regulation_id: str) -> dict[str, Any]:
    try:
        item = regulations.set_document_active(regulation_id, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    return {"regulation_id": regulation_id, "active": item["active"], "message": "技术规程已停用。"}


@app.post("/api/v1/knowledge/regulations/{regulation_id}/restore", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def restore_regulation(regulation_id: str) -> dict[str, Any]:
    try:
        item = regulations.set_document_active(regulation_id, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    return {"regulation_id": regulation_id, "active": item["active"], "message": "技术规程已恢复。"}


@app.delete("/api/v1/knowledge/regulations/{regulation_id}/permanent", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def delete_regulation(regulation_id: str) -> dict[str, Any]:
    try:
        item = regulations.delete_document(regulation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    cleanup = purge_rag_document(regulation_id)
    return {
        "regulation_id": regulation_id,
        "deleted": True,
        "title": item.get("title"),
        "cleanup": cleanup,
        "message": "技术规程、条款、规则和索引已彻底删除。",
    }


@app.post("/api/v1/knowledge/regulations/{regulation_id}/generate-rules", status_code=202, dependencies=[Depends(verify_service_token)], tags=["regulations"])
def generate_regulation_rules(regulation_id: str) -> dict[str, Any]:
    try:
        item = regulations.get_document(regulation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc

    def worker(task_id: str, progress):
        progress("正在筛选数值、条件和表格映射类候选条款。")
        batches = regulations.ai_rule_batches(regulation_id)
        if not batches:
            raise ValueError("未找到可转换为数值、条件或表格规则的候选条款。")
        total_candidates = sum(len(lookup) for _, _, lookup in batches)
        created = []
        errors = []
        future_map = {}

        def recognize(system: str, prompt: str, output_tokens: int):
            last_error = None
            for _ in range(2):
                try:
                    return agent.complete_json(system, prompt, max_tokens=output_tokens)
                except Exception as exc:
                    last_error = exc
            raise last_error

        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="regulation-ai") as executor:
            for batch_index, (system, prompt, lookup) in enumerate(batches):
                source_size = sum(len(value.get("text") or "") for value in lookup.values())
                output_tokens = min(6000, max(1600, 1200 + source_size))
                future = executor.submit(recognize, system, prompt, output_tokens)
                future_map[future] = (batch_index, lookup)

            for completed_batches, future in enumerate(as_completed(future_map), start=1):
                batch_index, lookup = future_map[future]
                candidate = next(iter(lookup.values()))
                try:
                    value = future.result()
                    created.extend(regulations.save_single_pass_ai_rules(regulation_id, value, lookup))
                except Exception as exc:
                    errors.append({
                        "clause": candidate.get("clause"),
                        "candidate_id": candidate.get("candidate_id"),
                        "error": "AI识别失败：" + str(exc),
                    })
                progress(f"已找到{total_candidates}条候选内容，已完成{completed_batches}/{len(batches)}批。")
        published = sum(1 for value in created if value.get("status") == "published")
        drafts = len(created) - published
        progress(f"处理完成：AI识别并自动发布{published}条，未形成合法规则{len(errors)}条。")
        return {
            "stage": "regulation_rule_generation",
            "regulation": _public_regulation(item),
            "rules": created,
            "summary": {"created": len(created), "auto_published": published, "draft": drafts, "failed_candidates": len(errors)},
            "candidate_errors": errors,
            "artifact_roots": [],
        }

    source = Path(item["stored_file"])
    task = tasks.create("regulation_rule_generation", source, worker)
    return {key: task[key] for key in ("task_id", "task_type", "status", "progress", "message")}


@app.get("/api/v1/knowledge/rules", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def list_regulation_rules(regulation_id: str | None = None, rule_status: str | None = None) -> list[dict[str, Any]]:
    return regulations.list_rules(regulation_id, rule_status)


@app.post("/api/v1/knowledge/rules/{rule_id}", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def update_regulation_rule(rule_id: str, payload: RulePayload) -> dict[str, Any]:
    try:
        return regulations.update_rule(rule_id, payload.rule)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc


@app.post("/api/v1/knowledge/rules/{rule_id}/test", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def test_regulation_rule(rule_id: str, payload: RuleTestPayload) -> dict[str, Any]:
    try:
        item = regulations.get_rule(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    return RuleEngine.execute(item["rule"], payload.data)


@app.post("/api/v1/knowledge/rules/{rule_id}/publish", dependencies=[Depends(verify_service_token)], tags=["regulations"])
def publish_regulation_rule(rule_id: str) -> dict[str, Any]:
    try:
        return regulations.publish_rule(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="???????") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/agent/config", dependencies=[Depends(verify_service_token)], tags=["agent"])
def get_agent_config() -> dict[str, Any]:
    return agent.status()


@app.post("/api/v1/agent/config", dependencies=[Depends(verify_service_token)], tags=["agent"])
def save_agent_config(request: AgentConfigRequest) -> dict[str, Any]:
    try:
        return agent.configure(request.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/agent/ask", dependencies=[Depends(verify_service_token)], tags=["agent"])
def ask_knowledge_agent(request: AgentQuestion) -> dict[str, Any]:
    use_knowledge = request.mode == "knowledge"
    sources = knowledge.search(request.question, request.top_k) if use_knowledge else []
    history = [
        item.model_dump() if hasattr(item, "model_dump") else item.dict()
        for item in request.history[-20:]
    ]
    try:
        result = agent.chat(request.question, history, sources, use_knowledge)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "question": request.question,
        "answer": result["answer"],
        "answer_mode": "model_knowledge" if use_knowledge else "model_general",
        "provider": result["provider"],
        "model": result["model"],
        "usage": result["usage"],
        "sources": sources,
        "knowledge_stats": knowledge.stats(),
    }


@app.post("/api/v1/stage1/tasks", status_code=202, dependencies=[Depends(verify_service_token)], tags=["stage1"])
async def create_stage1_task(
    file: Annotated[UploadFile, File(description="函件PDF")],
    payload: Annotated[str, Form(description="第一阶段表单JSON或完整统一输入JSON")],
    scheme_file: Annotated[UploadFile | None, File(description="可选方案文件")] = None,
    expert_opinion_file: Annotated[UploadFile | None, File(description="可选专家意见文件")] = None,
    attachmentFiles: Annotated[list[UploadFile] | None, File(description="会话中追加的补充附件")] = None,
) -> dict[str, Any]:
    payload_data = _parse_json(payload, "payload")
    manual_archive_only = bool(payload_data.pop("manual_archive_only", False))
    archive_context = _resolve_archive_context(payload_data.pop("archive_binding", None))
    source = await _save_upload(file, "第一阶段", STAGE1_SUFFIXES)
    attachments: dict[str, Path] = {}
    if scheme_file is not None:
        attachments["scheme_file"] = await _save_upload(scheme_file, "方案附件", ATTACHMENT_SUFFIXES)
    if expert_opinion_file is not None:
        attachments["expert_opinion_file"] = await _save_upload(expert_opinion_file, "专家意见附件", ATTACHMENT_SUFFIXES)
    for index, attachment in enumerate(attachmentFiles or [], start=1):
        attachments[f"attachment_{index}"] = await _save_upload(attachment, "补充附件", STAGE2_SUFFIXES | ATTACHMENT_SUFFIXES)
    task = _create_audit_task(
        "stage1",
        source,
        stage1_worker(source, payload_data, attachments, archive_context=archive_context),
        archive_context,
        attachments=attachments,
        auto_archive=not manual_archive_only,
        manual_context=payload_data,
    )
    return {key: task[key] for key in ("task_id", "task_type", "status", "progress", "message")}


@app.post("/api/v1/stage1/recognize", dependencies=[Depends(verify_service_token)], tags=["stage1"])
async def recognize_stage1_letter(
    file: Annotated[UploadFile, File(description="待分类识别的项目资料PDF、DOCX或TXT")],
) -> dict[str, Any]:
    source = await _save_upload(file, "函件识别", LETTER_RECOGNITION_SUFFIXES)
    return recognize_letter(source)


@app.post("/api/v1/stage2/audit/tasks", status_code=202, dependencies=[Depends(verify_service_token)], tags=["stage2"])
async def create_stage2_audit_task(
    file: Annotated[UploadFile, File(description="安全评估方案或报告")],
    options: Annotated[str | None, Form(description="可选参数JSON")] = None,
    attachmentFiles: Annotated[list[UploadFile] | None, File(description="会话中追加的补充附件")] = None,
) -> dict[str, Any]:
    option_values = _parse_json(options, "options")
    manual_archive_only = bool(option_values.pop("manual_archive_only", False))
    archive_context = _resolve_archive_context(option_values.pop("archive_binding", None))
    if archive_context:
        option_values["project_archive_context"] = archive_context
    source = await _save_upload(file, "第二阶段方案审核", STAGE2_SUFFIXES)
    attachments = {
        f"attachment_{index}": await _save_upload(attachment, "补充附件", STAGE2_SUFFIXES | ATTACHMENT_SUFFIXES)
        for index, attachment in enumerate(attachmentFiles or [], start=1)
    }
    task = _create_audit_task(
        "stage2_audit",
        source,
        stage2_audit_worker(source, option_values, attachments),
        archive_context,
        attachments=attachments,
        auto_archive=not manual_archive_only,
        manual_context=option_values.get("manual_context") if isinstance(option_values.get("manual_context"), dict) else option_values,
    )
    return {key: task[key] for key in ("task_id", "task_type", "status", "progress", "message")}


@app.post("/api/v1/stage2/advice/tasks", status_code=202, dependencies=[Depends(verify_service_token)], tags=["stage2"])
async def create_advice_task(
    file: Annotated[UploadFile, File(description="新案例文件或case.json")],
    options: Annotated[str | None, Form(description="top_k、rebuild_database等参数JSON")] = None,
) -> dict[str, Any]:
    option_values = _parse_json(options, "options")
    manual_archive_only = bool(option_values.pop("manual_archive_only", False))
    archive_context = _resolve_archive_context(option_values.pop("archive_binding", None))
    if archive_context:
        option_values["project_archive_context"] = archive_context
    source = await _save_upload(file, "案例建议匹配", ADVICE_SUFFIXES)
    task = _create_audit_task(
        "stage2_advice",
        source,
        advice_worker(source, option_values),
        archive_context,
        auto_archive=not manual_archive_only,
        manual_context=option_values.get("manual_context") if isinstance(option_values.get("manual_context"), dict) else option_values,
    )
    return {key: task[key] for key in ("task_id", "task_type", "status", "progress", "message")}


@app.post("/api/v1/stage2/full/tasks", status_code=202, dependencies=[Depends(verify_service_token)], tags=["stage2"])
async def create_stage2_full_task(
    file: Annotated[UploadFile, File(description="鍏堝鏍搞€佸啀鍖归厤寤鸿鐨勬柊鏂规")],
    options: Annotated[str | None, Form(description="瀹℃牳鍜屽尮閰嶉€夐」JSON")] = None,
    attachmentFiles: Annotated[list[UploadFile] | None, File(description="会话中追加的补充附件")] = None,
) -> dict[str, Any]:
    option_values = _parse_json(options, "options")
    manual_archive_only = bool(option_values.pop("manual_archive_only", False))
    archive_context = _resolve_archive_context(option_values.pop("archive_binding", None))
    if archive_context:
        option_values["project_archive_context"] = archive_context
    source = await _save_upload(file, "绗簩闃舵瀹屾暣澶勭悊", STAGE2_SUFFIXES)
    attachments = {
        f"attachment_{index}": await _save_upload(attachment, "补充附件", STAGE2_SUFFIXES | ATTACHMENT_SUFFIXES)
        for index, attachment in enumerate(attachmentFiles or [], start=1)
    }
    task = _create_audit_task(
        "stage2_full",
        source,
        stage2_full_worker(source, option_values, attachments),
        archive_context,
        attachments=attachments,
        auto_archive=not manual_archive_only,
        manual_context=option_values.get("manual_context") if isinstance(option_values.get("manual_context"), dict) else option_values,
    )
    return {key: task[key] for key in ("task_id", "task_type", "status", "progress", "message")}


@app.get("/api/v1/tasks", dependencies=[Depends(verify_service_token)], tags=["tasks"])
def list_tasks(limit: Annotated[int, Query(ge=1, le=500)] = 100) -> list[dict[str, Any]]:
    return tasks.list(limit)


@app.get("/api/v1/tasks/{task_id}", dependencies=[Depends(verify_service_token)], tags=["tasks"])
def get_task(task_id: str) -> dict[str, Any]:
    task = _task_or_404(task_id)
    task.pop("result", None)
    return task


@app.get("/api/v1/tasks/{task_id}/result", dependencies=[Depends(verify_service_token)], tags=["tasks"])
def get_task_result(task_id: str) -> dict[str, Any]:
    task = _task_or_404(task_id)
    if task["status"] != "success":
        raise HTTPException(status_code=409, detail=f"浠诲姟灏氭湭鎴愬姛瀹屾垚锛屽綋鍓嶇姸鎬侊細{task['status']}")
    return task["result"]


@app.get("/api/v1/tasks/{task_id}/files", dependencies=[Depends(verify_service_token)], tags=["files"])
def list_task_files(task_id: str) -> list[dict[str, Any]]:
    task = _task_or_404(task_id)
    return [{key: item[key] for key in ("file_id", "name", "relative_path", "size", "root_index")} for item in _artifact_files(task)]


@app.get("/api/v1/tasks/{task_id}/files/{file_id}", dependencies=[Depends(verify_service_token)], tags=["files"])
def download_task_file(task_id: str, file_id: str) -> FileResponse:
    task = _task_or_404(task_id)
    item = next((entry for entry in _artifact_files(task) if entry["file_id"] == file_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="???????")
    path = Path(item["path"])
    return FileResponse(path, filename=path.name, media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream")

