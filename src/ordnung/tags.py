"""Tags: labels across folders ("Steuer 2026", "Hochzeit", "Haus Musterweg").

Tags belong to a document's content, not to its place: they are kept per SHA-256
in ``tags.json`` in the data folder, so they survive renaming and moving and the
archive files stay untouched (the id in the file name is part of the hash).
Like the rules, this file is configuration – it cannot be rebuilt from the archive.

A "Mappe" (collection) is a tag shown like a folder: "Steuererklärung 2026" collects
receipts that stay in their own folders. It is listed under ``mappen`` with the area
it belongs to: only people who may read that area see it (and its label).
"""

from __future__ import annotations

import json
import os
import re
import threading
from collections import Counter
from pathlib import Path

MAX_LEN = 40
MAX_PER_DOC = 30
_BAD = re.compile(r"[,#\x00-\x1f]")


class TagError(ValueError):
    pass


def clean(tag: str) -> str:
    tag = _BAD.sub(" ", str(tag or ""))
    tag = re.sub(r"\s+", " ", tag).strip()
    if len(tag) > MAX_LEN:
        raise TagError("tag too long")
    return tag


class TagStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._cache: tuple[int, dict[str, list[str]], list[dict]] | None = None

    # ---------------------------------------------------------- persistence

    def _read(self) -> tuple[dict[str, list[str]], list[dict]]:
        try:
            mtime = self.path.stat().st_mtime_ns
        except FileNotFoundError:
            return {}, []
        if self._cache and self._cache[0] == mtime:
            return self._cache[1], self._cache[2]
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        docs = {sha: list(tags) for sha, tags in raw.get("docs", {}).items() if tags}
        # older files: plain names, which belonged to everyone → "gemeinsam"
        mappen = [m if isinstance(m, dict) else {"name": str(m), "area": "gemeinsam"}
                  for m in raw.get("mappen", [])]
        self._cache = (mtime, docs, mappen)
        return docs, mappen

    def _load(self) -> dict[str, list[str]]:
        return self._read()[0]

    def _save(self, docs: dict[str, list[str]], mappen: list[dict] | None = None) -> None:
        if mappen is None:
            mappen = self._read()[1]
        data = {"version": 1, "docs": {sha: tags for sha, tags in sorted(docs.items()) if tags},
                "mappen": sorted(mappen, key=lambda m: m["name"].casefold())}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)
        self._cache = None

    # ---------------------------------------------------------------- read

    def of(self, sha: str) -> list[str]:
        return list(self._load().get(sha, []))

    def mapping(self) -> dict[str, list[str]]:
        return self._load()

    def shas_with_all(self, tags: list[str]) -> set[str]:
        wanted = {t.casefold() for t in tags}
        return {sha for sha, have in self._load().items() if wanted <= {t.casefold() for t in have}}

    def counts(self, shas: set[str] | None = None) -> list[dict]:
        """All tags with their number of documents (only those in ``shas`` if given)."""
        counter: Counter = Counter()
        spelling: dict[str, str] = {}
        for sha, tags in self._load().items():
            if shas is not None and sha not in shas:
                continue
            for t in tags:
                spelling.setdefault(t.casefold(), t)
                counter[t.casefold()] += 1
        return sorted(({"name": spelling[k], "count": n} for k, n in counter.items()),
                      key=lambda x: x["name"].casefold())

    # --------------------------------------------------------------- write

    def _canonical(self, docs: dict[str, list[str]], tag: str) -> str:
        """Use the spelling a tag already has elsewhere ("steuer 2026" → "Steuer 2026")."""
        key = tag.casefold()
        for tags in docs.values():
            for t in tags:
                if t.casefold() == key:
                    return t
        return tag

    @staticmethod
    def _merge(current: list[str], add: list[str], remove: list[str]) -> list[str]:
        drop = {t.casefold() for t in remove}
        result = [t for t in current if t.casefold() not in drop]
        have = {t.casefold() for t in result}
        for t in add:
            if t.casefold() not in have:
                result.append(t)
                have.add(t.casefold())
        if len(result) > MAX_PER_DOC:
            raise TagError("too many tags")
        return sorted(result, key=str.casefold)

    def set(self, sha: str, tags: list[str]) -> list[str]:
        cleaned = [c for c in (clean(t) for t in tags) if c]
        with self._lock:
            docs = dict(self._load())
            cleaned = [self._canonical(docs, t) for t in cleaned]
            docs[sha] = self._merge([], cleaned, [])
            self._save(docs)
            return docs[sha]

    def change(self, shas: list[str], add: list[str], remove: list[str]) -> int:
        add = [c for c in (clean(t) for t in add) if c]
        remove = [c for c in (clean(t) for t in remove) if c]
        with self._lock:
            docs = dict(self._load())
            add = [self._canonical(docs, t) for t in add]
            changed = 0
            for sha in set(shas):
                before = docs.get(sha, [])
                after = self._merge(before, add, remove)
                if after != before:
                    docs[sha] = after
                    changed += 1
            if changed:
                self._save(docs)
            return changed

    # -------------------------------------------------------------- Mappen

    def mappen(self) -> list[dict]:
        """[{name, area}] – every Mappe belongs to an area, like a document."""
        return [dict(m) for m in self._read()[1]]

    def mappe(self, name: str) -> dict | None:
        key = name.casefold()
        return next((dict(m) for m in self._read()[1] if m["name"].casefold() == key), None)

    def is_mappe(self, name: str) -> bool:
        return self.mappe(name) is not None

    def add_mappe(self, name: str, area: str) -> str:
        name = clean(name)
        if not name:
            raise TagError("name missing")
        with self._lock:
            docs, mappen = self._read()
            name = self._canonical(docs, name)
            if name.casefold() in {m["name"].casefold() for m in mappen}:
                raise TagError("mappe exists")
            self._save(dict(docs), [*mappen, {"name": name, "area": area}])
        return name

    def set_mappe_area(self, name: str, area: str) -> None:
        with self._lock:
            docs, mappen = self._read()
            key = name.casefold()
            self._save(dict(docs), [{**m, "area": area} if m["name"].casefold() == key else m for m in mappen])

    def rename_tag(self, old: str, new: str) -> int:
        """Rename a tag (and Mappe) on every document."""
        new = clean(new)
        if not new:
            raise TagError("name missing")
        with self._lock:
            docs, mappen = self._read()
            key = old.casefold()
            if new.casefold() != key and new.casefold() in {m["name"].casefold() for m in mappen}:
                raise TagError("mappe exists")
            changed = 0
            out = {}
            for sha, tags in docs.items():
                if any(t.casefold() == key for t in tags):
                    tags = self._merge([t for t in tags if t.casefold() != key], [new], [])
                    changed += 1
                out[sha] = tags
            mappen = [{**m, "name": new} if m["name"].casefold() == key else m for m in mappen]
            self._save(out, mappen)
            return changed

    def remove_mappe(self, name: str, untag: bool = True) -> int:
        """Dissolve a Mappe; the documents stay where they are, only the label goes."""
        with self._lock:
            docs, mappen = self._read()
            key = name.casefold()
            changed = 0
            out = {}
            for sha, tags in docs.items():
                if untag and any(t.casefold() == key for t in tags):
                    tags = [t for t in tags if t.casefold() != key]
                    changed += 1
                out[sha] = tags
            self._save(out, [m for m in mappen if m["name"].casefold() != key])
            return changed

    def hidden_for(self, can_read) -> set[str]:
        """Casefolded names of Mappen the user may not see – their label is hidden, too."""
        return {m["name"].casefold() for m in self._read()[1] if not can_read(m["area"])}
