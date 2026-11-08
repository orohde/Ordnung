import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings
from ordnung.tags import TagError, TagStore, clean


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings, background=False)
    app.state.index.scan()
    c = TestClient(app)
    assert c.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    return c


def doc_id(c: TestClient, needle: str) -> str:
    items = c.get("/api/documents", params={"recursive": True}).json()["items"]
    return next(d["id"] for d in items if needle in d["path"])


def test_clean_and_store(tmp_path):
    assert clean("  Steuer,  2026 #x ") == "Steuer 2026 x"
    with pytest.raises(TagError):
        clean("x" * 41)
    store = TagStore(tmp_path / "tags.json")
    assert store.set("a" * 64, ["Steuer 2026", "haus", "Haus", ""]) == ["haus", "Steuer 2026"]
    # the existing spelling wins, duplicates (any case) are dropped
    assert store.change(["b" * 64], ["steuer 2026", "Neu"], []) == 1
    assert store.of("b" * 64) == ["Neu", "Steuer 2026"]
    assert store.change(["a" * 64, "b" * 64], [], ["STEUER 2026"]) == 2
    assert store.shas_with_all(["neu"]) == {"b" * 64}
    assert store.counts() == [{"name": "haus", "count": 1}, {"name": "Neu", "count": 1}]
    assert TagStore(tmp_path / "tags.json").of("a" * 64) == ["haus"]      # persisted


def test_tag_documents_filter_and_search(client: TestClient):
    kto = doc_id(client, "Kontoauszug")
    wg = doc_id(client, "Versicherungsschein")
    assert client.put(f"/api/documents/{kto}/tags", json={"tags": ["Steuer 2026"]}).json() == {"tags": ["Steuer 2026"]}
    assert client.get(f"/api/documents/{kto}").json()["tags"] == ["Steuer 2026"]
    res = client.post("/api/tags/change", json={"ids": [kto, wg], "add": ["Haus Musterweg", "steuer 2026"]})
    assert res.json() == {"changed": 2}
    assert client.get("/api/tags").json() == [{"name": "Haus Musterweg", "count": 2}, {"name": "Steuer 2026", "count": 2}]

    # filter across folders, also from the root without "recursive"
    found = client.get("/api/documents", params={"tags": "Steuer 2026"}).json()
    assert found["total"] == 2 and all("Steuer 2026" in d["tags"] for d in found["items"])
    # "#steuer2026" in the search box, combined with a word
    found = client.get("/api/documents", params={"q": "#steuer2026 kontoauszug"}).json()
    assert [d["id"] for d in found["items"]] == [kto]
    assert client.get("/api/documents", params={"q": "#gibtsnicht"}).json()["total"] == 0

    client.post("/api/tags/change", json={"ids": [wg], "remove": ["Steuer 2026"]})
    assert client.get("/api/tags").json()[1] == {"name": "Steuer 2026", "count": 1}
    assert client.put(f"/api/documents/{kto}/tags", json={"tags": ["x" * 50]}).status_code == 400


def test_tags_need_write_access(client: TestClient):
    erika = doc_id(client, "erika/Gesundheit")
    kto = doc_id(client, "Kontoauszug")
    client.post("/api/users", json={"name": "leser", "password": "leser-pass-2026",
                                    "areas": {"erika": "read", "oliver": "write"}})
    client.post("/api/logout")
    assert client.post("/api/login", json={"username": "leser", "password": "leser-pass-2026"}).status_code == 200
    assert client.put(f"/api/documents/{erika}/tags", json={"tags": ["x"]}).status_code == 403
    assert client.post("/api/tags/change", json={"ids": [erika], "add": ["x"]}).status_code == 404
    assert client.put(f"/api/documents/{kto}/tags", json={"tags": ["Steuer"]}).status_code == 200
    # tag counts only cover what the user can see
    assert client.get("/api/tags").json() == [{"name": "Steuer", "count": 1}]
