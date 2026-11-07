import functools
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings
from ordnung.inbox import clean_title, guess_date, meaningful
from ordnung.textextract import extract

from conftest import make_pdf

EXTRACT = functools.partial(extract, ocr=False)


def settle(path: Path) -> None:
    """Pretend the scanner finished writing long ago."""
    old = time.time() - 120
    os.utime(path, (old, old))


@pytest.fixture
def env(settings: Settings, tmp_path: Path):
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.index.extract_pending(EXTRACT)
    c = TestClient(app)
    assert c.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    inbox = tmp_path / "scanner"
    inbox.mkdir()
    fresh = tmp_path / "dokumente"
    (fresh / "oliver").mkdir(parents=True)
    (fresh / "erika").mkdir(parents=True)
    return app, c, inbox, fresh


def add_inbox(c: TestClient, path: Path, **kw) -> None:
    body = {"inboxes": [{"name": "Scanner", "path": str(path), "enabled": True, **kw}]}
    assert c.put("/api/storage", json=body).status_code == 200


def process(app) -> None:
    app.state.inbox.scan()
    app.state.inbox.extract_pending(EXTRACT)


def test_helpers():
    assert guess_date("Musterstadt, den 03.02.2025\nRechnung vom 01.01.2024") == "2025-02-03"
    assert guess_date("Rechnungsdatum: 15. März 2024") == "2024-03-15"
    assert guess_date("Datum: 2023-07-01") == "2023-07-01"
    assert guess_date("nichts") is None
    assert guess_date("geboren am 19.05.1936") is None      # a birth date, not the document date
    assert not meaningful("scan_0001") and not meaningful("20261106_123456") and meaningful("Kontoauszug")
    assert clean_title(' Rechnung: "A/B" ') == "Rechnung A B"


def test_switch_keeps_rules_and_learning_set(env):
    app, c, inbox, fresh = env
    rid = c.post("/api/rules", json={"folder": "Gesundheit/Rezepte", "conditions": [
        {"type": "contains", "value": "Fichtel"}]}).json()["id"]
    # plan: the folder gets a new name in the fresh archive
    c.put("/api/import/plan/row", json={"area": "erika", "folder": "Gesundheit/Rezepte",
                                        "target_area": "erika", "target_folder": "Gesundheit/Arzt/Rezepte"})
    res = c.post("/api/storage/switch", json={"archive_path": str(fresh)}).json()
    assert res["rules_remapped"] == 1 and res["folders_added"] >= 1
    assert c.get("/api/status").json()["total"] == 0
    rule = next(r for r in c.get("/api/rules/folder", params={"path": "Gesundheit/Arzt/Rezepte"}).json()["rules"]
                if r["id"] == rid)
    # measured against the learning set under the new folder name
    assert rule["stats"]["inside"] == 2 and rule["stats"]["outside"] == 0
    assert c.get("/api/rules").json()["reference"] >= 5
    folders = {f["path"] for f in c.get("/api/folders").json()["folders"]}
    assert "Gesundheit/Arzt/Rezepte" in folders
    # learning set documents can be opened from the rule page
    doc = rule["stats"]["outside_docs"] or c.post("/api/rules/evaluate", json={
        "folder": "Banken", "conditions": [{"type": "contains", "value": "Fichtel"}]}).json()["outside_docs"]
    assert c.get(f"/api/reference/{doc[0]['id']}/file").status_code == 200


