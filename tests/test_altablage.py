from datetime import date

from fastapi.testclient import TestClient

from ordnung.altablage import cutoff, from_alt, is_alt, prune_empty, to_alt
from test_api import client, login  # noqa: F401  (fixture)


def _doc(client, q, **params):
    return client.get("/api/documents", params={"recursive": True, "q": q, **params}).json()["items"][0]


def _search(client, q, **params):
    return client.get("/api/documents", params={"recursive": True, "q": q, **params}).json()["total"]


def test_helpers(tmp_path):
    assert is_alt("Altablage") and is_alt("Altablage/Banken") and not is_alt("Altablagen/x") and not is_alt("")
    assert to_alt("Banken/DKB") == "Altablage/Banken/DKB" and to_alt("") == "Altablage"
    assert from_alt("Altablage/Banken/DKB") == "Banken/DKB" and from_alt("Altablage") == ""
    assert cutoff(10, date(2026, 11, 8)) == "2016-11-08"
    assert cutoff(1, date(2028, 2, 29)) == "2027-02-28"
    keep = tmp_path / "a" / "x" / "voll"
    keep.mkdir(parents=True)
    (keep / "brief.pdf").write_bytes(b"x")
    empty = tmp_path / "a" / "x" / "leer" / "tief"
    empty.mkdir(parents=True)
    (empty / ".DS_Store").write_bytes(b"x")
    assert prune_empty(tmp_path, {empty}) == 2          # tief and leer, x still holds "voll"
    assert keep.is_dir() and (tmp_path / "a").is_dir() and not (tmp_path / "a/x/leer").exists()


def test_single_document_and_back(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "kontoauszug")
    res = client.post("/api/altablage", json={"ids": [doc["id"]]})
    assert res.status_code == 200, res.text
    assert res.json()["moved"] == 1
    assert (settings.archive / "oliver/Altablage/Banken/DKB/2026-03-01_Kontoauszug.pdf").is_file()
    assert not (settings.archive / "oliver/Banken/DKB").exists()          # emptied folder is gone
    # hidden from the search, unless asked for
    assert _search(client, "kontoauszug") == 0
    assert _search(client, "kontoauszug", alt=True) == 1
    # the tree keeps it apart
    tree = client.get("/api/tree").json()
    assert all(c["name"] != "Altablage" for c in tree["children"])
    assert tree["alt"]["count"] == 1 and tree["alt"]["children"][0]["path"] == "Altablage/Banken"
    assert tree["count"] == 5
    # browsing the Altablage folder works without the switch
    inside = client.get("/api/documents", params={"folder": "Altablage", "recursive": True}).json()
    assert inside["total"] == 1
    # moving it again is a no-op, restoring puts it back
    assert client.post("/api/altablage", json={"ids": [doc["id"]]}).json()["moved"] == 0
    back = client.post("/api/altablage", json={"ids": [doc["id"]], "restore": True})
    assert back.json()["moved"] == 1
    assert client.get(f"/api/documents/{doc['id']}").json()["folder"] == "Banken/DKB"
    assert not (settings.archive / "oliver/Altablage").exists()


def test_whole_folder_across_areas(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    client.post("/api/folders", json={"path": "Versicherungen/Continentale/Wohngebäude"})
    dry = client.post("/api/altablage", json={"folder": "Versicherungen", "dry_run": True}).json()
    assert dry["count"] == 2 and {f["folder"] for f in dry["folders"]} == {
        "Versicherungen/Continentale/Wohngebäude", "Versicherungen/ARAG"}
    assert (settings.archive / "oliver/Banken/DKB/2026-03-01_Kontoauszug.pdf").is_file()   # dry run moves nothing
    res = client.post("/api/altablage", json={"folder": "Versicherungen"}).json()
    assert res["moved"] == 2 and res["folder_removed"]
    names = [c["name"] for c in client.get("/api/tree").json()["children"]]
    assert "Versicherungen" not in names                                  # no empty plan folder left
    assert all(not f["path"].startswith("Altablage")
               for f in client.get("/api/folders").json()["folders"])     # never a filing target
    assert client.post("/api/altablage", json={"folder": "Altablage/Versicherungen"}).status_code == 400
    back = client.post("/api/altablage", json={"folder": "Versicherungen", "restore": True}).json()
    assert back["moved"] == 2
    assert (settings.archive / "gemeinsam/Versicherungen/ARAG/2025-05-05_Rechtsschutz.pdf").is_file()


def test_older_than_years(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    old = settings.archive / "oliver/Banken/DKB/2001-02-03_Altvertrag.pdf"
    old.write_bytes(old.with_name("2026-03-01_Kontoauszug.pdf").read_bytes() + b"\n")
    client.app.state.index.scan()
    dry = client.post("/api/altablage", json={"older_than_years": 10, "dry_run": True}).json()
    assert dry == {"count": 1, "folders": [{"folder": "Banken/DKB", "count": 1}]}   # undated root file stays
    assert client.post("/api/altablage", json={"older_than_years": 10, "restore": True}).status_code == 400
    assert client.post("/api/altablage", json={"older_than_years": 10}).json()["moved"] == 1
    assert (settings.archive / "oliver/Altablage/Banken/DKB/2001-02-03_Altvertrag.pdf").is_file()
    assert client.post("/api/altablage", json={"older_than_years": 10, "dry_run": True}).json()["count"] == 0


def test_needs_write_access_and_one_choice(client: TestClient):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "rechtsschutz")
    assert client.post("/api/altablage", json={}).status_code == 400
    assert client.post("/api/altablage", json={"ids": [doc["id"]], "folder": "X"}).status_code == 400
    client.post("/api/users", json={"name": "erika", "password": "erika-pass-2026", "areas": {"gemeinsam": "read"}})
    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass-2026")
    assert erika.post("/api/altablage", json={"ids": [doc["id"]]}).status_code == 404
    assert erika.post("/api/altablage", json={"folder": "Versicherungen"}).json()["moved"] == 0


def test_tags_only_in_altablage_stay_hidden(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    old, new = _doc(client, "kontoauszug"), _doc(client, "rechtsschutz")
    client.put(f"/api/documents/{old['id']}/tags", json={"tags": ["Alte Bank", "Beides"]})
    client.put(f"/api/documents/{new['id']}/tags", json={"tags": ["Beides"]})
    client.post("/api/altablage", json={"ids": [old["id"]]})
    names = lambda **p: {t["name"]: t["count"] for t in client.get("/api/tags", params=p).json()}  # noqa: E731
    assert names() == {"Beides": 1}
    assert names(alt=True) == {"Alte Bank": 1, "Beides": 2}
