"""Uploads from the browser (iPhone camera, Files, Finder) into the inbox.

Photos become PDFs right away – HEIC from the iPhone included – so preview,
editor, Mappen-PDF and the text search treat them like any scan. Several photos
or PDFs can be combined into one document (a three-page letter photographed page
by page). The result goes to the built-in inbox folder "Hochgeladen" in the data
folder; from there it is filed like everything else.
"""

from __future__ import annotations

import io
import os
import re
import threading
import time
import uuid
from pathlib import Path

IMAGE_EXT = {"jpg", "jpeg", "png", "heic", "heif", "tif", "tiff", "webp"}
KEEP_EXT = {"pdf", "docx", "txt"}
MAX_FILE_BYTES = 60 * 1024 * 1024
MAX_SIDE = 3000                    # px – plenty for A4 at ~250 dpi, keeps phone photos small
UPLOAD_ID = "upload"

_pdfium_lock = threading.Lock()


class UploadError(ValueError):
    pass


def _register_heif() -> None:
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:            # optional: without it HEIC is refused with a clear error
        pass


def safe_stem(name: str) -> str:
    stem = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    stem = stem.rsplit(".", 1)[0] if "." in stem else stem
    stem = re.sub(r"[^\w\-. äöüÄÖÜß()]+", "_", stem).strip(" ._") or "Upload"
    return stem[:80]


def image_to_pdf(data: bytes) -> bytes:
    """One image (also HEIC, multi-page TIFF) → PDF, upright and reasonably small."""
    from PIL import Image, ImageOps

    _register_heif()
    try:
        img = Image.open(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        raise UploadError("not an image (or HEIC support missing)") from exc
    pages = []
    try:
        while True:
            frame = ImageOps.exif_transpose(img.copy()).convert("RGB")
            frame.thumbnail((MAX_SIDE, MAX_SIDE))
            pages.append(frame)
            img.seek(img.tell() + 1)
    except EOFError:
        pass
    # the long side becomes A4 height (11.69 in), so a photo prints and edits like a letter
    dpi = max(72.0, max(pages[0].size) / 11.69)
    buf = io.BytesIO()
    pages[0].save(buf, "PDF", save_all=True, append_images=pages[1:], resolution=dpi, quality=85)
    return buf.getvalue()


def merge_pdfs(parts: list[bytes]) -> bytes:
    import pypdfium2 as pdfium

    with _pdfium_lock:
        out = pdfium.PdfDocument.new()
        try:
            for part in parts:
                src = pdfium.PdfDocument(part)
                try:
                    out.import_pages(src)
                finally:
                    src.close()
            buf = io.BytesIO()
            out.save(buf)
            return buf.getvalue()
        finally:
            out.close()


def prepare(files: list[tuple[str, bytes]], combine: bool) -> list[tuple[str, bytes]]:
    """Turn uploaded (name, bytes) into the files to put into the inbox."""
    if not files:
        raise UploadError("no files")
    prepared: list[tuple[str, str, bytes]] = []        # (stem, ext, data)
    for name, data in files:
        if len(data) > MAX_FILE_BYTES:
            raise UploadError(f"file too large: {name}")
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext in IMAGE_EXT:
            prepared.append((safe_stem(name), "pdf", image_to_pdf(data)))
        elif ext in KEEP_EXT:
            if ext == "pdf" and not data.startswith(b"%PDF-"):
                raise UploadError(f"not a PDF: {name}")
            prepared.append((safe_stem(name), ext, data))
        else:
            raise UploadError(f"unsupported file type: {name}")
    if combine and len(prepared) > 1:
        if any(ext != "pdf" for _, ext, _ in prepared):
            raise UploadError("only PDFs and photos can be combined")
        return [(prepared[0][0] + ".pdf", merge_pdfs([d for _, _, d in prepared]))]
    return [(f"{stem}.{ext}", data) for stem, ext, data in prepared]


def store(folder: Path, files: list[tuple[str, bytes]], settle: int) -> list[str]:
    """Write files atomically into the upload inbox; returns their names."""
    folder.mkdir(parents=True, exist_ok=True)
    names = []
    past = time.time() - settle - 1          # the inbox scan may take them at once (written atomically)
    for name, data in files:
        dest = folder / name
        n = 1
        while dest.exists():
            n += 1
            dest = folder / f"{Path(name).stem} ({n}){Path(name).suffix}"
        tmp = folder / f".{uuid.uuid4().hex}.part"
        tmp.write_bytes(data)
        os.utime(tmp, (past, past))
        os.replace(tmp, dest)
        names.append(dest.name)
    return names
