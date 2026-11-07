"""Inbox: new documents waiting to be filed.

The enabled inbox folders are scanned for documents. Each one gets its text
(taken over from the archive or the learning set when the very same file is
already known there, otherwise extracted), then a filing suggestion:

1. **rules**   – enabled rules whose conditions all match the text
2. **folder**  – the folder the file sits in inside the inbox, e.g. when a
                 folder was copied over from the old archive
3. **AI**      – only on request, or automatically when switched on and
                 neither of the above found anything

Nothing is filed without confirmation. Filing copies the file into the
archive as ``{area}/{folder}/{date}_{title}_{id}.{ext}``; afterwards the
original is either moved to ``_importiert`` inside the inbox or left in
place and remembered as filed.

The state lives in ``inbox.db`` in the data folder. Like the index it can
be deleted: the inbox is simply read again (files left in place would then
show up once more, flagged as already in the archive).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import threading
import time
import uuid
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from .folders import FolderError, clean_path
from .index import MIN_ID_LEN, SKIP_FILES, SKIP_NAMES, Index, fold, nfc, parse_name, sha256_file
from .storage import Inbox, StorageService, path_status

DONE_DIR = "_importiert"
EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tif", "tiff", "txt", "docx"}
SETTLE_SECONDS = 10           # a scanner may still be writing younger files
AI_TEXT_CHARS = 5000

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    key          TEXT PRIMARY KEY,
    inbox        TEXT NOT NULL,
    rel          TEXT NOT NULL,
    name         TEXT NOT NULL,
    ext          TEXT NOT NULL,
    size         INTEGER NOT NULL,
    mtime        REAL NOT NULL,
    sha256       TEXT NOT NULL,
    seen         INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'new',     -- new | filed | dismissed
    body         TEXT,                            -- NULL = text not extracted yet
    pages        INTEGER NOT NULL DEFAULT 0,
    ocr_pages    INTEGER NOT NULL DEFAULT 0,
    method       TEXT NOT NULL DEFAULT '',
    error        TEXT NOT NULL DEFAULT '',
    ai           TEXT,                            -- JSON answer of the AI
    sugg         TEXT,                            -- cached suggestion (JSON)
    sugg_key     TEXT NOT NULL DEFAULT '',
    filed_path   TEXT NOT NULL DEFAULT '',
    added        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS items_status ON items(status);
CREATE INDEX IF NOT EXISTS items_sha ON items(sha256);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

# file names a scanner or a mail program makes up – not worth keeping as a title
_MEANINGLESS = re.compile(
    r"^(?:(?:scan|img|image|dok|doc|document|dokument|file|datei|pdf|seite|page|untitled|unbenannt|"
    r"brother|canon|epson|hp|xerox|ricoh)[\s_\-]*)?[\d\s_\-\.:()]*$"
    r"|^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_MONTHS = {"januar": 1, "jan": 1, "februar": 2, "feb": 2, "märz": 3, "maerz": 3, "mär": 3, "april": 4,
           "apr": 4, "mai": 5, "juni": 6, "jun": 6, "juli": 7, "jul": 7, "august": 8, "aug": 8,
           "september": 9, "sep": 9, "sept": 9, "oktober": 10, "okt": 10, "november": 11, "nov": 11,
           "dezember": 12, "dez": 12}
_DATE_NUM = re.compile(r"(?<![\d.])(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4}|\d{2})(?![\d])")
_DATE_ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
_DATE_WORD = re.compile(r"(?<!\d)(\d{1,2})\.?\s+(" + "|".join(sorted(_MONTHS, key=len, reverse=True))
                        + r")\.?\s+(\d{4})", re.IGNORECASE)
_DATE_LABEL = re.compile(r"(?:datum|date|vom|den|ausgestellt am|rechnungsdatum|erstellt am)\s*[:.]?\s*$",
                         re.IGNORECASE)
_BAD_TITLE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


class InboxError(ValueError):
    pass


def item_key(inbox_id: str, rel: str) -> str:
    return hashlib.sha1(f"{inbox_id}|{rel}".encode()).hexdigest()[:12]


def clean_title(title: str) -> str:
    title = _BAD_TITLE.sub(" ", nfc(title or ""))
    title = re.sub(r"\s+", " ", title).strip(" .-_")
    return title[:120]


def meaningful(stem: str) -> bool:
    return bool(stem.strip()) and not _MEANINGLESS.match(stem.strip())


EARLIEST_YEAR = 1900        # oldest document date accepted when filing (family papers, diaries)
GUESS_EARLIEST_YEAR = 1950  # older dates in a text are mostly birth dates, not the document date


def _valid(y: int, m: int, d: int, earliest: int = EARLIEST_YEAR) -> str | None:
    try:
        value = date(y, m, d)
    except ValueError:
        return None
    if value.year < earliest or value > date.today().replace(year=date.today().year + 1):
        return None
    return value.isoformat()


def guess_date(text: str) -> str | None:
    """The document date: a date right after a label like "Datum", else the first one."""
    head = text[:4000]
    found: list[tuple[int, str, bool]] = []
    for m in _DATE_NUM.finditer(head):
        y = int(m[3])
        y = y + 2000 if y < 100 and y <= date.today().year % 100 + 1 else (y + 1900 if y < 100 else y)
        value = _valid(y, int(m[2]), int(m[1]), GUESS_EARLIEST_YEAR)
        if value:
            found.append((m.start(), value, bool(_DATE_LABEL.search(head[max(0, m.start() - 30):m.start()]))))
    for m in _DATE_WORD.finditer(head):
        value = _valid(int(m[3]), _MONTHS[m[2].lower()], int(m[1]), GUESS_EARLIEST_YEAR)
        if value:
            found.append((m.start(), value, bool(_DATE_LABEL.search(head[max(0, m.start() - 30):m.start()]))))
    for m in _DATE_ISO.finditer(head):
        value = _valid(int(m[1]), int(m[2]), int(m[3]), GUESS_EARLIEST_YEAR)
        if value:
            found.append((m.start(), value, False))
    if not found:
        return None
    labeled = [f for f in found if f[2]]
    return (min(labeled) if labeled else min(found))[1]


class InboxService:
    def __init__(self, db_path: Path, storage: StorageService, index: Index, rules, folders, importplan,
                 upload_dir: Path | None = None):
        self.db_path = db_path
        self.upload_dir = upload_dir      # built-in inbox for files uploaded in the browser
        self.storage = storage
        self.index = index
        self.rules = rules
        self.folders = folders
        self.importplan = importplan
        self.reference: Index | None = None
        # filed since the archive index was last scanned: sha256 -> archive path
        # (the index only learns about new archive files with its next scan)
        self._recent: dict[str, str] = {}
        self._scan_lock = threading.Lock()
        self._text_lock = threading.Lock()
        self._file_lock = threading.Lock()
        with self.connect() as con:
            con.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        return con

    # ----------------------------------------------------------------- scan

    def inboxes(self, enabled_only: bool = True) -> list[Inbox]:
        found = [i for i in self.storage.load().inboxes if i.enabled or not enabled_only]
        if self.upload_dir is not None:
            found.append(Inbox(id="upload", name="Hochgeladen", path=str(self.upload_dir),
                               area="", enabled=True, after_import="move"))
        return found

    def _walk(self, root: Path):
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith((".", "@", "#"))
                                 and d not in SKIP_NAMES and d != DONE_DIR)
            for name in filenames:
                if name.startswith(".") or name in SKIP_FILES:
                    continue
                ext = name.rpartition(".")[2].lower() if "." in name else ""
                if ext not in EXTENSIONS:
                    continue
                full = Path(dirpath) / name
                if full.is_file():
                    yield full, nfc(full.relative_to(root).as_posix()), ext

    def scan(self) -> dict:
        if not self._scan_lock.acquire(blocking=False):
            return {"started": False}
        try:
            return self._scan()
        finally:
            self._scan_lock.release()

    def _scan(self) -> dict:
        added = 0
        now = time.time()
        with self.connect() as con:
            generation = int((con.execute("SELECT value FROM meta WHERE key='gen'").fetchone() or ["0"])[0]) + 1
            known = {r["key"]: (r["size"], r["mtime"]) for r in con.execute("SELECT key, size, mtime FROM items")}
            scanned: set[str] = set()
            for inbox in self.inboxes():
                root = Path(inbox.path)
                if not path_status(inbox.path)["readable"]:
                    continue
                scanned.add(inbox.id)
                for full, rel, ext in self._walk(root):
                    stat = full.stat()
                    if now - stat.st_mtime < SETTLE_SECONDS:
                        continue
                    key = item_key(inbox.id, rel)
                    old = known.get(key)
                    if old and old[0] == stat.st_size and abs(old[1] - stat.st_mtime) < 1e-6:
                        con.execute("UPDATE items SET seen=? WHERE key=?", (generation, key))
                        continue
                    sha = sha256_file(full)
                    # a changed file is a new document: forget text, AI answer and status
                    con.execute(
                        """INSERT INTO items(key, inbox, rel, name, ext, size, mtime, sha256, seen, added)
                           VALUES(?,?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(key) DO UPDATE SET size=excluded.size, mtime=excluded.mtime,
                             sha256=excluded.sha256, seen=excluded.seen, status='new', body=NULL,
                             ai=NULL, sugg=NULL, sugg_key='', filed_path=''""",
                        (key, inbox.id, rel, rel.rsplit("/", 1)[-1], ext, stat.st_size, stat.st_mtime, sha,
                         generation, time.strftime("%Y-%m-%dT%H:%M:%S")),
                    )
                    added += 1
            # files that are gone (moved away, deleted) and items of removed inboxes
            configured = {i.id for i in self.inboxes(False)}
            removed = 0
            for row in con.execute("SELECT key, inbox, seen FROM items").fetchall():
                if (row["inbox"] in scanned and row["seen"] != generation) or row["inbox"] not in configured:
                    removed += con.execute("DELETE FROM items WHERE key=?", (row["key"],)).rowcount
            con.execute("INSERT INTO meta(key, value) VALUES('gen', ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(generation),))
        return {"started": True, "added": added, "removed": removed}

    # ----------------------------------------------------------------- text

    def _known_text(self, sha: str):
        for source in (self.index, self.reference):
            if source is None:
                continue
            with source.connect() as con:
                row = con.execute("SELECT body, pages, ocr_pages, method, error FROM texts WHERE sha256=?",
                                  (sha,)).fetchone()
            if row:
                return SimpleNamespace(text=row["body"], pages=row["pages"], ocr_pages=row["ocr_pages"],
                                       method=row["method"], error=row["error"])
        return None

    def extract_pending(self, extractor: Callable, stop: threading.Event | None = None) -> int:
        if not self._text_lock.acquire(blocking=False):
            return 0
        done = 0
        pool: ProcessPoolExecutor | None = None
        try:
            while not (stop and stop.is_set()):
                with self.connect() as con:
                    rows = con.execute("SELECT key, inbox, rel, ext, sha256 FROM items "
                                       "WHERE body IS NULL AND status='new' LIMIT 10").fetchall()
                if not rows:
                    break
                paths = {i.id: Path(i.path) for i in self.inboxes(False)}
                for row in rows:
                    result = self._known_text(row["sha256"])
                    if result is None:
                        if pool is None:
                            pool = ProcessPoolExecutor(max_workers=1)   # pdfium is not thread-safe
                        try:
                            result = pool.submit(extractor, paths[row["inbox"]] / row["rel"], row["ext"]).result()
                        except Exception as exc:  # noqa: BLE001
                            result = SimpleNamespace(text="", pages=0, ocr_pages=0, method="error", error=str(exc)[:300])
                    with self.connect() as con:
                        con.execute("UPDATE items SET body=?, pages=?, ocr_pages=?, method=?, error=?, sugg=NULL "
                                    "WHERE key=?", (result.text, result.pages, result.ocr_pages, result.method,
                                                    result.error, row["key"]))
                    done += 1
        finally:
            if pool is not None:
                pool.shutdown()
            self._text_lock.release()
        return done

    # ---------------------------------------------------------- suggestions

    def _context_key(self) -> str:
        """Suggestions are cached until rules, plan, folders or the archive change."""
        def mtime(p: Path) -> str:
            try:
                return str(p.stat().st_mtime_ns)
            except OSError:
                return "0"
        meta = self.index.meta()
        return "|".join([mtime(self.rules.path), mtime(self.importplan.path), mtime(self.folders.path),
                         str(meta["total"]), str(meta["last_scan"])])

    def _context(self) -> dict:
        folders = self.folders.effective()
        plan = self.importplan.mapping()
        return {
            "match": self.rules.matcher(),
            "folders": {fold(f): f for f in folders},
            "plan": plan,
            "plan_folders": self.importplan.folder_mapping() if plan else {},
            "areas": self.area_names(),
        }

    def area_names(self) -> set[str]:
        names = {a["name"] for a in self.index.areas() if a["name"]}
        names |= {i.area for i in self.storage.load().inboxes if i.area}
        archive = self.index.archive
        try:
            names |= {e.name for e in os.scandir(archive) if e.is_dir() and not e.name.startswith((".", "_", "@", "#"))}
        except OSError:
            pass
        return names

    def _folder_hint(self, rel: str, ctx: dict) -> tuple[str, str] | None:
        """Area and folder the file's place in the inbox points to."""
        parts = rel.split("/")[:-1]
        if not parts:
            return None
        area = ""
        if parts[0] in ctx["areas"]:
            area, parts = parts[0], parts[1:]
        folder = "/".join(parts)
        if not folder:
            return (area, "") if area else None
        if (area, folder) in ctx["plan"]:
            t_area, t_folder = ctx["plan"][(area, folder)]
            return t_area or area, t_folder
        if folder in ctx["plan_folders"]:
            return area, ctx["plan_folders"][folder]
        return area, ctx["folders"].get(fold(folder), folder)

    def _suggest(self, row: sqlite3.Row, inbox: Inbox | None, ctx: dict) -> dict:
        text = row["body"] or ""
        hits = ctx["match"](text) if text else []
        votes = Counter(h["folder"] for h in hits)
        candidates = [{"folder": f, "source": "rule", "rules": [h for h in hits if h["folder"] == f]}
                      for f, _ in votes.most_common()]
        hint = self._folder_hint(row["rel"], ctx)
        if hint and hint[1]:
            same = next((c for c in candidates if c["folder"] == hint[1]), None)
            if same:
                same["source"] = "rule+folder"
            else:
                candidates.append({"folder": hint[1], "source": "folder", "rules": []})
        ai = json.loads(row["ai"]) if row["ai"] else None
        if ai and ai.get("folder") and not any(c["folder"] == ai["folder"] for c in candidates):
            candidates.append({"folder": ai["folder"], "source": "ai", "rules": [], "reason": ai.get("reason", "")})
        elif ai and ai.get("folder"):
            for c in candidates:
                if c["folder"] == ai["folder"]:
                    c["source"] += "+ai"
        best = candidates[0] if candidates else None
        conflict = len({c["folder"] for c in candidates}) > 1

        stem = row["name"].rpartition(".")[0] or row["name"]
        parsed = parse_name(stem)
        title = ""
        if ai and ai.get("title"):
            title = clean_title(ai["title"])
        elif meaningful(parsed.title):
            title = clean_title(re.sub(r"_[0-9a-f]{6,64}$", "", parsed.title))
        doc_date = (ai or {}).get("date") or parsed.doc_date or guess_date(text)
        if doc_date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(doc_date)):
            doc_date = None
        area = (inbox.area if inbox and inbox.area else "") or (hint[0] if hint else "") or (ai or {}).get("area", "")
        duplicate = None
        with self.index.connect() as con:
            dup = con.execute("SELECT path, area, folder FROM files WHERE sha256=? LIMIT 1", (row["sha256"],)).fetchone()
        if dup:
            duplicate = dict(dup)
        elif row["sha256"] in self._recent:
            path = self._recent[row["sha256"]]
            parts = path.split("/")
            duplicate = {"path": path, "area": parts[0], "folder": "/".join(parts[1:-1])}
        return {
            "area": area if area in ctx["areas"] else "",
            "folder": best["folder"] if best else "",
            "source": best["source"] if best else "",
            "title": title,
            "title_fallback": (best["folder"].rsplit("/", 1)[-1] if best else "") or stem,
            "date": doc_date,
            "date_fallback": time.strftime("%Y-%m-%d", time.localtime(row["mtime"])),
            "candidates": candidates[:6],
            "conflict": conflict,
            "duplicate": duplicate,
        }

    def refresh(self, force: bool = False) -> int:
        """(Re)compute cached suggestions where the context changed."""
        key = self._context_key()
        ctx = None
        inboxes = {i.id: i for i in self.inboxes(False)}
        count = 0
        with self.connect() as con:
            rows = con.execute("SELECT * FROM items WHERE status='new' AND body IS NOT NULL" +
                               ("" if force else " AND (sugg IS NULL OR sugg_key != ?)"),
                               () if force else (key,)).fetchall()
            for row in rows:
                ctx = ctx or self._context()
                sugg = self._suggest(row, inboxes.get(row["inbox"]), ctx)
                con.execute("UPDATE items SET sugg=?, sugg_key=? WHERE key=?",
                            (json.dumps(sugg, ensure_ascii=False), key, row["key"]))
                count += 1
        return count

    # ----------------------------------------------------------------- read

    def _public(self, row: sqlite3.Row, inboxes: dict[str, Inbox]) -> dict:
        inbox = inboxes.get(row["inbox"])
        return {
            "key": row["key"], "inbox": row["inbox"], "inbox_name": inbox.name if inbox else "",
            "rel": row["rel"], "name": row["name"], "ext": row["ext"], "size": row["size"],
            "status": row["status"], "added": row["added"], "filed_path": row["filed_path"],
            "text": None if row["body"] is None else {
                "chars": len(row["body"]), "pages": row["pages"], "ocr_pages": row["ocr_pages"],
                "method": row["method"], "error": row["error"]},
            "ai": json.loads(row["ai"]) if row["ai"] else None,
            "suggestion": json.loads(row["sugg"]) if row["sugg"] else None,
        }

    def items(self, status: str = "new") -> list[dict]:
        self.refresh()
        inboxes = {i.id: i for i in self.inboxes(False)}
        with self.connect() as con:
            rows = con.execute("SELECT * FROM items WHERE status=? ORDER BY inbox, rel", (status,)).fetchall()
        return [self._public(r, inboxes) for r in rows]

    def counts(self) -> dict:
        with self.connect() as con:
            rows = dict(con.execute("SELECT status, COUNT(*) FROM items GROUP BY status").fetchall())
            pending = con.execute("SELECT COUNT(*) FROM items WHERE status='new' AND body IS NULL").fetchone()[0]
        return {"new": rows.get("new", 0), "filed": rows.get("filed", 0),
                "dismissed": rows.get("dismissed", 0), "reading": pending}

    def get(self, key: str) -> dict:
        self.refresh()
        with self.connect() as con:
            row = con.execute("SELECT * FROM items WHERE key=?", (key,)).fetchone()
        if not row:
            raise InboxError("unknown item")
        return self._public(row, {i.id: i for i in self.inboxes(False)})

    def path_of(self, key: str) -> tuple[Path, str]:
        with self.connect() as con:
            row = con.execute("SELECT inbox, rel, ext FROM items WHERE key=?", (key,)).fetchone()
        inbox = next((i for i in self.inboxes(False) if row and i.id == row["inbox"]), None)
        if not row or not inbox:
            raise InboxError("unknown item")
        root = Path(inbox.path).resolve()
        path = (root / row["rel"]).resolve()
        if root not in path.parents or not path.is_file():
            raise InboxError("file not found")
        return path, row["ext"]

    def text(self, key: str) -> str:
        with self.connect() as con:
            row = con.execute("SELECT body FROM items WHERE key=?", (key,)).fetchone()
        return (row["body"] or "") if row else ""

    # ------------------------------------------------------------------- AI

    def ask_ai(self, key: str, ai, instructions: str | None = None, prompt_name: str | None = None) -> dict:
        """Ask the AI for folder, title and date.

        The task text is ``instructions`` if given, else the named instruction
        ``prompt_name`` from the settings, else the default one; the answer format is
        always appended so an edit cannot break parsing.
        """
        with self.connect() as con:
            row = con.execute("SELECT * FROM items WHERE key=?", (key,)).fetchone()
        if not row:
            raise InboxError("unknown item")
        if not row["body"]:
            raise InboxError("no text yet")
        inbox = next((i for i in self.inboxes(False) if i.id == row["inbox"]), None)
        config = ai.load()
        ctx = self._context()
        hint = self._folder_hint(row["rel"], ctx)
        area = (inbox.area if inbox and inbox.area else "") or (hint[0] if hint else "")
        if area and area in config.excluded_areas:
            raise InboxError("area excluded from AI")
        book = self.rules.load()
        folders = sorted(ctx["folders"].values(), key=str.casefold)
        lines = []
        for f in folders:
            card = book.folders.get(f)
            lines.append(f"- {f}" + (f": {card.description}" if card and card.description else ""))
        prompt = (f"File name: {row['name']}\n\nFolders of the archive:\n" + "\n".join(lines[:600]) +
                  f"\n\n--- Document text (start) ---\n{row['body'][:AI_TEXT_CHARS]}")
        task = (instructions or "").strip() or pick_prompt(config, prompt_name)["text"]
        completion = ai.complete(task[:MAX_INSTRUCTIONS] + "\n\n" + AI_FORMAT, prompt, max_tokens=1500, effort="low")
        answer = _parse_json(completion.text)
        folder = str(answer.get("folder") or "").strip().strip("/")
        result = {
            "folder": ctx["folders"].get(fold(folder), folder),
            "new_folder": bool(folder) and fold(folder) not in ctx["folders"],
            "title": clean_title(str(answer.get("title") or "")),
            "date": str(answer.get("date") or "") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(answer.get("date") or "")) else "",
            "reason": str(answer.get("reason") or "")[:300],
            "model": completion.model, "cost": round(completion.cost, 5),
        }
        with self.connect() as con:
            con.execute("UPDATE items SET ai=?, sugg=NULL WHERE key=?", (json.dumps(result, ensure_ascii=False), key))
        return result

    def auto_ai(self, ai, limit: int = 20) -> int:
        """Ask the AI for items where neither a rule nor the inbox folder helps."""
        config = ai.load()
        if not (config.enabled and config.inbox_auto):
            return 0
        self.refresh()
        with self.connect() as con:
            rows = con.execute("SELECT key, sugg FROM items WHERE status='new' AND body != '' AND ai IS NULL "
                               "AND sugg IS NOT NULL").fetchall()
        done = 0
        for row in rows:
            if done >= limit:
                break
            if json.loads(row["sugg"]).get("folder"):
                continue
            try:
                self.ask_ai(row["key"], ai)
            except Exception:  # noqa: BLE001 - limit reached, excluded area, provider down …
                with self.connect() as con:   # do not ask again for this file
                    con.execute("UPDATE items SET ai='{}' WHERE key=?", (row["key"],))
            done += 1
        return done

    # ---------------------------------------------------------------- file

    def _archived(self, sha: str) -> str | None:
        """Archive path of a file with this content, including ones filed moments ago."""
        with self.index.connect() as con:
            dup = con.execute("SELECT path FROM files WHERE sha256=? LIMIT 1", (sha,)).fetchone()
        if dup:
            return dup[0]
        recent = self._recent.get(sha)
        if recent and (self.index.archive / recent).is_file():
            return recent
        return None

    def _short_id(self, sha: str) -> str:
        with self.index.connect() as con:
            others = [r[0] for r in con.execute("SELECT DISTINCT sha256 FROM files WHERE sha256 LIKE ? AND sha256 != ?",
                                                (sha[:MIN_ID_LEN] + "%", sha))]
        others += [s for s in self._recent if s != sha and s.startswith(sha[:MIN_ID_LEN])]
        need = MIN_ID_LEN
        for other in others:
            common = 0
            while common < len(sha) and sha[common] == other[common]:
                common += 1
            need = max(need, common + 1)
        return sha[:need]

    def file(self, key: str, area: str, folder: str, title: str, doc_date: str, force: bool = False) -> dict:
        archive = self.index.archive
        if not path_status(str(archive))["writable"]:
            raise InboxError("archive is read-only for filing")
        area = (area or "").strip()
        if not area or area not in self.area_names() or "/" in area or area.startswith((".", "_")):
            raise InboxError("unknown area")
        folder = (folder or "").strip().strip("/")
        if folder:
            try:
                folder = clean_path(folder)
            except FolderError as exc:
                raise InboxError(str(exc)) from exc
        title = clean_title(title)
        if not title:
            raise InboxError("title missing")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", doc_date or "") or not _valid(*map(int, doc_date.split("-"))):
            raise InboxError("invalid date")
        with self._file_lock:
            with self.connect() as con:
                row = con.execute("SELECT * FROM items WHERE key=?", (key,)).fetchone()
            if not row or row["status"] != "new":
                raise InboxError("unknown item")
            src, ext = self.path_of(key)
            if sha256_file(src) != row["sha256"]:
                raise InboxError("file changed – please reload")
            dup = self._archived(row["sha256"])
            if dup and not force:
                raise InboxError(f"already in the archive: {dup}")
            name = f"{doc_date}_{title}_{self._short_id(row['sha256'])}.{ext}"
            target_dir = archive / area / folder if folder else archive / area
            dest = target_dir / name
            if dest.exists():
                raise InboxError("target exists")
            tmp_dir = archive / ".ordnung-tmp"
            tmp_dir.mkdir(exist_ok=True)
            tmp = tmp_dir / (uuid.uuid4().hex + "." + ext)
            try:
                shutil.copyfile(src, tmp)
                os.chmod(tmp, 0o664)
                _makedirs(target_dir, archive)
                os.replace(tmp, dest)
            finally:
                tmp.unlink(missing_ok=True)
            # the text is known already: hand it to the archive index, no second OCR
            if row["body"] is not None:
                self.index.store_text(row["sha256"], SimpleNamespace(
                    text=row["body"], pages=row["pages"], ocr_pages=row["ocr_pages"],
                    method=row["method"] or "text", error=row["error"]))
            rel_dest = dest.relative_to(archive).as_posix()
            self._recent[row["sha256"]] = rel_dest
            moved = self._after_import(row, src)
            with self.connect() as con:
                if moved:
                    con.execute("DELETE FROM items WHERE key=?", (key,))
                else:
                    con.execute("UPDATE items SET status='filed', filed_path=? WHERE key=?", (rel_dest, key))
        sugg = json.loads(row["sugg"]) if row["sugg"] else {}
        return {"path": rel_dest, "moved": moved, "sha256": row["sha256"],
                "learn": folder != (sugg.get("folder") or "") or "rule" not in (sugg.get("source") or "")}

    def _after_import(self, row: sqlite3.Row, src: Path) -> bool:
        inbox = next((i for i in self.inboxes(False) if i.id == row["inbox"]), None)
        if inbox and inbox.id == "upload":
            # an upload has done its job once the archive holds the copy
            try:
                src.unlink()
                return True
            except OSError:
                return False
        if not inbox or inbox.after_import != "move" or not path_status(inbox.path)["writable"]:
            return False
        dest = Path(inbox.path) / DONE_DIR / row["rel"]
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                dest = dest.with_name(f"{dest.stem}_{row['sha256'][:6]}{dest.suffix}")
            os.replace(src, dest)
        except OSError:
            return False
        return True

    def dismiss(self, key: str, dismissed: bool = True) -> None:
        with self.connect() as con:
            changed = con.execute("UPDATE items SET status=? WHERE key=? AND status IN ('new', 'dismissed')",
                                  ("dismissed" if dismissed else "new", key)).rowcount
        if not changed:
            raise InboxError("unknown item")

    def delete(self, key: str) -> None:
        """Delete junk for good: the file in the inbox and its entry (not for filed items)."""
        with self.connect() as con:
            row = con.execute("SELECT status FROM items WHERE key=?", (key,)).fetchone()
        if not row or row["status"] not in ("new", "dismissed"):
            raise InboxError("unknown item")
        try:
            path, _ = self.path_of(key)
        except InboxError:
            path = None                     # already gone from the disk: just forget it
        if path is not None:
            try:
                path.unlink()
            except OSError as exc:
                raise InboxError("cannot delete") from exc
        with self.connect() as con:
            con.execute("DELETE FROM items WHERE key=?", (key,))

    def file_all(self, mode: str = "agree") -> dict:
        """File every item with a complete suggestion; ``agree`` only where rule and folder agree."""
        filed, failed = 0, []
        for item in self.items():
            s = item["suggestion"] or {}
            if s.get("duplicate") or not s.get("area") or not s.get("folder"):
                continue
            if mode == "agree" and s.get("source", "").split("+")[:2] != ["rule", "folder"]:
                continue
            if mode == "agree" and s.get("conflict"):
                continue
            try:
                self.file(item["key"], s["area"], s["folder"], s.get("title") or s["title_fallback"],
                          s.get("date") or s["date_fallback"])
                filed += 1
            except InboxError as exc:
                failed.append({"name": item["name"], "error": str(exc)})
        return {"filed": filed, "failed": failed[:20]}


