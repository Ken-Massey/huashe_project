from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from audit_api import main
from audit_api.audit_session import AuditSessionRepository
from audit_api.project_archive import ProjectArchiveRepository
from audit_api.task_manager import TaskManager


def wait_for_task(manager: TaskManager, task_id: str) -> dict:
    for _ in range(200):
        task = manager.get(task_id)
        if task["status"] in {"success", "failed"}:
            return task
        time.sleep(0.01)
    raise AssertionError("任务未在测试时限内结束")


class ArchiveTaskLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        root = Path(self.temp.name)
        self.repository = ProjectArchiveRepository(root / "archive.sqlite3")
        self.sessions = AuditSessionRepository(root / "sessions.sqlite3")
        self.manager = TaskManager(root / "tasks", max_workers=2)
        self.source = root / "source.pdf"
        self.source.write_bytes(b"pdf")
        self.patches = (
            patch.object(main, "project_archives", self.repository),
            patch.object(main, "audit_sessions", self.sessions),
            patch.object(main, "tasks", self.manager),
        )
        for item in self.patches:
            item.start()

    def tearDown(self):
        self.manager.executor.shutdown(wait=True)
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def create_stage_context(self, project_name: str = "自动归档项目"):
        project = self.repository.create_project({"name": project_name})
        stage = self.repository.create_stage(project["project_id"], {"name": "专项审核"})
        return stage, self.repository.history_context_for_stage(stage["stage_id"])

    @staticmethod
    def successful_result(risk_level: str = "低") -> dict:
        return {
            "stage": "stage2_audit",
            "dynamic_regulation_audit": {
                "risk_report": {
                    "overall_risk_level": risk_level,
                    "overall_conclusion": "本阶段审核完成。",
                    "findings": [{
                        "title": "施工监测要求",
                        "judgement": "risk",
                        "risk_level": risk_level,
                        "analysis": "施工阶段需关注地铁结构安全。",
                        "recommendation": "应完善施工监测方案。",
                        "regulation_evidence": [{"document_title": "保护条例", "section": "第十条", "quote": "应采取保护措施"}],
                    }],
                    "required_supplements": [],
                }
            },
            "artifact_roots": [],
        }

    def test_successful_task_is_written_to_unique_stage_record(self):
        stage, context = self.create_stage_context()

        task = main._create_audit_task(
            "stage2_audit",
            self.source,
            lambda task_id, progress: self.successful_result(),
            context,
        )
        completed = wait_for_task(self.manager, task["task_id"])
        record = self.repository.get_stage_audit(stage["stage_id"])

        self.assertEqual(completed["status"], "success")
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["source_task_id"], task["task_id"])
        self.assertEqual(record["result"], "审核完成")
        self.assertEqual(record["risk_level"], "低")
        self.assertEqual(record["result_data"]["stage"], "stage2_audit")
        self.assertEqual(completed["result"]["archive_record"]["audit_id"], record["audit_id"])
        self.assertTrue(completed["result"]["audit_session_id"].startswith("ses_"))
        self.assertEqual(completed["result"]["review_items"][0]["title"], "施工监测要求")
        session = self.sessions.get_session(completed["result"]["audit_session_id"])
        self.assertEqual(session["stage_id"], stage["stage_id"])
        self.assertEqual(session["items"][0]["recommendation"], "应完善施工监测方案。")

        with self.assertRaises(HTTPException) as captured:
            main._create_audit_task(
                "stage2_audit",
                self.source,
                lambda task_id, progress: self.successful_result(),
                context,
            )
        self.assertEqual(captured.exception.status_code, 409)

    def test_failed_task_releases_stage_for_retry_using_same_record(self):
        stage, context = self.create_stage_context("失败重试项目")

        def fail_worker(task_id, progress):
            raise RuntimeError("审核模型暂时不可用")

        first_task = main._create_audit_task(
            "stage2_audit", self.source, fail_worker, context
        )
        failed_task = wait_for_task(self.manager, first_task["task_id"])
        failed_record = self.repository.get_stage_audit(stage["stage_id"])
        self.assertEqual(failed_task["status"], "failed")
        self.assertEqual(failed_record["status"], "failed")
        self.assertIn("审核模型暂时不可用", failed_record["error_message"])

        retry_task = main._create_audit_task(
            "stage2_audit",
            self.source,
            lambda task_id, progress: self.successful_result("中"),
            context,
        )
        wait_for_task(self.manager, retry_task["task_id"])
        retried_record = self.repository.get_stage_audit(stage["stage_id"])
        self.assertEqual(retried_record["audit_id"], failed_record["audit_id"])
        self.assertEqual(retried_record["attempt_count"], 2)
        self.assertEqual(retried_record["status"], "success")

    def test_stage_is_reserved_before_worker_finishes(self):
        stage, context = self.create_stage_context("并发占用项目")
        release = threading.Event()

        def slow_worker(task_id, progress):
            release.wait(timeout=5)
            return self.successful_result()

        first = main._create_audit_task(
            "stage2_audit", self.source, slow_worker, context
        )
        try:
            record = self.repository.get_stage_audit(stage["stage_id"])
            self.assertIn(record["status"], {"pending", "running"})
            with self.assertRaises(HTTPException) as captured:
                main._create_audit_task(
                    "stage2_audit",
                    self.source,
                    lambda task_id, progress: self.successful_result(),
                    context,
                )
            self.assertEqual(captured.exception.status_code, 409)
        finally:
            release.set()
        self.assertEqual(wait_for_task(self.manager, first["task_id"])["status"], "success")


if __name__ == "__main__":
    unittest.main()
