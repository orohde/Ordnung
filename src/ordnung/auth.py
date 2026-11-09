"""Sessions and the current user."""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import HTTPException, Request


COOKIE = "ordnung_session"              # plain http (local testing, own LAN without TLS)
COOKIE_SECURE = "__Host-ordnung_session"  # https: Secure, whole host only, no Domain


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


def is_https(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "") == "https"


def cookie_name(request: Request) -> str:
    return COOKIE_SECURE if is_https(request) else COOKIE


def session_token(request: Request) -> str:
    return request.cookies.get(cookie_name(request), "")


def client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def is_external(request: Request) -> bool:
    return not request.app.state.networks.is_internal(client_ip(request))


def needs_mfa_outside(request: Request, account) -> bool:
    """From outside, an account needs the second factor if it has one or policy demands it."""
    return account.has_totp or request.app.state.security.load().require_2fa_external


def current_user(request: Request) -> User:
    header = request.headers.get("authorization", "")
    api_token = request.app.state.security.load().api_token if header.startswith("Bearer ") else ""
    if api_token:
        if hmac.compare_digest(header[7:].encode(), api_token.encode()):
            return User(name="api", display_name="API", is_admin=True)
    session = request.app.state.sessions.get(session_token(request), client_ip(request))
    account = request.app.state.users.get(session.user) if session else None
    if account:
        # a session from home without second factor does not open the door from outside
        if not session.mfa and is_external(request) and needs_mfa_outside(request, account):
            raise HTTPException(status_code=401, detail="not authenticated")
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
