import argparse
import json
from pathlib import Path

from common import ensure_dir, read_jsonl


def make_instruction(row):
    schema = row.get("schema", {})
    schema_text = json.dumps(schema, ensure_ascii=False, indent=2)
    base = row.get("instruction", "").strip()
    return (
        f"{base}\n\n"
        "请严格根据下面的属性 Schema 从 input 中抽取信息。\n"
        "要求：\n"
        "1. 只输出 JSON，不要解释。\n"
        "2. JSON 的 key 必须来自 Schema。\n"
        "3. 找不到的字段填 null。\n"
        "4. 数值尽量保留单位，例如 4.15m、19.2m、48616m2。\n"
        "5. 不要编造 input 中没有的信息。\n\n"
        f"Schema:\n{schema_text}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("deepke_input_dir")
    parser.add_argument("-o", "--output", default="outputs/oneke_inputs")
    args = parser.parse_args()

    out_dir = Path(args.output)
    ensure_dir(out_dir)
    for path in Path(args.deepke_input_dir).glob("*.deepke_input.jsonl"):
        rows = read_jsonl(path)
        out_path = out_dir / path.name.replace(".deepke_input.jsonl", ".oneke_input.jsonl")
        with out_path.open("w", encoding="utf-8") as writer:
            for row in rows:
                record = {
                    "instruction": make_instruction(row),
                    "input": row.get("input", ""),
                    "output": "test",
                    "doc_id": row.get("doc_id"),
                    "module": row.get("module"),
                    "source_file": row.get("source_file"),
                    "source_page": row.get("source_page"),
                    "source_paragraph": row.get("source_paragraph"),
                    "source_section": row.get("source_section"),
                }
                writer.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"oneke input: {out_path}, rows={len(rows)}")


if __name__ == "__main__":
    main()
