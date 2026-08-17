from __future__ import annotations

import json
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


Worker = Callable[[str, Callable[[str], None]], dict[str, Any]]
BeforeSubmit = Callable[[str], None]


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class TaskManager:
    def __init__(self, task_root: Path, max_workers: int = 2) -> None:
        self.task_root = task_root
        self.task_root.mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="audit-task")
        self.lock = threading.RLock()
        self._recover_interrupted_tasks()

    def _path(self, task_id: str) -> Path:
        return self.task_root / f"{task_id}.json"

    def _write(self, task: dict[str, Any]) -> None:
        path = self._path(task["task_id"])
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def _recover_interrupted_tasks(self) -> None:
        for path in self.task_root.glob("*.json"):
            try:
                task = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if task.get("status") in {"queued", "running"}:
                task.update(
                    status="failed",
                    progress=task.get("progress", 0),
                    message="Python服务重启，原任务已中断，请重新提交。",
                    error_code="SERVICE_RESTARTED",
                    finished_at=_now(),
                )
                self._write(task)

    def create(
        self,
        task_type: str,
        source_file: Path,
        worker: Worker,
        *,
        before_submit: BeforeSubmit | None = None,
    ) -> dict[str, Any]:
        task_id = uuid.uuid4().hex
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "queued",
            "progress": 0,
            "message": "任务已进入队列",
            "source_file": str(source_file),
            "result": None,
            "error_code": None,
            "error_message": None,
            "created_at": _now(),
            "started_at": None,
            "finished_at": None,
        }
        with self.lock:
            if before_submit is not None:
                before_submit(task_id)
            self._write(task)
        self.executor.submit(self._execute, task_id, worker)
        return task

    def _execute(self, task_id: str, worker: Worker) -> None:
        self.update(task_id, status="running", progress=2, message="任务开始执行", started_at=_now())
        progress_value = 2

        def notify(message: str) -> None:
            nonlocal progress_value
            progress_value = min(92, progress_value + 6)
            self.update(task_id, progress=progress_value, message=message)

        try:
            result = worker(task_id, notify)
            self.update(
                task_id,
                status="success",
                progress=100,
                message="任务完成",
                result=result,
                finished_at=_now(),
            )
        except Exception as exc:
            log_path = self.task_root / f"{task_id}.traceback.log"
            log_path.write_text(traceback.format_exc(), encoding="utf-8")
            self.update(
                task_id,
                status="failed",
                message="任务执行失败",
                error_code=type(exc).__name__,
                error_message=str(exc),
                traceback_log=str(log_path),
                finished_at=_now(),
            )

    def get(self, task_id: str) -> dict[str, Any]:
        path = self._path(task_id)
        if not path.exists():
            raise KeyError(task_id)
        with self.lock:
            return json.loads(path.read_text(encoding="utf-8"))

    def update(self, task_id: str, **changes: Any) -> dict[str, Any]:
        with self.lock:
            task = self.get(task_id)
            task.update(changes)
            self._write(task)
            return task

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        tasks = []
        for path in sorted(self.task_root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
            try:
                tasks.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return tasks
