from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter

from audit_api.mineru_parser import _content_rows, _pdf_parts, _publish_extracted_best_effort


class MinerUParserTests(unittest.TestCase):
    def test_locked_preview_directory_does_not_fail_completed_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            temporary = root / "extracted.tmp"
            temporary.mkdir()
            messages = []

            with patch.object(Path, "replace", side_effect=PermissionError(5, "access denied")):
                published = _publish_extracted_best_effort(
                    temporary,
                    root / "extracted",
                    messages.append,
                )

            self.assertFalse(published)
            self.assertTrue(any("正文结果已保存" in item for item in messages))

    def test_content_list_preserves_pages_headings_and_tables(self) -> None:
        rows = _content_rows([
            {"type": "text", "text": "7.2.4 监测要求", "text_level": 2, "page_idx": 4},
            {
                "type": "table",
                "table_caption": ["表7.2.4"],
                "table_body": "<table><tr><td>应测</td></tr></table>",
                "page_idx": 5,
            },
            {"type": "footer", "text": "页脚", "page_idx": 5},
        ])
        self.assertEqual(rows[0]["page"], 5)
        self.assertEqual(rows[0]["text"], "## 7.2.4 监测要求")
        self.assertEqual(rows[1]["text"], "表7.2.4")
        self.assertEqual(rows[2]["content_type"], "table")
        self.assertEqual(len(rows), 3)

    def test_long_pdf_is_split_with_original_page_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "long.pdf"
            writer = PdfWriter()
            for _ in range(5):
                writer.add_blank_page(width=100, height=100)
            with source.open("wb") as stream:
                writer.write(stream)

            parts = _pdf_parts(source, root / "cache", pages_per_part=2)

            self.assertEqual([part["page_offset"] for part in parts], [0, 2, 4])
            self.assertEqual([part["page_count"] for part in parts], [2, 2, 1])
            self.assertEqual([len(PdfReader(str(part["path"])).pages) for part in parts], [2, 2, 1])


if __name__ == "__main__":
    unittest.main()
