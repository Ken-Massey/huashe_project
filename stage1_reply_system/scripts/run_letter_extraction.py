import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stage1_reply_system.document_processing import (
    extract_letter_fields,
    extract_pdf,
    merge_extracted_with_manual,
)


# 在 PyCharm 中处理其他函件时，只需修改下面两行。
PDF_FILE = PROJECT_ROOT / "华设" / "1号线 太新路泵站及进出管道改扩建工程-无监测报审" / "规划阶段" / "报审单位提供资料" / "关于太新路泵站及进出水管道改扩建工程规划方案征求地铁意见的函.pdf"
MANUAL_INPUT_FILE = ROOT / "examples" / "project_input.example.json"
OUTPUT_DIR = ROOT / "outputs" / "letter_extraction" / "taixinlu"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    extraction = extract_pdf(PDF_FILE)
    fields = extract_letter_fields(extraction)
    manual_input = json.loads(MANUAL_INPUT_FILE.read_text(encoding="utf-8"))
    merge_result = merge_extracted_with_manual(manual_input, fields)

    write_json(OUTPUT_DIR / "01_pdf_text.json", extraction)
    write_json(OUTPUT_DIR / "02_extracted_fields.json", fields)
    write_json(OUTPUT_DIR / "03_merge_report.json", {
        key: value for key, value in merge_result.items() if key != "merged_input"
    })
    write_json(OUTPUT_DIR / "04_merged_input.json", merge_result["merged_input"])
    (OUTPUT_DIR / "函件全文.txt").write_text(extraction["full_text"], encoding="utf-8")

    print("函件处理完成")
    print(f"PDF类型：{'扫描件' if extraction['is_scanned'] else '文本型或混合型'}")
    for name, field in fields["fields"].items():
        value = field["value"]
        if value not in (None, "", []):
            print(f"{name}: {value}（置信度 {field['confidence']:.3f}，{field['status']}）")
    print(f"自动填入：{len(merge_result['applied_fields'])}项")
    print(f"冲突：{len(merge_result['conflicts'])}项")
    print(f"需复核：{len(merge_result['review_required'])}项")
    print(f"结果目录：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
