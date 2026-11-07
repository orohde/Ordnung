from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings
from ordnung.importplan import collapse_doubles


def test_collapse_doubles():
    assert collapse_doubles("Finanzamt/Finanzamt/Belege") == "Finanzamt/Belege"
    assert collapse_doubles("Apotheke/Apothekenkammer/Apothekenkammer") == "Apotheke/Apothekenkammer"
    assert collapse_doubles("Auto/T-Roc") == "Auto/T-Roc"


@pytest.fixture
def client(settings: Settings) -> TestClient:
    extra = {
        "oma/Finanzamt/Finanzamt/Belege/2024-01-01_Beleg.pdf": b"%PDF a1",
        "oma/Finanzamt/Finanzamt/Belege/2024-02-01_Beleg 2.pdf": b"%PDF a2",
        "oma/Auto/T-Roc/2024-01-01_Rechnung.pdf": b"%PDF b1",
        "oma/Auto/HUK24/T-Roc/2024-01-01_Police.pdf": b"%PDF b2",
    }
    for rel, data in extra.items():
        p = settings.archive / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    app = create_app(settings, background=False)
    app.state.index.scan()
    c = TestClient(app)
    assert c.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    return c


def rows_by(client):
    return {(r["area"], r["folder"]): r for r in client.get("/api/import/plan").json()["rows"]}


def test_suggestions(client: TestClient):
    rows = rows_by(client)
    dbl = rows[("oma", "Finanzamt/Finanzamt/Belege")]
    assert dbl["target_folder"] == "Finanzamt/Belege" and "double" in dbl["reasons"] and dbl["moves"]
    troc = rows[("oma", "Auto/T-Roc")]
    assert "scattered" in troc["hints"] and troc["same_name"] == ["Auto/HUK24/T-Roc"]
    assert "no_area" in rows[("", "")]["hints"]
    assert "single" in rows[("oliver", "Banken/DKB")]["hints"]


def test_decisions_and_summary(client: TestClient, settings: Settings):
    client.put("/api/import/plan/row", json={"area": "oma", "folder": "Auto/HUK24/T-Roc",
                                             "target_area": "oma", "target_folder": "Auto/T-Roc/Versicherung"})
    row = rows_by(client)[("oma", "Auto/HUK24/T-Roc")]
    assert row["target_folder"] == "Auto/T-Roc/Versicherung" and row["confirmed"] and row["manual"]
    assert client.put("/api/import/plan/row", json={"area": "a", "folder": "b", "target_area": "a",
                                                    "target_folder": "x/../y"}).status_code == 400
    client.delete("/api/import/plan/row", params={"area": "oma", "folder": "Auto/HUK24/T-Roc"})
    assert not rows_by(client)[("oma", "Auto/HUK24/T-Roc")]["manual"]
    summary = client.get("/api/import/plan").json()["summary"]
    assert summary["folders_after"] < summary["folders_before"]
    confirmed = client.post("/api/import/plan/confirm-all").json()["confirmed"]
    assert confirmed == summary["folders_before"] - 1   # the area-less row needs a decision
    files = list(settings.archive.rglob("*.pdf"))
    assert len(files) == 11                               # nothing was moved or copied


def test_target_tree(client: TestClient):
    tree = client.get("/api/import/tree").json()
    finanz = next(c for c in tree["children"] if c["name"] == "Finanzamt")
    assert [c["name"] for c in finanz["children"]] == ["Belege"]


def test_spelling_variants(settings: Settings, monkeypatch):
    # case-only differences cannot be created on a case-insensitive Mac file system
    from ordnung.importplan import ImportPlanner
    planner = ImportPlanner(settings.data / "plan.json", None)
    monkeypatch.setattr(planner, "_folders", lambda: [
        ("oliver", "Banken/kontoauszüge", 1), ("oliver", "Banken/Kontoauszüge", 5)])
    rows = {r["folder"]: r for r in planner.suggestions()}
    assert rows["Banken/kontoauszüge"]["suggested_folder"] == "Banken/Kontoauszüge"
    assert "spelling" in rows["Banken/kontoauszüge"]["reasons"]
    assert rows["Banken/Kontoauszüge"]["reasons"] == []
