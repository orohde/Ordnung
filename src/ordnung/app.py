"""FastAPI application: REST API and web UI."""

from __future__ import annotations

import base64
import binascii
import functools
import re
import shutil
import logging
import os
import sqlite3
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .ai import AIError, AIService
from .auth import COOKIE, SESSION_DAYS, User, current_user, make_session, require_admin
from .config import Settings, load_settings
from .docops import DocOpError
from .docops import move as move_doc
from .docops import rename as rename_doc
from .docops import purge_trash, trash_file, trash_list
from .docops import restore as restore_doc
from .docops import trash as trash_doc
from .editor import EditorError, SignatureStore, save_beside
from .index import Index
from .textextract import extract, render_thumb, tesseract_available
from .folders import STARTER_HOUSEHOLD, FolderError, FolderTemplate
from .importplan import ImportPlanner
from .inbox import AI_INSTRUCTIONS, InboxError, InboxService, inbox_prompts
from .prefs import PrefsStore
from .rules import RuleError, RuleService, check_conditions
from .senders import SenderBook, SenderService, describe
from .tags import TagError, TagStore
from .tags import clean as clean_tag
from .storage import StorageError, StorageService, path_status
from .users import UserError, UserStore

log = logging.getLogger("ordnung")
STATIC = Path(__file__).parent / "static"

MEDIA_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "txt": "text/plain; charset=utf-8",
}


class EditedIn(BaseModel):
    pdf: str = Field(max_length=120_000_000)        # base64
    title: str = Field(max_length=200)
    date: str | None = None
    text: str = Field(default="", max_length=50_000)
    keep_tags: bool = True


class UploadFile(BaseModel):
    name: str = Field(max_length=255)
    data: str = Field(max_length=90_000_000)      # base64


class UploadIn(BaseModel):
    files: list[UploadFile] = Field(min_length=1, max_length=30)
    combine: bool = False


class AreaIn(BaseModel):
    name: str = Field(max_length=40)
    label: str = Field(default="", max_length=40)


class MoveIn(BaseModel):
    folder: str = Field(max_length=1000)


class DocMetaIn(BaseModel):
    title: str = Field(max_length=200)
    date: str = Field(max_length=10)


class RestoreIn(BaseModel):
    trash_path: str = Field(max_length=2000)


class Login(BaseModel):
    username: str
    password: str


class TreePrefs(BaseModel):
    tree_open: list[str] | None = Field(None, max_length=5000)
    language: str | None = Field(None, max_length=5)


class NewUser(BaseModel):
    name: str
    password: str
    display_name: str = ""
    is_admin: bool = False
    areas: dict[str, str] = Field(default_factory=dict)


class UserChange(BaseModel):
    display_name: str | None = None
    password: str | None = None
    is_admin: bool | None = None
    areas: dict[str, str] | None = None


class AIChange(BaseModel):
    enabled: bool | None = None
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    clear_key: bool = False
    monthly_limit_usd: float | None = Field(None, ge=0)
    excluded_areas: list[str] | None = None
    inbox_auto: bool | None = None
    inbox_prompt: str | None = Field(None, max_length=6000)
    inbox_prompts: list[dict] | None = None
    inbox_default: str | None = Field(None, max_length=60)


class InboxAIIn(BaseModel):
    instructions: str | None = Field(None, max_length=6000)   # one-off text (API)
    prompt: str | None = Field(None, max_length=60)           # name of a saved instruction


class InboxIn(BaseModel):
    id: str | None = None
    name: str = ""
    path: str
    area: str = ""
    enabled: bool = False
    after_import: str = "move"


class StorageChange(BaseModel):
    archive_path: str | None = None
    reference_path: str | None = None
    inboxes: list[InboxIn] | None = None
    area_labels: dict[str, str] | None = None
    trash_days: int | None = None


class MappeIn(BaseModel):
    name: str = Field(max_length=60)
    area: str = Field(max_length=64)


class MappeChange(BaseModel):
    old: str = Field(max_length=60)
    new: str | None = Field(None, max_length=60)
    area: str | None = Field(None, max_length=64)


class ConditionIn(BaseModel):
    type: str
    value: str


class RuleIn(BaseModel):
    folder: str
    conditions: list[ConditionIn]
    source: str = "manual"
    note: str = ""
    label: str = ""


class SenderChange(BaseModel):
    name: str | None = None
    own: bool | None = None


class DeclineIn(BaseModel):
    folder: str


class RuleChange(BaseModel):
    conditions: list[ConditionIn] | None = None
    enabled: bool | None = None
    note: str | None = None
    folder: str | None = None


class FolderCardIn(BaseModel):
    folder: str
    description: str = ""


class EvaluateIn(BaseModel):
    folder: str
    conditions: list[ConditionIn]


class PlanRowIn(BaseModel):
    area: str
    folder: str
    target_area: str
    target_folder: str
    confirmed: bool = True


class FolderIn(BaseModel):
    path: str


class FolderRename(BaseModel):
    old: str
    new: str


class ArchiveSwitch(BaseModel):
    archive_path: str


class FileIn(BaseModel):
    area: str
    folder: str = ""
    title: str
    date: str
    force: bool = False
    tags: list[str] = Field(default_factory=list)


class TagsIn(BaseModel):
    tags: list[str]


class TagChangeIn(BaseModel):
    ids: list[str] = Field(max_length=5000)
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)


class DismissIn(BaseModel):
    dismissed: bool = True


class FileAllIn(BaseModel):
    mode: str = "agree"


class PasswordChange(BaseModel):
    old: str
    new: str


INBOX_SECONDS = 60


