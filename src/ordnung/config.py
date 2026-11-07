"""Configuration from environment variables."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path


def _flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    archive: Path
    data: Path
    readonly: bool
    admin_user: str
    admin_password: str
    api_token: str
    rescan_minutes: int
    secret: str
    ocr: bool = True
    ocr_lang: str = "deu+eng"
    ocr_max_pages: int = 30
    text_workers: int = 1
    starter: bool = True      # a fresh installation starts with the shipped rules and folders

    @property
    def db_path(self) -> Path:
        return self.data / "ordnung.db"

    @property
    def users_path(self) -> Path:
        return self.data / "users.json"


def _load_secret(data: Path) -> str:
    """Session signing key: from env, else persisted in the data dir."""
    env = os.environ.get("ORDNUNG_SECRET")
    if env:
        return env
    path = data / "secret.key"
    if path.exists():
        return path.read_text().strip()
    data.mkdir(parents=True, exist_ok=True)
    key = secrets.token_urlsafe(48)
    path.write_text(key)
    path.chmod(0o600)
    return key


def load_settings() -> Settings:
    data = Path(os.environ.get("ORDNUNG_DATA", "./data")).resolve()
    data.mkdir(parents=True, exist_ok=True)
    return Settings(
        archive=Path(os.environ.get("ORDNUNG_ARCHIVE", "./archiv")).resolve(),
        data=data,
        readonly=_flag("ORDNUNG_READONLY", True),
        admin_user=os.environ.get("ORDNUNG_ADMIN_USER", "admin"),
        admin_password=os.environ.get("ORDNUNG_ADMIN_PASSWORD", ""),
        api_token=os.environ.get("ORDNUNG_API_TOKEN", ""),
        rescan_minutes=int(os.environ.get("ORDNUNG_RESCAN_MINUTES", "10")),
        secret=_load_secret(data),
        ocr=_flag("ORDNUNG_OCR", True),
        ocr_lang=os.environ.get("ORDNUNG_OCR_LANG", "deu+eng"),
        ocr_max_pages=int(os.environ.get("ORDNUNG_OCR_MAX_PAGES", "30")),
        starter=_flag("ORDNUNG_STARTER", True),
        text_workers=int(os.environ.get("ORDNUNG_TEXT_WORKERS", str(max(1, min(4, (os.cpu_count() or 2) // 3))))),
    )
