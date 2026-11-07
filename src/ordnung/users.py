"""User accounts, stored as a readable JSON file in the data folder.

Accounts are configuration, not index data: they cannot be rebuilt from the
archive folders, so they live apart from the disposable SQLite index.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$")
PERMISSIONS = ("read", "write")
MIN_PASSWORD = 8


@dataclass
class Account:
    name: str
    display_name: str = ""
    password: str = ""            # scrypt hash, never the plain password
    is_admin: bool = False
    areas: dict[str, str] = field(default_factory=dict)  # area -> read|write

    def public(self) -> dict:
        data = asdict(self)
        data.pop("password")
        return data


class UserError(ValueError):
    pass


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(digest_b64)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=len(expected))
    return hmac.compare_digest(digest, expected)


class UserStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    # ------------------------------------------------------------ storage

    def _load(self) -> dict[str, Account]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {u["name"]: Account(**u) for u in raw.get("users", [])}

    def _save(self, users: dict[str, Account]) -> None:
        tmp = self.path.with_suffix(".tmp")
        data = {"version": 1, "users": [asdict(u) for u in sorted(users.values(), key=lambda u: u.name)]}
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)

    # ------------------------------------------------------------- access

    def all(self) -> list[Account]:
        with self._lock:
            return sorted(self._load().values(), key=lambda u: u.name)

    def get(self, name: str) -> Account | None:
        with self._lock:
            return self._load().get(name)

    def bootstrap(self, name: str, password: str) -> bool:
        """Create the first administrator if there are no accounts yet."""
        if not password:
            return False
        with self._lock:
            users = self._load()
            if users:
                return False
            users[name] = Account(name=name, display_name=name, password=hash_password(password), is_admin=True)
            self._save(users)
            return True

    def authenticate(self, name: str, password: str) -> Account | None:
        account = self.get(name)
        if account and verify_password(password, account.password):
            return account
        # spend comparable time for unknown users
        verify_password(password, "scrypt$" + base64.b64encode(b"0" * 16).decode() + "$" + base64.b64encode(b"0" * 32).decode())
        return None

    # ------------------------------------------------------------ changes

    def create(self, name: str, password: str, display_name: str = "", is_admin: bool = False,
               areas: dict[str, str] | None = None) -> Account:
        name = name.strip().lower()
        if not NAME_RE.match(name):
            raise UserError("invalid user name")
        _check_password(password)
        with self._lock:
            users = self._load()
            if name in users:
                raise UserError("user exists")
            account = Account(name=name, display_name=display_name.strip() or name,
                              password=hash_password(password), is_admin=is_admin,
                              areas=_clean_areas(areas))
            users[name] = account
            self._save(users)
            return account

    def update(self, name: str, *, display_name: str | None = None, password: str | None = None,
               is_admin: bool | None = None, areas: dict[str, str] | None = None) -> Account:
        with self._lock:
            users = self._load()
            account = users.get(name)
            if not account:
                raise UserError("unknown user")
            if is_admin is False and account.is_admin and _admin_count(users) == 1:
                raise UserError("last administrator")
            if display_name is not None:
                account.display_name = display_name.strip() or name
            if password:
                _check_password(password)
                account.password = hash_password(password)
            if is_admin is not None:
                account.is_admin = is_admin
            if areas is not None:
                account.areas = _clean_areas(areas)
            self._save(users)
            return account

    def delete(self, name: str) -> None:
        with self._lock:
            users = self._load()
            account = users.get(name)
            if not account:
                raise UserError("unknown user")
            if account.is_admin and _admin_count(users) == 1:
                raise UserError("last administrator")
            del users[name]
            self._save(users)


def _admin_count(users: dict[str, Account]) -> int:
    return sum(1 for u in users.values() if u.is_admin)


def _check_password(password: str) -> None:
    if len(password) < MIN_PASSWORD:
        raise UserError(f"password too short (min. {MIN_PASSWORD})")


def _clean_areas(areas: dict[str, str] | None) -> dict[str, str]:
    return {a: p for a, p in (areas or {}).items() if p in PERMISSIONS}
