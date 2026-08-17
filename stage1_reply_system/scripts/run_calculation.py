import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stage1_reply_system.rules import evaluate_project

# 在 PyCharm 中只需修改这一行，即可换成新的项目输入 JSON。
INPUT_FILE = ROOT / "examples" / "synthetic_calculation.example.json"
OUTPUT_FILE = ROOT / "outputs" / "latest_calculation.json"


def main() -> None:
    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    result = evaluate_project(data)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("计算完成")
    print(f"项目：{result['case_id']}")
    for name, value in result["summary"].items():
        print(f"{name}: {value}")
    print(f"完整结果：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