def test_inbox_rule_suggestion_and_filing(env):
    app, c, inbox, fresh = env
    c.post("/api/rules", json={"folder": "Gesundheit/Rezepte", "conditions": [
        {"type": "contains", "value": "Fichtel"}]})
    c.post("/api/storage/switch", json={"archive_path": str(fresh)})
    add_inbox(c, inbox, area="erika", after_import="move")
    f = inbox / "scan_0001.pdf"
    f.write_bytes(make_pdf("Praxis Dr. Fichtel Rezept Datum: 04.11.2026 Paracetamol"))
    settle(f)
    process(app)
    items = c.get("/api/inbox").json()["items"]
    assert len(items) == 1
    s = items[0]["suggestion"]
    assert s["folder"] == "Gesundheit/Rezepte" and s["source"] == "rule"
    assert s["area"] == "erika" and s["date"] == "2026-11-04" and s["title"] == ""
    key = items[0]["key"]
    assert c.get(f"/api/inbox/{key}/file").status_code == 200
    res = c.post(f"/api/inbox/{key}/file", json={"area": "erika", "folder": s["folder"],
                                                  "title": "Rezept Paracetamol", "date": s["date"]})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["path"].startswith("erika/Gesundheit/Rezepte/2026-11-04_Rezept Paracetamol_")
    assert body["moved"] and not f.exists() and (inbox / "_importiert" / "scan_0001.pdf").exists()
    assert (fresh / body["path"]).is_file()
    while not app.state.index.scan()["started"]:   # the endpoint started one in the background
        time.sleep(0.05)
    # the text came along: searchable without a second recognition
    found = c.get("/api/documents", params={"q": "Paracetamol", "recursive": True}).json()
    assert found["total"] == 1
    process(app)
    assert c.get("/api/inbox").json()["items"] == []


def test_inbox_folder_hint_duplicates_and_keep(env):
    app, c, inbox, fresh = env
    c.post("/api/storage/switch", json={"archive_path": str(fresh)})
    add_inbox(c, inbox, after_import="keep")
    # a folder copied over from the old archive, with its Paperless-style file name
    src = Path(app.state.reference.archive) / "oliver/Banken/DKB/2026-03-01_Kontoauszug.pdf"
    dest = inbox / "oliver/Banken/DKB" / src.name
    dest.parent.mkdir(parents=True)
    dest.write_bytes(src.read_bytes())
    settle(dest)
    process(app)
    item = c.get("/api/inbox").json()["items"][0]
    s = item["suggestion"]
    assert (s["area"], s["folder"], s["source"]) == ("oliver", "Banken/DKB", "folder")
    assert s["title"] == "Kontoauszug" and s["date"] == "2026-03-01"
    assert item["text"]["chars"] > 0          # taken over from the learning set
    assert c.post("/api/inbox/file-all", json={"mode": "agree"}).json()["filed"] == 0
    assert c.post("/api/inbox/file-all", json={"mode": "all"}).json()["filed"] == 1
    assert dest.exists()                      # keep: original stays …
    process(app)
    assert c.get("/api/inbox").json()["items"] == []   # … but is remembered as filed
    assert len(c.get("/api/inbox", params={"status": "filed"}).json()["items"]) == 1
    # the same file again under another name is a duplicate
    again = inbox / "nochmal.pdf"
    again.write_bytes(src.read_bytes())
    settle(again)
    process(app)
    app.state.index.scan()
    item = c.get("/api/inbox").json()["items"][0]
    assert item["suggestion"]["duplicate"]["path"].startswith("oliver/Banken/DKB/")
    res = c.post(f"/api/inbox/{item['key']}/file", json={"area": "oliver", "folder": "Banken/DKB",
                                                          "title": "x", "date": "2026-03-01"})
    assert res.status_code == 400 and "already" in res.json()["detail"]
    assert c.post(f"/api/inbox/{item['key']}/dismiss", json={"dismissed": True}).status_code == 200
    assert c.get("/api/inbox").json()["items"] == []


def test_same_file_twice_in_one_batch(env):
    """The archive index only learns about filed files with its next scan –
    a second copy filed right after the first must still count as a duplicate."""
    app, c, inbox, fresh = env
    c.post("/api/storage/switch", json={"archive_path": str(fresh)})
    add_inbox(c, inbox)
    src = Path(app.state.reference.archive) / "oliver/Banken/DKB/2026-03-01_Kontoauszug.pdf"
    for name in ("2026-03-01_Kontoauszug.pdf", "2026-03-01_Kontoauszug Kopie.pdf"):
        dest = inbox / "oliver/Banken/DKB" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        settle(dest)
    process(app)
    res = c.post("/api/inbox/file-all", json={"mode": "all"}).json()
    assert res["filed"] == 1 and "already" in res["failed"][0]["error"]
    assert len(list((fresh / "oliver/Banken/DKB").iterdir())) == 1
    item = c.get("/api/inbox").json()["items"][0]
    assert item["suggestion"]["duplicate"]["path"].startswith("oliver/Banken/DKB/")


