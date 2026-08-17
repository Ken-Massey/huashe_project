"""PyCharm entry: scan historical folders and build the reply database."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stage1_reply_system.history import build_history_database, load_history_cases


# 在 PyCharm 中直接运行。新增历史资料目录时，在列表中增加一行即可。
HISTORY_ROOTS = [
    PROJECT_ROOT / "华设",
    PROJECT_ROOT / "小微工程-报审资料及回函",
]
DATABASE_FILE = ROOT / "data" / "history_replies.sqlite3"
REPORT_FILE = ROOT / "outputs" / "history_database_build_report.json"
INDEX_FILE = ROOT / "outputs" / "history_replies_index.json"


def main() -> None:
    print("开始扫描历史来函与回函，请勿关闭 Word。", flush=True)
    result = build_history_database(
        HISTORY_ROOTS,
        DATABASE_FILE,
        rebuild=True,
        allow_pdf_ocr=True,
        progress=lambda current, total, name: print(f"[{current}/{total}] {name}", flush=True),
    )
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    INDEX_FILE.write_text(
        json.dumps(load_history_cases(DATABASE_FILE), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("历史回函数据库建立完成")
    print(f"来函文件：{result['incoming_count']}")
    print(f"回函源文件：{result['reply_file_count']}")
    print(f"去重后案例：{result['stored_case_count']}")
    print(f"警告：{len(result['warnings'])}")
    print(f"数据库：{DATABASE_FILE}")
    print(f"可读索引：{INDEX_FILE}")
    print(f"建库报告：{REPORT_FILE}")


if __name__ == "__main__":
    main()
