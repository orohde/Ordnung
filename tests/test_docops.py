from fastapi.testclient import TestClient

from test_api import client, login  # noqa: F401  (fixture)


def _doc(client, q):
    return client.get("/api/documents", params={"recursive": True, "q": q}).json()["items"][0]


def test_move_into_other_folder(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "kontoauszug")
    res = client.post(f"/api/documents/{doc['id']}/move", json={"folder": "Banken/Sparkasse"})
    assert res.status_code == 200, res.text
    assert res.json()["path"] == "oliver/Banken/Sparkasse/2026-03-01_Kontoauszug.pdf"
    assert (settings.archive / "oliver/Banken/Sparkasse/2026-03-01_Kontoauszug.pdf").is_file()
    assert not (settings.archive / doc["path"]).exists()
    assert client.get(f"/api/documents/{doc['id']}").json()["folder"] == "Banken/Sparkasse"
    same = client.post(f"/api/documents/{doc['id']}/move", json={"folder": "Banken/Sparkasse"})
    assert same.status_code == 400
    assert client.post(f"/api/documents/{doc['id']}/move", json={"folder": "../x"}).status_code == 400


def test_trash_and_restore(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "rechtsschutz")
    res = client.post(f"/api/documents/{doc['id']}/trash")
    assert res.status_code == 200, res.text
    trash = res.json()["trash_path"]
    assert trash.startswith(".papierkorb/") and trash.endswith(doc["path"])
    assert (settings.archive / trash).is_file()                 # never deleted for good
    assert client.get(f"/api/documents/{doc['id']}").status_code == 404
    assert client.post("/api/trash/restore", json={"trash_path": "../etc/passwd"}).status_code == 400
    back = client.post("/api/trash/restore", json={"trash_path": trash})
    assert back.status_code == 200 and back.json()["path"] == doc["path"]
    assert client.get(f"/api/documents/{doc['id']}").status_code == 200


def test_readers_cannot_move_or_trash(client: TestClient):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "rechtsschutz")
    client.post("/api/users", json={"name": "erika", "password": "erika-pass", "areas": {"gemeinsam": "read"}})
    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass")
    assert erika.post(f"/api/documents/{doc['id']}/trash").status_code == 403
    assert erika.post(f"/api/documents/{doc['id']}/move", json={"folder": "X"}).status_code == 403


