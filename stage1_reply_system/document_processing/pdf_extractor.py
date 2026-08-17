import hashlib
from pathlib import Path
from typing import Any


_OCR_ENGINE: Any | None = None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _direct_page(page: Any, page_number: int) -> dict[str, Any]:
    text = (page.extract_text() or "").strip()
    lines = [
        {
            "text": line.strip(),
            "confidence": 1.0,
            "bbox_pixels": None,
        }
        for line in text.splitlines()
        if line.strip()
    ]
    return {
        "page": page_number,
        "method": "direct",
        "text": "\n".join(line["text"] for line in lines),
        "average_confidence": 1.0 if lines else 0.0,
        "lines": lines,
    }


def _ocr_lines(engine: Any, image: Any, threshold: int, y_offset: int = 0) -> list[dict[str, Any]]:
    import cv2

    _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
    ocr_result, _ = engine(binary)
    lines: list[dict[str, Any]] = []
    for item in ocr_result or []:
        box, text, confidence = item
        clean_text = str(text).strip()
        if not clean_text:
            continue
        lines.append(
            {
                "text": clean_text,
                "confidence": round(float(confidence), 4),
                "bbox_pixels": [[round(float(x), 1), round(float(y + y_offset), 1)] for x, y in box],
            }
        )
    lines.sort(key=lambda item: (min(point[1] for point in item["bbox_pixels"]), min(point[0] for point in item["bbox_pixels"])))
    return lines


def _ocr_page(page: Any, page_number: int, resolution: int = 300, scan_footer: bool = False) -> dict[str, Any]:
    try:
        import cv2
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError(
            "扫描PDF需要OCR依赖。请在当前PyCharm解释器中安装 requirements.txt。"
        ) from exc

    image = np.array(page.to_image(resolution=resolution).original)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        _OCR_ENGINE = RapidOCR()
    engine = _OCR_ENGINE
    lines = _ocr_lines(engine, gray, 200)
    footer_lines: list[dict[str, Any]] = []
    if scan_footer:
        height = gray.shape[0]
        start = int(height * 0.45)
        end = int(height * 0.92)
        footer_lines = _ocr_lines(engine, gray[start:end, :], 160, y_offset=start)
    average = sum(line["confidence"] for line in lines) / len(lines) if lines else 0.0
    return {
        "page": page_number,
        "method": "ocr",
        "text": "\n".join(line["text"] for line in lines),
        "average_confidence": round(average, 4),
        "image_resolution_dpi": resolution,
        "lines": lines,
        "footer_lines": footer_lines,
    }


def extract_pdf(
    pdf_path: str | Path,
    direct_text_threshold: int = 30,
    *,
    ocr_resolution: int = 300,
    max_pages: int | None = None,
    scan_last_page_footer: bool = True,
) -> dict[str, Any]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("缺少 pdfplumber，请安装 requirements.txt。") from exc

    path = Path(pdf_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    pages: list[dict[str, Any]] = []
    with pdfplumber.open(path) as document:
        source_page_count = len(document.pages)
        selected_pages = document.pages[:max_pages] if max_pages else document.pages
        for page_number, page in enumerate(selected_pages, 1):
            direct = _direct_page(page, page_number)
            if len(direct["text"]) >= direct_text_threshold:
                pages.append(direct)
            else:
                pages.append(_ocr_page(
                    page,
                    page_number,
                    resolution=ocr_resolution,
                    scan_footer=scan_last_page_footer and page_number == len(selected_pages),
                ))

    methods = {page["method"] for page in pages}
    extraction_method = methods.pop() if len(methods) == 1 else "mixed"
    return {
        "format_version": "pdf_text_extraction_v1",
        "source_file": str(path),
        "sha256": _file_sha256(path),
        "page_count": len(pages),
        "source_page_count": source_page_count,
        "pages_truncated": max_pages is not None and source_page_count > max_pages,
        "extraction_method": extraction_method,
        "is_scanned": all(page["method"] == "ocr" for page in pages),
        "full_text": "\n\n".join(f"[第{page['page']}页]\n{page['text']}" for page in pages),
        "pages": pages,
    }
