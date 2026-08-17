import argparse
from pathlib import Path
from common import ensure_dir, read_document_paragraphs, write_jsonl


def convert_one(path, output_dir):
    path = Path(path)
    doc_id = path.stem
    paras = read_document_paragraphs(path)
    rows = []
    for idx, item in enumerate(paras, start=1):
        rows.append({
            "doc_id": doc_id,
            "source_file": str(path),
            "source_page": item.get("page"),
            "paragraph_id": idx,
            "text": item["text"],
        })
    txt_path = Path(output_dir) / f"{doc_id}.txt"
    jsonl_path = Path(output_dir) / f"{doc_id}.paragraphs.jsonl"
    txt_path.write_text("\n".join(r["text"] for r in rows), encoding="utf-8")
    write_jsonl(jsonl_path, rows)
    print(f"converted: {path.name}, paragraphs={len(rows)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("-o", "--output", default="data/texts")
    args = parser.parse_args()
    ensure_dir(args.output)
    input_path = Path(args.input)
    files = (
        [input_path]
        if input_path.is_file()
        else list(input_path.glob("*.docx")) + list(input_path.glob("*.pdf")) + list(input_path.glob("*.txt"))
    )
    for path in files:
        convert_one(path, args.output)


if __name__ == "__main__":
    main()
