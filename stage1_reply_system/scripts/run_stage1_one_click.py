"""PyCharm entry: run all stage-one processing steps for one project."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stage1_reply_system.pipeline import run_stage1_pipeline


# 在 PyCharm 中处理其他项目时，只需修改下面三行。
PDF_FILE = PROJECT_ROOT / "华设" / "1号线 太新路泵站及进出管道改扩建工程-无监测报审" / "规划阶段" / "报审单位提供资料" / "关于太新路泵站及进出水管道改扩建工程规划方案征求地铁意见的函.pdf"
MANUAL_INPUT_FILE = ROOT / "examples" / "project_input.example.json"
RUN_NAME = "太新路规划阶段"

DATABASE_FILE = ROOT / "data" / "history_replies.sqlite3"
OUTPUT_ROOT = ROOT / "outputs" / "one_click_runs"


def main() -> None:
    manual_input = json.loads(MANUAL_INPUT_FILE.read_text(encoding="utf-8"))
    result = run_stage1_pipeline(
        PDF_FILE,
        manual_input,
        DATABASE_FILE,
        OUTPUT_ROOT,
        run_name=RUN_NAME,
        progress=lambda message: print(message, flush=True),
    )
    summary = result["summary"]
    print("\n第一阶段一键审核完成")
    print(f"总体状态：{summary['overall_status']}")
    print(f"历史匹配：{summary['history_match_project']}（{summary['history_match_similarity']}）")
    print(f"结果目录：{result['output_dir']}")


if __name__ == "__main__":
    main()
