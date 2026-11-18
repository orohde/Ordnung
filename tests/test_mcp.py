"""The MCP endpoint: the archive as tools, over the same functions as the REST API."""

import functools
import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings
from ordnung.textextract import extract

from conftest import make_pdf

API = {"Authorization": "Bearer tok"}          # the key from before, taken over as "API" (write)
EXTRACT = functools.partial(extract, ocr=False)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.index.extract_pending(EXTRACT)
    app.state.system.update({"mcp": True})
    return TestClient(app)


def rpc(client: TestClient, method: str, params: dict | None = None, headers: dict = API, msg_id: int | None = 1):
    message = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if msg_id is not None:
        message["id"] = msg_id
    return client.post("/api/mcp", json=message, headers=headers)


def call(client: TestClient, tool: str, headers: dict = API, /, **arguments):
    """(is_error, content blocks parsed where they are JSON)"""
    res = rpc(client, "tools/call", {"name": tool, "arguments": arguments}, headers)
    assert res.status_code == 200, res.text
    result = res.json()["result"]
    blocks = []
    for block in result["content"]:
        try:
            blocks.append(json.loads(block["text"]))
        except ValueError:
            blocks.append(block["text"])
    return result["isError"], blocks


def reading_key(client: TestClient) -> dict:
    token = client.post("/api/security/api-keys", json={"name": "Nur lesen", "right": "read"}, headers=API).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_handshake(client: TestClient):
    assert client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"}).status_code == 401
    res = rpc(client, "initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}})
    info = res.json()["result"]
    assert info["protocolVersion"] == "2025-03-26" and info["serverInfo"] == {
        "name": "ordnung", "title": "Ordnung!", "version": info["serverInfo"]["version"]}
    assert info["capabilities"] == {"tools": {"listChanged": False}} and "Ordnung!" in info["instructions"]
    assert rpc(client, "initialize", {"protocolVersion": "1999-01-01"}).json()["result"]["protocolVersion"] == "2025-06-18"
    assert rpc(client, "notifications/initialized", msg_id=None).status_code == 202        # a notification gets no answer
    assert rpc(client, "ping").json() == {"jsonrpc": "2.0", "id": 1, "result": {}}
    assert rpc(client, "resources/list").json()["error"]["code"] == -32601
    assert client.get("/api/mcp", headers=API).status_code == 405
    assert client.post("/api/mcp", content=b"{", headers=API).json()["error"]["code"] == -32700
    both = client.post("/api/mcp", headers=API, json=[
        {"jsonrpc": "2.0", "id": 1, "method": "ping"}, {"jsonrpc": "2.0", "method": "notifications/initialized"}]).json()
    assert both == [{"jsonrpc": "2.0", "id": 1, "result": {}}]


def test_switched_off(client: TestClient):
    client.app.state.system.update({"mcp": False})
    res = rpc(client, "tools/list")
    assert res.status_code == 403 and "switched off" in res.json()["error"]["message"]
    # the switch lives in the system settings and is off in a fresh installation
    assert client.get("/api/system/settings", headers=API).json()["mcp"] is False
    assert client.put("/api/system/settings", json={"mcp": True}, headers=API).json()["mcp"] is True
    assert rpc(client, "tools/list").status_code == 200


def test_fresh_installation_is_off(settings: Settings):
    app = create_app(settings, background=False)
    assert app.state.system.load().mcp is False
    assert TestClient(app).post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
                                headers=API).status_code == 403


def test_tools_are_listed_by_right(client: TestClient):
    tools = rpc(client, "tools/list").json()["result"]["tools"]
    names = {t["name"] for t in tools}
    assert {"search_documents", "read_document", "set_tags", "update_document", "move_document", "trash_document",
            "restore_document", "list_inbox", "file_inbox_item", "list_mappen", "list_senders"} <= names
    for tool in tools:
        assert tool["description"] and tool["inputSchema"]["type"] == "object"
    by_name = {t["name"]: t["annotations"] for t in tools}
    assert by_name["trash_document"]["destructiveHint"] is True and by_name["trash_document"]["readOnlyHint"] is False
    assert by_name["search_documents"]["readOnlyHint"] is True and by_name["search_documents"]["destructiveHint"] is False
    assert not names & {"delete_document", "empty_trash", "create_user"}    # nothing for good, no configuration
    # a reading key sees every area but is offered no writing tool – and no inbox, which is for admins
    reader = reading_key(client)
    seen = {t["name"] for t in rpc(client, "tools/list", headers=reader).json()["result"]["tools"]}
    assert {"search_documents", "read_document", "list_trash", "list_tags", "list_mappen"} <= seen
    assert not seen & {"set_tags", "change_tags", "update_document", "move_document", "trash_document",
                       "restore_document", "create_mappe", "file_inbox_item", "list_inbox"}
    error, blocks = call(client, "set_tags", reader, id="abcdef", tags=["x"])
    assert error and "may not" in blocks[0]


