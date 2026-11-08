"""Mail inbox: PDFs mailed or forwarded to an address of its own land in the inbox.

Ordnung! collects the mails from an IMAP mailbox (``eingang@…``). Only mails from
addresses stored with an account are taken, and only their PDF attachments; the
account decides the area the documents are meant for. Everything else stays in
the mailbox, moved to the folder "Abgelehnt", so nothing is lost and nothing
unknown reaches the archive. Taken mails go to "Abgelegt". Refused mails are
deleted for good after ``reject_days`` (default 7, 0 = right away).

If the receiving server says the sender failed SPF, DKIM and DMARC alike (the
``Authentication-Results`` header), the mail counts as forged and is refused too.
"""

from __future__ import annotations

import email
import email.policy
import hashlib
import imaplib
import json
import logging
import os
import re
import ssl
import threading
import time
from dataclasses import asdict, dataclass
from email.utils import parseaddr
from pathlib import Path

from .upload import MAX_FILE_BYTES, safe_stem, store

log = logging.getLogger("ordnung.mail")

DONE_FOLDER = "Abgelegt"
REJECT_FOLDER = "Abgelehnt"
MAX_PER_RUN = 50
LOG_KEEP = 40
MAIL_ID = "mail"


class MailError(ValueError):
    pass


@dataclass
class MailConfig:
    enabled: bool = False
    host: str = ""
    port: int = 993
    user: str = ""
    password: str = ""
    folder: str = "INBOX"
    check_auth: bool = True          # refuse mails the server marks as forged
    reject_days: int = 7             # delete refused mails after n days, 0 = at once

    def public(self) -> dict:
        data = asdict(self)
        data["has_password"] = bool(data.pop("password"))
        return data


def _write_json(path: Path, data) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


