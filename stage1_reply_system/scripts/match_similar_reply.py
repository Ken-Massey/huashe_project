"""PyCharm entry: match one new case and copy the best historical advice verbatim."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stage1_reply_system.history import match_similar_replies


# 在 PyCharm 中匹配其他项目时，只需修改下面的 INPUT_FILE 和 LETTER_TEXT_FILE。
INPUT_FILE = ROOT / "outputs" / "letter_extraction" / "taixinlu" / "04_merged_input.json"
LETTER_TEXT_FILE = ROOT / "outputs" / "letter_extraction" / "taixinlu" / "函件全文.txt"
DATABASE_FILE = ROOT / "data" / "history_replies.sqlite3"
OUTPUT_FILE = ROOT / "outputs" / "latest_reply_match.json"
ADVICE_FILE = ROOT / "outputs" / "latest_matched_advice.txt"


def main() -> None:
    project_input = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    letter_text = LETTER_TEXT_FILE.read_text(encoding="utf-8") if LETTER_TEXT_FILE.exists() else ""
    result = match_similar_replies(project_input, DATABASE_FILE, letter_text=letter_text)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    selected = result["selected_match"]
    if selected:
        ADVICE_FILE.write_text(selected["advice_text"], encoding="utf-8")
        print("已匹配历史回函，并逐字复制其审核意见。")
        print(f"历史项目：{selected['project_name']}")
        print(f"相似度：{selected['similarity_score']:.4f}")
        print(f"回函来源：{selected['primary_reply_file']}")
        print(f"意见文件：{ADVICE_FILE}")
    else:
        if ADVICE_FILE.exists():
            ADVICE_FILE.unlink()
        print("最高相似度未达到自动采用阈值，请人工选择候选回函。")
    print(f"完整匹配依据：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