def _makedirs(path: Path, root: Path) -> None:
    """Create missing folders below ``root`` with group write access (SMB users)."""
    missing = []
    p = path
    while not p.exists() and p != root:
        missing.append(p)
        p = p.parent
    for d in reversed(missing):
        try:
            d.mkdir()
            os.chmod(d, 0o775)
        except FileExistsError:
            pass


def _parse_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise InboxError("AI answer contained no JSON")
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise InboxError("AI answer was not valid JSON") from exc
    if not isinstance(data, dict):
        raise InboxError("AI answer was not an object")
    return data


MAX_INSTRUCTIONS = 6000

# the task as the user sees and may edit it (Posteingang → KI fragen)
def inbox_prompts(config) -> tuple[list[dict], str]:
    """The named instructions for "KI fragen" and the default's name.

    Before there was a list there was one optional text; it becomes "Standard"
    (the built-in text when it was empty).
    """
    prompts = [dict(p) for p in config.inbox_prompts]
    if not prompts:
        prompts = [{"name": "Standard", "text": config.inbox_prompt.strip() or AI_INSTRUCTIONS}]
    names = {p["name"].casefold(): p["name"] for p in prompts}
    default = names.get((config.inbox_default or "").casefold(), prompts[0]["name"])
    return prompts, default


