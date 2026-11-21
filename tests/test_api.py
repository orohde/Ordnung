import json

import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings, background=False)
    app.state.index.scan()
    return TestClient(app)


def login(client: TestClient, name: str, password: str) -> None:
    res = client.post("/api/login", json={"username": name, "password": password})
    assert res.status_code == 200, res.text


def test_requires_login(client: TestClient):
    assert client.get("/api/tree").status_code == 401
    assert client.post("/api/login", json={"username": "oliver", "password": "falsch"}).status_code == 401


def test_first_admin_from_environment(client: TestClient, settings: Settings):
    assert settings.users_path.exists()
    assert "geheim123" not in settings.users_path.read_text()
    login(client, "oliver", "geheim123")
    assert client.get("/api/me").json()["is_admin"] is True


def test_documents_and_file(client: TestClient):
    login(client, "oliver", "geheim123")
    docs = client.get("/api/documents", params={"recursive": True, "q": "rezept"}).json()
    assert docs["total"] == 2
    doc_id = docs["items"][0]["id"]
    res = client.get(f"/api/documents/{doc_id}/file")
    assert res.status_code == 200 and res.content.startswith(b"%PDF")
    assert client.get("/api/documents/abcdef/file").status_code == 404
    assert client.get("/api/documents", params={"q": "rezept"}).json()["total"] == 2   # a search covers everything
    best = client.get("/api/documents", params={"recursive": True, "q": "rezept", "sort": "relevance"}).json()
    assert best["total"] == 2
    assert client.get("/api/documents", params={"sort": "zufall"}).status_code == 422


