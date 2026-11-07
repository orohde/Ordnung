"""Ordnung! – folder-based document archive."""

from importlib.metadata import PackageNotFoundError, version as _version
from pathlib import Path


def _read_version() -> str:
    here = Path(__file__).resolve()
    for candidate in (here.parent / "VERSION", here.parents[2] / "VERSION"):
        if candidate.is_file():
            return candidate.read_text().strip()
    try:
        return _version("ordnung")
    except PackageNotFoundError:
        return "0.0.0"


__version__ = _read_version()
