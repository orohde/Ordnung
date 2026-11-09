"""Background work settings: text recognition, rescan interval, worker count.

They used to come only from the environment; now they live in ``system.json`` and can be changed
under Settings → System. The environment still gives the defaults for a fresh installation.
"""

from __future__ import annotations

import functools
import json
import os
import re
import shutil
import subprocess
import threading
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

LANG_RE = re.compile(r"^[A-Za-z_]+(\+[A-Za-z_]+)*$")
LIMITS = {
    "ocr_max_pages": (1, 1000),
    "rescan_minutes": (1, 1440),
    "text_workers": (1, 16),
}


@dataclass
class SystemConfig:
    ocr: bool = True                 # text recognition for scans
    ocr_lang: str = "deu+eng"        # Tesseract languages
    ocr_max_pages: int = 30          # recognise at most this many pages per document
    rescan_minutes: int = 10         # full re-read of the archive folders
    text_workers: int = 1            # documents read at the same time


class SystemStore:
    def __init__(self, path: Path, defaults: SystemConfig):
        self.path = path
        self.defaults = defaults
        self._lock = threading.Lock()

    def _raw(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
        return raw if isinstance(raw, dict) else {}

    def load(self) -> SystemConfig:
        known = {f.name for f in fields(SystemConfig)}
        return replace(self.defaults, **{k: v for k, v in self._raw().items() if k in known})

    def public(self) -> dict:
        return {**asdict(self.load()), "defaults": asdict(self.defaults),
                "languages": tesseract_languages(), "cpus": os.cpu_count() or 1}

    def update(self, changes: dict) -> SystemConfig:
        with self._lock:
            config = self.load()
            for key, value in changes.items():
                if value is None or key not in SystemConfig.__dataclass_fields__:
                    continue
                if key == "ocr_lang":
                    value = value.strip()
                    if not LANG_RE.match(value):
                        raise ValueError("languages like deu+eng")
                elif key in LIMITS:
                    low, high = LIMITS[key]
                    if not low <= int(value) <= high:
                        raise ValueError(f"{key} must be between {low} and {high}")
                    value = int(value)
                setattr(config, key, value)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
            tmp.replace(self.path)
            return config


@functools.lru_cache(maxsize=1)
def tesseract_languages() -> list[str]:
    """Installed Tesseract language packs (empty without Tesseract)."""
    exe = shutil.which("tesseract")
    if not exe:
        return []
    try:
        out = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return sorted(x.strip() for x in out.splitlines()[1:] if x.strip() and x.strip() != "osd")
