"""PyCharm entry: generate the regulation review and reply draft for one case."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stage1_reply_system.review_generation import (
    build_review_package,
    render_reply_draft_markdown,
    render_review_markdown,
)


# 在 PyCharm 中审核其他项目时，只需修改下面三行。
INPUT_FILE = ROOT / "outputs" / "letter_extraction" / "taixinlu" / "04_merged_input.json"
LETTER_TEXT_FILE = ROOT / "outputs" / "letter_extraction" / "taixinlu" / "函件全文.txt"
OUTPUT_NAME = "taixinlu"

DATABASE_FILE = ROOT / "data" / "history_replies.sqlite3"
OUTPUT_DIR = ROOT / "outputs" / "review_packages" / OUTPUT_NAME


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    letter_text = LETTER_TEXT_FILE.read_text(encoding="utf-8") if LETTER_TEXT_FILE.exists() else ""
    package = build_review_package(data, DATABASE_FILE, letter_text=letter_text)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "01_calculation.json", package["calculation"])
    write_json(OUTPUT_DIR / "02_history_match.json", package["history_match"])
    write_json(OUTPUT_DIR / "03_review_package.json", package)
    (OUTPUT_DIR / "审核意见.md").write_text(render_review_markdown(package), encoding="utf-8")
    (OUTPUT_DIR / "回函草稿.md").write_text(render_reply_draft_markdown(package), encoding="utf-8")

    print("第五步审核意见生成完成")
    print(f"总体状态：{package['overall_status']}")
    print(f"待补充字段：{len(package['missing_required_inputs'])}项")
    print(f"历史注意事项：{len(package['historical_advice']['attention_items'])}条")
    print(f"输出目录：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