def test_filing_needs_writable_archive_and_valid_input(env):
    app, c, inbox, fresh = env
    add_inbox(c, inbox, area="oliver")
    f = inbox / "brief.pdf"
    f.write_bytes(make_pdf("Irgendein Brief"))
    settle(f)
    process(app)
    key = c.get("/api/inbox").json()["items"][0]["key"]
    os.chmod(app.state.index.archive, 0o555)
    try:
        res = c.post(f"/api/inbox/{key}/file", json={"area": "oliver", "folder": "", "title": "Brief", "date": "2026-01-01"})
        assert res.status_code == 400 and "read-only" in res.json()["detail"]
    finally:
        os.chmod(app.state.index.archive, 0o755)
    for bad in ({"area": "niemand"}, {"date": "2026-13-01"}, {"date": "1899-12-31"}, {"title": "  "}, {"folder": "../x"}):
        body = {"area": "oliver", "folder": "", "title": "Brief", "date": "2026-01-01", **bad}
        assert c.post(f"/api/inbox/{key}/file", json=body).status_code == 400
    # old family papers: dates back to 1900 are fine
    res = c.post(f"/api/inbox/{key}/file", json={"area": "oliver", "folder": "", "title": "Tagebuch", "date": "1940-05-09"})
    assert res.status_code == 200 and res.json()["path"].startswith("oliver/1940-05-09_Tagebuch_")


def test_ask_ai_with_editable_instructions(env, monkeypatch):
    """The task text for "KI fragen" can be edited per call or saved; the answer format is always appended."""
    from types import SimpleNamespace
    from ordnung.inbox import AI_FORMAT, AI_INSTRUCTIONS
    app, c, inbox, fresh = env
    add_inbox(c, inbox, area="oliver")
    f = inbox / "brief.pdf"
    f.write_bytes(make_pdf("Beitragsrechnung der Versicherung"))
    settle(f)
    process(app)
    key = c.get("/api/inbox").json()["items"][0]["key"]
    seen = []

    def complete(system, prompt, **kw):
        seen.append(system)
        return SimpleNamespace(text='{"folder": "Banken/DKB", "title": "Rechnung", "date": "2026-01-02", "reason": "x"}',
                               model="fake", cost=0.0)
    monkeypatch.setattr(app.state.ai, "complete", complete)

    assert c.get("/api/ai").json()["inbox_prompt_default"] == AI_INSTRUCTIONS
    assert c.post(f"/api/inbox/{key}/ai").status_code == 200                      # default text
    assert seen[-1].startswith(AI_INSTRUCTIONS) and seen[-1].endswith(AI_FORMAT)
    res = c.post(f"/api/inbox/{key}/ai", json={"instructions": "Das ist Erikas Apotheke."})
    assert res.status_code == 200 and res.json()["folder"] == "Banken/DKB"
    assert seen[-1].startswith("Das ist Erikas Apotheke.") and seen[-1].endswith(AI_FORMAT)
    # several named instructions in the settings, one of them the default
    cfg = c.get("/api/ai").json()
    assert cfg["inbox_prompts"] == [{"name": "Standard", "text": AI_INSTRUCTIONS}] and cfg["inbox_default"] == "Standard"
    prompts = [{"name": "Standard", "text": AI_INSTRUCTIONS}, {"name": " Erika  Apotheke ", "text": "Das ist Erikas Apotheke."}]
    cfg = c.put("/api/ai", json={"inbox_prompts": prompts, "inbox_default": "erika apotheke"}).json()
    assert [p["name"] for p in cfg["inbox_prompts"]] == ["Standard", "Erika Apotheke"]
    assert cfg["inbox_default"] == "Erika Apotheke"  # any case, shown as written
    assert c.put("/api/ai", json={"inbox_default": "weg"}).json()["inbox_default"] == "Standard"   # unknown: the first
    c.put("/api/ai", json={"inbox_default": "Erika Apotheke"})
    c.post(f"/api/inbox/{key}/ai", json={})
    assert seen[-1].startswith("Das ist Erikas Apotheke.")
    c.post(f"/api/inbox/{key}/ai", json={"prompt": "standard"})
    assert seen[-1].startswith(AI_INSTRUCTIONS)
    assert c.post(f"/api/inbox/{key}/ai", json={"prompt": "Gibt es nicht"}).status_code == 400
    bad = [{"name": "A", "text": "x"}, {"name": "a", "text": "y"}]
    assert c.put("/api/ai", json={"inbox_prompts": bad}).status_code == 400
    assert c.put("/api/ai", json={"inbox_prompts": [{"name": "A", "text": ""}]}).status_code == 400
    # an old single saved text becomes "Standard"
    cfg = app.state.ai.load()
    cfg.inbox_prompts, cfg.inbox_prompt, cfg.inbox_default = [], "Mein alter Text", ""
    app.state.ai._save(cfg)
    assert c.get("/api/ai").json()["inbox_prompts"] == [{"name": "Standard", "text": "Mein alter Text"}]