def test_change_title_and_date(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    doc = next(d for d in client.get("/api/documents", params={"recursive": True, "q": "rezept"}).json()["items"]
               if d["name"].endswith("_a3f9c1.pdf"))
    res = client.patch(f"/api/documents/{doc['id']}", json={"title": "Rezept Ibuprofen", "date": "2026-09-30"})
    assert res.status_code == 200, res.text
    assert res.json()["path"] == "erika/Gesundheit/Rezepte/2026-09-30_Rezept Ibuprofen_a3f9c1.pdf"
    new = client.get(f"/api/documents/{doc['id']}").json()
    assert (new["title"], new["date"]) == ("Rezept Ibuprofen", "2026-09-30")
    assert client.patch(f"/api/documents/{doc['id']}", json={"title": "x", "date": "2026-13-01"}).status_code == 400
    assert client.patch(f"/api/documents/{doc['id']}", json={"title": "  ", "date": "2026-01-01"}).status_code == 400


def test_trash_listing_and_file(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.get("/api/trash").json()["items"] == []
    doc = _doc(client, "kontoauszug")
    trash = client.post(f"/api/documents/{doc['id']}/trash").json()["trash_path"]
    items = client.get("/api/trash").json()["items"]
    assert [(i["title"], i["folder"], i["area"]) for i in items] == [("Kontoauszug", "Banken/DKB", "oliver")]
    assert client.get("/api/trash/file", params={"path": trash}).content.startswith(b"%PDF")
    assert client.get("/api/trash/file", params={"path": ".papierkorb/../../x"}).status_code == 404
    client.post("/api/users", json={"name": "erika", "password": "erika-pass", "areas": {"erika": "write"}})
    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass")
    assert erika.get("/api/trash").json()["items"] == []
    assert erika.get("/api/trash/file", params={"path": trash}).status_code == 404


def test_tree_shows_empty_template_folders(client: TestClient):
    login(client, "oliver", "geheim123")
    client.post("/api/folders", json={"path": "Sonstiges/Hochzeit 2025/Unterlagen Erika"})
    tree = client.get("/api/tree").json()
    names = [c["name"] for c in tree["children"]]
    assert "Sonstiges" in names


def test_mappen(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.post("/api/mappen", json={"name": "Steuererklärung 2026", "area": "gemeinsam"}).status_code == 201
    assert client.post("/api/mappen", json={"name": "steuererklärung 2026", "area": "oliver"}).status_code == 409
    assert client.post("/api/mappen", json={"name": "X", "area": "nirgends"}).status_code == 400
    assert client.get("/api/mappen").json() == [
        {"name": "Steuererklärung 2026", "area": "gemeinsam", "count": 0, "writable": True}]
    ids = [_doc(client, "kontoauszug")["id"], _doc(client, "rechtsschutz")["id"]]
    client.post("/api/tags/change", json={"ids": ids, "add": ["Steuererklärung 2026"]})
    assert client.get("/api/mappen").json()[0]["count"] == 2
    z = client.get("/api/mappen/download", params={"name": "Steuererklärung 2026"})
    assert z.status_code == 200 and z.content[:2] == b"PK"
    import io
    import zipfile
    assert len(zipfile.ZipFile(io.BytesIO(z.content)).namelist()) == 2
    pdf = client.get("/api/mappen/download", params={"name": "Steuererklärung 2026", "format": "pdf"})
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    import pypdfium2 as pdfium
    assert len(pdfium.PdfDocument(pdf.content)) == 2
    assert client.patch("/api/mappen", json={"old": "Steuererklärung 2026", "new": "Steuer 2026"}).json()["changed"] == 2
    assert client.get(f"/api/documents/{ids[0]}").json()["tags"] == ["Steuer 2026"]
    assert client.delete("/api/mappen", params={"name": "Steuer 2026"}).json()["changed"] == 2
    assert client.get("/api/mappen").json() == []
    assert client.get(f"/api/documents/{ids[0]}").status_code == 200        # the document itself stays


def test_trash_purge(settings):
    from datetime import date

    from ordnung.docops import purge_trash
    root = settings.archive
    old = root / ".papierkorb" / "2026-01-01" / "oliver" / "a.pdf"
    new = root / ".papierkorb" / "2026-11-01" / "oliver" / "b.pdf"
    for p in (old, new):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"%PDF-1.4")
    assert purge_trash(root, 0, date(2026, 11, 7)) == 0          # 0 = never
    assert purge_trash(root, 30, date(2026, 11, 7)) == 1
    assert not old.exists() and new.exists()


def test_trash_days_setting(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.get("/api/storage").json()["trash_days"] == 30
    assert client.put("/api/storage", json={"trash_days": 90}).json()["trash_days"] == 90
    assert client.put("/api/storage", json={"trash_days": -1}).status_code == 400
    assert client.get("/api/trash").json()["days"] == 90


def test_mappe_belongs_to_area(client: TestClient):
    login(client, "oliver", "geheim123")
    client.post("/api/users", json={"name": "erika", "password": "erika-pass",
                                    "areas": {"erika": "write", "gemeinsam": "read"}})
    assert client.post("/api/mappen", json={"name": "Pflegegrad", "area": "oliver"}).status_code == 201
    assert client.post("/api/mappen", json={"name": "Hochzeit", "area": "gemeinsam"}).status_code == 201
    rezept = _doc(client, "rezept")                          # in Erika's area, readable for her
    client.post("/api/tags/change", json={"ids": [rezept["id"]], "add": ["Pflegegrad", "privat"]})
    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass")
    assert [m["name"] for m in erika.get("/api/mappen").json()] == ["Hochzeit"]
    assert erika.get("/api/mappen/download", params={"name": "Pflegegrad"}).status_code == 404
    assert erika.get(f"/api/documents/{rezept['id']}").json()["tags"] == ["privat"]      # label hidden
    assert "Pflegegrad" not in [t["name"] for t in erika.get("/api/tags").json()]
    # Erika saves her tags: the hidden label must survive
    erika.put(f"/api/documents/{rezept['id']}/tags", json={"tags": ["privat", "Apotheke"]})
    assert "Pflegegrad" in client.get(f"/api/documents/{rezept['id']}").json()["tags"]
    # read-only area: neither create nor change
    assert erika.post("/api/mappen", json={"name": "Neu", "area": "gemeinsam"}).status_code == 403
    assert erika.delete("/api/mappen", params={"name": "Hochzeit"}).status_code == 403
    assert erika.post("/api/mappen", json={"name": "Erikas Mappe", "area": "erika"}).status_code == 201
    # move a Mappe to another area
    assert client.patch("/api/mappen", json={"old": "Pflegegrad", "area": "erika"}).status_code == 200
    assert "Pflegegrad" in [m["name"] for m in erika.get("/api/mappen").json()]


def test_move_into_other_area(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "kontoauszug")
    client.post("/api/areas", json={"name": "haus"})
    res = client.post(f"/api/documents/{doc['id']}/move", json={"folder": doc["folder"], "area": "haus"})
    assert res.status_code == 200, res.text
    assert res.json()["path"].startswith("haus/")
    assert (settings.archive / res.json()["path"]).is_file() and not (settings.archive / doc["path"]).exists()
    moved = client.get(f"/api/documents/{doc['id']}").json()
    assert moved["area"] == "haus"
    assert client.post(f"/api/documents/{doc['id']}/move", json={"folder": "", "area": "gibtsnicht"}).status_code == 400
    assert client.post(f"/api/documents/{doc['id']}/move", json={"folder": "", "area": "../x"}).status_code == 400


def test_move_into_area_without_write_access(client: TestClient):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "rechtsschutz")
    client.post("/api/areas", json={"name": "haus"})
    client.post("/api/users", json={"name": "erika2", "password": "erika-pass",
                                    "areas": {doc["area"]: "write", "haus": "read"}})
    erika = TestClient(client.app)
    login(erika, "erika2", "erika-pass")
    res = erika.post(f"/api/documents/{doc['id']}/move", json={"folder": "", "area": "haus"})
    assert res.status_code == 403
