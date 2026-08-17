import argparse
import json
import sys
import tempfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from common import write_json


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


def load_builder():
    path = Path(__file__).with_name("16_build_case_advice_database.py")
    spec = spec_from_file_location("knowledge_case_builder", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def _fallback_text(path):
    from stage1_reply_system.history.text_extract import extract_document

    result = extract_document(path, allow_pdf_ocr=True)
    text = result["text"]
    paragraphs = [{"page": None, "text": line.strip()} for line in text.splitlines() if line.strip()]
    return text, paragraphs, result["method"]


def extract_case(path, case_id, case_name=None, category=None, text_output=None):
    source = Path(path).resolve()
    suffix = source.suffix.lower()
    if suffix not in {".pdf", ".doc", ".docx", ".txt"}:
        raise ValueError(f"不支持的知识库文件格式：{suffix}")

    method = "case_builder"
    if suffix == ".doc":
        text, paragraphs, method = _fallback_text(source)
    else:
        text, paragraphs = builder.document_text(source)
        if len(text.strip()) < 100 and suffix == ".pdf":
            text, paragraphs, method = _fallback_text(source)

    advice_source = source
    temporary = None
    if suffix == ".doc" or method != "case_builder":
        temporary = Path(tempfile.gettempdir()) / f"knowledge_{case_id}.txt"
        temporary.write_text(text, encoding="utf-8")
        advice_source = temporary
    try:
        advices = builder.extract_advices_from_document(advice_source)
        if not advices:
            advices = builder.numbered_advice_candidates(paragraphs, advice_source)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()

    name = case_name or source.stem
    features = builder.extract_features(text, category=category or "", case_name=name)
    if text_output:
        Path(text_output).parent.mkdir(parents=True, exist_ok=True)
        Path(text_output).write_text(text, encoding="utf-8")
    return {
        "case_id": case_id,
        "case_name": name,
        "category": category,
        "case_folder": str(source.parent),
        "report_file": str(source),
        "features": features,
        "advice_count": len(advices),
        "advices": advices,
        "paragraph_count": len(paragraphs),
        "text_length": len(text),
        "extraction_method": method,
    }


def main():
    parser = argparse.ArgumentParser(description="Extract one uploaded case for the maintainable knowledge base.")
    parser.add_argument("input")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--case-name", default=None)
    parser.add_argument("--category", default=None)
    parser.add_argument("--text-output", default=None)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    result = extract_case(
        args.input,
        args.case_id,
        case_name=args.case_name,
        category=args.category,
        text_output=args.text_output,
    )
    write_json(args.output, result)
    print(json.dumps({"case_id": result["case_id"], "advice_count": result["advice_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
