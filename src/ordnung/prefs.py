"""Per-person view settings that follow the account, not the browser.

Kept in ``prefs.json`` in the data folder, one entry per user name. So far only
which folders are expanded in the sidebar tree, the language and the own stamp
templates of the PDF editor.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

LANGUAGES = ("de", "en", "fr", "it")
MAX_PATHS = 5000
MAX_PATH_LEN = 1000
MAX_STAMPS = 30
STAMP_COLORS = ("red", "blue", "green", "black")
STAMP_SIZE = (12, 60)


def clean_stamp(raw: dict) -> dict:
    """A stamp template: big text, whether a date goes below it, an extra line, a colour; optionally size and spot."""
    if not isinstance(raw, dict):
        raise ValueError("invalid stamp")
    text = " ".join(str(raw.get("text") or "").split())
    extra = " ".join(str(raw.get("extra") or "").split())
    color = str(raw.get("color") or "red")
    if not text or len(text) > 40 or len(extra) > 60:
        raise ValueError("invalid stamp text")
    if color not in STAMP_COLORS:
        raise ValueError("invalid stamp colour")
    out = {"text": text, "date": bool(raw.get("date", True)), "extra": extra, "color": color}
    # optional: size in pt and the spot on the page as a share of width/height (centre of the stamp)
    if raw.get("size") is not None:
        size = raw["size"]
        if isinstance(size, bool) or not isinstance(size, (int, float)) or not STAMP_SIZE[0] <= size <= STAMP_SIZE[1]:
            raise ValueError("invalid stamp size")
        out["size"] = int(round(size))
    if raw.get("fx") is not None or raw.get("fy") is not None:
        pos = [raw.get("fx"), raw.get("fy")]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1 for v in pos):
            raise ValueError("invalid stamp position")
        out["fx"], out["fy"] = (round(float(v), 4) for v in pos)
    return out


class PrefsStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def _load(self) -> dict[str, dict]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        return {name: dict(p) for name, p in raw.get("users", {}).items()}

    def _save(self, users: dict[str, dict]) -> None:
        data = {"version": 1, "users": dict(sorted(users.items()))}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def get(self, user: str) -> dict:
        with self._lock:
            p = self._load().get(user, {})
        return {"tree_open": list(p.get("tree_open", [])), "language": p.get("language", ""),
                "stamps": list(p.get("stamps", []))}

    def set_stamps(self, user: str, stamps: list[dict]) -> list[dict]:
        clean, seen = [], set()
        for raw in stamps[:MAX_STAMPS]:
            st = clean_stamp(raw)
            key = (st["text"].casefold(), st["date"], st["extra"].casefold(), st["color"])
            if key not in seen:
                seen.add(key)
                clean.append(st)
        with self._lock:
            users = self._load()
            users.setdefault(user, {})["stamps"] = clean
            self._save(users)
        return clean

    def set_language(self, user: str, language: str) -> str:
        if language not in LANGUAGES:
            raise ValueError("unknown language")
        with self._lock:
            users = self._load()
            users.setdefault(user, {})["language"] = language
            self._save(users)
        return language

    def set_tree_open(self, user: str, paths: list[str]) -> list[str]:
        clean = sorted({str(p) for p in paths if p and len(str(p)) <= MAX_PATH_LEN})[:MAX_PATHS]
        with self._lock:
            users = self._load()
            users.setdefault(user, {})["tree_open"] = clean
            self._save(users)
        return clean

    def forget(self, user: str) -> None:
        with self._lock:
            users = self._load()
            if users.pop(user, None) is not None:
                self._save(users)