def test_file_with_tags(env):
    app, c, inbox, fresh = env
    add_inbox(c, inbox, area="oliver")
    f = inbox / "brief.pdf"
    f.write_bytes(make_pdf("Spendenquittung Rotes Kreuz"))
    settle(f)
    process(app)
    key = c.get("/api/inbox").json()["items"][0]["key"]
    body = {"area": "oliver", "folder": "Steuer", "title": "Spendenquittung", "date": "2026-02-01"}
    assert c.post(f"/api/inbox/{key}/file", json={**body, "tags": ["x" * 50]}).status_code == 400
    assert f.exists()                                      # nothing filed with a bad tag
    res = c.post(f"/api/inbox/{key}/file", json={**body, "tags": ["Steuer 2026"]})
    assert res.status_code == 200
    assert app.state.tags.of(res.json()["sha256"]) == ["Steuer 2026"]


def test_filing_proposes_a_rule_in_plain_words(env):
    app, c, inbox, fresh = env
    add_inbox(c, inbox, area="oliver")
    f = inbox / "brief.pdf"
    f.write_bytes(make_pdf("Stadtwerke Musterstadt www.stadtwerke-muster.de Abschlag Strom 2026"))
    settle(f)
    process(app)
    key = c.get("/api/inbox").json()["items"][0]["key"]
    res = c.post(f"/api/inbox/{key}/file", json={"area": "oliver", "folder": "Wohnen/Strom",
                                                  "title": "Abschlag", "date": "2026-01-02"}).json()
    p = res["proposal"]
    assert p["label"] == "Post von Stadtwerke Muster" and p["folder"] == "Wohnen/Strom"
    # "Ja": the rule is created as learned, with its plain label
    assert c.post("/api/rules", json={"folder": p["folder"], "conditions": p["conditions"],
                                      "source": "learned", "label": p["label"]}).status_code == 201
    view = c.get("/api/rules/folder", params={"path": "Wohnen/Strom"}).json()
    assert view["rules"][0]["plain"] == "Post von Stadtwerke Muster" and view["rules"][0]["source"] == "learned"
    assert view["rules"][0]["stats"]["grade"] in ("green", "red")      # red until the index has the file
    # senders: rename, mark own address, decline
    app.state.index.scan()
    assert c.patch("/api/senders/stadtwerke-muster.de", json={"name": "Stadtwerke"}).json()["name"] == "Stadtwerke"
    rows = c.get("/api/senders").json()["senders"]
    assert rows[0]["name"] == "Stadtwerke" and rows[0]["docs"] == 1
    c.patch("/api/senders/stadtwerke-muster.de", json={"own": True})
    assert c.get("/api/senders").json()["senders"] == []
    assert c.post("/api/senders/x.de/decline", json={"folder": "A"}).json() == {"ok": True}
    # a small picture of the first page
    doc = c.get("/api/documents", params={"recursive": True}).json()["items"][0]
    thumb = c.get(f"/api/documents/{doc['id']}/thumb")
    assert thumb.status_code == 200 and thumb.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_delete_junk_from_inbox(env):
    app, c, inbox, fresh = env
    add_inbox(c, inbox)
    junk = inbox / "schrott.pdf"
    junk.write_bytes(make_pdf("Leere Seite"))
    settle(junk)
    process(app)
    item = c.get("/api/inbox").json()["items"][0]
    assert c.delete(f"/api/inbox/{item['key']}").status_code == 200
    assert not junk.exists()
    process(app)
    assert c.get("/api/inbox").json()["items"] == []
    assert c.get("/api/inbox", params={"status": "dismissed"}).json()["items"] == []
    assert c.delete(f"/api/inbox/{item['key']}").status_code == 400


