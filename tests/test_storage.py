from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings


@pytest.fixture
def client(settings: Settings, tmp_path: Path, monkeypatch) -> TestClient:
    (tmp_path / "scanner").mkdir()
    (tmp_path / "scanner" / "scan1.pdf").write_bytes(b"%PDF")
    (tmp_path / "neu-archiv" / "oliver" / "Banken").mkdir(parents=True)
    monkeypatch.setenv("ORDNUNG_BROWSE_ROOTS", str(tmp_path))
    app = create_app(settings, background=False)
    app.state.index.scan()
    c = TestClient(app)
    assert c.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    return c


def test_defaults_to_environment_archive(client: TestClient, settings: Settings):
    data = client.get("/api/storage").json()
    assert data["archive_path"] == str(settings.archive)
    assert data["archive"]["readable"] is True
    assert data["inboxes"] == [] and data["processing_available"] is True


def test_inbox_is_configuration_only(client: TestClient, tmp_path: Path):
    res = client.put("/api/storage", json={"inboxes": [
        {"name": "Scanner", "path": str(tmp_path / "scanner"), "area": "oliver", "enabled": True}]})
    assert res.status_code == 200, res.text
    inbox = res.json()["inboxes"][0]
    assert inbox["name"] == "Scanner" and inbox["files"] == 1 and inbox["id"]
    assert (tmp_path / "scanner" / "scan1.pdf").exists()  # nothing was touched


def test_inbox_validation(client: TestClient, tmp_path: Path, settings: Settings):
    bad = client.put("/api/storage", json={"inboxes": [{"path": str(tmp_path / "fehlt")}]})
    assert bad.status_code == 400
    overlap = client.put("/api/storage", json={"inboxes": [{"path": str(settings.archive / "oliver")}]})
    assert overlap.status_code == 400 and overlap.json()["detail"] == "inbox and archive must not overlap"
    assert client.put("/api/storage", json={"archive_path": "relativ"}).status_code == 400


def test_change_archive_rescans(client: TestClient, tmp_path: Path):
    new = tmp_path / "neu-archiv"
    (new / "oliver" / "Banken" / "2026-01-01_Auszug.pdf").write_bytes(b"%PDF-1 x")
    assert client.put("/api/storage", json={"archive_path": str(new)}).status_code == 200
    client.app.state.index.scan()
    docs = client.get("/api/documents", params={"recursive": True}).json()
    assert docs["total"] == 1 and docs["items"][0]["title"] == "Auszug"


def test_folder_picker_stays_inside_roots(client: TestClient, tmp_path: Path):
    roots = [r["path"] for r in client.get("/api/fs/roots").json()]
    assert str(tmp_path) in roots
    listing = client.get("/api/fs/list", params={"path": str(tmp_path)}).json()
    assert "scanner" in listing["dirs"] and "neu-archiv" in listing["dirs"]
    assert client.get("/api/fs/list", params={"path": "/etc"}).status_code == 400


def test_area_labels(client: TestClient):
    client.patch("/api/users/oliver", json={"display_name": "Oliver Muster"})
    labels = {a["name"]: a["label"] for a in client.get("/api/areas").json()}
    assert labels["oliver"] == "Oliver Muster"      # from the account
    assert labels["gemeinsam"] == "Gemeinsam"        # capitalised
    assert labels[""] == ""                          # files without area
    client.put("/api/storage", json={"area_labels": {"gemeinsam": "Familie", "erika": "  "}})
    labels = {a["name"]: a["label"] for a in client.get("/api/areas").json()}
    assert labels["gemeinsam"] == "Familie" and labels["erika"] == "Erika"
