"""Update check against a local stand-in for version.worldgate.de."""

import json
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ordnung.versionspruefung import UpdateCheck, is_newer


@pytest.fixture()
def service():
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            calls.append(self.path)
            body = json.dumps({"app": "ordnung", "version": "2026.12.01", "url": "https://example.org/r",
                               "notizen": "Neu", "datum": "2026-12-01"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", calls
    server.shutdown()


def test_is_newer():
    assert is_newer("2026.11.10", "2026.11.9")
    assert is_newer("2027.01.01", "2026.12.40")
    assert not is_newer("2026.11.09", "2026.11.9")
    assert not is_newer("", "2026.11.9")
    assert not is_newer("quatsch", "2026.11.9")


def test_check_sends_only_app_version_kind(tmp_path, service):
    url, calls = service
    uc = UpdateCheck("ordnung", "2026.11.72", tmp_path, kind="docker", service=url)
    info = uc.check()
    assert calls == ["/v1/ordnung?v=2026.11.72&art=docker"]
    assert info["newer"] and info["latest"] == "2026.12.01" and info["notes"] == "Neu"
    assert info["checked"] and not info["error"]


def test_once_a_day_after_the_chosen_minute(tmp_path, service):
    url, calls = service
    uc = UpdateCheck("ordnung", "2026.11.72", tmp_path, kind="docker", service=url)
    minute = json.loads((tmp_path / "versionspruefung.json").read_text())["minute"] if (
        tmp_path / "versionspruefung.json").exists() else uc._load()["minute"]
    later = datetime(2026, 11, 20, 23, 59)
    assert uc.due(later)
    if minute > 0:
        assert not uc.due(datetime(2026, 11, 20, 0, 0))
    uc.check()
    today = datetime.now().replace(hour=23, minute=59)
    assert not uc.due(today)            # already asked today – a restart does not count twice


def test_switch_and_environment(tmp_path, service, monkeypatch):
    url, calls = service
    uc = UpdateCheck("ordnung", "2026.11.72", tmp_path, kind="docker", service=url)
    uc.set_enabled(False)
    assert not uc.enabled() and not uc.due(datetime(2026, 11, 20, 23, 59))
    uc.set_enabled(True)
    monkeypatch.setenv("VERSIONSPRUEFUNG", "0")
    info = uc.public()
    assert info["locked"] and not info["on"]


def test_offline_is_quiet(tmp_path):
    uc = UpdateCheck("ordnung", "2026.11.72", tmp_path, kind="docker", service="http://127.0.0.1:9")
    info = uc.check()
    assert info["error"] and not info["newer"] and info["checked"]


def test_api(settings, service):
    from fastapi.testclient import TestClient

    from ordnung.app import create_app

    url, calls = service
    app = create_app(settings, background=False)
    app.state.update_check.service = url
    client = TestClient(app)
    assert client.get("/api/update").status_code == 401
    assert client.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    info = client.post("/api/update/check").json()
    assert info["newer"] and info["latest"] == "2026.12.01" and len(calls) == 1
    assert client.put("/api/update", json={"on": False}).json()["on"] is False
    assert client.post("/api/update/check").status_code == 409
    assert client.get("/api/update").json()["on"] is False


def test_only_https_links_reach_the_page():
    from ordnung.versionspruefung import safe_url
    assert safe_url("https://github.com/orohde/x/releases/tag/1") == "https://github.com/orohde/x/releases/tag/1"
    for bad in ("javascript:alert(1)", "JAVASCRIPT:alert(1)", "http://example.org", "data:text/html,x",
                'https://x" onclick="a', ""):
        assert safe_url(bad) == "", bad
