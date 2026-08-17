import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from audit_api.services import _run_dynamic_for_case


class ArchiveAuditContextTests(unittest.TestCase):
    def test_stage_two_case_receives_project_archive_context(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            case_path = root / "run" / "case.json"
            case_path.parent.mkdir(parents=True)
            case_path.write_text(json.dumps({"project_name": "测试项目"}), encoding="utf-8")
            context = {
                "current_stage": {"stage_name": "专项施工"},
                "previous_stage_count": 1,
                "previous_stages": [{"stage_name": "深化设计", "summary": "落实监测"}],
            }
            fake_audit = {
                "format_version": "pure_llm_rag_audit_v1",
                "risk_report": {"overall_risk_level": "低", "findings": []},
            }
            with patch(
                "audit_api.services.run_ima_rag_audit", return_value=fake_audit
            ) as run_audit:
                _run_dynamic_for_case(
                    case_path,
                    root / "reports",
                    project_archive_context=context,
                )

            case_data = run_audit.call_args.args[0]
            self.assertEqual(case_data["project_archive_context"], context)


if __name__ == "__main__":
    unittest.main()