def _worker(app: FastAPI, stop: threading.Event) -> None:
    """Scan archive and learning set, work through the text queue, watch the inboxes."""
    settings: Settings = app.state.settings
    extractor = app.state.extractor
    try:
        os.nice(5)  # text recognition must not slow down the UI
    except OSError:
        pass
    last_full = 0.0
    while not stop.is_set():
        full = app.state.full_scan.is_set() or time.time() - last_full >= max(1, settings.rescan_minutes) * 60
        try:
            if full:
                app.state.full_scan.clear()
                last_full = time.time()
                index: Index = app.state.index
                log.info("scan: %s", index.scan())
                done = index.extract_pending(extractor, stop=stop, workers=settings.text_workers)
                if done:
                    log.info("texts extracted: %s, status %s", done, index.text_status())
                reference: Index | None = app.state.reference
                # an empty or missing learning-set folder (mount removed) must not wipe its index
                if reference is not None and reference.archive.is_dir() and any(reference.archive.iterdir()):
                    log.info("learning set: %s", reference.scan())
                    reference.extract_pending(extractor, stop=stop, workers=settings.text_workers)
            inbox: InboxService = app.state.inbox
            result = inbox.scan()
            if result.get("added"):
                log.info("inbox: %s", result)
            inbox.extract_pending(extractor, stop=stop)
            inbox.refresh()
            asked = inbox.auto_ai(app.state.ai)
            if asked:
                log.info("inbox: asked the AI for %s documents", asked)
        except Exception:  # noqa: BLE001 - keep the loop alive
            log.exception("background work failed")
        if settings.rescan_minutes <= 0:
            return
        # once a day: empty what has been in the trash longer than the set number of days
        today = time.strftime("%Y-%m-%d")
        if app.state.last_purge != today:
            app.state.last_purge = today
            try:
                days = app.state.storage.load().trash_days
                removed = purge_trash(app.state.index.archive, days)
                if removed:
                    log.info("trash: %d file(s) older than %d days deleted", removed, days)
            except Exception:  # noqa: BLE001
                log.exception("emptying the trash failed")
        app.state.wake.wait(INBOX_SECONDS)
        app.state.wake.clear()


