"""Sign-in security: server-side sessions, lockout, second factor, notifications.

Everything here is configuration or short-lived state, kept as readable JSON in
the data folder like the accounts themselves.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import struct
import threading
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import quote

log = logging.getLogger("ordnung.security")

DAY = 86400
SESSION_DAYS_INTERNAL = 30
SESSION_DAYS_EXTERNAL = 7
TOUCH_SECONDS = 300            # write "last seen" at most every five minutes per session

DEFAULT_INTERNAL = (
    "127.0.0.0/8", "::1/128", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    "100.64.0.0/10",            # carrier-grade NAT range, used by Tailscale
    "fc00::/7", "fe80::/10",
)


def _write_json(path: Path, data) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


# ------------------------------------------------------------------ network


class Networks:
    """Which client addresses count as "at home" (LAN, VPN)."""

    def __init__(self, spec: str | None = None):
        parts = [p.strip() for p in (spec or "").split(",") if p.strip()] or list(DEFAULT_INTERNAL)
        self.nets = [ipaddress.ip_network(p, strict=False) for p in parts]

    def is_internal(self, host: str | None) -> bool:
        try:
            ip = ipaddress.ip_address((host or "").strip("[]"))
        except ValueError:
            return False            # unknown = outside, the stricter side
        if ip.version == 6 and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        return any(ip in net for net in self.nets)


# ----------------------------------------------------------------- sessions


@dataclass
class Session:
    id: str                    # public id, safe to show and to address in the API
    user: str
    created: float
    expires: float
    last_seen: float
    ip: str = ""
    agent: str = ""
    external: bool = False     # created from outside
    mfa: bool = False          # second factor was checked at sign-in


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class SessionStore:
    """Sessions live on the server, so signing out and revoking really end them."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._cache: dict[str, Session] | None = None

    def _load(self) -> dict[str, Session]:
        if self._cache is None:
            raw = {}
            if self.path.exists():
                try:
                    raw = json.loads(self.path.read_text(encoding="utf-8")).get("sessions", {})
                except (ValueError, OSError):
                    log.warning("sessions.json unreadable, starting empty")
            self._cache = {k: Session(**v) for k, v in raw.items()}
        return self._cache

    def _save(self) -> None:
        now = time.time()
        sessions = {k: s for k, s in self._load().items() if s.expires > now}
        self._cache = sessions
        _write_json(self.path, {"version": 1, "sessions": {k: asdict(s) for k, s in sessions.items()}})

    def create(self, user: str, *, ip: str, agent: str, external: bool, mfa: bool) -> str:
        token = secrets.token_urlsafe(32)
        now = time.time()
        days = SESSION_DAYS_EXTERNAL if external else SESSION_DAYS_INTERNAL
        session = Session(id=secrets.token_hex(6), user=user, created=now, expires=now + days * DAY,
                          last_seen=now, ip=ip, agent=agent[:300], external=external, mfa=mfa)
        with self._lock:
            self._load()[_hash(token)] = session
            self._save()
        return token

    @staticmethod
    def max_age(external: bool) -> int:
        return (SESSION_DAYS_EXTERNAL if external else SESSION_DAYS_INTERNAL) * DAY

    def get(self, token: str, ip: str = "") -> Session | None:
        if not token:
            return None
        key = _hash(token)
        now = time.time()
        with self._lock:
            session = self._load().get(key)
            if not session:
                return None
            if session.expires < now:
                del self._load()[key]
                self._save()
                return None
            if now - session.last_seen > TOUCH_SECONDS or (ip and ip != session.ip):
                session.last_seen = now
                if ip:
                    session.ip = ip
                self._save()
            return session

    def for_user(self, user: str) -> list[Session]:
        now = time.time()
        with self._lock:
            return sorted((s for s in self._load().values() if s.user == user and s.expires > now),
                          key=lambda s: -s.last_seen)

    def revoke_token(self, token: str) -> None:
        with self._lock:
            if self._load().pop(_hash(token), None):
                self._save()

    def revoke(self, user: str, session_id: str | None = None, keep_token: str | None = None) -> int:
        """End one session, or all of a user's sessions (optionally except the current one)."""
        keep = _hash(keep_token) if keep_token else None
        with self._lock:
            sessions = self._load()
            gone = [k for k, s in sessions.items()
                    if s.user == user and k != keep and (session_id is None or s.id == session_id)]
            for k in gone:
                del sessions[k]
            if gone:
                self._save()
            return len(gone)

    def mark_mfa(self, token: str) -> None:
        with self._lock:
            session = self._load().get(_hash(token))
            if session and not session.mfa:
                session.mfa = True
                self._save()