def test_search_and_read(client: TestClient):
    error, blocks = call(client, "list_areas")
    assert not error and {a["name"] for a in blocks[0]} >= {"oliver", "erika", "gemeinsam"}
    error, blocks = call(client, "list_folders", area="erika")
    assert not error and "Gesundheit/Rezepte" in [f["folder"] for f in blocks[0]]
    error, blocks = call(client, "search_documents", query="Fichtel")
    assert not error and blocks[0]["total"] == 2
    hit = blocks[0]["documents"][0]
    assert hit["area"] == "erika" and "**" in hit["snippet"]
    error, blocks = call(client, "search_documents", area="oliver", date_from="2026")
    assert [d["title"] for d in blocks[0]["documents"]] == ["Kontoauszug"]
    error, blocks = call(client, "search_documents", date_to="2024")
    assert blocks[0]["total"] == 1
    error, blocks = call(client, "read_document", id=hit["id"])
    assert not error and blocks[0]["id"] == hit["id"] and "Rezept" in blocks[1]
    error, blocks = call(client, "read_document", id=hit["id"], max_chars=5)
    assert len(blocks[1]) == 5 and "offset 5" in blocks[0]["note"]
    error, blocks = call(client, "read_document", id="ffffff")
    assert error and "not found" in blocks[0]
    error, blocks = call(client, "search_documents", bogus=1)
    assert error and "unknown argument" in blocks[0]
    error, blocks = call(client, "read_document")
    assert error and "missing argument: id" in blocks[0]
    # the reading key reads, too
    error, blocks = call(client, "search_documents", reading_key(client), query="Rechtsschutz")
    assert not error and blocks[0]["total"] == 1


def test_write_tools(client: TestClient):
    doc = call(client, "search_documents", query="Kontoauszug")[1][0]["documents"][0]
    error, blocks = call(client, "set_tags", id=doc["id"], tags=["Steuer 2026"])
    assert not error and blocks[0]["tags"] == ["Steuer 2026"]
    assert not call(client, "create_mappe", name="Steuererklärung 2026", area="oliver")[0]
    assert call(client, "change_tags", ids=[doc["id"]], add=["Steuererklärung 2026"])[1][0]["changed"] == 1
    mappen = call(client, "list_mappen")[1][0]
    assert mappen == [{"name": "Steuererklärung 2026", "area": "oliver", "documents": 1, "writable": True}]
    assert call(client, "search_documents", tags=["Steuer 2026"])[1][0]["total"] == 1

    error, blocks = call(client, "update_document", id=doc["id"], title="Kontoauszug März")
    assert not error, blocks
    client.app.state.index.scan()
    moved = call(client, "read_document", id=doc["id"])[1][0]
    assert moved["title"] == "Kontoauszug März" and moved["date"] == "2026-03-01" and moved["tags"]
    error, blocks = call(client, "move_document", id=doc["id"], folder="Banken/Archiv")
    assert not error, blocks
    client.app.state.index.scan()
    assert call(client, "read_document", id=doc["id"])[1][0]["folder"] == "Banken/Archiv"

    error, blocks = call(client, "trash_document", id=doc["id"])
    assert not error
    trash_path = blocks[0]["trash_path"]
    client.app.state.index.scan()
    assert call(client, "read_document", id=doc["id"])[0]
    items = call(client, "list_trash")[1][0]["items"]
    assert [i["trash_path"] for i in items] == [trash_path]
    assert not call(client, "restore_document", trash_path=trash_path)[0]
    client.app.state.index.scan()
    assert call(client, "read_document", id=doc["id"])[1][0]["folder"] == "Banken/Archiv"


def test_inbox_tools(client: TestClient, tmp_path: Path):
    inbox = tmp_path / "scanner"
    inbox.mkdir()
    assert client.put("/api/storage", headers=API, json={"inboxes": [
        {"name": "Scanner", "path": str(inbox), "enabled": True, "area": "oliver", "after_import": "keep"}]}).status_code == 200
    scan = inbox / "scan_0001.pdf"
    scan.write_bytes(make_pdf("Stadtwerke Abschlag Strom 2026"))
    old = time.time() - 120
    os.utime(scan, (old, old))
    client.app.state.inbox.scan()
    client.app.state.inbox.extract_pending(EXTRACT)

    error, blocks = call(client, "list_inbox")
    assert not error and blocks[0]["counts"]["new"] == 1
    item = blocks[0]["items"][0]
    assert item["name"] == "scan_0001.pdf" and item["suggestion"]["area"] == "oliver"
    error, blocks = call(client, "read_inbox_item", key=item["key"])
    assert not error and "Stadtwerke" in blocks[1]
    assert not call(client, "dismiss_inbox_item", key=item["key"])[0]
    assert call(client, "list_inbox", status="dismissed")[1][0]["counts"]["dismissed"] == 1
    assert not call(client, "dismiss_inbox_item", key=item["key"], dismissed=False)[0]
    error, blocks = call(client, "file_inbox_item", key=item["key"], area="oliver", folder="Energie/Stadtwerke",
                         title="Abschlag Strom", date="2026-11-01", tags=["Strom"])
    assert not error, blocks
    assert blocks[0]["path"].startswith("oliver/Energie/Stadtwerke/2026-11-01_Abschlag Strom_")
    for _ in range(50):                      # filing reads the archive in again in the background
        if client.app.state.index.scan().get("started"):
            break
        time.sleep(0.1)
    found = call(client, "search_documents", tags=["Strom"])[1][0]
    assert found["total"] == 1 and found["documents"][0]["folder"] == "Energie/Stadtwerke"
    error, blocks = call(client, "file_inbox_item", key=item["key"], area="oliver", title="x", date="2026-13-01")
    assert error