class MailStore:
    def __init__(self, path: Path):
        self.path = path
        self.log_path = path.with_name(path.stem + "-log.json")
        self._lock = threading.Lock()

    def load(self) -> MailConfig:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return MailConfig()
        known = MailConfig.__dataclass_fields__
        return MailConfig(**{k: v for k, v in raw.items() if k in known})

    def update(self, changes: dict) -> MailConfig:
        with self._lock:
            config = self.load()
            if changes.pop("clear_password", False):
                config.password = ""
            for key, value in changes.items():
                if value is None or key not in MailConfig.__dataclass_fields__:
                    continue
                if isinstance(value, str):
                    value = value.strip()
                if key == "password" and not value:
                    continue
                if key == "port" and not (0 < int(value) < 65536):
                    raise MailError("invalid port")
                if key == "reject_days" and not (0 <= int(value) <= 3650):
                    raise MailError("invalid number of days")
                if key == "folder" and not value:
                    value = "INBOX"
                setattr(config, key, value)
            if config.enabled and not (config.host and config.user and config.password):
                raise MailError("server, user and password are needed")
            _write_json(self.path, asdict(config))
            return config

    def events(self) -> list[dict]:
        try:
            return json.loads(self.log_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def add_events(self, new: list[dict]) -> None:
        if not new:
            return
        with self._lock:
            _write_json(self.log_path, (list(reversed(new)) + self.events())[:LOG_KEEP])


# ------------------------------------------------------------------ one mail


def _auth_failed(msg) -> bool:
    """True if the receiving server says no check (SPF, DKIM, DMARC) passed, or DMARC failed."""
    headers = msg.get_all("Authentication-Results") or []
    if not headers:
        return False
    results = re.findall(r"\b(spf|dkim|dmarc)=([a-z]+)", " ".join(str(h) for h in headers).lower())
    if not results:
        return False
    if ("dmarc", "fail") in results:
        return True
    return not any(value == "pass" for _, value in results)


def pdf_parts(msg) -> list[tuple[str, bytes]]:
    """All PDF attachments, forwarded mails included; the same file only once."""
    found: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for part in msg.walk():
        if part.is_multipart():
            continue
        name = part.get_filename() or ""
        if part.get_content_type() != "application/pdf" and not name.lower().endswith(".pdf"):
            continue
        data = part.get_payload(decode=True) or b""
        if not data.startswith(b"%PDF-") or len(data) > MAX_FILE_BYTES:
            continue
        digest = hashlib.sha256(data).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        found.append((safe_stem(name or msg.get("Subject", "") or "E-Mail") + ".pdf", data))
    return found


class MailInbox:
    def __init__(self, store: MailStore, users, target: Path, settle: int):
        self.store = store
        self.users = users
        self.target = target
        self.settle = settle
        self._lock = threading.Lock()
        self._last_purge = 0.0

    def process(self, raw: bytes) -> dict:
        """Check one mail and, if it is welcome, put its PDFs into the inbox."""
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        sender = parseaddr(str(msg.get("From", "")))[1].strip().casefold()
        event = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "from": sender,
                 "subject": str(msg.get("Subject", ""))[:200], "files": [], "user": "", "area": ""}
        account = self.users.by_email(sender)
        if not account:
            return {**event, "result": "rejected", "reason": "unknown_sender"}
        event.update(user=account.name, area=account.own_area())
        if self.store.load().check_auth and _auth_failed(msg):
            return {**event, "result": "rejected", "reason": "forged"}
        files = pdf_parts(msg)
        if not files:
            return {**event, "result": "rejected", "reason": "no_pdf"}
        folder = self.target / event["area"] if event["area"] else self.target
        event["files"] = store(folder, files, self.settle)
        return {**event, "result": "accepted", "reason": ""}

    # ------------------------------------------------------------- IMAP

    def _connect(self, config: MailConfig) -> imaplib.IMAP4:
        if not (config.host and config.user and config.password):
            raise MailError("server, user and password are needed")
        try:
            if config.port == 143:
                con = imaplib.IMAP4(config.host, config.port, timeout=30)
                con.starttls(ssl_context=ssl.create_default_context())
            else:
                con = imaplib.IMAP4_SSL(config.host, config.port, ssl_context=ssl.create_default_context(), timeout=30)
            con.login(config.user, config.password)
        except (OSError, imaplib.IMAP4.error) as exc:
            raise MailError(f"connection failed: {exc}") from exc
        return con

    def test(self) -> dict:
        config = self.store.load()
        con = self._connect(config)
        try:
            status, data = con.select(_quote(config.folder), readonly=True)
            if status != "OK":
                raise MailError(f"folder not found: {config.folder}")
            return {"ok": True, "waiting": int(data[0] or 0)}
        finally:
            _logout(con)

    def fetch(self, force: bool = False) -> dict:
        """Collect waiting mails. Runs once at a time; ``force`` also when switched off."""
        config = self.store.load()
        if not (config.enabled or force):
            return {"started": False}
        if not self._lock.acquire(blocking=False):
            return {"started": False}
        events: list[dict] = []
        try:
            con = self._connect(config)
            try:
                if con.select(_quote(config.folder))[0] != "OK":
                    raise MailError(f"folder not found: {config.folder}")
                for folder in (DONE_FOLDER, REJECT_FOLDER):
                    con.create(_quote(folder))          # fails harmlessly if it exists
                status, data = con.uid("SEARCH", None, "ALL")
                uids = (data[0] or b"").split()[:MAX_PER_RUN] if status == "OK" else []
                can_move = "MOVE" in getattr(con, "capabilities", ())
                for uid in uids:
                    status, parts = con.uid("FETCH", uid, "(BODY.PEEK[])")
                    raw = next((p[1] for p in parts or [] if isinstance(p, tuple)), None)
                    if status != "OK" or raw is None:
                        continue
                    try:
                        event = self.process(raw)
                    except Exception as exc:  # noqa: BLE001 - leave the mail for the next round
                        log.exception("mail %s could not be processed", uid)
                        events.append({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "result": "error",
                                       "reason": str(exc)[:200], "from": "", "subject": "", "files": []})
                        continue
                    if event["result"] == "accepted":
                        _move(con, uid, DONE_FOLDER, can_move)
                    elif config.reject_days == 0:
                        con.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                    else:
                        _move(con, uid, REJECT_FOLDER, can_move)
                    events.append(event)
                con.expunge()
                if time.time() - self._last_purge > 3600:
                    self._last_purge = time.time()
                    _purge(con, max(config.reject_days, 0))
            finally:
                _logout(con)
        finally:
            self.store.add_events(events)
            self._lock.release()
        accepted = [e for e in events if e["result"] == "accepted"]
        return {"started": True, "mails": len(events), "accepted": len(accepted),
                "files": sum(len(e["files"]) for e in accepted),
                "rejected": sum(1 for e in events if e["result"] == "rejected")}


def _quote(folder: str) -> str:
    return '"' + folder.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _move(con, uid: bytes, folder: str, can_move: bool) -> None:
    if can_move:
        con.uid("MOVE", uid, _quote(folder))
        return
    if con.uid("COPY", uid, _quote(folder))[0] == "OK":
        con.uid("STORE", uid, "+FLAGS", "(\\Deleted)")


def _purge(con, days: int) -> int:
    """Delete refused mails that arrived more than ``days`` days ago."""
    if con.select(_quote(REJECT_FOLDER))[0] != "OK":
        return 0
    t = time.gmtime(time.time() - days * 86400)
    since = f"{t.tm_mday:02d}-{_MONTHS[t.tm_mon - 1]}-{t.tm_year}"   # IMAP wants English month names
    status, data = con.uid("SEARCH", None, "BEFORE", since)
    uids = (data[0] or b"").split() if status == "OK" else []
    for uid in uids:
        con.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
    if uids:
        con.expunge()
        log.info("mail inbox: %d refused mail(s) older than %d days deleted", len(uids), days)
    return len(uids)


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _logout(con) -> None:
    try:
        con.logout()
    except Exception:  # noqa: BLE001
        pass
