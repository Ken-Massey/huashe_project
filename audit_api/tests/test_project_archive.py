from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from audit_api.project_archive import ProjectArchiveRepository


def repository(root: Path) -> ProjectArchiveRepository:
    return ProjectArchiveRepository(root / "project_archive.sqlite3")


def test_custom_stages_are_ordered_and_can_be_reordered():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        project = archive.create_project({"name": "北站综合体"})
        planning = archive.create_stage(project["project_id"], {"name": "前期方案"})
        construction = archive.create_stage(project["project_id"], {"name": "围护结构施工"})
        review = archive.create_stage(
            project["project_id"], {"name": "专家复核", "stage_order": 2}
        )

        assert [item["name"] for item in archive.get_project(project["project_id"])["stages"]] == [
            "前期方案", "专家复核", "围护结构施工"
        ]

        archive.update_stage(construction["stage_id"], {"stage_order": 1})
        assert [item["name"] for item in archive.get_project(project["project_id"])["stages"]] == [
            "围护结构施工", "前期方案", "专家复核"
        ]
        assert planning["name"] == "前期方案"
        assert review["name"] == "专家复核"


def test_project_and_stage_names_are_unique_within_their_scope():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        project = archive.create_project({"name": "南站项目"})
        archive.create_stage(project["project_id"], {"name": "专项设计"})

        with unittest.TestCase().assertRaisesRegex(ValueError, "项目名称已存在"):
            archive.create_project({"name": "南站项目"})
        with unittest.TestCase().assertRaisesRegex(ValueError, "同名阶段"):
            archive.create_stage(project["project_id"], {"name": "专项设计"})


def test_project_search_only_matches_project_name():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        archive.create_project({"name": "北站综合体", "code": "CODE-001", "location": "鼓楼区"})

        assert [item["name"] for item in archive.list_projects(search="北站")] == ["北站综合体"]
        assert archive.list_projects(search="CODE-001") == []
        assert archive.list_projects(search="鼓楼区") == []


def test_each_stage_has_only_one_successful_audit_and_failed_audit_can_retry():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        project = archive.create_project({"name": "线路保护项目"})
        stage = archive.create_stage(project["project_id"], {"name": "专项论证"})

        first = archive.begin_audit(stage["stage_id"], "task-1")
        archive.mark_audit_running(first["audit_id"])
        failed = archive.fail_audit(first["audit_id"], "模型服务超时")
        assert failed["status"] == "failed"

        retried = archive.begin_audit(stage["stage_id"], "task-2")
        assert retried["audit_id"] == first["audit_id"]
        assert retried["attempt_count"] == 2
        completed = archive.complete_audit(retried["audit_id"], {
            "result": "修改后通过",
            "risk_level": "中",
            "summary": "需落实监测措施。",
            "result_data": {"findings": [{"title": "监测频率"}]},
            "artifacts": [{"name": "审核意见.md"}],
        })
        assert completed["status"] == "success"
        assert completed["result_data"]["findings"][0]["title"] == "监测频率"

        with unittest.TestCase().assertRaisesRegex(ValueError, "只能有一份"):
            archive.begin_audit(stage["stage_id"], "task-3")


def test_previous_history_only_contains_successful_earlier_stages():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        project = archive.create_project({"name": "历史审核项目"})
        first = archive.create_stage(project["project_id"], {"name": "选址论证"})
        second = archive.create_stage(project["project_id"], {"name": "方案设计"})
        current = archive.create_stage(project["project_id"], {"name": "施工准备"})
        later = archive.create_stage(project["project_id"], {"name": "施工实施"})

        for index, stage in enumerate((first, second, later), 1):
            audit = archive.begin_audit(stage["stage_id"], f"task-{index}")
            if stage == second:
                archive.fail_audit(audit["audit_id"], "材料不完整")
            else:
                archive.complete_audit(audit["audit_id"], {
                    "result": "通过", "risk_level": "低", "summary": stage["name"]
                })

        history = archive.previous_successful_audits(current["stage_id"])
        assert [item["stage_name"] for item in history] == ["选址论证"]


def test_archived_stage_cannot_start_audit():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        project = archive.create_project({"name": "归档测试"})
        stage = archive.create_stage(project["project_id"], {"name": "临时阶段"})
        archive.set_stage_archived(stage["stage_id"])

        with unittest.TestCase().assertRaisesRegex(ValueError, "已归档"):
            archive.begin_audit(stage["stage_id"], "task-archived")


def test_history_context_is_compact_and_contains_previous_risks():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        project = archive.create_project({"name": "上下文项目"})
        previous = archive.create_stage(project["project_id"], {"name": "方案论证"})
        current = archive.create_stage(project["project_id"], {"name": "施工图设计"})
        audit = archive.begin_audit(previous["stage_id"], "task-history")
        archive.complete_audit(audit["audit_id"], {
            "result": "修改后通过",
            "risk_level": "中",
            "summary": "需在下一阶段落实自动化监测。",
            "result_data": {
                "dynamic_regulation_audit": {
                    "risk_report": {
                        "findings": [{
                            "title": "监测频率不足",
                            "risk_level": "中",
                            "judgement": "risk",
                            "analysis": "原方案频率偏低。",
                            "recommendation": "下一阶段提高监测频率。",
                        }],
                        "required_supplements": [{
                            "field": "监测方案", "reason": "需确认频率和报警值"
                        }],
                    }
                }
            },
        })

        context = archive.history_context_for_stage(current["stage_id"])
        assert context["previous_stage_count"] == 1
        assert context["current_stage"]["stage_name"] == "施工图设计"
        assert context["previous_stages"][0]["key_findings"][0]["title"] == "监测频率不足"
        assert context["previous_stages"][0]["required_supplements"][0]["field"] == "监测方案"


def test_resolve_reuses_names_and_automatically_creates_missing_archive():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        first = archive.resolve_project_stage("自动识别项目", "规划")
        assert first["project_created"] is True
        assert first["stage_created"] is True

        again = archive.resolve_project_stage("自动识别项目", "规划")
        assert again["project_created"] is False
        assert again["stage_created"] is False
        assert again["project"]["project_id"] == first["project"]["project_id"]
        assert again["stage"]["stage_id"] == first["stage"]["stage_id"]

        next_stage = archive.resolve_project_stage("自动识别项目", "施工准备")
        assert next_stage["project_created"] is False
        assert next_stage["stage_created"] is True
        assert next_stage["stage"]["stage_order"] == 2


def test_project_can_be_renamed_and_deleted_with_its_history():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        resolved = archive.resolve_project_stage("待重命名项目", "方案设计")
        project_id = resolved["project"]["project_id"]
        stage_id = resolved["stage"]["stage_id"]
        renamed = archive.update_project(project_id, {"name": "已重命名项目"})
        assert renamed["name"] == "已重命名项目"

        audit = archive.begin_audit(stage_id, "delete-after-complete")
        archive.complete_audit(audit["audit_id"], {"result": "通过"})
        deleted = archive.delete_project(project_id)
        assert deleted["deleted_stage_count"] == 1
        assert deleted["deleted_audit_count"] == 1
        with unittest.TestCase().assertRaises(KeyError):
            archive.get_project(project_id)


def test_project_with_running_audit_cannot_be_deleted():
    with TemporaryDirectory() as temp:
        archive = repository(Path(temp))
        resolved = archive.resolve_project_stage("审核中项目", "施工")
        archive.begin_audit(resolved["stage"]["stage_id"], "running-delete")
        with unittest.TestCase().assertRaisesRegex(ValueError, "正在排队或执行"):
            archive.delete_project(resolved["project"]["project_id"])
