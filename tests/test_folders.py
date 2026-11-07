import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings
from ordnung.folders import clean_path, FolderError


def test_clean_path():
    assert clean_path(" Banken / DKB ") == "Banken/DKB"
    for bad in ["", "../x", "a/./b", ".versteckt", "a:b"]:
        with pytest.raises(FolderError):
            clean_path(bad)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings, background=False)
    app.state.index.scan()
    c = TestClient(app)
    assert c.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    return c


def paths(client):
    return {f["path"]: f for f in client.get("/api/folders").json()["folders"]}


def test_add_empty_folder_shows_in_tree(client: TestClient):
    assert client.post("/api/folders", json={"path": "Auto/T-Roc/Versicherung"}).status_code == 201
    f = paths(client)
    assert f["Auto/T-Roc/Versicherung"]["template_only"] and f["Auto"]["template_only"]
    assert not f["Gesundheit/Rezepte"]["template_only"]
    tree = client.get("/api/tree").json()          # the archive view shows empty template folders too
    auto = next(c for c in tree["children"] if c["name"] == "Auto")
    assert auto["count"] == 0 and auto["children"][0]["name"] == "T-Roc"
    assert client.post("/api/folders", json={"path": "gesundheit/rezepte"}).status_code == 400  # exists


def test_starter_template(client: TestClient):
    added = client.post("/api/folders/starter").json()["added"]
    assert added > 30
    assert client.post("/api/folders/starter").json()["added"] == 0


def test_delete_only_empty(client: TestClient):
    client.post("/api/folders", json={"path": "Leer/Unterordner"})
    assert client.delete("/api/folders", params={"path": "Gesundheit/Rezepte"}).status_code == 400
    assert client.delete("/api/folders", params={"path": "Leer"}).status_code == 200
    assert "Leer/Unterordner" not in paths(client)


def test_rename_template_folder_moves_rules(client: TestClient):
    client.post("/api/folders", json={"path": "Neu/Alt"})
    client.post("/api/rules", json={"folder": "Neu/Alt", "conditions": [{"type": "contains", "value": "Irgendwas"}]})
    res = client.patch("/api/folders", json={"old": "Neu/Alt", "new": "Neu/Besser"}).json()
    assert res["rules"] == 1 and res["moved_areas"] == 0
    assert "Neu/Besser" in paths(client)
    assert client.get("/api/rules").json()["folders"]["Neu/Besser"]["rules"] == 1


def test_rename_folder_with_documents(client: TestClient, settings: Settings):
    # archive is writable in tests: documents move on disk in every area
    res = client.patch("/api/folders", json={"old": "Gesundheit/Rezepte", "new": "Gesundheit/Verordnungen"})
    assert res.status_code == 200 and res.json()["moved_areas"] == 1
    assert (settings.archive / "erika/Gesundheit/Verordnungen").is_dir()
    docs = client.get("/api/documents", params={"folder": "Gesundheit/Verordnungen"}).json()
    assert docs["total"] == 2


def test_rename_with_documents_needs_writable_archive(client: TestClient, settings: Settings):
    (settings.archive).chmod(0o555)
    try:
        res = client.patch("/api/folders", json={"old": "Gesundheit/Rezepte", "new": "Gesundheit/X"})
        assert res.status_code == 400 and res.json()["detail"] == "archive is read-only"
    finally:
        (settings.archive).chmod(0o755)