def test_api_token(client: TestClient):
    assert client.get("/api/me", headers={"Authorization": "Bearer tok"}).status_code == 200
    assert client.get("/api/me", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_api_keys_in_settings(client: TestClient):
    login(client, "oliver", "geheim123")
    # the key from before lives on as the named key "API", the settings file forgets the plain text
    keys = client.get("/api/security/api-keys").json()
    assert [(k["name"], k["right"]) for k in keys] == [("API", "write")]
    assert "hash" not in keys[0] and "token" not in keys[0] and keys[0]["hint"] == "tok"[-4:]
    assert client.app.state.security.load().api_token == ""
    assert json.loads((client.app.state.settings.data / "security.json").read_text())["api_token"] == ""
    made = client.post("/api/security/api-keys", json={"name": "Claude"}).json()
    token = made["token"]
    assert token.startswith("ord_") and made["right"] == "write"
    assert "ord_" not in client.app.state.apikeys.path.read_text()        # only the hash is stored
    assert client.post("/api/security/api-keys", json={"name": "claude"}).status_code == 409
    assert client.post("/api/security/api-keys", json={"name": "x", "right": "admin"}).status_code == 422
    bearer = {"Authorization": f"Bearer {token}"}
    client.cookies.clear()
    assert client.get("/api/me", headers=bearer).json()["is_admin"] is True
    assert client.get("/api/security/api-keys", headers=bearer).json()[1]["last"]   # use is remembered
    renewed = client.post(f"/api/security/api-keys/{made['id']}/renew", headers=bearer).json()["token"]
    assert client.get("/api/me", headers=bearer).status_code == 401
    bearer = {"Authorization": f"Bearer {renewed}"}
    assert client.get("/api/me", headers=bearer).status_code == 200
    assert client.patch(f"/api/security/api-keys/{made['id']}", json={"name": "Claude Code"},
                        headers=bearer).json()["name"] == "Claude Code"
    assert client.delete(f"/api/security/api-keys/{made['id']}", headers=bearer).status_code == 200
    assert client.get("/api/me", headers=bearer).status_code == 401
    assert client.get("/api/me", headers={"Authorization": "Bearer tok"}).status_code == 200   # the other one still works
    assert client.delete("/api/security/api-keys/nope", headers={"Authorization": "Bearer tok"}).status_code == 404
    # the environment does not bring a deleted key back
    old = client.get("/api/security/api-keys", headers={"Authorization": "Bearer tok"}).json()[0]["id"]
    client.delete(f"/api/security/api-keys/{old}", headers={"Authorization": "Bearer tok"})
    assert client.get("/api/me", headers={"Authorization": "Bearer tok"}).status_code == 401
    assert not client.app.state.security.import_api_token("tok")


def test_key_from_before_survives_the_update(settings: Settings):
    """An installation from before named keys: its one token in security.json keeps working."""
    from dataclasses import replace

    from ordnung.app import create_app

    settings = replace(settings, api_token="")
    (settings.data / "security.json").write_text(json.dumps({"api_token": "alter-schluessel-123"}))
    app = create_app(settings, background=False)
    app.state.index.scan()
    c = TestClient(app)
    assert c.get("/api/documents", headers={"Authorization": "Bearer alter-schluessel-123"}).json()["total"] > 0
    assert "alter-schluessel-123" not in (settings.data / "security.json").read_text()
    assert "alter-schluessel-123" not in (settings.data / "apikeys.json").read_text()
    # a second start changes nothing
    again = TestClient(create_app(settings, background=False))
    assert [k.name for k in again.app.state.apikeys.all()] == ["API"]
    assert again.get("/api/me", headers={"Authorization": "Bearer alter-schluessel-123"}).status_code == 200


def test_reading_key(client: TestClient):
    login(client, "oliver", "geheim123")
    token = client.post("/api/security/api-keys", json={"name": "Nur lesen", "right": "read"}).json()["token"]
    client.cookies.clear()
    bearer = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/me", headers=bearer).json()
    assert me["is_admin"] is False and set(me["areas"]) >= {"oliver", "erika", "gemeinsam"} and me["write_areas"] == []
    assert client.get("/api/documents", params={"q": "rezept"}, headers=bearer).json()["total"] == 2
    doc = client.get("/api/documents", params={"q": "rezept"}, headers=bearer).json()["items"][0]
    assert client.get(f"/api/documents/{doc['id']}/text", headers=bearer).status_code == 200
    # admin-only routes stay shut, and nothing that changes anything goes through
    for path in ("/api/security/api-keys", "/api/inbox", "/api/users", "/api/system/settings"):
        assert client.get(path, headers=bearer).status_code == 403, path
    assert client.put(f"/api/documents/{doc['id']}/tags", json={"tags": ["x"]}, headers=bearer).status_code == 403
    assert client.patch(f"/api/documents/{doc['id']}", json={"title": "x", "date": "2026-01-01"},
                        headers=bearer).status_code == 403
    assert client.post(f"/api/documents/{doc['id']}/trash", headers=bearer).status_code == 403
    assert client.put("/api/me/prefs", json={"language": "en"}, headers=bearer).status_code == 403
    assert client.post("/api/mappen", json={"name": "M", "area": "oliver"}, headers=bearer).status_code == 403


def test_date_filter(client: TestClient):
    login(client, "oliver", "geheim123")
    get = lambda **p: client.get("/api/documents", params={"recursive": True, **p}).json()["total"]
    assert get(date_from="2026") == 3
    assert get(date_from="2026-03", date_to="2026-03") == 1
    assert get(date_to="2024-12-31") == 1
    assert client.get("/api/documents", params={"date_from": "gestern"}).status_code == 422


def test_user_management_and_area_rights(client: TestClient, settings: Settings):
    login(client, "oliver", "geheim123")
    res = client.post("/api/users", json={
        "name": "erika", "password": "erika-pass-2026", "display_name": "Erika",
        "areas": {"erika": "write", "gemeinsam": "read", "oliver": "bogus"},
    })
    assert res.status_code == 201, res.text
    assert res.json()["areas"] == {"erika": "write", "gemeinsam": "read"}
    assert client.post("/api/users", json={"name": "erika", "password": "xxxxxxxx"}).status_code == 400
    assert client.post("/api/users", json={"name": "kurz", "password": "123"}).status_code == 400

    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass-2026")
    assert {a["name"] for a in erika.get("/api/areas").json()} == {"erika", "gemeinsam"}
    docs = erika.get("/api/documents", params={"recursive": True}).json()
    assert {d["area"] for d in docs["items"]} == {"erika", "gemeinsam"}
    assert erika.get("/api/users").status_code == 403
    secret = client.get("/api/documents", params={"recursive": True, "q": "kontoauszug"}).json()["items"][0]
    assert erika.get(f"/api/documents/{secret['id']}/file").status_code == 404

    assert client.patch("/api/users/erika", json={"areas": {"erika": "read"}}).status_code == 200
    assert {a["name"] for a in erika.get("/api/areas").json()} == {"erika"}


def test_admin_safeguards(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.delete("/api/users/oliver").status_code == 400
    assert client.patch("/api/users/oliver", json={"is_admin": False}).status_code == 400


def test_deleted_user_loses_session(client: TestClient):
    login(client, "oliver", "geheim123")
    client.post("/api/users", json={"name": "gast", "password": "gast-pass-2026"})
    guest = TestClient(client.app)
    login(guest, "gast", "gast-pass-2026")
    assert guest.get("/api/me").status_code == 200
    client.delete("/api/users/gast")
    assert guest.get("/api/me").status_code == 401


def test_change_own_password(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.post("/api/me/password", json={"old": "falsch", "new": "neu-1234567890"}).status_code == 403
    assert client.post("/api/me/password", json={"old": "geheim123", "new": "neu-1234567890"}).status_code == 200
    fresh = TestClient(client.app)
    login(fresh, "oliver", "neu-1234567890")


def test_ai_settings_never_return_key(client: TestClient, settings: Settings):
    login(client, "oliver", "geheim123")
    res = client.put("/api/ai", json={"enabled": True, "api_key": "sk-ant-test-1234567890", "monthly_limit_usd": 5})
    assert res.status_code == 200
    body = res.json()
    assert "api_key" not in body and body["key_set"] is True and body["key_hint"] == "…7890"
    assert "sk-ant-test" not in client.get("/api/ai").text
    assert oct((settings.data / "ai.json").stat().st_mode)[-3:] == "600"
    assert client.put("/api/ai", json={"clear_key": True}).json()["key_set"] is False
    assert client.put("/api/ai", json={"provider": "nope"}).status_code == 400


def test_ai_test_without_key_fails_cleanly(client: TestClient):
    login(client, "oliver", "geheim123")
    res = client.post("/api/ai/test")
    assert res.status_code == 400 and res.json()["detail"] == "no API key"


def test_ai_openai_compatible(client: TestClient, monkeypatch):
    import io
    import json as _json

    from ordnung import ai as ai_module

    def fake_urlopen(request, timeout=0):
        assert request.full_url == "http://llm.local/v1/chat/completions"
        return io.BytesIO(_json.dumps({"model": "qwen", "choices": [{"message": {"content": "OK"}}],
                                       "usage": {"prompt_tokens": 12, "completion_tokens": 1}}).encode())

    monkeypatch.setattr(ai_module.urllib.request, "urlopen", fake_urlopen)
    login(client, "oliver", "geheim123")
    client.put("/api/ai", json={"provider": "openai", "base_url": "http://llm.local/v1/", "model": "qwen"})
    res = client.post("/api/ai/test").json()
    assert res["text"] == "OK" and res["cost"] == 0
    assert client.get("/api/ai").json()["month_usage"]["calls"] == 1


def test_ai_settings_admin_only(client: TestClient):
    login(client, "oliver", "geheim123")
    client.post("/api/users", json={"name": "gast", "password": "gast-pass-2026"})
    guest = TestClient(client.app)
    login(guest, "gast", "gast-pass-2026")
    assert guest.get("/api/ai").status_code == 403


def test_ai_model_friendly_names(client: TestClient, settings: Settings):
    from ordnung.ai import normalize_model, AIError

    assert normalize_model("anthropic", "Opus 5.5") == "claude-opus-5-5"
    assert normalize_model("anthropic", "Claude Haiku 5.5") == "claude-haiku-5-5"
    assert normalize_model("anthropic", "claude-sonnet-5-5") == "claude-sonnet-5-5"
    assert normalize_model("openai", "qwen3:14b") == "qwen3:14b"
    with pytest.raises(AIError):
        normalize_model("anthropic", "GPT 5")
    login(client, "oliver", "geheim123")
    assert client.put("/api/ai", json={"model": "Opus 5.5"}).json()["model"] == "claude-opus-5-5"
    assert client.put("/api/ai", json={"model": "Banane"}).status_code == 400
    # an old stored friendly name is repaired on load
    data = __import__("json").loads((settings.data / "ai.json").read_text())
    data["model"] = "Sonnet 5.5"
    (settings.data / "ai.json").write_text(__import__("json").dumps(data))
    assert client.get("/api/ai").json()["model"] == "claude-sonnet-5-5"


def test_ai_models_fallback_and_openai(client: TestClient, monkeypatch):
    import io
    import json as _json

    from ordnung import ai as ai_module

    login(client, "oliver", "geheim123")
    res = client.get("/api/ai/models").json()
    assert res["source"] == "builtin" and res["error"] == "no API key"
    assert any(m["id"] == "claude-opus-5-5" for m in res["models"])

    def fake_urlopen(request, timeout=0):
        assert request.full_url == "http://llm.local/v1/models"
        return io.BytesIO(_json.dumps({"data": [{"id": "qwen3:14b"}, {"id": "llama3.2"}]}).encode())

    monkeypatch.setattr(ai_module.urllib.request, "urlopen", fake_urlopen)
    client.put("/api/ai", json={"provider": "openai", "base_url": "http://llm.local/v1"})
    res = client.get("/api/ai/models").json()
    assert res["source"] == "provider"
    assert [m["id"] for m in res["models"]] == ["llama3.2", "qwen3:14b"]


def test_ai_ollama_provider(client: TestClient, monkeypatch):
    import io
    import json as _json

    from ordnung import ai as ai_module

    def fake_urlopen(request, timeout=0):
        assert request.full_url == "http://10.0.0.5:11434/v1/models"
        return io.BytesIO(_json.dumps({"data": [{"id": "qwen3:8b"}, {"id": "nomic-embed-text:latest"}]}).encode())

    monkeypatch.setattr(ai_module.urllib.request, "urlopen", fake_urlopen)
    login(client, "oliver", "geheim123")
    cfg = client.put("/api/ai", json={"provider": "ollama", "base_url": "http://10.0.0.5:11434/", "model": "qwen3:8b"}).json()
    assert cfg["base_url"] == "http://10.0.0.5:11434/v1" and cfg["model"] == "qwen3:8b"
    assert [m["id"] for m in client.get("/api/ai/models").json()["models"]] == ["qwen3:8b"]


def test_ai_rejects_password_manager_fill(client: TestClient):
    login(client, "oliver", "geheim123")
    client.put("/api/ai", json={"api_key": "sk-ant-real-key-123456"})
    res = client.put("/api/ai", json={"api_key": "MeinBitwardenPasswort!"})
    assert res.status_code == 400 and res.json()["detail"] == "not an Anthropic key"
    assert client.get("/api/ai").json()["key_hint"] == "…3456"


def test_tree_prefs_per_person(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.get("/api/me/prefs").json()["tree_open"] == []
    res = client.put("/api/me/prefs", json={"tree_open": ["Haus/Strom", "Haus", "Haus", ""]})
    assert res.json()["tree_open"] == ["Haus", "Haus/Strom"]
    assert client.post("/api/users", json={"name": "erika", "password": "erika-pass-2026"}).status_code == 201

    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass-2026")
    assert erika.get("/api/me/prefs").json()["tree_open"] == []
    erika.put("/api/me/prefs", json={"tree_open": ["Auto"]})
    assert client.get("/api/me/prefs").json()["tree_open"] == ["Haus", "Haus/Strom"]

    assert client.delete("/api/users/erika").status_code == 200
    assert "erika" not in client.app.state.prefs._load()


def test_language_preference(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.get("/api/me").json()["language"] == ""
    assert client.put("/api/me/prefs", json={"language": "it"}).json()["language"] == "it"
    assert client.get("/api/me").json()["language"] == "it"
    assert client.put("/api/me/prefs", json={"language": "xx"}).status_code == 400
    client.put("/api/me/prefs", json={"tree_open": ["Banken"]})          # tree state keeps the language
    assert client.get("/api/me/prefs").json() == {"tree_open": ["Banken"], "language": "it", "stamps": []}


def test_text_errors_list_and_retry(client: TestClient):
    from types import SimpleNamespace
    login(client, "oliver", "geheim123")
    idx = client.app.state.index
    docs = client.get("/api/documents", params={"recursive": True}).json()["items"]
    a, b = docs[0], docs[1]
    idx.store_text(a["sha256"], SimpleNamespace(text="", pages=0, ocr_pages=0, method="error",
                                                error="PdfiumError: Failed to load document (PDFium: Incorrect password error)."))
    idx.store_text(b["sha256"], SimpleNamespace(text="", pages=0, ocr_pages=0, method="error",
                                                error="FileNotFoundError: /archiv/alt/weg.pdf"))
    items = {i["id"]: i["reason"] for i in client.get("/api/text-errors").json()["items"]}
    assert items == {a["id"]: "password", b["id"]: "missing"}
    idx.scan()                                       # stale "file not found" heals itself
    assert [i["reason"] for i in client.get("/api/text-errors").json()["items"]] == ["password"]
    assert client.post("/api/text-errors/retry").json() == {"retried": 1}
    assert client.get("/api/text-errors").json()["items"] == []


def test_area_without_owner(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    res = client.post("/api/areas", json={"name": "haus", "label": "Haus Musterweg"})
    assert res.status_code == 201, res.text
    assert res.json() == {"name": "haus", "label": "Haus Musterweg"}
    assert (settings.archive / "haus").is_dir()
    assert {"name": "haus", "count": 0, "label": "Haus Musterweg"} in client.get("/api/areas").json()
    assert client.post("/api/areas", json={"name": "Haus"}).status_code == 409
    assert client.post("/api/areas", json={"name": "../x"}).status_code == 400
    # nobody owns it – a member gets rights like for any other area
    client.post("/api/users", json={"name": "erika", "password": "erika-pass-2026", "areas": {"haus": "write"}})
    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass-2026")
    assert [a["name"] for a in erika.get("/api/areas").json()] == ["haus"]
    assert erika.get("/api/me").json()["write_areas"] == ["haus"]
    # an area with documents stays, an empty one may go
    assert client.delete("/api/areas/oliver").status_code == 409
    assert client.delete("/api/areas/haus").status_code == 200
    assert not (settings.archive / "haus").exists()
