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
                        {"title": "既有结论", "conclusion": "应保留原审核控制要求并继续落实。"},
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
                items=[main.AuditReviewItemPayload(title="既有结论", conclusion="应保留原审核控制要求并继续落实。")],
            ))
            response = main.revise_audit_session_by_chat(
                session["session_id"],
                main.AuditSessionChatPayload(instruction="添加一条关于施工监测的审核结果"),
            )

        self.assertIn("不得编造工程数值", fake.system)
        self.assertIn("添加一条关于施工监测", fake.prompt)
        self.assertEqual(len(response["review_items"]), 2)
        self.assertEqual(response["review_items"][1]["title"], "施工监测要求")
        self.assertIn("已补充施工监测要求", response["message"]["content"])

    def test_review_profile_infers_supported_document_types(self):
        self.assertEqual(
            main._infer_review_profile_from_text("滨湖社区项目安全性影响评估预评估报告.pdf"),
            "safety_assessment_report",
        )
        self.assertEqual(
            main._infer_review_profile_from_text("长泰路110kV上跨轨道交通区间安全专项评估.pdf"),
            "safety_assessment_report",
        )
        self.assertEqual(
            main._infer_review_profile_from_text("20241206 滨湖社区项目设计方案.pdf"),
            "design_scheme",
        )
        self.assertEqual(
            main._infer_review_profile_from_text("桩基和支护专项施工方案.pdf"),
            "construction_scheme",
        )
        self.assertEqual(main._infer_review_profile_from_text("会议纪要及往来函.pdf"), "")

    def test_expand_review_items_applies_document_type_style_only_when_matched(self):
        class FakeAgent:
            def complete_json(self, system, prompt, max_tokens):
                self.system = system
                self.prompt = prompt
                return {
                    "items": [
                        {"title": "止水帷幕核实", "conclusion": "基于水文地质条件，应核实止水帷幕和降水井设计的可控性。"}
                    ]
                }

        fake = FakeAgent()
        result = {
            "manual_context_for_consistency": {
                "uploaded_documents": [{"name": "滨湖社区安全性影响评估预评估报告.pdf"}]
            }
        }
        with patch.object(main, "agent", fake):
            main._ai_expand_review_items(result, [{"title": "止水帷幕", "conclusion": "应复核止水帷幕。"}])
        self.assertIn("常用动词必须以“核实、建议、完善、确定、提出合理设计及施工要求”为主", fake.system)
        self.assertIn("safety_assessment_report", fake.prompt)

        generic = FakeAgent()
        with patch.object(main, "agent", generic):
            main._ai_expand_review_items({}, [{"title": "普通资料", "conclusion": "应复核资料。"}])
        self.assertNotIn("本次资料识别为", generic.system)

    def test_safety_profile_rewrites_supplement_wording(self):
        items = main._apply_review_profile_wording(
            [
                {
                    "title": "补充止水帷幕资料",
                    "conclusion": "需补充完善止水帷幕和降水井设计要求。",
                    "recommendation": "应补充关键参数。",
                }
            ],
            "safety_assessment_report",
        )
        self.assertNotIn("补充", items[0]["title"])
        self.assertNotIn("补充", items[0]["conclusion"])
        self.assertNotIn("补充", items[0]["recommendation"])
        self.assertIn("完善", items[0]["conclusion"])

    def test_construction_profile_keeps_supplement_wording(self):
        items = main._apply_review_profile_wording(
            [{"title": "补充施工监测", "conclusion": "应补充施工监测方案。"}],
            "construction_scheme",
        )
        self.assertIn("补充", items[0]["title"])
        self.assertIn("补充", items[0]["conclusion"])

    def test_overall_opinion_uses_engineering_overview_and_document_profile(self):
        overall = main._sanitize_overall_opinion(
            {},
            {},
            [{"title": "止水帷幕", "conclusion": "核实止水帷幕可控性。", "risk_level": "中"}],
            {
                "review_profile": "safety_assessment_report",
                "relative_relationship": "北侧",
                "metro_line_name": "地铁2号线",
                "metro_section_name": "云锦路站~莫愁湖站区间隧道",
                "pit_depth_m": 6.7,
                "support_components": ["钻孔灌注桩", "三轴搅拌桩止水帷幕"],
                "minimum_horizontal_clearance_m": 20.1,
                "dewatering_method": "管井降水",
                "buried_depth_m": "14.5~16.5米",
            },
            force_formal=True,
        )

        text = overall["conclusion"]
        self.assertIn("本项目与地铁2号线云锦路站~莫愁湖站区间隧道呈北侧关系", text)
        self.assertIn("基坑开挖深度约为6.7米", text)
        self.assertIn("采用钻孔灌注桩、三轴搅拌桩止水帷幕", text)
        self.assertIn("支护结构与地铁结构边线最小水平距离约为20.1米", text)
        self.assertIn("降水方式为管井降水", text)
        self.assertIn("对应地铁结构埋深约为14.5~16.5米", text)
        self.assertIn("本次专项评估报告总体符合", text)
        self.assertNotIn("落实专项评估", text)

    def test_chat_rewrite_keeps_document_type_style_from_session_metadata(self):
        class FakeAgent:
            def complete_json(self, system, prompt, max_tokens):
                self.system = system
                self.prompt = prompt
                return {
                    "reply": "已按施工方案口吻细化。",
                    "overall_opinion": {"title": "综合评价", "conclusion": "经审查，本次资料具备施工方案审查基础。"},
                    "items": [
                        {"title": "施工时序优化", "conclusion": "应优化围护桩、止水帷幕及坑底加固施工时序，明确关键工序衔接要求。", "risk_level": "中"}
                    ],
                }

        fake = FakeAgent()
        with patch.object(main, "agent", fake):
            session = main.create_audit_session(main.AuditSessionCreatePayload(
                metadata={"review_profile": "construction_scheme"},
                items=[main.AuditReviewItemPayload(title="施工时序", conclusion="应明确施工时序。", risk_level="中")],
            ))
            main.revise_audit_session_by_chat(
                session["session_id"],
                main.AuditSessionChatPayload(instruction="将第一条意见写得详细一点"),
            )
        self.assertIn("常用动词以“补充、优化、建议、协同、协调、明确、采取、严禁、确保”为主", fake.system)
        self.assertIn("construction_scheme", fake.prompt)

    def test_chat_instruction_detail_fallback_changes_target_item(self):
        class FakeAgent:
            def complete_json(self, system, prompt, max_tokens):
                return {
                    "reply": "已细化第五条。",
                    "items": [
                        {"title": f"第{index}条", "conclusion": f"第{index}条应补充完善相关资料。", "risk_level": "中"}
                        for index in range(1, 7)
                    ],
                }

        with patch.object(main, "agent", FakeAgent()):
            session = main.create_audit_session(main.AuditSessionCreatePayload(
                items=[
                    main.AuditReviewItemPayload(title=f"第{index}条", conclusion=f"第{index}条应补充完善相关资料。", risk_level="中")
                    for index in range(1, 7)
                ],
            ))
            response = main.revise_audit_session_by_chat(
                session["session_id"],
                main.AuditSessionChatPayload(instruction="将第五点写的详细一点"),
            )

        fifth = response["review_items"][4]
        self.assertEqual(fifth["order_no"], 5)
        self.assertIn("资料补充要求", fifth["conclusion"])
        self.assertIn("技术复核要求", fifth["conclusion"])
        self.assertGreater(len(fifth["conclusion"]), len("第5条应补充完善相关资料。") + 60)

    def test_chat_review_updates_increment_assistant_message_versions(self):
        class FakeAgent:
            def complete_json(self, system, prompt, max_tokens):
                return {
                    "reply": "已更新。",
                    "items": [
                        {"title": "监测方案完善", "conclusion": "应补充完善专项监测方案并明确报警阈值。", "risk_level": "中"}
                    ],
                }

        with patch.object(main, "agent", FakeAgent()):
            session = main.create_audit_session(main.AuditSessionCreatePayload(
                items=[main.AuditReviewItemPayload(title="监测方案", conclusion="应补充监测方案。", risk_level="中")],
            ))
            first = main.revise_audit_session_by_chat(
                session["session_id"],
                main.AuditSessionChatPayload(instruction="将第一条意见写得详细一点"),
            )
            second = main.revise_audit_session_by_chat(
                session["session_id"],
                main.AuditSessionChatPayload(instruction="将第一条意见再详细一点"),
            )

        self.assertEqual(first["message"]["version_no"], 2)
        self.assertEqual(first["message"]["result_snapshot"]["version_no"], 2)
        self.assertEqual(second["message"]["version_no"], 3)
        self.assertEqual(second["message"]["result_snapshot"]["version_no"], 3)


if __name__ == "__main__":
    unittest.main()
