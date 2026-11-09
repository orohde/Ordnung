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

from .security import new_recovery_codes, new_totp_secret, recovery_hash, totp_match

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$")
EMAIL_RE = re.compile(r"^[^@\s<>,;]+@[^@\s<>,;]+\.[a-z]{2,}$", re.IGNORECASE)
PERMISSIONS = ("read", "write")
MIN_PASSWORD = 12


@dataclass
class Account:
    name: str
    display_name: str = ""
    password: str = ""            # scrypt hash, never the plain password
    is_admin: bool = False
    areas: dict[str, str] = field(default_factory=dict)  # area -> read|write
    totp_secret: str = ""         # second factor (RFC 6238), empty = off
    totp_pending: str = ""        # being set up, not active until a code was confirmed
    totp_last_step: int = 0       # last accepted time step, so a code works only once
    recovery: list[str] = field(default_factory=list)   # SHA-256 of the unused recovery codes
    emails: list[str] = field(default_factory=list)     # sender addresses the mail inbox accepts
    mail_area: str = ""           # area mails of this person are meant for, "" = own area

    def own_area(self) -> str:
        """Area a mail from this person goes to: the set one, else the area named like the
        account, else the only area with write access, else none (chosen when filing)."""
        if self.mail_area:
            return self.mail_area
        if self.name in self.areas or (self.is_admin and not self.areas):
            return self.name
        writable = [a for a, p in self.areas.items() if p == "write"]
        return writable[0] if len(writable) == 1 else ""

    @property
    def has_totp(self) -> bool:
        return bool(self.totp_secret)

    def public(self) -> dict:
        data = asdict(self)
        for secret in ("password", "totp_secret", "totp_pending", "totp_last_step", "recovery"):
            data.pop(secret)
        data["totp"] = self.has_totp
        data["recovery_left"] = len(self.recovery) if self.has_totp else 0
        data["mail_target"] = self.own_area()
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
        known = Account.__dataclass_fields__
        return {u["name"]: Account(**{k: v for k, v in u.items() if k in known}) for u in raw.get("users", [])}

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

    def by_email(self, address: str) -> Account | None:
        address = address.strip().casefold()
        if not address:
            return None
        return next((u for u in self.all() if address in u.emails), None)

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
               areas: dict[str, str] | None = None, emails: list[str] | None = None,
               mail_area: str = "", only_if_empty: bool = False) -> Account:
        name = name.strip().lower()
        if not NAME_RE.match(name):
            raise UserError("invalid user name")
        _check_password(password)
        with self._lock:
            users = self._load()
            if only_if_empty and users:
                raise UserError("already set up")
            if name in users:
                raise UserError("user exists")
            account = Account(name=name, display_name=display_name.strip() or name,
                              password=hash_password(password), is_admin=is_admin,
                              areas=_clean_areas(areas), emails=_clean_emails(emails, users, name),
                              mail_area=mail_area.strip())
            users[name] = account
            self._save(users)
            return account

    def update(self, name: str, *, display_name: str | None = None, password: str | None = None,
               is_admin: bool | None = None, areas: dict[str, str] | None = None,
               emails: list[str] | None = None, mail_area: str | None = None) -> Account:
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
            if emails is not None:
                account.emails = _clean_emails(emails, users, name)
            if mail_area is not None:
                account.mail_area = mail_area.strip()
            self._save(users)
            return account

    # ------------------------------------------------------ second factor

    def _change(self, name: str, fn):
        with self._lock:
            users = self._load()
            account = users.get(name)
            if not account:
                raise UserError("unknown user")
            result = fn(account)
            self._save(users)
            return result

    def totp_begin(self, name: str) -> str:
        secret = new_totp_secret()

        def begin(account: Account) -> str:
            account.totp_pending = secret
            return secret
        return self._change(name, begin)

    def totp_confirm(self, name: str, code: str) -> list[str]:
        """Activate the pending secret if the code fits; returns fresh recovery codes."""
        codes = new_recovery_codes()

        def confirm(account: Account) -> list[str]:
            if not account.totp_pending:
                raise UserError("no second factor being set up")
            step = totp_match(account.totp_pending, code)
            if step is None:
                raise UserError("invalid code")
            account.totp_secret, account.totp_pending = account.totp_pending, ""
            account.totp_last_step = step
            account.recovery = [recovery_hash(c) for c in codes]
            return codes
        return self._change(name, confirm)

    def totp_off(self, name: str) -> None:
        def off(account: Account) -> None:
            account.totp_secret = account.totp_pending = ""
            account.totp_last_step = 0
            account.recovery = []
        self._change(name, off)

    def new_recovery(self, name: str) -> list[str]:
        codes = new_recovery_codes()

        def renew(account: Account) -> list[str]:
            if not account.has_totp:
                raise UserError("no second factor")
            account.recovery = [recovery_hash(c) for c in codes]
            return codes
        return self._change(name, renew)

    def second_factor(self, name: str, code: str) -> str | None:
        """Check a TOTP or recovery code: "totp", "recovery" or None. Each code works once."""
        def check(account: Account) -> str | None:
            if not account.has_totp:
                return None
            step = totp_match(account.totp_secret, code, account.totp_last_step)
            if step is not None:
                account.totp_last_step = step
                return "totp"
            digest = recovery_hash(code)
            if digest in account.recovery:
                account.recovery.remove(digest)
                return "recovery"
            return None
        return self._change(name, check)

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


def _clean_emails(emails: list[str] | None, users: dict[str, Account], name: str) -> list[str]:
    """Lower-cased, checked, each address belongs to one account only."""
    clean: list[str] = []
    for raw in emails or []:
        address = raw.strip().strip("<>").casefold()
        if not address:
            continue
        if not EMAIL_RE.match(address):
            raise UserError(f"invalid e-mail address: {raw.strip()}")
        other = next((u.name for u in users.values() if u.name != name and address in u.emails), None)
        if other:
            raise UserError(f"e-mail address already belongs to {other}: {address}")
        if address not in clean:
            clean.append(address)
    return clean


def _clean_areas(areas: dict[str, str] | None) -> dict[str, str]:
    return {a: p for a, p in (areas or {}).items() if p in PERMISSIONS}
