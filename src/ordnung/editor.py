"""Saving PDFs edited in the browser and the stored signature per person.

The browser (PDF.js to show, pdf-lib to write) sends the finished PDF. It is
put next to the original as a new file; the original stays untouched. The
signature is a transparent PNG in ``signatures/<user>.png`` in the data folder.
"""

from __future__ import annotations

import io
import os
import re
import threading
import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from .inbox import _makedirs, clean_title
from .index import sha256_file
from .storage import path_status

MAX_PDF_BYTES = 80 * 1024 * 1024
MAX_SIGNATURE_BYTES = 2 * 1024 * 1024
MAX_SIGNATURE_SIDE = 1600


class EditorError(ValueError):
    pass


_save_lock = threading.Lock()


def save_beside(index, inbox, doc: dict, data: bytes, title: str, doc_date: str | None,
                text: str = "") -> dict:
    """Write ``data`` as a new PDF in the folder of ``doc``; return path and sha256."""
    if len(data) > MAX_PDF_BYTES:
        raise EditorError("file too large")
    if not data.startswith(b"%PDF-"):
        raise EditorError("not a PDF")
    archive: Path = index.archive
    if not path_status(str(archive))["writable"]:
        raise EditorError("archive is read-only")
    title = clean_title(title)
    if not title:
        raise EditorError("title missing")
    doc_date = doc_date or doc.get("date") or date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", doc_date):
        raise EditorError("invalid date")
    target_dir = (archive / doc["path"]).parent
    if archive.resolve() not in target_dir.resolve().parents and target_dir.resolve() != archive.resolve():
        raise EditorError("outside the archive")

    tmp_dir = archive / ".ordnung-tmp"
    tmp_dir.mkdir(exist_ok=True)
    tmp = tmp_dir / (uuid.uuid4().hex + ".pdf")
    try:
        tmp.write_bytes(data)
        os.chmod(tmp, 0o664)
        sha = sha256_file(tmp)
        if sha == doc["sha256"]:
            raise EditorError("nothing changed")
        with _save_lock:
            dup = inbox._archived(sha)
            if dup:
                raise EditorError(f"already in the archive: {dup}")
            dest = target_dir / f"{doc_date}_{title}_{inbox._short_id(sha)}.pdf"
            if dest.exists():
                raise EditorError("target exists")
            _makedirs(target_dir, archive)
            os.replace(tmp, dest)
            rel = dest.relative_to(archive).as_posix()
            inbox._recent[sha] = rel
    finally:
        tmp.unlink(missing_ok=True)

    # text of the original plus what was typed in: no OCR run for a scan that got a signature
    old = index.document_text(doc["sha256"]) or ""
    added = (text or "").strip()[:20_000]
    body = (old + ("\n\n" + added if added else "")).strip()
    if body:
        index.store_text(sha, SimpleNamespace(text=body, pages=0, ocr_pages=0, method="editor", error=""))
    return {"path": rel, "sha256": sha, "name": dest.name}


class SignatureStore:
    def __init__(self, folder: Path):
        self.folder = folder

    def _path(self, user: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", user) or user.startswith("."):
            raise EditorError("invalid user")
        return self.folder / f"{user}.png"

    def get(self, user: str) -> Path | None:
        p = self._path(user)
        return p if p.is_file() else None

    def put(self, user: str, data: bytes) -> None:
        from PIL import Image

        if len(data) > MAX_SIGNATURE_BYTES:
            raise EditorError("image too large")
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except Exception as exc:  # noqa: BLE001
            raise EditorError("not an image") from exc
        img = img.convert("RGBA")
        bbox = img.getchannel("A").getbbox()
        if not bbox:
            raise EditorError("empty signature")
        img = img.crop(bbox)
        img.thumbnail((MAX_SIGNATURE_SIDE, MAX_SIGNATURE_SIDE))
        self.folder.mkdir(parents=True, exist_ok=True)
        p = self._path(user)
        tmp = p.with_suffix(".tmp")
        img.save(tmp, "PNG", optimize=True)
        os.replace(tmp, p)

    def delete(self, user: str) -> None:
        self._path(user).unlink(missing_ok=True)

