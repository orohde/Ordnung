"""Sessions and the current user."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

from .config import Settings

COOKIE = "ordnung_session"
SESSION_DAYS = 30


@dataclass(frozen=True)
class User:
    name: str
    display_name: str = ""
    is_admin: bool = False
    areas: dict[str, str] | None = None  # None = every area (administrators)

    def can_read(self, area: str) -> bool:
        return self.areas is None or area in self.areas

    def can_write(self, area: str) -> bool:
        return self.areas is None or self.areas.get(area) == "write"


def _sign(secret: str, payload: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session(settings: Settings, user: str) -> str:
    expires = int(time.time()) + SESSION_DAYS * 86400
    payload = f"{user}|{expires}"
    token = f"{payload}|{_sign(settings.secret, payload)}"
    return base64.urlsafe_b64encode(token.encode()).decode()


def read_session(settings: Settings, value: str) -> str | None:
    try:
        user, expires, signature = base64.urlsafe_b64decode(value.encode()).decode().rsplit("|", 2)
    except (ValueError, UnicodeDecodeError):
        return None
    if not hmac.compare_digest(signature, _sign(settings.secret, f"{user}|{expires}")):
        return None
    if int(expires) < time.time():
        return None
    return user


def current_user(request: Request) -> User:
    settings: Settings = request.app.state.settings
    header = request.headers.get("authorization", "")
    if settings.api_token and header.startswith("Bearer "):
        if hmac.compare_digest(header[7:].encode(), settings.api_token.encode()):
            return User(name="api", display_name="API", is_admin=True)
    cookie = request.cookies.get(COOKIE)
    if cookie:
        name = read_session(settings, cookie)
        account = request.app.state.users.get(name) if name else None
        if account:
            return User(
                name=account.name,
                display_name=account.display_name or account.name,
                is_admin=account.is_admin,
                areas=None if account.is_admin else dict(account.areas),
            )
    raise HTTPException(status_code=401, detail="not authenticated")


def require_admin(request: Request) -> User:
    user = current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="administrators only")
    return user
