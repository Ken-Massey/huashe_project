from pathlib import Path
import os
import shutil
import unittest
import uuid

from audit_api import main
from audit_api import patrol as patrol_module
from audit_api.patrol import PatrolRepository, apply_watermark

WORKSPACE_TMP = Path(__file__).resolve().parents[2] / "logs" / "patrol_test_tmp"

ADMIN = {"user_id": "1", "name": "管理员", "is_admin": True}
PATROL1 = {"user_id": "10", "name": "张三", "is_admin": False}
PATROL2 = {"user_id": "11", "name": "李四", "is_admin": False}


def _sample_image(tmp: Path, name: str = "photo.jpg") -> Path:
    from PIL import Image

    path = tmp / name
    Image.new("RGB", (320, 240), color=(90, 140, 120)).save(path, format="JPEG")
    return path


class PatrolRepositoryTests(unittest.TestCase):
    def setUp(self):
        WORKSPACE_TMP.mkdir(parents=True, exist_ok=True)
        root = WORKSPACE_TMP / f"patrol_{os.getpid()}_{uuid.uuid4().hex[:12]}"
        root.mkdir()
        self.root = root
        self.repository = PatrolRepository(root / "patrol.sqlite3", root / "uploads")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _task(self, **overrides):
        payload = {
            "name": "新街口站东侧基坑巡查",
            "line": "1号线",
            "location_desc": "新街口站东侧",
            "requirement": "核查是否超范围施工",
            "assigned_user_id": "10",
            "assigned_user_name": "张三",
        }
        payload.update(overrides)
        return self.repository.create_task(payload, ADMIN)

    def test_dicts_seeded_four_types(self):
        for dict_type in ("line", "construction_type", "hazard_type", "hazard_risk"):
            self.assertTrue(self.repository.list_dicts(dict_type), dict_type)

    def test_task_lifecycle_and_row_filter(self):
        task1 = self._task()
        task2 = self._task(name="二号任务", assigned_user_id="11", assigned_user_name="李四")
        self.assertTrue(task1["task_no"].startswith("RW"))

        # 巡查员只能看到指派给自己的
        mine = self.repository.list_tasks(PATROL1)
        self.assertEqual(mine["total"], 1)
        self.assertEqual(mine["items"][0]["task_id"], task1["task_id"])

        # 管理员看到全部
        self.assertEqual(self.repository.list_tasks(ADMIN)["total"], 2)

        # 巡查员访问他人任务 → KeyError
        with self.assertRaises(KeyError):
            self.repository.get_task(task2["task_id"], PATROL1)

        # 平台更新任务（改派）
        updated = self.repository.update_task(task1["task_id"], {"assigned_user_id": "11", "assigned_user_name": "李四"}, ADMIN)
        self.assertEqual(updated["assigned_user_id"], "11")

        # 软删除（仅待执行）
        self.repository.soft_delete_task(task2["task_id"], ADMIN)
        self.assertEqual(self.repository.list_tasks(ADMIN)["total"], 1)

    def test_task_completed_requires_all_hazards_closed(self):
        task = self._task()
        hazard = self.repository.create_hazard(task["task_id"], {
            "description": "超范围施工", "hazard_type": "超范围施工", "risk_level": "高",
            "rectify_owner": "某施工方", "rectify_requirement": "停止超范围施工并恢复",
        }, ADMIN)
        with self.assertRaises(ValueError):
            self.repository.set_task_status(task["task_id"], "completed", ADMIN)

        # 走完整改闭环：整改反馈 → 提交复核 → 复核通过
        self.repository.create_record(task["task_id"], {"type": "rectify", "hazard_id": hazard["hazard_id"]}, PATROL1)
        self.repository.submit_rectify_review(hazard["hazard_id"], PATROL1)
        self.repository.review_hazard(hazard["hazard_id"], {"result": "closed", "comment": ""}, ADMIN)

        done = self.repository.set_task_status(task["task_id"], "completed", ADMIN)
        self.assertEqual(done["status"], "completed")

    def test_record_and_media(self):
        task = self._task()
        record = self.repository.create_record(task["task_id"], {
            "type": "patrol", "longitude": 118.784, "latitude": 32.0415, "accuracy": 12.5, "note": "现场核实",
        }, PATROL1)
        self.assertEqual(record["type"], "patrol")

        image = _sample_image(self.root)
        photo = self.repository.add_media(record["record_id"], "photo", image, "photo.jpg", "2026-08-21 16:30:00")
        self.assertTrue(photo["media_id"].startswith("pmed_"))

        video = self.root / "clip.mp4"
        video.write_bytes(b"\x00\x00\x00\x18ftypmp42")
        vid = self.repository.add_media(record["record_id"], "video", video, "clip.mp4", "")
        self.assertEqual(vid["kind"], "video")

        detail = self.repository.get_task(task["task_id"], PATROL1)
        self.assertEqual(detail["records"][0]["media"][0]["kind"], "photo")
        self.assertEqual(len(detail["records"][0]["media"]), 2)

    def test_hazard_closed_loop(self):
        task = self._task()
        # 巡查员记录隐患 → 待确认
        hazard = self.repository.create_hazard(task["task_id"], {
            "description": "现场疑似超范围开挖", "hazard_type": "超范围施工", "risk_level": "中",
        }, PATROL1)
        self.assertEqual(hazard["status"], "pending_confirm")

        # 平台确认 + 下发整改要求 → 待整改
        confirmed = self.repository.confirm_hazard(hazard["hazard_id"], {"rectify_requirement": "立即停止并恢复原状"}, ADMIN)
        self.assertEqual(confirmed["status"], "pending_rectify")

        # 巡查员提交整改反馈（关联隐患）→ 隐患转整改中
        record = self.repository.create_record(task["task_id"], {
            "type": "rectify", "hazard_id": hazard["hazard_id"], "note": "已完成整改",
        }, PATROL1)
        self.assertEqual(record["type"], "rectify")
        self.assertEqual(self.repository.get_hazard(hazard["hazard_id"])["status"], "rectifying")

        # 提交复核 → 待复核
        self.repository.submit_rectify_review(hazard["hazard_id"], PATROL1)
        self.assertEqual(self.repository.get_hazard(hazard["hazard_id"])["status"], "pending_review")

        # 平台复核不通过 → 退回整改中
        rejected = self.repository.review_hazard(hazard["hazard_id"], {"result": "reject", "comment": "未完全恢复"}, ADMIN)
        self.assertEqual(rejected["status"], "rectifying")

        # 再次提交复核并复核通过 → 已闭环
        self.repository.create_record(task["task_id"], {"type": "rectify", "hazard_id": hazard["hazard_id"]}, PATROL1)
        self.repository.submit_rectify_review(hazard["hazard_id"], PATROL1)
        closed = self.repository.review_hazard(hazard["hazard_id"], {"result": "closed", "comment": "整改到位"}, ADMIN)
        self.assertEqual(closed["status"], "closed")

    def test_rectify_record_requires_hazard(self):
        task = self._task()
        with self.assertRaises(ValueError):
            self.repository.create_record(task["task_id"], {"type": "rectify", "hazard_id": ""}, PATROL1)

    def test_watermark_produces_jpeg(self):
        source = _sample_image(self.root, "src.jpg")
        destination = self.root / "out.jpg"
        apply_watermark(source, destination, ["任务 RW202608240001", "时间 2026-08-21 16:30:00"])
        self.assertTrue(destination.read_bytes().startswith(b"\xff\xd8"))


class PatrolRouteRegistrationTests(unittest.TestCase):
    def test_routes_registered(self):
        paths = main.app.openapi()["paths"]
        for expected in (
            "/api/v1/patrol/tasks",
            "/api/v1/patrol/tasks/{task_id}",
            "/api/v1/patrol/tasks/{task_id}/status",
            "/api/v1/patrol/tasks/{task_id}/records",
            "/api/v1/patrol/tasks/{task_id}/hazards",
            "/api/v1/patrol/records/{record_id}/media",
            "/api/v1/patrol/hazards/{hazard_id}/confirm",
            "/api/v1/patrol/hazards/{hazard_id}/submit",
            "/api/v1/patrol/hazards/{hazard_id}/review",
            "/api/v1/patrol/media/{media_id}/file",
            "/api/v1/patrol/statistics",
            "/api/v1/patrol/dicts",
        ):
            self.assertIn(expected, paths, f"缺少路由 {expected}")


if __name__ == "__main__":
    unittest.main()
