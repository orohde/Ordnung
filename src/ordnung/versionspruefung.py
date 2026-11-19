"""Update check: once a day ask version.worldgate.de whether a newer version exists.

The same module ships unchanged in CutStock, Ordnung!, Augenblick! and Wissen! – keep the copies equal.

What is sent: the app name, the installed version and the kind of installation (docker, mac,
windows). No identifier, no cookie. The service only keeps daily totals, which is how we learn
how many installations are running. Admins switch it off under Settings, or for good with the
environment variable ``VERSIONSPRUEFUNG=0``.

The check runs on the server (not in the browser), at most once per calendar day and at a random
time of day picked once per installation, so restarts do not count twice and not every
installation knocks at midnight. Errors stay quiet: no answer simply means no notice that day.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import sys
import threading
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

log = logging.getLogger(__name__)

SERVICE = "https://version.worldgate.de"
TIMEOUT = 15
VERSION_RE = re.compile(r"^\d{4}\.\d{1,2}\.\d{1,4}$")


def install_kind() -> str:
    """docker, mac or windows – what the service may count."""
    if Path("/.dockerenv").exists() or os.environ.get("container"):
        return "docker"
    if sys.platform == "darwin":
        return "mac"
    if sys.platform.startswith("win"):
        return "windows"
    return "?"


def _key(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in version.strip().lstrip("v").split("."))
    except ValueError:
        return ()


def is_newer(latest: str, installed: str) -> bool:
    a, b = _key(latest), _key(installed)
    return bool(a and b and a > b)


def disabled_by_env() -> bool:
    return os.environ.get("VERSIONSPRUEFUNG", "").strip().lower() in {"0", "false", "no", "off", "aus"}


def safe_url(url: str) -> str:
    """The link of the release goes into the page: only an https address, never javascript: and the like."""
    url = (url or "").strip()
    return url if url.lower().startswith("https://") and not any(c in url for c in ' "<>\'\\') else ""


class UpdateCheck:
    """State in ``<data>/versionspruefung.json``: switch, chosen minute of the day, last answer."""

    def __init__(self, app: str, version: str, data: Path, kind: str | None = None, service: str = SERVICE):
        self.app, self.version, self.kind = app, version, kind or install_kind()
        self.path = data / "versionspruefung.json"
        self.service = service.rstrip("/")
        self._lock = threading.Lock()

    # ── state ──────────────────────────────────────────────────────────────
    def _load(self) -> dict:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
        if not isinstance(raw, dict):
            raw = {}
        if not isinstance(raw.get("minute"), int):
            raw["minute"] = random.randrange(24 * 60)
            self._save(raw)
        return raw

    def _save(self, state: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def enabled(self) -> bool:
        return not disabled_by_env() and self._load().get("on", True)

    def set_enabled(self, on: bool) -> dict:
        with self._lock:
            state = self._load()
            state["on"] = bool(on)
            self._save(state)
        return self.public()

    def public(self) -> dict:
        state = self._load()
        latest = state.get("latest") or {}
        return {
            "on": self.enabled(),
            "locked": disabled_by_env(),          # switched off by the environment, not changeable in the UI
            "installed": self.version,
            "kind": self.kind,
            "latest": latest.get("version", ""),
            "newer": is_newer(latest.get("version", ""), self.version),
            "url": safe_url(latest.get("url", "")),
            "notes": latest.get("notizen", ""),
            "released": latest.get("datum", ""),
            "checked": state.get("checked", ""),
            "error": state.get("error", ""),
            "service": self.service,
        }

    # ── checking ───────────────────────────────────────────────────────────
    def check(self) -> dict:
        """Ask the service now (also used by the "check now" button)."""
        query = urllib.parse.urlencode({"v": self.version if VERSION_RE.match(self.version) else "?", "art": self.kind})
        req = urllib.request.Request(f"{self.service}/v1/{self.app}?{query}",
                                     headers={"User-Agent": f"{self.app}/{self.version}", "Accept": "application/json"})
        with self._lock:
            state = self._load()
            state["checked"] = date.today().isoformat()
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    answer = json.loads(r.read().decode("utf-8"))
                if not isinstance(answer, dict) or not answer.get("version"):
                    raise ValueError("no version in the answer")
                state["latest"] = {k: str(answer.get(k, "")) for k in ("version", "url", "notizen", "datum")}
                state["error"] = ""
            except Exception as exc:  # noqa: BLE001 – offline etc.: quiet, try again tomorrow
                state["error"] = str(exc)[:200]
                log.info("update check failed: %s", state["error"])
            self._save(state)
        return self.public()

    def due(self, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        if not self.enabled():
            return False
        state = self._load()
        return state.get("checked") != now.date().isoformat() and now.hour * 60 + now.minute >= state["minute"]

    def run(self, stop: threading.Event, interval: float = 600) -> None:
        """Background loop: look every few minutes whether today's check is due."""
        while not stop.is_set():
            try:
                if self.due():
                    self.check()
            except Exception:  # noqa: BLE001
                log.exception("update check")
            stop.wait(interval)
