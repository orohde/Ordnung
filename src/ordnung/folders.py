"""The shared folder template.

All areas share one folder structure. A folder can be part of the template
before any document lives in it; on disk it only appears with its first
document (no empty folder clutter in the areas).

The template is stored in ``folders.json`` in the data folder. Folders that
exist on disk are always part of the effective structure, whether or not
they were added to the template explicitly.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from .index import Index, fold

INVALID = set('<>:"\\|?*')

# A sensible start for a household that begins from scratch
STARTER_HOUSEHOLD = [
    "Arbeit/Gehaltsabrechnungen", "Arbeit/Verträge", "Arbeit/Zeugnisse",
    "Auto/Kaufvertrag", "Auto/Versicherung", "Auto/Werkstatt", "Auto/Steuer",
    "Banken/Girokonto", "Banken/Kredite", "Banken/Depot", "Banken/Kreditkarte",
    "Behörden/Ausweise", "Behörden/Meldewesen", "Behörden/Rundfunkbeitrag",
    "Finanzamt/Steuererklärung", "Finanzamt/Bescheide", "Finanzamt/Belege",
    "Gesundheit/Arztbriefe", "Gesundheit/Befunde", "Gesundheit/Rechnungen", "Gesundheit/Rezepte",
    "Gesundheit/Krankenversicherung",
    "Rechnungen/Elektronik", "Rechnungen/Haushalt", "Rechnungen/Möbel",
    "Versicherungen/Haftpflicht", "Versicherungen/Hausrat", "Versicherungen/Rechtsschutz",
    "Versicherungen/Wohngebäude", "Versicherungen/Leben und Rente",
    "Verträge/Internet und Telefon", "Verträge/Mobilfunk", "Verträge/Strom und Gas", "Verträge/Abos",
    "Wohnen/Miete oder Eigentum", "Wohnen/Nebenkosten", "Wohnen/Handwerker",
    "Bedienungsanleitungen", "Sonstiges",
]


class FolderError(ValueError):
    pass


def clean_path(path: str) -> str:
    parts = [p.strip() for p in (path or "").replace("\\", "/").split("/") if p.strip()]
    if not parts:
        raise FolderError("empty folder name")
    for part in parts:
        if part in (".", "..") or part.startswith(".") or INVALID & set(part) or len(part) > 80:
            raise FolderError(f"invalid folder name: {part}")
    return "/".join(parts)


def with_parents(paths) -> set[str]:
    result = set()
    for path in paths:
        parts = path.split("/")
        for i in range(1, len(parts) + 1):
            result.add("/".join(parts[:i]))
    return result


class FolderTemplate:
    def __init__(self, path: Path, index: Index):
        self.path = path
        self.index = index
        self._lock = threading.Lock()

    # ---------------------------------------------------------- persistence

    def load(self) -> set[str]:
        if not self.path.exists():
            return set()
        return set(json.loads(self.path.read_text(encoding="utf-8")).get("folders", []))

    def _save(self, folders: set[str]) -> None:
        # only leaves are stored; parents follow from them
        leaves = sorted(f for f in folders if not any(o.startswith(f + "/") for o in folders))
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, "folders": leaves}, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(tmp, self.path)

    # ---------------------------------------------------------------- views

    def on_disk(self) -> dict[str, int]:
        """Folders that hold documents (over all areas) with their own document count."""
        with self.index.connect() as con:
            rows = con.execute("SELECT folder, COUNT(*) FROM files WHERE folder != '' GROUP BY folder")
            return {r[0]: r[1] for r in rows}

    def effective(self) -> set[str]:
        return with_parents(self.load()) | with_parents(self.on_disk())

    def template_only(self) -> set[str]:
        """Template folders that have no documents anywhere below them."""
        used = with_parents(self.on_disk())
        return with_parents(self.load()) - used

    # -------------------------------------------------------------- changes

    def add(self, path: str) -> str:
        path = clean_path(path)
        existing = {fold(f): f for f in self.effective()}
        if fold(path) in existing:
            raise FolderError("folder exists")
        with self._lock:
            folders = self.load()
            folders.add(path)
            self._save(folders)
        return path

    def add_many(self, paths: list[str]) -> int:
        existing = {fold(f) for f in self.effective()}
        added = 0
        with self._lock:
            folders = self.load()
            for raw in paths:
                path = clean_path(raw)
                if fold(path) not in existing:
                    folders.add(path)
                    existing.add(fold(path))
                    added += 1
            self._save(folders)
        return added

    def include(self, paths) -> int:
        """Add folders to the template without looking at the archive (used when switching archives)."""
        added = 0
        with self._lock:
            folders = with_parents(self.load())
            for raw in paths:
                try:
                    path = clean_path(raw)
                except FolderError:
                    continue
                if path not in folders:
                    folders.add(path)
                    added += 1
            self._save(folders)
        return added

    def delete(self, path: str) -> None:
        path = clean_path(path)
        if path in with_parents(self.on_disk()):
            raise FolderError("folder contains documents")
        with self._lock:
            folders = {f for f in with_parents(self.load()) if f != path and not f.startswith(path + "/")}
            self._save(folders)

    def rename(self, old: str, new: str, archive: Path, areas: list[str]) -> dict:
        """Rename or move a folder; with documents only when the archive is writable."""
        old, new = clean_path(old), clean_path(new)
        if old == new:
            return {"moved_areas": 0}
        if new.startswith(old + "/"):
            raise FolderError("cannot move a folder into itself")
        effective = self.effective()
        if old not in effective:
            raise FolderError("unknown folder")
        if fold(new) in {fold(f) for f in effective} and fold(new) != fold(old):
            raise FolderError("folder exists")
        moved = 0
        if old in with_parents(self.on_disk()):
            if not os.access(archive, os.W_OK):
                raise FolderError("archive is read-only")
            for area in areas:
                src, dst = archive / area / old, archive / area / new
                if src.is_dir():
                    if dst.exists():
                        raise FolderError(f"target exists in area {area}")
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(src, dst)
                    moved += 1
        with self._lock:
            folders = set()
            for f in with_parents(self.load()) | {old}:
                if f == old or f.startswith(old + "/"):
                    folders.add(new + f[len(old):])
                else:
                    folders.add(f)
            self._save(folders)
        return {"moved_areas": moved}