# ------------------------------------------------------------------ lockout

LOCK_AFTER = 5                 # failed attempts before the first pause
LOCK_FIRST = 60                # seconds; doubles with every further failure
LOCK_MAX = 15 * 60


class LoginGuard:
    """Per-account brake on failed sign-ins.

    Counted separately for inside and outside, so somebody on the internet
    can lock an account for the internet only – at home it keeps working.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._state: dict[tuple[str, bool], list[float]] = {}   # key -> [failures, locked_until, last]

    def locked_for(self, name: str, external: bool) -> int:
        with self._lock:
            state = self._state.get((name, external))
            if not state:
                return 0
            return max(0, int(state[1] - time.time() + 0.999))

    def fail(self, name: str, external: bool) -> tuple[int, int]:
        """Count a failure; returns (failures, seconds locked now – 0 if not locked)."""
        now = time.time()
        with self._lock:
            if len(self._state) > 10_000:
                self._state = {k: v for k, v in self._state.items() if now - v[2] < DAY}
            state = self._state.setdefault((name, external), [0, 0.0, now])
            if now - state[2] > DAY:
                state[0] = 0
            state[0] += 1
            state[2] = now
            seconds = 0
            if state[0] >= LOCK_AFTER:
                seconds = min(LOCK_FIRST * 2 ** (int(state[0]) - LOCK_AFTER), LOCK_MAX)
                state[1] = now + seconds
            return int(state[0]), int(seconds)

    def success(self, name: str, external: bool) -> None:
        with self._lock:
            self._state.pop((name, external), None)


# --------------------------------------------------------------------- TOTP

TOTP_STEP = 30
TOTP_DIGITS = 6
RECOVERY_COUNT = 10


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _b32(secret: str) -> bytes:
    secret = secret.strip().replace(" ", "").upper()
    return base64.b32decode(secret + "=" * (-len(secret) % 8))


def totp_code(secret: str, step: int) -> str:
    digest = hmac.new(_b32(secret), struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(value % 10 ** TOTP_DIGITS).zfill(TOTP_DIGITS)


def totp_match(secret: str, code: str, last_step: int = 0, now: float | None = None) -> int | None:
    """Time step the code belongs to (±1 step of clock drift), or None.

    A step at or before ``last_step`` is refused, so a code cannot be used twice.
    """
    code = "".join(ch for ch in code if ch.isdigit())
    if len(code) != TOTP_DIGITS:
        return None
    current = int((now if now is not None else time.time()) // TOTP_STEP)
    for step in (current - 1, current, current + 1):
        if step > last_step and hmac.compare_digest(totp_code(secret, step), code):
            return step
    return None


def otpauth_uri(secret: str, account: str, issuer: str = "Ordnung!") -> str:
    label = quote(f"{issuer}:{account}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"


def qr_data_uri(text: str) -> str:
    import segno

    return segno.make(text, error="m").svg_data_uri(scale=6, border=2, dark="#000", light="#fff")


def new_recovery_codes() -> list[str]:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"          # no 0/o, 1/l/i
    return ["".join(secrets.choice(alphabet) for _ in range(4)) + "-"
            + "".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(RECOVERY_COUNT)]


def recovery_hash(code: str) -> str:
    clean = "".join(ch for ch in code.lower() if ch.isalnum())
    return hashlib.sha256(clean.encode()).hexdigest()


# ----------------------------------------------------------------- settings


@dataclass
class SecurityConfig:
    require_2fa_external: bool = False   # outside: only accounts with a second factor
    require_2fa_internal: bool = False   # at home too, for accounts that have one
    ntfy_url: str = ""                   # full topic URL, e.g. https://ntfy.example.org/ordnung
    ntfy_token: str = ""
    notify_external_login: bool = True
    notify_lockout: bool = True
    notify_2fa_changes: bool = True
    language: str = "de"                 # of the notifications; set from whoever saves

    def public(self) -> dict:
        data = asdict(self)
        data["has_ntfy_token"] = bool(data.pop("ntfy_token"))
        return data


class SecurityStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def load(self) -> SecurityConfig:
        if not self.path.exists():
            return SecurityConfig()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return SecurityConfig()
        known = SecurityConfig.__dataclass_fields__
        return SecurityConfig(**{k: v for k, v in raw.items() if k in known})

    def update(self, changes: dict) -> SecurityConfig:
        with self._lock:
            config = self.load()
            if changes.pop("clear_ntfy_token", False):
                config.ntfy_token = ""
            for key, value in changes.items():
                if value is None or key not in SecurityConfig.__dataclass_fields__:
                    continue
                if key == "ntfy_url":
                    value = value.strip()
                    if value and not value.startswith(("http://", "https://")):
                        raise ValueError("ntfy address must start with http:// or https://")
                if key == "ntfy_token":
                    value = value.strip()
                    if not value:
                        continue
                setattr(config, key, value)
            _write_json(self.path, asdict(config))
            return config


# ------------------------------------------------------------ notifications

TEXTS = {
    "de": {
        "external.title": "Ordnung!: Anmeldung von außen",
        "external.body": "{user} hat sich von außen angemeldet ({ip}, {agent}).",
        "lock.title": "Ordnung!: Konto gebremst",
        "lock.body": "{count} Fehlversuche für „{user}“ {where} ({ip}). Anmeldung {minutes} min gesperrt.",
        "where.ext": "von außen", "where.int": "im Heimnetz",
        "2fa.on.title": "Ordnung!: Zweiter Faktor eingerichtet",
        "2fa.on.body": "{user} hat den zweiten Faktor eingeschaltet.",
        "2fa.off.title": "Ordnung!: Zweiter Faktor ausgeschaltet",
        "2fa.off.body": "Der zweite Faktor von {user} wurde ausgeschaltet (von {by}).",
        "recovery.title": "Ordnung!: Wiederherstellungscode benutzt",
        "recovery.body": "{user} hat sich mit einem Wiederherstellungscode angemeldet, {left} übrig ({ip}).",
        "test.title": "Ordnung!: Test",
        "test.body": "Die Benachrichtigungen kommen an.",
    },
    "en": {
        "external.title": "Ordnung!: sign-in from outside",
        "external.body": "{user} signed in from outside ({ip}, {agent}).",
        "lock.title": "Ordnung!: account slowed down",
        "lock.body": "{count} failed attempts for “{user}” {where} ({ip}). Sign-in paused for {minutes} min.",
        "where.ext": "from outside", "where.int": "from the home network",
        "2fa.on.title": "Ordnung!: second factor set up",
        "2fa.on.body": "{user} turned on the second factor.",
        "2fa.off.title": "Ordnung!: second factor turned off",
        "2fa.off.body": "The second factor of {user} was turned off (by {by}).",
        "recovery.title": "Ordnung!: recovery code used",
        "recovery.body": "{user} signed in with a recovery code, {left} left ({ip}).",
        "test.title": "Ordnung!: test",
        "test.body": "Notifications are arriving.",
    },
}


class Notifier:
    def __init__(self, store: SecurityStore):
        self.store = store

    def text(self, key: str, **values) -> str:
        lang = self.store.load().language
        table = TEXTS.get(lang, TEXTS["en"])
        return table.get(key, TEXTS["en"][key]).format(**values)

    def send(self, kind: str, title_key: str, body_key: str, *, wait: bool = False,
             priority: int = 3, tags: str = "lock", **values) -> str | None:
        """Push to ntfy in the background. ``kind`` is the switch that must be on."""
        config = self.store.load()
        if not config.ntfy_url or (kind and not getattr(config, kind, False)):
            return "not configured" if not config.ntfy_url else None
        title, body = self.text(title_key, **values), self.text(body_key, **values)
        request = urllib.request.Request(config.ntfy_url, data=body.encode("utf-8"), method="POST")
        # RFC 2047, which ntfy understands: headers themselves are Latin-1 only
        request.add_header("Title", "=?UTF-8?B?" + base64.b64encode(title.encode()).decode() + "?=")
        request.add_header("Priority", str(priority))
        request.add_header("Tags", tags)
        if config.ntfy_token:
            request.add_header("Authorization", "Bearer " + config.ntfy_token)

        def push() -> str | None:
            try:
                with urllib.request.urlopen(request, timeout=5) as res:
                    res.read()
                return None
            except Exception as exc:  # noqa: BLE001 – a notification must never break a sign-in
                log.warning("ntfy: %s", exc)
                return str(exc)

        if wait:
            return push()
        threading.Thread(target=push, daemon=True).start()
        return None


def describe_agent(agent: str) -> str:
    """Short, human description of a browser: "Safari · iPhone"."""
    a = agent or ""
    browser = ("Edge" if "Edg/" in a else "Firefox" if "Firefox/" in a else "Chrome" if "Chrome/" in a
               else "Safari" if "Safari/" in a else a.split("/")[0][:30] or "?")
    system = ("iPhone" if "iPhone" in a else "iPad" if "iPad" in a else "Android" if "Android" in a
              else "Mac" if "Mac OS" in a else "Windows" if "Windows" in a else "Linux" if "Linux" in a else "")
    return f"{browser} · {system}" if system else browser
