from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from audit_api.knowledge_base import KnowledgeBase
from audit_api.regulation_rules import RegulationRepository


def test_regulation_folder_lifecycle_preserves_documents():
    with TemporaryDirectory() as temp:
        root = Path(temp)
        repository = RegulationRepository(root / "regulations.sqlite3", root / "files")
        folder = repository.create_folder("轨道交通")
        renamed = repository.rename_folder(folder["folder_id"], "轨道交通保护专项")
        assert renamed["name"] == "轨道交通保护专项"

        document_id = "REG-TEST"
        document_root = root / "files" / document_id
        document_root.mkdir(parents=True)
        source = document_root / "source.txt"
        text = document_root / "content.txt"
        source.write_text("test", encoding="utf-8")
        text.write_text("test", encoding="utf-8")
        with repository._connect() as connection:
            connection.execute(
                """INSERT INTO regulation(
                    regulation_id,title,version,original_file_name,stored_file,text_file,
                    sha256,extraction_method,text_length,paragraph_count,status,active,
                    created_at,updated_at,folder_id
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    document_id, "测试规程", None, source.name, str(source), str(text),
                    "test-sha", "text", 4, 1, "ready", 1,
                    "2026-07-24T00:00:00", "2026-07-24T00:00:00", folder["folder_id"],
                ),
            )

        assert repository.list_documents(folder_id=folder["folder_id"])[0]["folder_name"] == "轨道交通保护专项"
        deleted = repository.delete_folder(folder["folder_id"])
        assert deleted["regulation_count"] == 1
        uncategorized = repository.list_documents(folder_id="__uncategorized__")
        assert uncategorized[0]["regulation_id"] == document_id
        assert repository.get_document(document_id)["folder_id"] is None


def test_regulation_folder_names_are_unique_only_within_same_parent():
    with TemporaryDirectory() as temp:
        root = Path(temp)
        repository = RegulationRepository(root / "regulations.sqlite3", root / "files")
        national = repository.create_folder("国家标准")
        local = repository.create_folder("地方标准")

        national_child = repository.create_folder("结构保护", national["folder_id"])
        local_child = repository.create_folder("结构保护", local["folder_id"])

        assert national_child["name"] == local_child["name"]
        assert national_child["parent_id"] != local_child["parent_id"]
        with pytest.raises(ValueError, match="同名"):
            repository.create_folder("结构保护", national["folder_id"])
        other_child = repository.create_folder("其他", local["folder_id"])
        with pytest.raises(ValueError, match="同名"):
            repository.rename_folder(other_child["folder_id"], "结构保护")


def test_case_folder_names_are_unique_only_within_same_parent():
    with TemporaryDirectory() as temp:
        root = Path(temp)
        repository = KnowledgeBase(root / "cases.sqlite3", root / "files")
        reviewed = repository.create_folder("已审核")
        pending = repository.create_folder("待审核")

        reviewed_child = repository.create_folder("结构保护", reviewed["folder_id"])
        pending_child = repository.create_folder("结构保护", pending["folder_id"])

        assert reviewed_child["name"] == pending_child["name"]
        assert reviewed_child["parent_id"] != pending_child["parent_id"]
        with pytest.raises(ValueError, match="同名"):
            repository.create_folder("结构保护", reviewed["folder_id"])
        other_child = repository.create_folder("其他", pending["folder_id"])
        with pytest.raises(ValueError, match="同名"):
            repository.rename_folder(other_child["folder_id"], "结构保护")


def test_default_folders_and_automatic_classification():
    with TemporaryDirectory() as temp:
        root = Path(temp)
        repository = RegulationRepository(root / "regulations.sqlite3", root / "files")
        folders = {item["system_key"]: item for item in repository.list_folders()}
        assert set(folders) == {
            "rail_transit", "foundation_pit", "building_fire",
            "environment_monitoring", "other",
        }

        document_id = "REG-AUTO"
        document_root = root / "files" / document_id
        document_root.mkdir(parents=True)
        source = document_root / "source.txt"
        text = document_root / "content.txt"
        source.write_text("test", encoding="utf-8")
        text.write_text("建筑基坑支护技术规程", encoding="utf-8")
        with repository._connect() as connection:
            connection.execute(
                """INSERT INTO regulation(
                    regulation_id,title,version,original_file_name,stored_file,text_file,
                    sha256,extraction_method,text_length,paragraph_count,status,active,
                    created_at,updated_at,folder_id
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
                (
                    document_id, "建筑基坑支护技术规程", None, source.name, str(source), str(text),
                    "auto-sha", "text", 10, 1, "ready", 1,
                    "2026-07-24T00:00:00", "2026-07-24T00:00:00",
                ),
            )

        repository._classify_uncategorized_documents()
        item = repository.get_document(document_id)
        assert item["folder_id"] == folders["foundation_pit"]["folder_id"]
