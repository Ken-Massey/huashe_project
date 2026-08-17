import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


# ===== 你平时只需要改这里 =====

# 新案例文件路径：支持 .docx / .pdf / 已抽取好的 .case.json
NEW_CASE_FILE = r"D:\桌面\华设项目\安全评估报告\银城中央门NO.2019G38地块安全影响评价报告20200210y正式版.pdf"

# 是否先重建历史案例建议数据库：
# 第一次使用、或者“项目安全评估”文件夹新增了案例时，改成 True；
# 平时只是匹配新案例，保持 False 即可，速度更快。
REBUILD_DATABASE = False

# 历史案例文件夹
HISTORICAL_CASE_ROOT = r"D:\桌面\华设项目\项目安全评估"

# 输出名称。留空则自动用新案例文件名。
RUN_NAME = ""

# ===== 一般不用改下面 =====

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILE = PROJECT_ROOT / "data" / "case_advice_database.json"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_advice_match"


def safe_name(text, max_len=80):
    invalid = '<>:"/\\|?*.'
    for ch in invalid:
        text = text.replace(ch, "_")
    text = "_".join(text.split())
    return (text.strip("_") or "new_case")[:max_len]


def run_step(command):
    print("RUN:", " ".join(str(part) for part in command), flush=True)
    subprocess.run(command, cwd=str(PROJECT_ROOT), check=True)


def main():
    print("=" * 60)
    print("正在运行：01_match_new_case_advice.py")
    print(f"新案例文件：{NEW_CASE_FILE}")
    print(f"历史案例库：{DATABASE_FILE}")
    print("=" * 60)

    new_case = Path(NEW_CASE_FILE)
    if not new_case.exists():
        raise FileNotFoundError(f"找不到新案例文件：{new_case}")

    if REBUILD_DATABASE or not DATABASE_FILE.exists():
        run_step(
            [
                sys.executable,
                "scripts/16_build_case_advice_database.py",
                HISTORICAL_CASE_ROOT,
                "-o",
                str(DATABASE_FILE),
            ]
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = RUN_NAME.strip() or f"{safe_name(new_case.stem)}_{timestamp}"
    output_dir = OUTPUT_ROOT / output_name

    run_step(
        [
            sys.executable,
            "scripts/17_match_case_advice.py",
            str(new_case),
            "--database",
            str(DATABASE_FILE),
            "-o",
            str(output_dir),
        ]
    )

    result_json = output_dir / "case_advice_match.json"
    if result_json.exists():
        result = json.loads(result_json.read_text(encoding="utf-8"))
        best = result.get("best_match") or {}
        advices = best.get("advices") or []
        print("\n匹配摘要：")
        print(f"最相似案例：{best.get('case_name')}")
        print(f"相似度：{best.get('score')}")
        print(f"可复制建议数量：{len(advices)}")
        if not advices:
            print("注意：最相似案例没有提取到建议。请先把 REBUILD_DATABASE 改成 True 重建数据库，或检查历史案例中是否有“建议/审查意见”章节。")

    print("\n完成。请打开下面这个文件查看匹配结果和可复制建议：")
    print(output_dir / "case_advice_match.md")


if __name__ == "__main__":
    main()
