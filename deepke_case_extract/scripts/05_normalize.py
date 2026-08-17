import argparse
import re
from pathlib import Path
from common import ensure_dir, read_jsonl, write_jsonl


WORK_TYPE_MAP = {
    "基坑": "基坑工程",
    "基坑工程": "基坑工程",
    "桩基": "基础工程",
    "管线": "管线工程",
    "道路": "道路工程",
    "降水工程": "降水工程",
    "勘察": "勘察作业",
    "修缮工程": "建筑修缮工程",
}


def normalize_value(field, value):
    if isinstance(value, str):
        value = value.replace("㎡", "m2").replace("ｍ", "m").replace("M", "m")
        value = re.sub(r"\s+", "", value)
    if field in {"case_type", "external_work_type"} and isinstance(value, str):
        for k, v in WORK_TYPE_MAP.items():
            if k in value:
                return v
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_extract_dir")
    parser.add_argument("-o", "--output", default="outputs/normalized")
    args = parser.parse_args()
    ensure_dir(args.output)
    for path in Path(args.raw_extract_dir).glob("*.raw_extract.jsonl"):
        rows = []
        for row in read_jsonl(path):
            row["normalized_value"] = normalize_value(row["field_name"], row["field_value"])
            rows.append(row)
        out = Path(args.output) / path.name.replace(".raw_extract.jsonl", ".normalized.jsonl")
        write_jsonl(out, rows)
        print(f"normalized: {out.name}, rows={len(rows)}")


if __name__ == "__main__":
    main()

