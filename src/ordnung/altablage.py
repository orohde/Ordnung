"""Altablage: old documents that are kept but no longer shown.

A document goes to ``<area>/Altablage/<its folder>/`` – still a normal file,
indexed and readable, so preview, text and download keep working and a
restore knows where it came from (just drop the prefix). The tree shows the
Altablage apart from the other folders, the search includes it only on
request, and the inbox never suggests it as a target.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

ALT = "Altablage"


def is_alt(folder: str | None) -> bool:
    folder = (folder or "").strip("/")
    return folder == ALT or folder.startswith(ALT + "/")


def to_alt(folder: str | None) -> str:
    folder = (folder or "").strip("/")
    return f"{ALT}/{folder}" if folder else ALT


def from_alt(folder: str | None) -> str:
    folder = (folder or "").strip("/")
    if folder == ALT:
        return ""
    if folder.startswith(ALT + "/"):
        return folder[len(ALT) + 1:]
    return folder


def cutoff(years: int, today: date | None = None) -> str:
    """ISO date ``years`` years before today (29 February falls back to the 28th)."""
    today = today or date.today()
    try:
        return today.replace(year=today.year - years).isoformat()
    except ValueError:
        return today.replace(year=today.year - years, day=28).isoformat()


def prune_empty(archive: Path, dirs: set[Path]) -> int:
    """Remove the given directories (and their parents up to the area) once they are empty.

    Only folders a move just emptied are touched; ``os.rmdir`` refuses anything
    that still holds a file, so nothing else can be lost. A lone ``.DS_Store``
    from the Mac does not keep a folder alive.
    """
    archive = archive.resolve()
    removed = 0
    for start in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
        path = start.resolve()
        while archive in path.parents and len(path.relative_to(archive).parts) > 1:
            try:
                entries = os.listdir(path)
            except OSError:
                break
            if entries == [".DS_Store"]:
                try:
                    os.remove(path / ".DS_Store")
                except OSError:
                    break
            elif entries:
                break
            try:
                os.rmdir(path)
            except OSError:
                break
            removed += 1
            path = path.parent
    return removed
