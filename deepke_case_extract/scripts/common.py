import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def write_json(path, data):
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path, rows):
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def clean_value(value):
    if value is None:
        return None
    return str(value).strip(" ：:，,；;。 \t\r\n")


def first_match(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return clean_value(m.group(1))
    return None


def read_docx_paragraphs(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs = []
    for p in root.findall(".//w:p", DOCX_NS):
        text = "".join(t.text or "" for t in p.findall(".//w:t", DOCX_NS)).strip()
        if text:
            paragraphs.append({"page": None, "text": text})
    return paragraphs


def read_pdf_paragraphs(path):
    try:
        import pdfplumber
    except Exception as exc:
        raise RuntimeError("缺少 pdfplumber，请使用 Codex 自带 Python 运行脚本。") from exc

    rows = []
    with pdfplumber.open(str(path)) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.replace("\r", "\n")
            for para in re.split(r"\n+", text):
                para = para.strip()
                if para:
                    rows.append({"page": page_idx, "text": para})
    return rows


def read_txt_paragraphs(path):
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    rows = []
    for paragraph in re.split(r"\n+", text.replace("\r", "\n")):
        paragraph = paragraph.strip()
        if paragraph:
            rows.append({"page": None, "text": paragraph})
    return rows


def read_document_paragraphs(path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx_paragraphs(path)
    if suffix == ".pdf":
        return read_pdf_paragraphs(path)
    if suffix == ".txt":
        return read_txt_paragraphs(path)
    raise ValueError(f"暂不支持文件类型: {suffix}")
