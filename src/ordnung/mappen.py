"""Download a Mappe: all its documents as a ZIP, or merged into one PDF."""

from __future__ import annotations

import io
import threading
import zipfile
from pathlib import Path

MAX_BUNDLE_BYTES = 300 * 1024 * 1024
_pdfium_lock = threading.Lock()   # pdfium is not thread-safe


def _files(root: Path, docs: list[dict]):
    total = 0
    base = root.resolve()
    for d in docs:
        path = (root / d["path"]).resolve()
        if base not in path.parents or not path.is_file():
            continue
        total += path.stat().st_size
        if total > MAX_BUNDLE_BYTES:
            raise ValueError("mappe too large to download at once")
        yield d, path


def bundle_zip(root: Path, docs: list[dict]) -> bytes:
    buf = io.BytesIO()
    used: set[str] = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _d, path in _files(root, docs):
            name = path.name
            n = 1
            while name.casefold() in used:
                n += 1
                name = f"{path.stem} ({n}){path.suffix}"
            used.add(name.casefold())
            zf.write(path, name)
    return buf.getvalue()


def bundle_pdf(root: Path, docs: list[dict]) -> bytes:
    """PDFs and images in date order, one after the other; other file types are skipped."""
    import pypdfium2 as pdfium
    from PIL import Image

    with _pdfium_lock:
        out = pdfium.PdfDocument.new()
        try:
            for d, path in _files(root, docs):
                ext = d["ext"]
                if ext == "pdf":
                    src = pdfium.PdfDocument(str(path))
                elif ext in {"png", "jpg", "jpeg", "tif", "tiff"}:
                    with Image.open(path) as img:
                        pdfbuf = io.BytesIO()
                        frames = []
                        try:
                            while True:
                                frames.append(img.convert("RGB"))
                                img.seek(img.tell() + 1)
                        except EOFError:
                            pass
                        frames[0].save(pdfbuf, "PDF", save_all=True, append_images=frames[1:], resolution=150)
                    src = pdfium.PdfDocument(pdfbuf.getvalue())
                else:
                    continue
                try:
                    out.import_pages(src)
                finally:
                    src.close()
            if len(out) == 0:
                raise ValueError("no PDF or image in this mappe")
            buf = io.BytesIO()
            out.save(buf)
            return buf.getvalue()
        finally:
            out.close()