def pick_prompt(config, name: str | None = None) -> dict:
    prompts, default = inbox_prompts(config)
    wanted = (name or default).casefold()
    found = next((p for p in prompts if p["name"].casefold() == wanted), None)
    if found is None:
        raise InboxError("unknown instruction")
    return found


AI_INSTRUCTIONS = """Du sortierst Dokumente eines Familienarchivs (meist deutsche Briefe, Rechnungen, Verträge und Kontoauszüge). Du bekommst den Dateinamen, die Ordnerliste des Archivs und den Anfang des Dokumenttextes.

Wähle den einen Ordner, in den das Dokument gehört. Nimm einen vorhandenen Ordner; schlage nur dann einen neuen vor (als sinnvollen Unterordner eines vorhandenen), wenn wirklich keiner passt.

Gib außerdem einen kurzen deutschen Titel, so wie man das Dokument in einem Ordner beschriften würde: Art des Dokuments und worum es geht, ohne Datum und ohne den Ordnernamen zu wiederholen (z. B. „Beitragsrechnung 2026“, „Kündigungsbestätigung Mobilfunkvertrag“, „Arztbrief Dr. Müller“).

Und das Dokumentdatum: der Tag, an dem das Schreiben verfasst oder ausgestellt wurde – kein Geburtsdatum, keine Frist."""

# fixed, always appended – keeps the answer machine-readable whatever the user wrote above
AI_FORMAT = """Answer with JSON only, no prose:
{"folder": "Path/From/The/List", "title": "...", "date": "YYYY-MM-DD or empty", "reason": "short German explanation"}"""