def _file_one(app, c, inbox, fresh, text, name):
    f = inbox / name
    f.write_bytes(make_pdf(text))
    settle(f)
    process(app)
    item = next(i for i in c.get("/api/inbox").json()["items"] if i["name"] == name)
    res = c.post(f"/api/inbox/{item['key']}/file", json={"area": "oliver", "folder": "Post",
                                                         "title": name[:-4], "date": "2026-11-01"})
    assert res.status_code == 200, res.text
    return f, res.json()


def test_delete_after_verified_copy(env):
    app, c, inbox, fresh = env
    c.post("/api/storage/switch", json={"archive_path": str(fresh)})
    add_inbox(c, inbox, area="oliver", after_import="delete", delete_days=0)
    assert c.get("/api/storage").json()["inboxes"][0]["delete_days"] == 0
    f, body = _file_one(app, c, inbox, fresh, "Brief Nummer eins", "brief1.pdf")
    assert body["moved"] and not f.exists()
    assert not (inbox / "_importiert").exists()
    assert (fresh / body["path"]).read_bytes() == make_pdf("Brief Nummer eins")


def test_delete_keeps_original_when_copy_differs(env, monkeypatch):
    app, c, inbox, fresh = env
    c.post("/api/storage/switch", json={"archive_path": str(fresh)})
    add_inbox(c, inbox, area="oliver", after_import="delete", delete_days=0)
    monkeypatch.setattr(type(app.state.inbox), "_same_content", staticmethod(lambda *a: False))
    f, body = _file_one(app, c, inbox, fresh, "Brief Nummer zwei", "brief2.pdf")
    assert not body["moved"] and f.exists()            # not verified: the original stays


def test_delete_after_days(env):
    app, c, inbox, fresh = env
    c.post("/api/storage/switch", json={"archive_path": str(fresh)})
    add_inbox(c, inbox, area="oliver", after_import="delete", delete_days=7)
    f, body = _file_one(app, c, inbox, fresh, "Brief Nummer drei", "brief3.pdf")
    parked = inbox / "_importiert" / "brief3.pdf"
    assert body["moved"] and not f.exists() and parked.exists()
    app.state.index.scan()
    assert app.state.inbox.purge_done() == 0                      # too young
    assert app.state.inbox.purge_done(now=time.time() + 8 * 86400) == 1
    assert not parked.exists()
    # a parked file whose archive copy is gone stays
    stray = inbox / "_importiert" / "sub" / "fremd.pdf"
    stray.parent.mkdir(parents=True)
    stray.write_bytes(make_pdf("nicht im Archiv"))
    assert app.state.inbox.purge_done(now=time.time() + 30 * 86400) == 0 and stray.exists()


def test_delete_days_validated(env):
    app, c, inbox, fresh = env
    body = {"inboxes": [{"name": "S", "path": str(inbox), "after_import": "delete", "delete_days": -1}]}
    assert c.put("/api/storage", json=body).status_code == 400


def test_zero_days_cleans_up_old_parked_files(env):
    app, c, inbox, fresh = env
    c.post("/api/storage/switch", json={"archive_path": str(fresh)})
    add_inbox(c, inbox, area="oliver", after_import="move")
    f, body = _file_one(app, c, inbox, fresh, "Brief Nummer vier", "brief4.pdf")
    parked = inbox / "_importiert" / "brief4.pdf"
    assert parked.exists()
    add_inbox(c, inbox, area="oliver", after_import="delete", delete_days=0)
    app.state.index.scan()
    assert app.state.inbox.purge_done() == 1 and not parked.exists()
    assert not (inbox / "_importiert").exists() or not any((inbox / "_importiert").iterdir())
