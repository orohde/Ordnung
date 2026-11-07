"""Extract searchable text from documents.

PDF pages with a text layer are read directly. Pages without one are
rendered and passed to Tesseract (if installed). The archive files are never
modified; the text only goes into the index.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import threading
import zipfile
from dataclasses import dataclass
from pathlib import Path

MIN_PAGE_CHARS = 25        # fewer characters on a page → treat it as a scan
MAX_TEXT_CHARS = 300_000   # keep the index small for huge documents


@dataclass
class Extracted:
    text: str
    pages: int = 0
    ocr_pages: int = 0
    method: str = "none"
    error: str = ""


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _ocr_image_bytes(data: bytes, lang: str, timeout: int = 180) -> str:
    result = subprocess.run(
        ["tesseract", "stdin", "stdout", "-l", lang, "--psm", "3"],
        input=data, capture_output=True, timeout=timeout, check=False,
    )
    return result.stdout.decode("utf-8", "replace")


def _clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()[:MAX_TEXT_CHARS]


def extract_pdf(path: Path, ocr: bool, lang: str, max_ocr_pages: int) -> Extracted:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(path))
    try:
        parts: list[str] = []
        ocr_pages = 0
        for index in range(len(pdf)):
            page = pdf[index]
            try:
                textpage = page.get_textpage()
                text = textpage.get_text_bounded()
                textpage.close()
                if len(text.strip()) < MIN_PAGE_CHARS and ocr and ocr_pages < max_ocr_pages:
                    bitmap = page.render(scale=300 / 72, grayscale=True)
                    image = bitmap.to_pil()
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG")
                    text = _ocr_image_bytes(buffer.getvalue(), lang)
                    ocr_pages += 1
                parts.append(text)
            finally:
                page.close()
        method = "ocr" if ocr_pages and ocr_pages == len(pdf) else ("mixed" if ocr_pages else "text")
        return Extracted(_clean("\n\n".join(parts)), pages=len(pdf), ocr_pages=ocr_pages, method=method)
    finally:
        pdf.close()


def extract_docx(path: Path) -> Extracted:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    return Extracted(_clean(text), method="docx")


def extract(path: Path, ext: str, ocr: bool = True, lang: str = "deu+eng", max_ocr_pages: int = 30) -> Extracted:
    ocr = ocr and tesseract_available()
    try:
        if ext == "pdf":
            return extract_pdf(path, ocr, lang, max_ocr_pages)
        if ext == "docx":
            return extract_docx(path)
        if ext in {"txt", "md"}:
            return Extracted(_clean(path.read_text(encoding="utf-8", errors="replace")), method="text")
        if ext in {"png", "jpg", "jpeg", "tif", "tiff"}:
            if not ocr:
                return Extracted("", method="none")
            return Extracted(_clean(_ocr_image_bytes(path.read_bytes(), lang)), pages=1, ocr_pages=1, method="ocr")
        return Extracted("", method="none")
    except Exception as exc:  # noqa: BLE001 - one broken file must not stop the queue
        return Extracted("", method="error", error=f"{type(exc).__name__}: {exc}"[:500])


_THUMB_LOCK = threading.Lock()   # pdfium is not thread-safe


def render_thumb(path: Path, ext: str, dest: Path, width: int = 240) -> None:
    """First page (or the picture itself) as a small PNG at ``dest``."""
    from PIL import Image

    with _THUMB_LOCK:
        if ext == "pdf":
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(str(path))
            try:
                page = pdf[0]
                try:
                    image = page.render(scale=width / page.get_width()).to_pil()
                finally:
                    page.close()
            finally:
                pdf.close()
        elif ext in {"png", "jpg", "jpeg", "tif", "tiff"}:
            image = Image.open(path)
            image.thumbnail((width, width * 2))
        else:
            raise ValueError("no picture for this type")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp")
    image.convert("RGB").save(tmp, format="PNG", optimize=True)
    os.replace(tmp, dest)
