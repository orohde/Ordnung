"""Several named API keys instead of one.

Each key has a name ("Claude", "Mail-Sortierer"), a right (``write``: everything an
administrator may do; ``read``: read every area, change nothing) and remembers when it was
made and last used. Only a hash is stored; the key itself is shown exactly once, when it is
made. Stored as ``apikeys.json`` in the data folder.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path

PREFIX = "ord_"
RIGHTS = ("read", "write")
TOUCH_SECONDS = 60        # "last used" is written at most once a minute per key


class KeyError_(ValueError):
    pass


@dataclass
class ApiKey:
    id: str
    name: str
    hash: str
    right: str = "write"
    hint: str = ""        # the last four characters, to tell keys apart
    made: str = ""
    last: str = ""

    def public(self) -> dict:
        data = asdict(self)
        data.pop("hash")
        return data


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name or "").strip()
    if not name or len(name) > 60:
        raise KeyError_("name must have 1 to 60 characters")
    return name


class ApiKeyStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._touched: dict[str, float] = {}

    def all(self) -> list[ApiKey]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return []
        return [ApiKey(**k) for k in raw.get("keys", [])]

    def _save(self, keys: list[ApiKey]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"keys": [asdict(k) for k in keys]}, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)

    def create(self, name: str, right: str = "write", token: str | None = None) -> tuple[ApiKey, str]:
        """A new key; returns it together with the token, which is never shown again."""
        if right not in RIGHTS:
            raise KeyError_("right must be read or write")
        name = _clean_name(name)
        token = token or PREFIX + secrets.token_urlsafe(32)
        with self._lock:
            keys = self.all()
            if any(k.name.casefold() == name.casefold() for k in keys):
                raise KeyError_("a key with this name exists")
            key = ApiKey(id=secrets.token_hex(4), name=name, hash=_hash(token), right=right,
                         hint=token[-4:], made=_now())
            keys.append(key)
            self._save(keys)
        return key, token

    def change(self, key_id: str, name: str | None = None, right: str | None = None) -> ApiKey:
        with self._lock:
            keys = self.all()
            key = next((k for k in keys if k.id == key_id), None)
            if not key:
                raise KeyError_("unknown key")
            if name is not None:
                name = _clean_name(name)
                if any(k.id != key_id and k.name.casefold() == name.casefold() for k in keys):
                    raise KeyError_("a key with this name exists")
                key.name = name
            if right is not None:
                if right not in RIGHTS:
                    raise KeyError_("right must be read or write")
                key.right = right
            self._save(keys)
            return key

    def renew(self, key_id: str) -> tuple[ApiKey, str]:
        """Same name and right, new secret; the old one stops working at once."""
        token = PREFIX + secrets.token_urlsafe(32)
        with self._lock:
            keys = self.all()
            key = next((k for k in keys if k.id == key_id), None)
            if not key:
                raise KeyError_("unknown key")
            key.hash, key.hint, key.made, key.last = _hash(token), token[-4:], _now(), ""
            self._save(keys)
        return key, token

    def delete(self, key_id: str) -> None:
        with self._lock:
            keys = self.all()
            rest = [k for k in keys if k.id != key_id]
            if len(rest) == len(keys):
                raise KeyError_("unknown key")
            self._save(rest)

    def check(self, token: str) -> ApiKey | None:
        """The key this token belongs to, or None. Compares every hash in constant time."""
        if not token:
            return None
        wanted = _hash(token)
        found = None
        for key in self.all():
            if hmac.compare_digest(key.hash, wanted):
                found = key
        if found and time.time() - self._touched.get(found.id, 0) > TOUCH_SECONDS:
            self._touched[found.id] = time.time()
            with self._lock:
                keys = self.all()
                for k in keys:
                    if k.id == found.id:
                        k.last = _now()
                self._save(keys)
        return found

    def take_over(self, token: str, name: str) -> bool:
        """Carry the single key from before (settings or environment) over as a named one with
        the write right. True once the token is safely here (also when it already was), so the
        caller may forget the plain text."""
        if not token:
            return False
        if any(hmac.compare_digest(k.hash, _hash(token)) for k in self.all()):
            return True
        taken = {k.name.casefold() for k in self.all()}
        free = next(n for n in (name, *(f"{name} {i}" for i in range(2, 100)), secrets.token_hex(4))
                    if n.casefold() not in taken)
        try:
            self.create(free, "write", token=token)
        except (KeyError_, OSError):
            return False
        return True
