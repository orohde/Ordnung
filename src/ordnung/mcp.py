"""MCP endpoint: the archive as tools for an AI assistant.

A thin layer over the REST API, spoken as JSON-RPC over HTTP (the "streamable HTTP"
transport of the Model Context Protocol, answered with plain JSON). The API key from
*Settings → Connections* goes along as ``Authorization: Bearer <key>``, exactly as for the
REST API; what a key may not do there it may not do here either. The endpoint is
off until an administrator switches it on (Settings → Connections).

Every tool calls the same functions the REST routes use, so rights, the trash and
the file names behave the same. Nothing here deletes for good, and the configuration
(users, security, storage, rules) is left to the interface.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from . import __version__
from .auth import User, current_user
from .index import HL_END, HL_START

PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
TEXT_LIMIT = 30_000          # characters of recognised text per call, unless asked for more

INSTRUCTIONS = (
    "Ordnung! is a folder-based archive of scanned and digital documents (mostly PDFs). Documents "
    "live in areas (top folders, often one per person plus shared ones) and folders below them, "
    "e.g. \"Versicherungen/HUK/KFZ\". Title and date are part of the file name; a document keeps "
    "its short id when it is renamed or moved, so use the id for every later call. Search first, "
    "then read a document's recognised text before you judge or change it. Tags label documents; "
    "a Mappe is a tag that gathers documents for a purpose (\"Steuererklärung 2026\"). New post "
    "waits in the inbox with a suggested place; file_inbox_item puts it into the archive. "
    "trash_document only moves to the trash, restore_document brings it back."
)


class ToolError(Exception):
    pass


def _text(value: Any) -> dict:
    return {"type": "text", "text": value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1)}


def _snippet(text: str | None) -> str | None:
    return text.replace(HL_START, "**").replace(HL_END, "**") if text else None


def _brief(doc: dict) -> dict:
    out = {"id": doc["id"], "title": doc["title"], "date": doc.get("date"), "area": doc["area"],
           "folder": doc["folder"], "type": doc["ext"]}
    if doc.get("tags"):
        out["tags"] = doc["tags"]
    if doc.get("snippet"):
        out["snippet"] = _snippet(doc["snippet"])
    return out


def _cut(text: str, offset: int, max_chars: int) -> tuple[str, dict]:
    offset = max(0, int(offset))
    max_chars = max(1, min(int(max_chars), 200_000))
    part = text[offset:offset + max_chars]
    info = {"text_chars": len(text)}
    if offset or offset + max_chars < len(text):
        info.update(text_offset=offset, text_shown=len(part))
        if offset + max_chars < len(text):
            info["note"] = f"text cut off; call again with offset {offset + max_chars} for more"
    return part, info


def _schema(properties: dict, required: tuple[str, ...] = ()) -> dict:
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


_ID = {"type": "string", "description": "The document's short id, as returned by search_documents."}
_AREA = {"type": "string", "description": "Area name (see list_areas)."}
_FOLDER = {"type": "string", "description": "Folder path inside the area, e.g. \"Versicherungen/HUK\"; empty for the area itself."}
_DATE = {"type": "string", "description": "ISO date YYYY-MM-DD."}
_TAGS = {"type": "array", "items": {"type": "string"}}
_KEY = {"type": "string", "description": "The inbox item's key, as returned by list_inbox."}
_OFFSET = {"type": "integer", "minimum": 0, "description": "Start of the text part, for long documents (default 0)."}
_MAX = {"type": "integer", "minimum": 1, "maximum": 200000, "description": f"Characters of text at most (default {TEXT_LIMIT})."}


def build_tools(ops: SimpleNamespace) -> dict[str, dict]:
    """The tools by name: description, input schema, what it needs, and the function behind it."""
    from .app import DismissIn, DocMetaIn, FileIn, MappeIn, MoveIn, RestoreIn, TagChangeIn, TagsIn

    def list_areas(user: User):
        return [{"name": a["name"], "label": a["label"], "documents": a["count"],
                 "writable": user.can_write(a["name"])} for a in ops.areas(user=user)]

    def list_folders(user: User, area: str = ""):
        def walk(node):
            rows = [{"folder": node["path"], "documents": node["own"], "with_subfolders": node["count"],
                     "areas": node["areas"]}] if node["path"] else []
            for child in node["children"]:
                rows += walk(child)
            return rows
        return walk(ops.tree(areas=area or None, template=False, user=user))

    def search_documents(user: User, query: str = "", area: str = "", folder: str = "", recursive: bool = True,
                         tags: list[str] | None = None, date_from: str = "", date_to: str = "",
                         include_altablage: bool = False, sort: str = "", limit: int = 30, offset: int = 0):
        if sort not in ("", "date", "title", "area", "relevance"):
            raise ToolError("sort must be relevance, date, title or area")
        for value in (date_from, date_to):
            if value and not (len(value) in (4, 7, 10) and value[:4].isdigit()):
                raise ToolError("dates as YYYY, YYYY-MM or YYYY-MM-DD")
        result = ops.documents(
            folder=folder, recursive=recursive or bool(query), q=query, areas=area or None,
            tags=",".join(tags) if tags else None, alt=include_altablage,
            limit=max(1, min(int(limit), 200)), offset=max(0, int(offset)),
            sort=sort or ("relevance" if query else "date"), desc=sort != "title",
            date_from=date_from or None, date_to=date_to or None, user=user)
        return {"total": result["total"], "documents": [_brief(d) for d in result["items"]]}

    def read_document(user: User, id: str, offset: int = 0, max_chars: int = TEXT_LIMIT):
        doc = ops.document(id, user=user)
        text, info = _cut(ops.document_text(id, user=user), offset, max_chars)
        meta = {**_brief(doc), "file_name": doc["name"], "size": doc["size"],
                "writable": user.can_write(doc["area"]), **info}
        return [_text(meta), _text(text or "(no text recognised in this document)")]

    def list_tags(user: User, area: str = ""):
        return ops.tag_list(areas=area or None, alt=True, user=user)

    def set_tags(user: User, id: str, tags: list[str]):
        return ops.document_tags(id, TagsIn(tags=tags), user=user)

    def change_tags(user: User, ids: list[str], add: list[str] | None = None, remove: list[str] | None = None):
        if not add and not remove:
            raise ToolError("give tags to add and/or to remove")
        return ops.tags_change(TagChangeIn(ids=ids, add=add or [], remove=remove or []), user=user)

    def update_document(user: User, id: str, title: str = "", date: str = ""):
        if not title and not date:
            raise ToolError("give a new title and/or date")
        doc = ops.document(id, user=user)
        if not date and not doc.get("date"):
            raise ToolError("this document has no date yet; give one together with the title")
        ops.document_meta(id, DocMetaIn(title=title or doc["title"], date=date or doc["date"]), user=user)
        return {"id": id, "title": title or doc["title"], "date": date or doc["date"], "changed": True}

    def move_document(user: User, id: str, folder: str = "", area: str = ""):
        return ops.document_move(id, MoveIn(folder=folder, area=area or None), user=user)

    def trash_document(user: User, id: str):
        return ops.document_trash(id, user=user)

    def list_trash(user: User):
        return ops.trash_items(user=user)

    def restore_document(user: User, trash_path: str):
        return ops.trash_restore(RestoreIn(trash_path=trash_path), user=user)

    def list_mappen(user: User):
        return [{"name": m["name"], "area": m["area"], "documents": m["count"], "writable": m["writable"]}
                for m in ops.mappen_list(areas=None, user=user)]

    def create_mappe(user: User, name: str, area: str):
        return ops.mappen_add(MappeIn(name=name, area=area), user=user)

    def _inbox_brief(item: dict) -> dict:
        s = item.get("suggestion") or {}
        out = {"key": item["key"], "name": item["name"], "inbox": item["inbox_name"] or item["inbox"],
               "place_in_inbox": item["rel"], "added": item["added"], "status": item["status"],
               "text": "not read yet" if item["text"] is None else
                       {"chars": item["text"]["chars"], "pages": item["text"]["pages"], "error": item["text"]["error"]}}
        if item.get("filed_path"):
            out["filed_path"] = item["filed_path"]
        if s:
            out["suggestion"] = {"area": s.get("area"), "folder": s.get("folder"), "source": s.get("source"),
                                 "title": s.get("title") or s.get("title_fallback"),
                                 "date": s.get("date") or s.get("date_fallback"),
                                 "conflict": s.get("conflict"), "duplicate_of": (s.get("duplicate") or {}).get("path"),
                                 "other_folders": [c["folder"] for c in s.get("candidates", [])[1:]]}
        return out

    def list_inbox(user: User, status: str = "new"):
        if status not in ("new", "filed", "dismissed"):
            raise ToolError("status must be new, filed or dismissed")
        result = ops.inbox_list(status=status, user=user)
        return {"counts": result["counts"], "areas": result["areas"],
                "archive_writable": result["archive_writable"],
                "items": [_inbox_brief(i) for i in result["items"]]}

    def read_inbox_item(user: User, key: str, offset: int = 0, max_chars: int = TEXT_LIMIT):
        item = ops.inbox_item(key, user=user)
        text, info = _cut(ops.inbox_text(key, user=user), offset, max_chars)
        return [_text({**_inbox_brief(item), **info}), _text(text or "(no text recognised yet)")]

    def file_inbox_item(user: User, key: str, area: str, title: str, date: str, folder: str = "",
                        tags: list[str] | None = None, force: bool = False):
        result = ops.inbox_do_file(key, FileIn(area=area, folder=folder, title=title, date=date, force=force,
                                               tags=tags or []), user=user)
        # the id is a prefix of the content hash; search finds the document once it is read in
        out = {"path": result["path"], "id": result["sha256"][:12] if result.get("sha256") else None}
        if result.get("proposal"):
            out["rule_proposal"] = "the interface offers a rule for letters like this one (Rules)"
        return out

    def dismiss_inbox_item(user: User, key: str, dismissed: bool = True):
        return ops.inbox_dismiss(key, DismissIn(dismissed=dismissed), user=user)

    def list_senders(user: User, area: str = ""):
        result = ops.senders_list(areas=area or None, user=user)
        return [{"domain": s["domain"], "name": s["name"], "documents": s["docs"],
                 "folders": [{"folder": f["folder"], "documents": f["docs"]} for f in s["folders"]]}
                for s in result["senders"]]

    def tool(fn: Callable, title: str, description: str, schema: dict, write: bool = False,
             destructive: bool = False, admin: bool = False) -> dict:
        return {"fn": fn, "title": title, "description": description, "schema": schema, "write": write,
                "destructive": destructive, "admin": admin}

    return {
        "list_areas": tool(list_areas, "List areas",
                           "The areas (top folders) of the archive with their number of documents and whether you may change them.",
                           _schema({})),
        "list_folders": tool(list_folders, "List folders",
                             "All folders with their number of documents (own and with subfolders) and the areas they occur in. "
                             "Optionally only one area.",
                             _schema({"area": _AREA})),
        "search_documents": tool(
            search_documents, "Search documents",
            "Full-text search over title, folder and recognised text. Without a query it lists documents (newest first). "
            "Filters: area, folder, tags (all must match), date range. Returns id, title, date, area, folder, tags and "
            "a snippet around the hit.",
            _schema({"query": {"type": "string", "description": "Words that must all occur; \"#tag\" filters by tag."},
                     "area": _AREA, "folder": _FOLDER,
                     "recursive": {"type": "boolean", "description": "Include subfolders (default true)."},
                     "tags": {**_TAGS, "description": "Only documents carrying all of these tags or Mappen."},
                     "date_from": {"type": "string", "description": "Dated on or after: YYYY, YYYY-MM or YYYY-MM-DD."},
                     "date_to": {"type": "string", "description": "Dated on or before: YYYY, YYYY-MM or YYYY-MM-DD."},
                     "include_altablage": {"type": "boolean", "description": "Also search the Altablage (old documents put aside)."},
                     "sort": {"type": "string", "enum": ["relevance", "date", "title", "area"],
                              "description": "Default: relevance for a search, else date."},
                     "limit": {"type": "integer", "minimum": 1, "maximum": 200, "description": "Default 30."},
                     "offset": {"type": "integer", "minimum": 0, "description": "Skip this many hits (paging)."}})),
        "read_document": tool(
            read_document, "Read a document",
            "A document's details (title, date, area, folder, tags) and the text read from it (text layer or OCR). "
            "Long texts come in parts: use offset for the next part.",
            _schema({"id": _ID, "offset": _OFFSET, "max_chars": _MAX}, ("id",))),
        "list_tags": tool(list_tags, "List tags", "All tags with the number of documents carrying them (Mappen not included).",
                          _schema({"area": _AREA})),
        "set_tags": tool(
            set_tags, "Set a document's tags", "Replace all tags of one document with these (an empty list removes them).",
            _schema({"id": _ID, "tags": _TAGS}, ("id", "tags")), write=True),
        "change_tags": tool(
            change_tags, "Add or remove tags",
            "Add and/or remove tags on one or many documents at once; other tags stay. Adding a Mappe's name puts the "
            "documents into that Mappe.",
            _schema({"ids": {"type": "array", "items": {"type": "string"}, "description": "Document ids."},
                     "add": _TAGS, "remove": _TAGS}, ("ids",)), write=True),
        "update_document": tool(
            update_document, "Change title or date",
            "Give a document a new title and/or date. Both live in the file name, so the file is renamed; the id stays.",
            _schema({"id": _ID, "title": {"type": "string"}, "date": _DATE}, ("id",)), write=True),
        "move_document": tool(
            move_document, "Move a document",
            "Move a document into another folder, also into another area (needs write access to both).",
            _schema({"id": _ID, "folder": _FOLDER, "area": {**_AREA, "description": "Target area; default: the document's own."}},
                    ("id",)), write=True),
        "trash_document": tool(
            trash_document, "Move a document to the trash",
            "Moves a document to the trash, from where restore_document brings it back until the trash is emptied.",
            _schema({"id": _ID}, ("id",)), write=True, destructive=True),
        "list_trash": tool(list_trash, "List the trash",
                           "What lies in the trash, newest first, and after how many days it is emptied.", _schema({})),
        "restore_document": tool(
            restore_document, "Restore from the trash", "Put a document from the trash back to where it was.",
            _schema({"trash_path": {"type": "string", "description": "trash_path from list_trash or trash_document."}},
                    ("trash_path",)), write=True),
        "list_mappen": tool(list_mappen, "List Mappen",
                            "Mappen (collections such as \"Steuererklärung 2026\") with their area and number of documents. "
                            "search_documents with tags=[name] lists a Mappe's documents.", _schema({})),
        "create_mappe": tool(
            create_mappe, "Create a Mappe",
            "A new, empty Mappe belonging to an area. Put documents into it with change_tags (add its name).",
            _schema({"name": {"type": "string"}, "area": _AREA}, ("name", "area")), write=True),
        "list_inbox": tool(
            list_inbox, "List the inbox",
            "Post waiting to be filed, each with a suggested area, folder, title and date (from rules, its place in the "
            "inbox or the AI) and a hint if it is already in the archive. status: new (default), filed or dismissed.",
            _schema({"status": {"type": "string", "enum": ["new", "filed", "dismissed"]}}), admin=True),
        "read_inbox_item": tool(
            read_inbox_item, "Read an inbox item", "One inbox item with its suggestion and the text read from it.",
            _schema({"key": _KEY, "offset": _OFFSET, "max_chars": _MAX}, ("key",)), admin=True),
        "file_inbox_item": tool(
            file_inbox_item, "File an inbox item",
            "Put an inbox item into the archive under area/folder as \"date_title\". Refuses a document already in the "
            "archive unless force is set. Optionally tags it.",
            _schema({"key": _KEY, "area": _AREA, "folder": _FOLDER, "title": {"type": "string"}, "date": _DATE,
                     "tags": _TAGS, "force": {"type": "boolean", "description": "File even if already in the archive."}},
                    ("key", "area", "title", "date")), write=True, admin=True),
        "dismiss_inbox_item": tool(
            dismiss_inbox_item, "Set an inbox item aside",
            "Mark an inbox item as not to be filed (it stays in the inbox folder); dismissed=false takes it back.",
            _schema({"key": _KEY, "dismissed": {"type": "boolean"}}, ("key",)), write=True, admin=True),
        "list_senders": tool(
            list_senders, "List senders",
            "Senders recognised in the documents (by their web or mail domain) with the folders their post lies in.",
            _schema({"area": _AREA}), admin=True),
    }


def mount_mcp(app: FastAPI, ops: SimpleNamespace) -> None:
    tools = build_tools(ops)

    def offered(user: User) -> dict[str, dict]:
        """What this user may use: a reading key gets no writing tool, only admins see the inbox."""
        writer = any(user.can_write(a["name"]) for a in app.state.index.areas())
        return {name: t for name, t in tools.items()
                if (writer or not t["write"]) and (user.is_admin or not t["admin"])}

    def listing(user: User) -> list[dict]:
        return [
            {"name": name, "title": t["title"], "description": t["description"], "inputSchema": t["schema"],
             "annotations": {"title": t["title"], "readOnlyHint": not t["write"], "destructiveHint": t["destructive"],
                             "idempotentHint": False, "openWorldHint": False}}
            for name, t in offered(user).items()
        ]

    def call(user: User, name: str, arguments: dict) -> dict:
        spec = tools.get(name)
        if not spec:
            raise ValueError(f"unknown tool: {name}")
        try:
            if name not in offered(user):
                raise ToolError("this API key may not use this tool")
            unknown = sorted(set(arguments) - set(spec["schema"]["properties"]))
            if unknown:
                raise ToolError(f"unknown argument: {', '.join(unknown)}")
            missing = [key for key in spec["schema"]["required"] if arguments.get(key) in (None, "")]
            if missing:
                raise ToolError(f"missing argument: {', '.join(missing)}")
            result = spec["fn"](user, **arguments)
        except ToolError as exc:
            return {"content": [_text(str(exc))], "isError": True}
        except HTTPException as exc:
            return {"content": [_text(f"{exc.detail} (status {exc.status_code})")], "isError": True}
        except (TypeError, ValueError) as exc:        # wrong kind of argument
            return {"content": [_text(f"invalid arguments: {exc}")], "isError": True}
        content = result if isinstance(result, list) and result and isinstance(result[0], dict) and "type" in result[0] \
            else [_text(result)]
        return {"content": content, "isError": False}

    def answer(user: User, message: Any) -> dict | None:
        """One JSON-RPC message in, its answer out (None for a notification)."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request"}}
        method, params, msg_id = message["method"], message.get("params") or {}, message.get("id")
        if "id" not in message:
            return None
        try:
            if method == "initialize":
                wanted = params.get("protocolVersion")
                result = {"protocolVersion": wanted if wanted in PROTOCOLS else PROTOCOLS[0],
                          "capabilities": {"tools": {"listChanged": False}},
                          "serverInfo": {"name": "ordnung", "title": "Ordnung!", "version": __version__},
                          "instructions": INSTRUCTIONS}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": listing(user)}
            elif method == "tools/call":
                arguments = params.get("arguments") or {}
                if not isinstance(params.get("name"), str) or not isinstance(arguments, dict):
                    raise ValueError("tools/call needs a name and an arguments object")
                result = call(user, params["name"], arguments)
            else:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"method not found: {method}"}}
        except ValueError as exc:
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32602, "message": str(exc)}}
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @app.post("/api/mcp", tags=["mcp"])
    async def mcp(request: Request, user: User = Depends(current_user)):
        """Model Context Protocol over HTTP: JSON-RPC in, JSON out. Connect an assistant to this address.

        Off in a fresh installation; an administrator turns it on under Settings → Connections.
        """
        if not app.state.system.load().mcp:
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {
                "code": -32000, "message": "MCP is switched off in this installation (Settings → Connections)"}}, status_code=403)
        try:
            body = json.loads(await request.body())
        except ValueError:
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}, status_code=400)
        # the tools read files and the database: not on the event loop
        if isinstance(body, list):
            answers = [a for a in [await run_in_threadpool(answer, user, m) for m in body] if a is not None]
            return JSONResponse(answers) if answers else Response(status_code=202)
        reply = await run_in_threadpool(answer, user, body)
        return JSONResponse(reply) if reply is not None else Response(status_code=202)

    @app.get("/api/mcp", tags=["mcp"], include_in_schema=False)
    @app.delete("/api/mcp", tags=["mcp"], include_in_schema=False)
    def mcp_no_stream(user: User = Depends(current_user)):
        # no server-initiated messages and no sessions: there is nothing to listen to or to end
        return Response(status_code=405, headers={"Allow": "POST"})
