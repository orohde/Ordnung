import functools

import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings
from ordnung.textextract import extract

WOHN = "Versicherungen/Continentale/Wohngebäude"


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.index.extract_pending(functools.partial(extract, ocr=False))
    c = TestClient(app)
    assert c.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    return c


def test_evaluate_counts_inside_and_outside(client: TestClient):
    res = client.post("/api/rules/evaluate", json={"folder": WOHN, "conditions": [
        {"type": "contains", "value": "Continentale"}]}).json()
    assert res["inside"] == 1 and res["inside_total"] == 1 and res["outside"] == 0
    res = client.post("/api/rules/evaluate", json={"folder": "Gesundheit/Rezepte", "conditions": [
        {"type": "contains", "value": "Versicherung"}]}).json()
    assert res["inside"] == 0 and res["outside"] >= 1
    assert res["outside_docs"][0]["folder"] != "Gesundheit/Rezepte"


def test_id_condition_ignores_spaces(client: TestClient):
    res = client.post("/api/rules/evaluate", json={"folder": WOHN, "conditions": [
        {"type": "id", "value": "Nr 47 11"}]}).json()
    assert res["inside"] == 1


def test_rule_crud_and_folder_view(client: TestClient):
    rid = client.post("/api/rules", json={"folder": WOHN, "conditions": [
        {"type": "contains", "value": "Continentale"}, {"type": "contains", "value": "Wohngebaeude"}]}).json()["id"]
    client.put("/api/rules/folder", json={"folder": WOHN, "description": "Wohngebäudeversicherung"})
    view = client.get("/api/rules/folder", params={"path": WOHN}).json()
    assert view["description"] == "Wohngebäudeversicherung"
    assert view["rules"][0]["stats"]["inside"] == 1
    assert client.get("/api/rules").json()["folders"][WOHN]["rules"] == 1
    assert client.patch(f"/api/rules/{rid}", json={"enabled": False}).status_code == 200
    assert client.delete(f"/api/rules/{rid}").status_code == 200
    assert client.delete(f"/api/rules/{rid}").status_code == 400


def test_rule_validation(client: TestClient):
    bad = [{"type": "contains", "value": "ab"}], [{"type": "regex", "value": "(("}], [{"type": "magic", "value": "abc"}], []
    for conds in bad:
        assert client.post("/api/rules", json={"folder": WOHN, "conditions": conds}).status_code == 400


def test_suggestions_are_exclusive(client: TestClient):
    sugg = client.get("/api/rules/suggest", params={"path": "Gesundheit/Rezepte"}).json()
    assert sugg, "expected at least one suggestion"
    for s in sugg:
        assert s["outside"] == 0 and s["inside"] >= 1
    assert any(c["value"] in ("fichtel", "rezept") for s in sugg for c in s["conditions"])


def test_match_for_inbox(client: TestClient):
    client.post("/api/rules", json={"folder": WOHN, "conditions": [{"type": "contains", "value": "Continentale"}]})
    hits = client.app.state.rules.match("Ihre CONTINENTALE Versicherung, Beitragsrechnung")
    assert hits and hits[0]["folder"] == WOHN


def test_rules_admin_only(client: TestClient):
    client.post("/api/users", json={"name": "gast", "password": "gast-pass"})
    guest = TestClient(client.app)
    guest.post("/api/login", json={"username": "gast", "password": "gast-pass"})
    assert guest.get("/api/rules").status_code == 403


def test_ai_suggestions_are_measured(client: TestClient, monkeypatch):
    from ordnung.ai import Completion

    calls = {}

    def fake_complete(system, prompt, max_tokens=0, effort="", force=False):
        calls["prompt"] = prompt
        return Completion(text='Hier: {"rules": [{"conditions": [{"type": "contains", "value": "Fichtel"}], '
                               '"reason": "Arzt"}, {"conditions": [{"type": "contains", "value": "x"}]}]}',
                          model="claude-test", input_tokens=10, output_tokens=5, cost=0.01, seconds=1.0)

    monkeypatch.setattr(client.app.state.ai, "complete", fake_complete)
    res = client.post("/api/rules/ai-suggest", params={"path": "Gesundheit/Rezepte"}).json()
    assert res["model"] == "claude-test" and res["samples"] == 2
    assert len(res["suggestions"]) == 1          # the invalid 1-char rule is dropped
    s = res["suggestions"][0]
    assert s["kind"] == "ai" and s["inside"] == 2 and s["outside"] == 0 and s["reason"] == "Arzt"
    assert "Ibuprofen" in calls["prompt"]


def test_ai_suggestions_respect_excluded_areas(client: TestClient):
    client.put("/api/ai", json={"excluded_areas": ["erika"]})
    res = client.post("/api/rules/ai-suggest", params={"path": "Gesundheit/Rezepte"})
    assert res.status_code == 400 and "may be sent" in res.json()["detail"]


def test_ai_suggestions_need_enabled_ai(client: TestClient):
    res = client.post("/api/rules/ai-suggest", params={"path": "Gesundheit/Rezepte"})
    assert res.status_code == 400 and res.json()["detail"] == "AI is disabled"


def test_ai_suggestions_folder_without_own_documents(client: TestClient):
    client.put("/api/ai", json={"enabled": True})
    res = client.post("/api/rules/ai-suggest", params={"path": "Versicherungen"})
    assert res.status_code == 400 and res.json()["detail"] == "folder has no documents of its own"


def test_generate_all_from_archive(client: TestClient):
    rs = client.app.state.rules
    result = rs.generate_all(min_docs=2)
    assert result["running"] is False and result["total"] >= 1 and result["rules"] >= 1
    auto = [r for r in rs.load().rules if r.source == "auto"]
    assert auto and all(r.folder == "Gesundheit/Rezepte" for r in auto)
    for r in auto:
        stats = rs.evaluate(r.folder, r.conditions)
        assert stats["outside"] == 0 and stats["inside"] >= 1
    again = rs.generate_all(min_docs=2)          # folders with rules are skipped
    assert again["total"] == 0
    assert client.get("/api/rules/generate").json()["running"] is False


def test_starter_rules_adapt_to_own_folders(client: TestClient):
    from ordnung.starter import STARTER_RULES
    STARTER_RULES.append(("Versicherungen/Wohngebäude", [["continentale"]]))
    try:
        res = client.post("/api/rules/starter").json()
    finally:
        STARTER_RULES.pop()
    # moved to the folder where the documents really are; min_hits keeps single hits out
    assert res["added"] == 0
    rules = client.app.state.rules
    out = rules.adapt_starter(min_hits=1)
    assert out["rules"] == [] or all(r["folder"] for r in out["rules"])
    STARTER_RULES.append(("Versicherungen/Wohngebäude", [["continentale"]]))
    try:
        out = rules.adapt_starter(min_hits=1)
    finally:
        STARTER_RULES.pop()
    assert {"folder": WOHN, "conditions": [{"type": "contains", "value": "continentale"}],
            "inside": 1, "outside": 0} in out["rules"]


def test_first_start_installs_starter_set(settings):
    from dataclasses import replace
    app = create_app(replace(settings, starter=True), background=False)
    book = app.state.rules.load()
    assert len(book.rules) > 50 and all(r.source == "starter" for r in book.rules)
    assert "Banken/Girokonto" in app.state.folders.load()
    assert app.state.rules.install_starter() == 0      # not twice
