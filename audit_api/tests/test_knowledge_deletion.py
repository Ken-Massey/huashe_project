from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_api.knowledge_base import KnowledgeBase
from audit_api.regulation_rules import RegulationRepository


class KnowledgeDeletionTests(unittest.TestCase):
    def test_permanent_case_deletion_removes_record_files_and_match_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            files = root / "cases"
            case_folder = files / "case-1"
            case_folder.mkdir(parents=True)
            source = case_folder / "case.docx"
            source.write_bytes(b"case")
            text_file = case_folder / "extracted_text.txt"
            text_file.write_text("案例正文", encoding="utf-8")
            database = root / "knowledge.sqlite3"
            match_database = root / "case_advice_database.json"
            repository = KnowledgeBase(database, files, match_database)
            with repository._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO kb_case(
                        case_id,case_name,original_file_name,stored_file,source_file,sha256,
                        file_size,text_file,features_json,advices_json,advice_count,status,
                        active,managed_file,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        "case-1", "测试案例", source.name, str(source), str(source), "digest",
                        source.stat().st_size, str(text_file), "{}", json.dumps(["建议"]),
                        1, "ready", 1, 1, "2026-01-01T00:00:00", "2026-01-01T00:00:00",
                    ),
                )
                repository._export_locked(connection)

            deleted = repository.delete_case("case-1")

            self.assertEqual(deleted["case_name"], "测试案例")
            self.assertFalse(case_folder.exists())
            with self.assertRaises(KeyError):
                repository.get_case("case-1")
            exported = json.loads(match_database.read_text(encoding="utf-8"))
            self.assertEqual(exported["case_count"], 0)

    def test_permanent_regulation_deletion_removes_document_clauses_rules_and_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "regulation.txt"
            source.write_text("5.3.2 基坑工程应实施监测。", encoding="utf-8")
            repository = RegulationRepository(root / "regulations.sqlite3", root / "regulations")
            document = repository.import_document(source, "测试规程", "2026", lambda _: None)
            rule = repository.create_rule(
                document["regulation_id"],
                {
                    "rule_type": "conditional_rule",
                    "name": "基坑监测",
                    "conditions": [{"field": "project_type", "operator": "==", "value": "基坑"}],
                    "requirement": {"field": "monitoring_required", "operator": "==", "value": True},
                    "source": {"original_text": "基坑工程应实施监测。", "clause": "5.3.2"},
                },
            )
            managed_folder = Path(document["stored_file"]).parent

            deleted = repository.delete_document(document["regulation_id"])

            self.assertEqual(deleted["title"], "测试规程")
            self.assertFalse(managed_folder.exists())
            with self.assertRaises(KeyError):
                repository.get_document(document["regulation_id"])
            with repository._connect() as connection:
                clause_count = connection.execute(
                    "SELECT COUNT(*) FROM regulation_clause WHERE regulation_id=?",
                    (document["regulation_id"],),
                ).fetchone()[0]
                rule_count = connection.execute(
                    "SELECT COUNT(*) FROM regulation_rule WHERE rule_id=?",
                    (rule["rule_id"],),
                ).fetchone()[0]
            self.assertEqual(clause_count, 0)
            self.assertEqual(rule_count, 0)


if __name__ == "__main__":
    unittest.main()
