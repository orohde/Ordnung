"""Moving documents between folders and the trash.

Nothing is deleted for good: "delete" moves the file to
``.papierkorb/<date>/<original path>`` inside the archive. The index skips
dot folders, so it disappears from the app but stays reachable via SMB and can
be restored with its original path.
"""

from __future__ import annotations

import os
import threading
from datetime import date
from pathlib import Path

from .folders import FolderError, clean_path
from .inbox import _makedirs
from .storage import path_status

TRASH = ".papierkorb"


class DocOpError(ValueError):
    pass


_lock = threading.Lock()


def _writable(archive: Path) -> None:
    if not path_status(str(archive))["writable"]:
        raise DocOpError("archive is read-only")


def _source(archive: Path, doc: dict) -> Path:
    src = (archive / doc["path"]).resolve()
    if archive.resolve() not in src.parents or not src.is_file():
        raise DocOpError("file not found")
    return src


def move(archive: Path, doc: dict, folder: str, area: str | None = None) -> str:
    """Move ``doc`` into ``folder`` of ``area`` (default: its own); returns the new relative path."""
    _writable(archive)
    folder = (folder or "").strip().strip("/")
    if folder:
        try:
            folder = clean_path(folder)
        except FolderError as exc:
            raise DocOpError(str(exc)) from exc
    area = area or doc["area"]
    if area.startswith((".", "_")) or "/" in area or not (archive / area).is_dir():
        raise DocOpError("unknown area")
    if area == doc["area"] and folder == (doc.get("folder") or ""):
        raise DocOpError("already in this folder")
    src = _source(archive, doc)
    target_dir = archive / area / folder if folder else archive / area
    dest = target_dir / src.name
    with _lock:
        if dest.exists():
            raise DocOpError("target exists")
        _makedirs(target_dir, archive)
        os.replace(src, dest)
    return dest.relative_to(archive).as_posix()


def trash(archive: Path, doc: dict) -> str:
    """Move ``doc`` to the trash; returns the trash path (relative to the archive)."""
    _writable(archive)
    src = _source(archive, doc)
    dest = archive / TRASH / date.today().isoformat() / doc["path"]
    with _lock:
        n = 1
        while dest.exists():
            n += 1
            dest = dest.with_name(f"{Path(doc['path']).stem} ({n}){src.suffix}")
        _makedirs(dest.parent, archive)
        os.replace(src, dest)
    return dest.relative_to(archive).as_posix()


def restore(archive: Path, trash_path: str, allowed) -> str:
    """Put a file from the trash back to its original place; ``allowed(area)`` checks rights."""
    _writable(archive)
    parts = Path(trash_path).parts
    if len(parts) < 4 or parts[0] != TRASH or ".." in parts:
        raise DocOpError("not in the trash")
    src = (archive / trash_path).resolve()
    if (archive / TRASH).resolve() not in src.parents or not src.is_file():
        raise DocOpError("not in the trash")
    rel = Path(*parts[2:])
    if not allowed(rel.parts[0]):
        raise DocOpError("no write access")
    dest = archive / rel
    with _lock:
        if dest.exists():
            raise DocOpError("target exists")
        _makedirs(dest.parent, archive)
        os.replace(src, dest)
    return rel.as_posix()


def rename(archive: Path, doc: dict, title: str, doc_date: str) -> str:
    """Change title and date, i.e. the file name ``{date}_{title}_{id}``; the id stays."""
    import re

    from .inbox import _valid, clean_title
    from .index import _NAME_RE, nfc

    _writable(archive)
    title = clean_title(title)
    if not title:
        raise DocOpError("title missing")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", doc_date or "") or not _valid(*map(int, doc_date.split("-"))):
        raise DocOpError("invalid date")
    src = _source(archive, doc)
    match = _NAME_RE.match(nfc(src.stem))
    sid = (match and match["sid"]) or doc["id"]
    dest = src.with_name(f"{doc_date}_{title}_{sid}{src.suffix}")
    if dest == src:
        raise DocOpError("nothing changed")
    with _lock:
        if dest.exists() and dest.name.casefold() != src.name.casefold():
            raise DocOpError("target exists")
        os.replace(src, dest)
    return dest.relative_to(archive).as_posix()


def trash_list(archive: Path, can_read) -> list[dict]:
    """Everything in the trash the user may see, newest first."""
    from .index import parse_name

    root = archive / TRASH
    items = []
    if not root.is_dir():
        return items
    for day in sorted((d for d in root.iterdir() if d.is_dir()), reverse=True):
        for dirpath, _dirs, files in os.walk(day):
            for name in files:
                full = Path(dirpath) / name
                rel = full.relative_to(day)
                if len(rel.parts) < 2 or not can_read(rel.parts[0]):
                    continue
                stem, _, ext = name.rpartition(".")
                parsed = parse_name(stem or name)
                items.append({
                    "trash_path": full.relative_to(archive).as_posix(),
                    "path": rel.as_posix(),
                    "area": rel.parts[0],
                    "folder": "/".join(rel.parts[1:-1]),
                    "title": parsed.title,
                    "date": parsed.doc_date,
                    "ext": ext.lower(),
                    "deleted": day.name,
                    "size": full.stat().st_size,
                })
    return items


def trash_file(archive: Path, trash_path: str, can_read) -> Path:
    parts = Path(trash_path).parts
    if len(parts) < 4 or parts[0] != TRASH or ".." in parts or not can_read(parts[2]):
        raise DocOpError("not in the trash")
    full = (archive / trash_path).resolve()
    if (archive / TRASH).resolve() not in full.parents or not full.is_file():
        raise DocOpError("not in the trash")
    return full


def purge_trash(archive: Path, days: int, today: date | None = None) -> int:
    """Delete trash day folders older than ``days`` for good; returns the number of files removed."""
    import shutil

    if days <= 0:
        return 0
    root = archive / TRASH
    if not root.is_dir():
        return 0
    today = today or date.today()
    removed = 0
    for day in root.iterdir():
        try:
            when = date.fromisoformat(day.name)
        except ValueError:
            continue
        if day.is_dir() and (today - when).days >= days:
            removed += sum(len(files) for _, _, files in os.walk(day))
            shutil.rmtree(day)
    return removed