def create_app(settings: Settings | None = None, background: bool = True) -> FastAPI:
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        stop = threading.Event()
        if background:
            threading.Thread(target=_worker, args=(app, stop), daemon=True).start()
        yield
        stop.set()
        app.state.wake.set()

    app = FastAPI(
        title="Ordnung!",
        version=__version__,
        description="Folder-based document archive",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.settings = settings
    extra_roots = [r for r in os.environ.get("ORDNUNG_BROWSE_ROOTS", "").split(",") if r]
    app.state.storage = StorageService(settings.data / "storage.json", settings.archive, extra_roots)
    app.state.index = Index(settings.db_path, app.state.storage.archive())
    app.state.users = UserStore(settings.users_path)
    app.state.wake = threading.Event()
    app.state.ai = AIService(settings.data / "ai.json")
    app.state.rules = RuleService(settings.data / "rules.json", app.state.index)
    app.state.tags = TagStore(settings.data / "tags.json")
    app.state.prefs = PrefsStore(settings.data / "prefs.json")
    app.state.signatures = SignatureStore(settings.data / "signatures")
    app.state.senders = SenderService(SenderBook(settings.data / "senders.json"), app.state.rules)
    app.state.importplan = ImportPlanner(settings.data / "import-plan.json", app.state.index)
    app.state.folders = FolderTemplate(settings.data / "folders.json", app.state.index)
    app.state.inbox = InboxService(settings.data / "inbox.db", app.state.storage, app.state.index,
                                   app.state.rules, app.state.folders, app.state.importplan,
                                   upload_dir=settings.data / "hochgeladen")
    app.state.last_purge = ""
    app.state.full_scan = threading.Event()
    app.state.full_scan.set()
    app.state.reference = None
    app.state.extractor = functools.partial(
        extract, ocr=settings.ocr, lang=settings.ocr_lang, max_ocr_pages=settings.ocr_max_pages)
    reference_db = settings.data / "reference.db"

    def set_reference(path: str | None) -> None:
        """Use (or stop using) a learning set: rules, import plan and inbox see it."""
        ref = None
        if path:
            ref = app.state.reference if app.state.reference is not None else Index(reference_db, Path(path))
            ref.archive = Path(path)
        app.state.reference = ref
        app.state.rules.reference = ref
        app.state.inbox.reference = ref
        app.state.importplan.index = ref if ref is not None else app.state.index
        app.state.rules.invalidate()

    app.state.rules.mapping = app.state.importplan.mapping
    set_reference(app.state.storage.load().reference_path or None)

    def kick(full: bool = True) -> None:
        if full:
            app.state.full_scan.set()
        app.state.wake.set()
    if settings.starter and not app.state.rules.path.exists():
        # first start: the shipped folder structure and rules
        if not app.state.folders.path.exists():
            app.state.folders.include(STARTER_HOUSEHOLD)
        log.info("first start: %s standard rules installed", app.state.rules.install_starter())
    if app.state.users.bootstrap(settings.admin_user, settings.admin_password):
        log.info("created first administrator %r from the environment", settings.admin_user)

    def area_label(name: str) -> str:
        """Display name of an area: own label, else the matching account, else capitalised."""
        if not name:
            return ""
        custom = app.state.storage.load().area_labels.get(name)
        if custom:
            return custom
        account = app.state.users.get(name)
        if account and account.display_name and account.display_name != account.name:
            return account.display_name
        return name[:1].upper() + name[1:]

    def allowed_areas(user: User) -> list[str]:
        return [a["name"] for a in app.state.index.areas() if user.can_read(a["name"])]

    def pick_areas(user: User, wanted: str | None) -> list[str]:
        allowed = allowed_areas(user)
        if not wanted:
            return allowed
        chosen = set(wanted.split(","))
        return [a for a in allowed if a in chosen]

    # ----------------------------------------------------------- public

    @app.get("/api/version", tags=["system"])
    def version():
        return {"name": "Ordnung!", "version": __version__}

    @app.post("/api/login", tags=["auth"])
    def login(body: Login, request: Request, response: Response):
        account = app.state.users.authenticate(body.username.strip().lower(), body.password)
        if not account:
            time.sleep(1)
            raise HTTPException(status_code=401, detail="invalid credentials")
        secure = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
        response.set_cookie(
            COOKIE, make_session(settings, account.name), max_age=SESSION_DAYS * 86400,
            httponly=True, samesite="lax", secure=secure,
        )
        return account.public()

    @app.post("/api/logout", tags=["auth"])
    def logout(response: Response):
        response.delete_cookie(COOKIE)
        return {"ok": True}

    # ------------------------------------------------------ authenticated

    @app.get("/api/me", tags=["auth"])
    def me(user: User = Depends(current_user)):
        return {"name": user.name, "display_name": user.display_name,
                "is_admin": user.is_admin, "areas": allowed_areas(user),
                "write_areas": [a for a in allowed_areas(user) if user.can_write(a)],
                "signature": app.state.signatures.get(user.name) is not None,
                "language": app.state.prefs.get(user.name)["language"]}

    @app.get("/api/me/signature", tags=["editor"])
    def my_signature(user: User = Depends(current_user)):
        path = app.state.signatures.get(user.name)
        if not path:
            raise HTTPException(status_code=404, detail="no signature")
        return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-store"})

    @app.put("/api/me/signature", tags=["editor"])
    async def put_my_signature(request: Request, user: User = Depends(current_user)):
        data = await request.body()
        try:
            app.state.signatures.put(user.name, data)
        except EditorError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True}

    @app.delete("/api/me/signature", tags=["editor"])
    def delete_my_signature(user: User = Depends(current_user)):
        app.state.signatures.delete(user.name)
        return {"ok": True}

    @app.get("/api/me/prefs", tags=["auth"])
    def my_prefs(user: User = Depends(current_user)):
        return app.state.prefs.get(user.name)

    @app.put("/api/me/prefs", tags=["auth"])
    def put_my_prefs(body: TreePrefs, user: User = Depends(current_user)):
        if body.language is not None:
            try:
                app.state.prefs.set_language(user.name, body.language)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        if body.tree_open is not None:
            app.state.prefs.set_tree_open(user.name, body.tree_open)
        return app.state.prefs.get(user.name)

    @app.post("/api/me/password", tags=["auth"])
    def change_own_password(body: PasswordChange, user: User = Depends(current_user)):
        if not app.state.users.authenticate(user.name, body.old):
            raise HTTPException(status_code=403, detail="wrong password")
        try:
            app.state.users.update(user.name, password=body.new)
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True}

    @app.get("/api/status", tags=["system"])
    def status(user: User = Depends(current_user)):
        writable = path_status(str(app.state.index.archive))["writable"]
        return {**app.state.index.meta(), "readonly": not writable, "version": __version__,
                "ocr": settings.ocr and tesseract_available(),
                "inbox": app.state.inbox.counts() if user.is_admin else None,
                "reference": app.state.reference.meta() if app.state.reference is not None and user.is_admin else None}

    @app.get("/api/text-errors", tags=["system"])
    def text_errors(user: User = Depends(current_user)):
        """Documents whose text could not be read (password, damaged file …)."""
        return {"items": app.state.index.text_errors(allowed_areas(user))}

    @app.post("/api/text-errors/retry", tags=["system"])
    def text_errors_retry(user: User = Depends(require_admin)):
        n = app.state.index.retry_text_errors()
        kick()
        return {"retried": n}

    @app.post("/api/rescan", tags=["system"])
    def rescan(user: User = Depends(require_admin)):
        kick()
        return {"started": True}

    @app.get("/api/areas", tags=["archive"])
    def areas(user: User = Depends(current_user)):
        return [{**a, "label": area_label(a["name"])}
                for a in app.state.index.areas() if user.can_read(a["name"])]

    @app.post("/api/areas", tags=["archive"], status_code=201)
    def area_create(body: AreaIn, user: User = Depends(require_admin)):
        """A new area: a top folder in the archive that belongs to no account; members get rights per area."""
        name = body.name.strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,39}", name):
            raise HTTPException(status_code=400, detail="invalid area name")
        archive = app.state.index.archive
        if not path_status(str(archive))["writable"]:
            raise HTTPException(status_code=400, detail="archive is read-only")
        if any(a["name"].lower() == name for a in app.state.index.areas()):
            raise HTTPException(status_code=409, detail="area exists")
        (archive / name).mkdir()
        os.chmod(archive / name, 0o775)
        if body.label.strip():
            labels = {**app.state.storage.load().area_labels, name: body.label.strip()}
            app.state.storage.update(None, None, labels)
        return {"name": name, "label": area_label(name)}

    @app.delete("/api/areas/{name}", tags=["archive"])
    def area_delete(name: str, user: User = Depends(require_admin)):
        """Remove an area – only while it holds no documents (empty subfolders are fine)."""
        archive = app.state.index.archive
        if not any(a["name"] == name for a in app.state.index.areas()) or name.startswith((".", "_")) or "/" in name:
            raise HTTPException(status_code=404, detail="unknown area")
        if next((a for a in app.state.index.areas() if a["name"] == name), {}).get("count"):
            raise HTTPException(status_code=409, detail="area contains documents")
        target = archive / name
        if any(p.is_file() for p in target.rglob("*")):
            raise HTTPException(status_code=409, detail="area contains documents")
        shutil.rmtree(target)
        return {"ok": True}

    @app.get("/api/tree", tags=["archive"])
    def tree(areas: str | None = Query(None, description="comma-separated areas"),
             template: bool = Query(False, description="include empty template folders (admins)"),
             user: User = Depends(current_user)):
        # the shared folder template is shown to everyone, empty folders included
        extra = app.state.folders.template_only()
        return app.state.index.tree(pick_areas(user, areas), extra)

    @app.get("/api/documents", tags=["archive"])
    def documents(
        folder: str = "",
        recursive: bool = False,
        q: str = "",
        areas: str | None = Query(None, description="comma-separated areas"),
        tags: str | None = Query(None, description="comma-separated tags, all must be present"),
        limit: int = Query(500, ge=1, le=5000),
        offset: int = Query(0, ge=0),
        user: User = Depends(current_user),
    ):
        store = app.state.tags
        # "#steuer2026" in the search, or tags=… from the tag list: documents carrying all of them
        wanted = [t for t in (tags or "").split(",") if t.strip()]
        words = []
        for word in q.split():
            if word.startswith("#") and len(word) > 1:
                key = word[1:].casefold()
                match = next((x["name"] for x in store.counts() if x["name"].casefold().replace(" ", "") == key), None)
                wanted.append(match or word[1:])
            else:
                words.append(word)
        shas = store.shas_with_all(wanted) if wanted else None
        result = app.state.index.documents(
            pick_areas(user, areas), folder="" if wanted and not folder else folder,
            recursive=recursive or bool(wanted), query=" ".join(words), limit=limit, offset=offset, shas=shas,
        )
        tagmap = store.mapping()
        hidden = store.hidden_for(user.can_read)
        for item in result["items"]:
            item["tags"] = [t for t in tagmap.get(item["sha256"], []) if t.casefold() not in hidden]
        return result

    def _doc_or_404(doc_id: str, user: User) -> dict:
        doc = app.state.index.document(doc_id, allowed_areas(user))
        if not doc:
            raise HTTPException(status_code=404, detail="document not found")
        hidden = app.state.tags.hidden_for(user.can_read)
        doc["tags"] = [t for t in app.state.tags.of(doc["sha256"]) if t.casefold() not in hidden]
        return doc

    # ------------------------------------------------------------- tags

    @app.get("/api/tags", tags=["tags"])
    def tag_list(areas: str | None = Query(None), user: User = Depends(current_user)):
        """Tags with the number of visible documents carrying them."""
        # Mappen have their own list in the sidebar, so they are not repeated as tags
        mappen = {m["name"].casefold() for m in app.state.tags.mappen()}
        return [t for t in app.state.tags.counts(app.state.index.shas(pick_areas(user, areas)))
                if t["name"].casefold() not in mappen]

    @app.put("/api/documents/{doc_id}/tags", tags=["tags"])
    def document_tags(doc_id: str, body: TagsIn, user: User = Depends(current_user)):
        doc = _doc_or_404(doc_id, user)
        if not user.can_write(doc["area"]):
            raise HTTPException(status_code=403, detail="no write access")
        try:
            # labels of Mappen this user cannot see stay untouched
            hidden = app.state.tags.hidden_for(user.can_read)
            keep = [t for t in app.state.tags.of(doc["sha256"]) if t.casefold() in hidden]
            tags = app.state.tags.set(doc["sha256"], [*body.tags, *keep])
            return {"tags": [t for t in tags if t.casefold() not in hidden]}
        except TagError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/tags/change", tags=["tags"])
    def tags_change(body: TagChangeIn, user: User = Depends(current_user)):
        """Add and/or remove tags on many documents at once."""
        writable = [a for a in allowed_areas(user) if user.can_write(a)]
        shas = []
        for doc_id in body.ids:
            doc = app.state.index.document(doc_id, writable)
            if not doc:
                raise HTTPException(status_code=404, detail="document not found")
            shas.append(doc["sha256"])
        try:
            return {"changed": app.state.tags.change(shas, body.add, body.remove)}
        except TagError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/documents/{doc_id}", tags=["archive"])
    def document(doc_id: str, user: User = Depends(current_user)):
        return _doc_or_404(doc_id, user)

    @app.get("/api/documents/{doc_id}/text", tags=["archive"], response_class=PlainTextResponse)
    def document_text(doc_id: str, user: User = Depends(current_user)):
        doc = _doc_or_404(doc_id, user)
        return app.state.index.document_text(doc["sha256"])

    @app.get("/api/documents/{doc_id}/file", tags=["archive"])
    def document_file(doc_id: str, download: bool = False, user: User = Depends(current_user)):
        doc = _doc_or_404(doc_id, user)
        root = app.state.index.archive.resolve()
        path = (root / doc["path"]).resolve()
        if root not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        return FileResponse(
            path,
            media_type=MEDIA_TYPES.get(doc["ext"], "application/octet-stream"),
            filename=doc["name"],
            content_disposition_type="attachment" if download else "inline",
        )

    def _writable_doc(doc_id: str, user: User) -> dict:
        doc = _doc_or_404(doc_id, user)
        if not user.can_write(doc["area"]):
            raise HTTPException(status_code=403, detail="no write access to this area")
        return doc

    def _rescan() -> None:
        kick()                      # worker: read the text of new or restored files right away
        if not app.state.index.scan().get("started"):
            def later():
                time.sleep(3)
                app.state.index.scan()
            threading.Thread(target=later, daemon=True).start()

    @app.post("/api/documents/{doc_id}/move", tags=["archive"])
    def document_move(doc_id: str, body: MoveIn, user: User = Depends(current_user)):
        """Move a document into another folder of its area (drag and drop in the tree)."""
        doc = _writable_doc(doc_id, user)
        try:
            path = move_doc(app.state.index.archive, doc, body.folder)
        except (DocOpError, OSError) as exc:
            raise HTTPException(status_code=409 if "exists" in str(exc) else 400, detail=str(exc)) from exc
        _rescan()
        return {"path": path, "id": doc["id"]}

    @app.post("/api/documents/{doc_id}/trash", tags=["archive"])
    def document_trash(doc_id: str, user: User = Depends(current_user)):
        """Move a document to the trash (``.papierkorb`` in the archive). Never deletes for good."""
        doc = _writable_doc(doc_id, user)
        try:
            path = trash_doc(app.state.index.archive, doc)
        except (DocOpError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        _rescan()
        return {"trash_path": path}

    @app.patch("/api/documents/{doc_id}", tags=["archive"])
    def document_meta(doc_id: str, body: DocMetaIn, user: User = Depends(current_user)):
        """Change title and date – they live in the file name, so this renames the file."""
        doc = _writable_doc(doc_id, user)
        try:
            path = rename_doc(app.state.index.archive, doc, body.title, body.date)
        except (DocOpError, OSError) as exc:
            raise HTTPException(status_code=409 if "exists" in str(exc) else 400, detail=str(exc)) from exc
        _rescan()
        return {"path": path, "id": doc["id"]}

    @app.get("/api/trash", tags=["archive"])
    def trash_items(user: User = Depends(current_user)):
        return {"items": trash_list(app.state.index.archive, user.can_read),
                "days": app.state.storage.load().trash_days}

    # ----------------------------------------------------------- Mappen

    def _tag_error(exc: TagError):
        return HTTPException(status_code=409 if "exists" in str(exc) else 400, detail=str(exc))

    def _visible_mappe(name: str, user: User, write: bool = False) -> dict:
        m = app.state.tags.mappe(name)
        if not m or not user.can_read(m["area"]):
            raise HTTPException(status_code=404, detail="unknown mappe")
        if write and not user.can_write(m["area"]):
            raise HTTPException(status_code=403, detail="no write access to this area")
        return m

    def _mappe_area(area: str, user: User) -> str:
        area = (area or "").strip()
        known = {a["name"] for a in app.state.index.areas() if a["name"]} | app.state.inbox.area_names()
        if area not in known:
            raise HTTPException(status_code=400, detail="unknown area")
        if not user.can_write(area):
            raise HTTPException(status_code=403, detail="no write access to this area")
        return area

    @app.get("/api/mappen", tags=["tags"])
    def mappen_list(areas: str | None = Query(None), user: User = Depends(current_user)):
        """Collections ("Steuererklärung 2026") the user may see, with visible document counts."""
        shown = pick_areas(user, areas)
        counts = {t["name"].casefold(): t["count"] for t in
                  app.state.tags.counts(app.state.index.shas(shown))}
        return [{**m, "count": counts.get(m["name"].casefold(), 0), "writable": user.can_write(m["area"])}
                for m in sorted(app.state.tags.mappen(), key=lambda m: m["name"].casefold())
                if user.can_read(m["area"]) and (not areas or m["area"] in shown)]

    @app.post("/api/mappen", tags=["tags"], status_code=201)
    def mappen_add(body: MappeIn, user: User = Depends(current_user)):
        area = _mappe_area(body.area, user)
        try:
            return {"name": app.state.tags.add_mappe(body.name, area), "area": area}
        except TagError as exc:
            raise _tag_error(exc) from exc

    @app.patch("/api/mappen", tags=["tags"])
    def mappen_change(body: MappeChange, user: User = Depends(current_user)):
        """Rename a Mappe and/or give it to another area."""
        m = _visible_mappe(body.old, user, write=True)
        changed = 0
        if body.area is not None and body.area != m["area"]:
            app.state.tags.set_mappe_area(m["name"], _mappe_area(body.area, user))
        if body.new and body.new.strip() != m["name"]:
            try:
                changed = app.state.tags.rename_tag(m["name"], body.new)
            except TagError as exc:
                raise _tag_error(exc) from exc
        return {"changed": changed}

    @app.delete("/api/mappen", tags=["tags"])
    def mappen_delete(name: str, user: User = Depends(current_user)):
        """Dissolve a Mappe. No document is touched, they only lose the label."""
        m = _visible_mappe(name, user, write=True)
        return {"changed": app.state.tags.remove_mappe(m["name"])}

    @app.get("/api/mappen/download", tags=["tags"])
    def mappen_download(name: str, format: str = Query("zip", pattern="^(zip|pdf)$"),
                        user: User = Depends(current_user)):
        """All documents of a Mappe as ZIP, or as one PDF (sorted by date)."""
        from .mappen import bundle_pdf, bundle_zip

        _visible_mappe(name, user)
        shas = app.state.tags.shas_with_all([name])
        docs = [d for d in app.state.index.documents(allowed_areas(user), recursive=True, limit=5000,
                                                     shas=shas)["items"]]
        if not docs:
            raise HTTPException(status_code=404, detail="mappe is empty")
        seen, unique = set(), []
        for d in sorted(docs, key=lambda d: (d["date"] or "", d["title"].casefold())):
            if d["sha256"] not in seen:
                seen.add(d["sha256"])
                unique.append(d)
        root = app.state.index.archive
        safe = "".join(c if c.isalnum() or c in " -_." else "_" for c in name).strip() or "Mappe"
        try:
            data = bundle_pdf(root, unique) if format == "pdf" else bundle_zip(root, unique)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        media = "application/pdf" if format == "pdf" else "application/zip"
        from urllib.parse import quote
        return Response(data, media_type=media, headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe + '.' + format)}"})

    @app.get("/api/trash/file", tags=["archive"])
    def trash_get_file(path: str, user: User = Depends(current_user)):
        try:
            full = trash_file(app.state.index.archive, path, user.can_read)
        except DocOpError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        ext = full.suffix.lstrip(".").lower()
        return FileResponse(full, media_type=MEDIA_TYPES.get(ext, "application/octet-stream"),
                            filename=full.name, content_disposition_type="inline")

    @app.post("/api/trash/restore", tags=["archive"])
    def trash_restore(body: RestoreIn, user: User = Depends(current_user)):
        try:
            path = restore_doc(app.state.index.archive, body.trash_path,
                               user.can_write)  # the area may have vanished with its last document
        except (DocOpError, OSError) as exc:
            raise HTTPException(status_code=409 if "exists" in str(exc) else 400, detail=str(exc)) from exc
        _rescan()
        return {"path": path}

    @app.post("/api/documents/{doc_id}/edited", tags=["editor"], status_code=201)
    def document_edited(doc_id: str, body: EditedIn, user: User = Depends(current_user)):
        """Store a PDF edited in the browser next to the original (which stays as it is)."""
        doc = _writable_doc(doc_id, user)
        if doc["ext"] != "pdf":
            raise HTTPException(status_code=400, detail="only PDFs can be edited")
        try:
            data = base64.b64decode(body.pdf, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=400, detail="invalid data") from exc
        try:
            result = save_beside(app.state.index, app.state.inbox, doc, data, body.title, body.date, body.text)
        except (EditorError, OSError) as exc:
            raise HTTPException(status_code=409 if "already" in str(exc) or "exists" in str(exc) else 400,
                                detail=str(exc)) from exc
        if body.keep_tags and doc.get("tags"):
            app.state.tags.change([result["sha256"]], doc["tags"], [])
        _rescan()
        result["id"] = result["sha256"][:12]
        return result

    # ------------------------------------------------------------ admin

    @app.get("/api/users", tags=["users"])
    def list_users(user: User = Depends(require_admin)):
        return [u.public() for u in app.state.users.all()]

    @app.post("/api/users", tags=["users"], status_code=201)
    def create_user(body: NewUser, user: User = Depends(require_admin)):
        try:
            return app.state.users.create(**body.model_dump()).public()
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/api/users/{name}", tags=["users"])
    def update_user(name: str, body: UserChange, user: User = Depends(require_admin)):
        if name == user.name and body.is_admin is False:
            raise HTTPException(status_code=400, detail="cannot remove your own admin role")
        try:
            return app.state.users.update(name, **body.model_dump(exclude_unset=True)).public()
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/users/{name}", tags=["users"])
    def delete_user(name: str, user: User = Depends(require_admin)):
        if name == user.name:
            raise HTTPException(status_code=400, detail="cannot delete yourself")
        try:
            app.state.users.delete(name)
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        app.state.prefs.forget(name)
        return {"ok": True}

    @app.get("/api/storage", tags=["storage"])
    def get_storage(user: User = Depends(require_admin)):
        return app.state.storage.public()

    @app.put("/api/storage", tags=["storage"])
    def put_storage(body: StorageChange, user: User = Depends(require_admin)):
        try:
            config = app.state.storage.update(
                body.archive_path,
                [i.model_dump() for i in body.inboxes] if body.inboxes is not None else None,
                body.area_labels,
                body.reference_path,
                body.trash_days,
            )
        except StorageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        new_archive = Path(config.archive_path)
        if new_archive != app.state.index.archive:
            log.info("archive folder changed to %s, rescanning", new_archive)
            app.state.index.archive = new_archive
        current_ref = str(app.state.reference.archive) if app.state.reference is not None else ""
        if (config.reference_path or "") != current_ref:
            set_reference(config.reference_path or None)
        kick()
        return app.state.storage.public()

    @app.post("/api/storage/switch", tags=["storage"])
    def switch_archive(body: ArchiveSwitch, user: User = Depends(require_admin)):
        """Start a fresh archive; the current one becomes the learning set.

        The index of the current archive is kept as the learning set's index (no
        second text recognition), rules and folder cards move to the folder names
        of the import plan, and the plan's target folders become template folders.
        Nothing is copied or moved on disk.
        """
        index: Index = app.state.index
        old = index.archive
        new = Path(os.path.normpath(body.archive_path.strip() or "/"))
        if not body.archive_path.strip().startswith("/") or new == old:
            raise HTTPException(status_code=400, detail="choose a different absolute folder")
        if not path_status(str(new))["writable"]:
            raise HTTPException(status_code=400, detail="new archive folder must be writable")
        if str(new).startswith(str(old) + "/") or str(old).startswith(str(new) + "/"):
            raise HTTPException(status_code=400, detail="old and new archive must not overlap")
        if not index._scan_lock.acquire(timeout=600):
            raise HTTPException(status_code=409, detail="scan running, please try again")
        try:
            folder_map = app.state.importplan.folder_mapping()
            targets = {f for _a, f in app.state.importplan.mapping().values() if f}
            for suffix in ("", "-wal", "-shm"):
                Path(str(reference_db) + suffix).unlink(missing_ok=True)
            src, dst = sqlite3.connect(index.db_path), sqlite3.connect(reference_db)
            try:
                src.backup(dst)
            finally:
                src.close()
                dst.close()
            try:
                app.state.storage.update(str(new), None, None, reference_path=str(old))
            except StorageError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            app.state.reference = None
            set_reference(str(old))
            remapped = app.state.rules.remap(folder_map)
            added = app.state.folders.include(sorted(targets))
            index.archive = new
        finally:
            index._scan_lock.release()
        index.scan()
        app.state.rules.invalidate()
        kick()
        log.info("archive switched to %s, learning set %s", new, old)
        return {"archive_path": str(new), "reference_path": str(old), "rules_remapped": remapped,
                "folders_added": added}

    @app.get("/api/fs/roots", tags=["storage"])
    def fs_roots(user: User = Depends(require_admin)):
        return [{"path": r, "status": path_status(r)} for r in app.state.storage.roots()]

    @app.get("/api/fs/list", tags=["storage"])
    def fs_list(path: str, user: User = Depends(require_admin)):
        try:
            return app.state.storage.list_dir(path)
        except StorageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # ------------------------------------------------------------ rules

    def _rule_error(exc: RuleError):
        return HTTPException(status_code=400, detail=str(exc))

    @app.get("/api/rules", tags=["rules"])
    def rules_overview(user: User = Depends(require_admin)):
        return app.state.rules.overview()

    @app.get("/api/rules/folder", tags=["rules"])
    def rules_folder(path: str = "", user: User = Depends(require_admin)):
        view = app.state.rules.folder_view(path)
        names = app.state.senders.book.name
        for r in view["rules"]:
            r["plain"] = r.get("label") or describe(r["conditions"], names)
        return view

    @app.put("/api/rules/folder", tags=["rules"])
    def rules_folder_card(body: FolderCardIn, user: User = Depends(require_admin)):
        app.state.rules.set_description(body.folder, body.description)
        return {"ok": True}

    @app.post("/api/rules/evaluate", tags=["rules"])
    def rules_evaluate(body: EvaluateIn, user: User = Depends(require_admin)):
        try:
            conds = check_conditions([c.model_dump() for c in body.conditions])
        except RuleError as exc:
            raise _rule_error(exc) from exc
        return app.state.rules.evaluate(body.folder, conds)

    @app.get("/api/rules/suggest", tags=["rules"])
    def rules_suggest(path: str = "", user: User = Depends(require_admin)):
        return app.state.rules.suggest(path)

    @app.post("/api/rules/ai-suggest", tags=["rules"])
    def rules_ai_suggest(path: str = "", user: User = Depends(require_admin)):
        config = app.state.ai.load()
        try:
            return app.state.rules.ai_suggest(path, app.state.ai, config.excluded_areas)
        except (RuleError, AIError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/rules/generate", tags=["rules"])
    def rules_generate(user: User = Depends(require_admin)):
        if app.state.rules.generation.get("running"):
            return app.state.rules.generation

        def run():
            try:
                app.state.rules.generate_all()
            except Exception:  # noqa: BLE001
                log.exception("rule generation failed")
        threading.Thread(target=run, daemon=True).start()
        return {"running": True}

    @app.post("/api/rules/starter", tags=["rules"])
    def rules_starter(adapt: bool = True, dry_run: bool = False, user: User = Depends(require_admin)):
        """Shipped rules: adapted to this archive's folders, or as they are (adapt=false)."""
        if adapt:
            return app.state.rules.adapt_starter(dry_run=dry_run)
        return {"added": app.state.rules.install_starter(), "skipped": 0, "rules": []}

    @app.get("/api/rules/generate", tags=["rules"])
    def rules_generate_status(user: User = Depends(require_admin)):
        return app.state.rules.generation

    @app.post("/api/rules", tags=["rules"], status_code=201)
    def rules_create(body: RuleIn, user: User = Depends(require_admin)):
        try:
            rule = app.state.rules.create(body.folder, [c.model_dump() for c in body.conditions],
                                          source=body.source, note=body.note, label=body.label)
        except RuleError as exc:
            raise _rule_error(exc) from exc
        return {"id": rule.id}

    @app.patch("/api/rules/{rule_id}", tags=["rules"])
    def rules_update(rule_id: str, body: RuleChange, user: User = Depends(require_admin)):
        try:
            app.state.rules.update(
                rule_id,
                conditions=[c.model_dump() for c in body.conditions] if body.conditions is not None else None,
                enabled=body.enabled, note=body.note, folder=body.folder,
            )
        except RuleError as exc:
            raise _rule_error(exc) from exc
        return {"ok": True}

    @app.delete("/api/rules/{rule_id}", tags=["rules"])
    def rules_delete(rule_id: str, user: User = Depends(require_admin)):
        try:
            app.state.rules.delete(rule_id)
        except RuleError as exc:
            raise _rule_error(exc) from exc
        return {"ok": True}

    # ---------------------------------------------------------- folders

    @app.get("/api/folders", tags=["folders"])
    def folders_list(user: User = Depends(require_admin)):
        own = app.state.folders.on_disk()
        empty = app.state.folders.template_only()
        return {
            "folders": [{"path": f, "docs": own.get(f, 0), "template_only": f in empty}
                        for f in sorted(app.state.folders.effective(), key=lambda s: s.casefold())],
            "writable": path_status(str(app.state.index.archive))["writable"],
        }

    def _folder_error(exc: FolderError):
        return HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/folders", tags=["folders"], status_code=201)
    def folders_add(body: FolderIn, user: User = Depends(require_admin)):
        try:
            return {"path": app.state.folders.add(body.path)}
        except FolderError as exc:
            raise _folder_error(exc) from exc

    @app.post("/api/folders/starter", tags=["folders"])
    def folders_starter(user: User = Depends(require_admin)):
        return {"added": app.state.folders.add_many(STARTER_HOUSEHOLD)}

    @app.patch("/api/folders", tags=["folders"])
    def folders_rename(body: FolderRename, user: User = Depends(require_admin)):
        try:
            areas = [a["name"] for a in app.state.index.areas() if a["name"]]
            result = app.state.folders.rename(body.old, body.new, app.state.index.archive, areas)
        except (FolderError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        old, new = body.old.strip("/"), body.new.strip("/")
        result["rules"] = app.state.rules.rename_folder(old, new)
        app.state.importplan.rename_target(old, new)
        if result["moved_areas"]:
            app.state.index.scan()
        return result

    @app.delete("/api/folders", tags=["folders"])
    def folders_delete(path: str, user: User = Depends(require_admin)):
        try:
            app.state.folders.delete(path)
        except FolderError as exc:
            raise _folder_error(exc) from exc
        return {"ok": True}

    # ----------------------------------------------------------- import

    @app.get("/api/import/plan", tags=["import"])
    def import_plan(user: User = Depends(require_admin)):
        return app.state.importplan.view()

    @app.put("/api/import/plan/row", tags=["import"])
    def import_plan_row(body: PlanRowIn, user: User = Depends(require_admin)):
        try:
            app.state.importplan.decide(body.area, body.folder, body.target_area, body.target_folder, body.confirmed)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True}

    @app.delete("/api/import/plan/row", tags=["import"])
    def import_plan_reset(area: str, folder: str, user: User = Depends(require_admin)):
        app.state.importplan.reset(area, folder)
        return {"ok": True}

    @app.post("/api/import/plan/confirm-all", tags=["import"])
    def import_plan_confirm_all(user: User = Depends(require_admin)):
        return {"confirmed": app.state.importplan.confirm_all()}

    @app.get("/api/import/tree", tags=["import"])
    def import_tree(user: User = Depends(require_admin)):
        return app.state.importplan.target_tree()

    # ---------------------------------------------------------- senders

    @app.get("/api/senders", tags=["senders"])
    def senders_list(areas: str | None = Query(None), user: User = Depends(require_admin)):
        return {"senders": app.state.senders.overview(pick_areas(user, areas)),
                "own": sorted(app.state.senders.book.own())}

    @app.get("/api/senders/{domain}/documents", tags=["senders"])
    def sender_docs(domain: str, folder: str | None = None, areas: str | None = Query(None),
                    user: User = Depends(require_admin)):
        return app.state.senders.documents(domain, folder, pick_areas(user, areas))

    @app.get("/api/senders/{domain}/propose", tags=["senders"])
    def sender_propose(domain: str, folder: str, user: User = Depends(require_admin)):
        """A rule for this sender's post into ``folder``, built from its latest document there."""
        svc = app.state.senders
        docs = [d for d, _ in svc._by_sender()["senders"].get(domain, []) if d.folder == folder.strip("/")]
        docs.sort(key=lambda d: d.date or "", reverse=True)
        for d in docs[:5]:
            proposal = svc.propose(d.raw, folder, allowed_areas(user), sender=domain)
            if proposal:
                return proposal
        return None

    @app.patch("/api/senders/{domain}", tags=["senders"])
    def sender_change(domain: str, body: SenderChange, user: User = Depends(require_admin)):
        book = app.state.senders.book
        if body.name is not None:
            book.rename(domain, body.name)
        if body.own is not None:
            book.set_own(domain, body.own)
        return {"ok": True, "name": book.name(domain)}

    @app.post("/api/senders/{domain}/decline", tags=["senders"])
    def sender_decline(domain: str, body: DeclineIn, user: User = Depends(require_admin)):
        app.state.senders.book.decline(domain, body.folder.strip("/"))
        return {"ok": True}

    @app.get("/api/documents/{doc_id}/thumb", tags=["archive"])
    def document_thumb(doc_id: str, user: User = Depends(current_user)):
        """First page as a small picture (cached in the data folder)."""
        doc = _doc_or_404(doc_id, user)
        cache = settings.data / "thumbs" / f"{doc['sha256']}.png"
        if not cache.exists():
            root = app.state.index.archive.resolve()
            path = (root / doc["path"]).resolve()
            if root not in path.parents or not path.is_file():
                raise HTTPException(status_code=404, detail="file not found")
            try:
                render_thumb(path, doc["ext"], cache)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=404, detail="no preview") from exc
        return FileResponse(cache, media_type="image/png", headers={"Cache-Control": "max-age=86400"})

    # ------------------------------------------------------------ inbox

    def _inbox_error(exc: Exception):
        return HTTPException(status_code=400, detail=str(exc))

    @app.get("/api/inbox", tags=["inbox"])
    def inbox_list(status: str = Query("new", pattern="^(new|filed|dismissed)$"),
                   user: User = Depends(require_admin)):
        return {"items": app.state.inbox.items(status), "counts": app.state.inbox.counts(),
                "archive_writable": path_status(str(app.state.index.archive))["writable"],
                "inboxes": [{"id": i.id, "name": i.name, "area": i.area, "enabled": i.enabled,
                             "after_import": i.after_import, "status": path_status(i.path)}
                            for i in app.state.storage.load().inboxes],
                "folders": sorted(app.state.folders.effective(), key=str.casefold),
                "areas": sorted(app.state.inbox.area_names())}

    @app.post("/api/inbox/rescan", tags=["inbox"])
    def inbox_rescan(user: User = Depends(require_admin)):
        kick(full=False)
        return {"started": True}

    @app.post("/api/inbox/file-all", tags=["inbox"])
    def inbox_file_all(body: FileAllIn, user: User = Depends(require_admin)):
        if body.mode not in ("agree", "all"):
            raise HTTPException(status_code=400, detail="invalid mode")
        result = app.state.inbox.file_all(body.mode)
        if result["filed"]:
            threading.Thread(target=app.state.index.scan, daemon=True).start()
        return result

    @app.get("/api/inbox/{key}", tags=["inbox"])
    def inbox_item(key: str, user: User = Depends(require_admin)):
        try:
            return app.state.inbox.get(key)
        except InboxError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/inbox/{key}/file", tags=["inbox"])
    def inbox_file(key: str, user: User = Depends(require_admin)):
        try:
            path, ext = app.state.inbox.path_of(key)
        except InboxError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FileResponse(path, media_type=MEDIA_TYPES.get(ext, "application/octet-stream"),
                            filename=path.name, content_disposition_type="inline")

    @app.get("/api/inbox/{key}/text", tags=["inbox"], response_class=PlainTextResponse)
    def inbox_text(key: str, user: User = Depends(require_admin)):
        return app.state.inbox.text(key)

    @app.post("/api/inbox/{key}/file", tags=["inbox"])
    def inbox_do_file(key: str, body: FileIn, user: User = Depends(require_admin)):
        try:
            [clean_tag(t) for t in body.tags]          # refuse bad tags before anything is copied
        except TagError as exc:
            raise _inbox_error(exc) from exc
        try:
            result = app.state.inbox.file(key, body.area, body.folder, body.title, body.date, body.force)
        except (InboxError, OSError) as exc:
            raise _inbox_error(exc) from exc
        if body.tags:
            try:
                app.state.tags.change([result["sha256"]], body.tags, [])
            except TagError as exc:
                raise _inbox_error(exc) from exc
        # "Sollen Briefe wie dieser künftig automatisch hierhin?" – never let this break filing
        try:
            folder = "/".join(result["path"].split("/")[1:-1])
            text = app.state.index.document_text(result["sha256"])
            result["proposal"] = app.state.senders.propose(text, folder, allowed_areas(user)) if folder else None
        except Exception:  # noqa: BLE001
            log.exception("rule proposal failed")
            result["proposal"] = None
        threading.Thread(target=app.state.index.scan, daemon=True).start()
        return result

    @app.post("/api/inbox/upload", tags=["inbox"], status_code=201)
    def inbox_upload(body: UploadIn, user: User = Depends(require_admin)):
        """Files from the browser (iPhone camera too). Photos become PDFs; ``combine`` makes one document."""
        from .inbox import SETTLE_SECONDS
        from .upload import UploadError, prepare, store
        try:
            files = [(f.name, base64.b64decode(f.data, validate=True)) for f in body.files]
            names = store(settings.data / "hochgeladen", prepare(files, body.combine), SETTLE_SECONDS)
        except (UploadError, binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        app.state.inbox.scan()
        kick(full=False)                 # read the text right away
        return {"names": names}

    @app.post("/api/inbox/{key}/ai", tags=["inbox"])
    def inbox_ai(key: str, body: InboxAIIn | None = None, user: User = Depends(require_admin)):
        try:
            return app.state.inbox.ask_ai(key, app.state.ai, body.instructions if body else None,
                                          body.prompt if body else None)
        except (InboxError, AIError) as exc:
            raise _inbox_error(exc) from exc

    @app.post("/api/inbox/{key}/dismiss", tags=["inbox"])
    def inbox_dismiss(key: str, body: DismissIn, user: User = Depends(require_admin)):
        try:
            app.state.inbox.dismiss(key, body.dismissed)
        except InboxError as exc:
            raise _inbox_error(exc) from exc
        return {"ok": True}

    @app.delete("/api/inbox/{key}", tags=["inbox"])
    def inbox_delete(key: str, user: User = Depends(require_admin)):
        try:
            app.state.inbox.delete(key)
        except InboxError as exc:
            raise _inbox_error(exc) from exc
        return {"ok": True}

    @app.get("/api/reference/{doc_id}/file", tags=["rules"])
    def reference_file(doc_id: str, user: User = Depends(require_admin)):
        ref: Index | None = app.state.reference
        doc = ref.document(doc_id, [a["name"] for a in ref.areas()]) if ref is not None else None
        if not doc:
            raise HTTPException(status_code=404, detail="document not found")
        root = ref.archive.resolve()
        path = (root / doc["path"]).resolve()
        if root not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        return FileResponse(path, media_type=MEDIA_TYPES.get(doc["ext"], "application/octet-stream"),
                            filename=doc["name"], content_disposition_type="inline")

    def ai_view(config) -> dict:
        prompts, default = inbox_prompts(config)
        data = config.public()
        data.pop("inbox_prompt", None)
        return {**data, "inbox_prompts": prompts, "inbox_default": default,
                "inbox_prompt_default": AI_INSTRUCTIONS}

    @app.get("/api/ai", tags=["ai"])
    def get_ai(user: User = Depends(require_admin)):
        return ai_view(app.state.ai.load())

    @app.put("/api/ai", tags=["ai"])
    def put_ai(body: AIChange, user: User = Depends(require_admin)):
        try:
            return ai_view(app.state.ai.update(body.model_dump(exclude_unset=True)))
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/ai/models", tags=["ai"])
    def ai_models(user: User = Depends(require_admin)):
        return app.state.ai.list_models()

    @app.post("/api/ai/test", tags=["ai"])
    def test_ai(user: User = Depends(require_admin)):
        try:
            result = app.state.ai.complete(
                "You are a connection test. Reply with exactly one word.",
                "Antworte nur mit: OK", max_tokens=1000, force=True,
            )
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"text": result.text[:200], "model": result.model, "seconds": result.seconds,
                "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
                "cost": round(result.cost, 6)}

    @app.middleware("http")
    async def no_stale_ui(request: Request, call_next):
        """The UI must always be revalidated, otherwise a deploy shows the old version."""
        response = await call_next(request)
        if not request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    app.mount("/", StaticFiles(directory=STATIC, html=True), name="ui")
    return app
