from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from audit_api import main
from audit_api.audit_session import AuditSessionRepository
from audit_api.project_archive import ProjectArchiveRepository


class ProjectArchiveApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.repository = ProjectArchiveRepository(
            Path(self.temp.name) / "project_archive.sqlite3"
        )
        self.sessions = AuditSessionRepository(
            Path(self.temp.name) / "audit_sessions.sqlite3"
        )
        self.repository_patch = patch.object(main, "project_archives", self.repository)
        self.sessions_patch = patch.object(main, "audit_sessions", self.sessions)
        self.repository_patch.start()
        self.sessions_patch.start()

    def tearDown(self):
        self.sessions_patch.stop()
        self.repository_patch.stop()
        self.temp.cleanup()

    def test_archive_routes_are_registered(self):
        paths = main.app.openapi()["paths"]
        expected = {
            "/api/v1/project-archives/projects",
            "/api/v1/project-archives/resolve",
            "/api/v1/project-archives/projects/{project_id}",
            "/api/v1/project-archives/projects/{project_id}/archive",
            "/api/v1/project-archives/projects/{project_id}/restore",
            "/api/v1/project-archives/projects/{project_id}/stages",
            "/api/v1/project-archives/stages/{stage_id}",
            "/api/v1/project-archives/stages/{stage_id}/archive",
            "/api/v1/project-archives/stages/{stage_id}/restore",
            "/api/v1/project-archives/stages/{stage_id}/audit",
            "/api/v1/project-archives/stages/{stage_id}/previous-audits",
        }
        self.assertTrue(expected.issubset(paths))

    def test_project_and_custom_stage_lifecycle(self):
        project = main.create_archive_project(main.ArchiveProjectCreatePayload(
            name="北站综合体", code="P-001", location="北站"
        ))
        stage = main.create_archive_stage(
            project["project_id"],
            main.ArchiveStageCreatePayload(name="第三方专项复核", stage_order=1),
        )

        detail = main.get_archive_project(project["project_id"])
        self.assertEqual(detail["stages"][0]["name"], "第三方专项复核")
        updated = main.update_archive_stage(
            stage["stage_id"],
            main.ArchiveStageUpdatePayload(description="人工新增阶段"),
        )
        self.assertEqual(updated["description"], "人工新增阶段")

        archived = main.archive_stage(stage["stage_id"])
        self.assertEqual(archived["status"], "archived")
        restored = main.restore_stage(stage["stage_id"])
        self.assertEqual(restored["status"], "active")

    def test_duplicate_project_is_returned_as_422(self):
        payload = main.ArchiveProjectCreatePayload(name="重复项目")
        main.create_archive_project(payload)
        with self.assertRaises(HTTPException) as captured:
            main.create_archive_project(payload)
        self.assertEqual(captured.exception.status_code, 422)

    def test_missing_stage_is_returned_as_404(self):
        with self.assertRaises(HTTPException) as captured:
            main.get_archive_stage("stg_missing")
        self.assertEqual(captured.exception.status_code, 404)

    def test_previous_audits_endpoint_returns_only_earlier_successes(self):
        project = self.repository.create_project({"name": "历史接口项目"})
        first = self.repository.create_stage(project["project_id"], {"name": "初步论证"})
        second = self.repository.create_stage(project["project_id"], {"name": "深化设计"})
        current = self.repository.create_stage(project["project_id"], {"name": "专项施工"})

        audit = self.repository.begin_audit(first["stage_id"], "task-success")
        self.repository.complete_audit(audit["audit_id"], {
            "result": "通过", "risk_level": "低", "summary": "完成初步论证"
        })
        failed = self.repository.begin_audit(second["stage_id"], "task-failed")
        self.repository.fail_audit(failed["audit_id"], "资料不足")

        response = main.get_previous_stage_audits(current["stage_id"])
        self.assertEqual(response["record_count"], 1)
        self.assertEqual(response["records"][0]["stage_name"], "初步论证")

    def test_stage_audit_endpoint_tolerates_empty_legacy_review_items(self):
        project = self.repository.create_project({"name": "旧版空结果项目"})
        stage = self.repository.create_stage(project["project_id"], {"name": "设计阶段"})
        audit = self.repository.begin_audit(stage["stage_id"], "legacy-empty")
        self.repository.complete_audit(audit["audit_id"], {
            "result": "通过",
            "risk_level": "低",
            "summary": "旧版记录未保存结构化审核条目",
            "result_data": {
                "latest_result": {"items": []},
                "review_items": [],
                "summary": "旧版记录未保存结构化审核条目",
            },
        })

        response = main.get_archive_stage_audit(stage["stage_id"])

        self.assertIsNotNone(response)
        self.assertEqual(response["status"], "success")
        self.assertTrue(response["audit_session_id"].startswith("ses_"))
        self.assertEqual(response["result_data"]["review_items"], [])

    def test_archive_binding_resolves_structured_history(self):
        project = self.repository.create_project({"name": "绑定项目"})
        previous = self.repository.create_stage(project["project_id"], {"name": "前序阶段"})
        current = self.repository.create_stage(project["project_id"], {"name": "当前阶段"})
        audit = self.repository.begin_audit(previous["stage_id"], "task-previous")
        self.repository.complete_audit(audit["audit_id"], {
            "result": "通过", "risk_level": "低", "summary": "前序审核完成"
        })

        context = main._resolve_archive_context({
            "project_id": project["project_id"], "stage_id": current["stage_id"]
        })
        self.assertEqual(context["previous_stage_count"], 1)
        self.assertEqual(context["current_stage"]["stage_name"], "当前阶段")

        with self.assertRaises(HTTPException) as captured:
            main._resolve_archive_context({
                "project_id": "prj_wrong", "stage_id": current["stage_id"]
            })
        self.assertEqual(captured.exception.status_code, 422)

    def test_resolve_and_delete_project_endpoints(self):
        resolved = main.resolve_archive_project_stage(
            main.ArchiveResolvePayload(project_name="接口自动项目", stage_name="规划")
        )
        self.assertTrue(resolved["project_created"])
        project_id = resolved["project"]["project_id"]
        deleted = main.delete_archive_project(project_id)
        self.assertEqual(deleted["deleted_stage_count"], 1)
        with self.assertRaises(HTTPException) as captured:
            main.get_archive_project(project_id)
        self.assertEqual(captured.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
