from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from audit_api import main
from audit_api.audit_session import AuditSessionRepository
from audit_api.project_archive import ProjectArchiveRepository


class AuditSessionRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.repository = AuditSessionRepository(Path(self.temp.name) / "sessions.sqlite3")

    def tearDown(self):
        self.temp.cleanup()

    def test_session_item_and_message_lifecycle(self):
        session = self.repository.create_session({
            "source_task_id": "task-1",
            "metadata": {"project_name": "测试项目"},
            "items": [{
                "title": "控制保护区范围核查",
                "conclusion": "需补充保护区范围核查材料。",
                "risk_level": "高",
                "basis": [{"clause": "条例"}],
                "recommendation": "补充相关说明。",
            }],
            "initial_message": "已完成第一版审核结果。",
        })

        self.assertEqual(session["source_task_id"], "task-1")
        self.assertEqual(session["current_version"], 1)
        self.assertEqual(len(session["items"]), 1)
        self.assertEqual(session["messages"][0]["role"], "assistant")

        item = self.repository.create_item(session["session_id"], {
            "title": "施工监测要求",
            "conclusion": "施工前应完善监测方案。",
            "risk_level": "中",
        })
        self.assertEqual(item["order_no"], 2)

        updated = self.repository.update_item(item["item_id"], {
            "conclusion": "施工前应完善专项监测方案。",
        })
        self.assertTrue(updated["manual_modified"])
        self.assertIn("专项监测", updated["conclusion"])

        deleted = self.repository.delete_item(session["items"][0]["item_id"])
        self.assertTrue(deleted["deleted"])
        current = self.repository.get_session(session["session_id"])
        self.assertEqual(len(current["items"]), 1)
        self.assertEqual(current["items"][0]["order_no"], 1)
        self.assertGreater(current["current_version"], 1)

        message = self.repository.add_message(session["session_id"], {
            "role": "user",
            "content": "不要第一条审核结果",
        })
        self.assertEqual(message["version_no"], current["current_version"])
        self.assertEqual(len(self.repository.list_messages(session["session_id"])), 2)


class AuditSessionApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.repository = AuditSessionRepository(Path(self.temp.name) / "sessions.sqlite3")
        self.archives = ProjectArchiveRepository(Path(self.temp.name) / "archives.sqlite3")
        self.patch = patch.object(main, "audit_sessions", self.repository)
        self.archive_patch = patch.object(main, "project_archives", self.archives)
        self.patch.start()
        self.archive_patch.start()

    def tearDown(self):
        self.archive_patch.stop()
        self.patch.stop()
        self.temp.cleanup()

    def test_routes_are_registered(self):
        paths = main.app.openapi()["paths"]
        expected = {
            "/api/v1/audit-sessions",
            "/api/v1/audit-sessions/{session_id}",
            "/api/v1/audit-sessions/{session_id}/items",
            "/api/v1/audit-sessions/{session_id}/items/{item_id}",
            "/api/v1/audit-sessions/{session_id}/messages",
            "/api/v1/audit-sessions/{session_id}/chat",
            "/api/v1/audit-sessions/{session_id}/archive",
            "/api/v1/audit-sessions/{session_id}/reply",
        }
        self.assertTrue(expected.issubset(paths))

    def test_api_functions_manage_items(self):
        session = main.create_audit_session(main.AuditSessionCreatePayload(
            source_task_id="task-api",
            items=[main.AuditReviewItemPayload(
                title="净距核查",
                conclusion="需复核净距。",
                risk_level="高",
            )],
        ))
        self.assertEqual(len(session["items"]), 1)
        session_id = session["session_id"]

        item = main.create_audit_session_item(
            session_id,
            main.AuditReviewItemPayload(title="监测要求", conclusion="完善监测。"),
        )
        updated = main.update_audit_session_item(
            session_id,
            item["item_id"],
            main.AuditReviewItemUpdatePayload(recommendation="补充监测频率。"),
        )
        self.assertEqual(updated["recommendation"], "补充监测频率。")

        deleted = main.delete_audit_session_item(session_id, item["item_id"])
        self.assertTrue(deleted["deleted"])
        self.assertEqual(len(main.list_audit_session_items(session_id)), 1)

        user_message = main.create_audit_session_message(
            session_id,
            main.AuditChatMessagePayload(role="user", content="删除第一条"),
        )
        self.assertEqual(user_message["role"], "user")

    def test_missing_session_is_returned_as_404(self):
        with self.assertRaises(HTTPException) as captured:
            main.get_audit_session("ses_missing")
        self.assertEqual(captured.exception.status_code, 404)

    def test_write_session_to_archive_requires_overwrite_for_existing_record(self):
        session = main.create_audit_session(main.AuditSessionCreatePayload(
            source_task_id="task-write",
            items=[main.AuditReviewItemPayload(
                title="监测要求",
                conclusion="施工前应完善监测方案。",
                risk_level="高",
                recommendation="明确监测频率。",
            )],
        ))
        payload = main.AuditSessionArchivePayload(project_name="归档写入项目", stage_name="设计阶段")

        first = main.write_audit_session_to_archive(session["session_id"], payload)
        self.assertFalse(first["overwritten"])
        self.assertEqual(first["archive_record"]["risk_level"], "高")
        self.assertIn("监测要求", first["archive_record"]["summary"])

        with self.assertRaises(HTTPException) as captured:
            main.write_audit_session_to_archive(session["session_id"], payload)
        self.assertEqual(captured.exception.status_code, 409)

        overwritten = main.write_audit_session_to_archive(
            session["session_id"],
            main.AuditSessionArchivePayload(
                project_name="归档写入项目",
                stage_name="设计阶段",
                overwrite=True,
            ),
        )
        self.assertTrue(overwritten["overwritten"])
        self.assertEqual(overwritten["archive_record"]["attempt_count"], 2)

    def test_generate_session_reply_uses_latest_review_items(self):
        session = main.create_audit_session(main.AuditSessionCreatePayload(
            source_task_id="task-reply",
            items=[main.AuditReviewItemPayload(
                title="施工监测要求",
                conclusion="施工前应完善专项监测方案。",
                risk_level="高",
                recommendation="明确监测频率和报警值。",
            )],
        ))
        captured = {}

        def fake_formal_reply(package, data, dynamic_audit, agent=None):
            captured["package"] = package
            captured["data"] = data
            return {
                "title": "关于测试项目征求地铁意见的复函",
                "recipient": "测试单位",
                "lead": "贵司相关资料已收悉。经研究，具体意见函复如下：",
                "items": ["施工前应完善专项监测方案。"],
            }

        def fake_render(package, target):
            captured["rendered"] = package
            target.write_bytes(b"docx")

        with TemporaryDirectory() as temp_dir, \
                patch.object(main, "RESULT_ROOT", Path(temp_dir)), \
                patch.object(main, "generate_formal_reply_content", fake_formal_reply), \
                patch.object(main, "render_reply_draft_docx", fake_render):
            response = main.generate_audit_session_reply(
                session["session_id"],
                main.AuditSessionReplyPayload(
                    project_name="测试项目",
                    applicant="测试单位",
                    project_stage="设计阶段",
                    form_data={"minimum_horizontal_clearance_m": 12},
                ),
            )
            self.assertTrue(Path(response.path).exists())

        self.assertIn("施工监测要求", captured["package"]["audit_opinions"][0]["topic"])
        self.assertEqual(captured["data"]["project"]["project_name"], "测试项目")
        self.assertEqual(captured["rendered"]["formal_reply"]["items"][0], "施工前应完善专项监测方案。")

    def test_chat_instruction_deletes_numbered_item_without_ai(self):
        session = main.create_audit_session(main.AuditSessionCreatePayload(
            items=[
                main.AuditReviewItemPayload(title="第一条", conclusion="删除目标"),
                main.AuditReviewItemPayload(title="第二条", conclusion="保留目标"),
            ],
        ))

        response = main.revise_audit_session_by_chat(
            session["session_id"],
            main.AuditSessionChatPayload(instruction="不要第一条审核结果"),
        )

        self.assertEqual(len(response["review_items"]), 1)
        self.assertEqual(response["review_items"][0]["title"], "第二条")
        self.assertEqual(response["review_items"][0]["order_no"], 1)
        self.assertIn("已删除第1条", response["message"]["content"])
        messages = main.list_audit_session_messages(session["session_id"])
        self.assertEqual([item["role"] for item in messages], ["user", "assistant"])

    def test_chat_instruction_uses_ai_for_addition(self):
        class FakeAgent:
            def complete_json(self, system, prompt, max_tokens):
                self.system = system
                self.prompt = prompt
                return {
                    "reply": "已补充施工监测要求。",
                    "items": [
                        {"title": "既有结论", "conclusion": "保留原审核结论。"},
                        {
                            "title": "施工监测要求",
                            "conclusion": "施工前应补充专项监测方案。",
                            "risk_level": "中",
                            "basis": ["用户要求补充"],
                            "recommendation": "明确监测频率和报警值。",
                        },
                    ],
                }

        fake = FakeAgent()
        with patch.object(main, "agent", fake):
            session = main.create_audit_session(main.AuditSessionCreatePayload(
                items=[main.AuditReviewItemPayload(title="既有结论", conclusion="保留原审核结论。")],
            ))
            response = main.revise_audit_session_by_chat(
                session["session_id"],
                main.AuditSessionChatPayload(instruction="添加一条关于施工监测的审核结果"),
            )

        self.assertIn("不得编造工程数值", fake.system)
        self.assertIn("添加一条关于施工监测", fake.prompt)
        self.assertEqual(len(response["review_items"]), 2)
        self.assertEqual(response["review_items"][1]["title"], "施工监测要求")
        self.assertEqual(response["message"]["content"], "已补充施工监测要求。")


if __name__ == "__main__":
    unittest.main()
