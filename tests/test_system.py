"""Settings that moved from the environment into the app: background work, home network, first setup."""

import dataclasses

from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings

HOME = ("10.10.30.5", 50000)
OUTSIDE = ("203.0.113.7", 50000)


def admin(settings: Settings, where=HOME) -> TestClient:
    c = TestClient(create_app(settings, background=False), client=where)
    assert c.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    return c


def test_system_settings_default_from_env_and_change(settings: Settings):
    c = admin(settings)
    got = c.get("/api/system/settings").json()
    assert (got["ocr"], got["ocr_lang"], got["rescan_minutes"]) == (False, "deu+eng", 0)   # from Settings
    res = c.put("/api/system/settings", json={"ocr": True, "ocr_lang": "deu+fra", "ocr_max_pages": 50,
                                              "rescan_minutes": 15, "text_workers": 2})
    assert res.status_code == 200, res.text
    assert res.json()["ocr_lang"] == "deu+fra" and res.json()["defaults"]["ocr_lang"] == "deu+eng"
    assert c.get("/api/status").json()["ocr"] in (True, False)       # depends on Tesseract being there
    # survives a restart, the environment no longer wins
    again = admin(settings).get("/api/system/settings").json()
    assert (again["ocr"], again["ocr_max_pages"], again["rescan_minutes"], again["text_workers"]) == (True, 50, 15, 2)
    for bad in ({"ocr_lang": "deu; rm -rf"}, {"rescan_minutes": 0}, {"text_workers": 99}, {"ocr_max_pages": 0}):
        assert c.put("/api/system/settings", json=bad).status_code == 400, bad


def test_home_networks_in_settings(settings: Settings):
    c = admin(settings)
    assert c.get("/api/security").json()["client_ip"] == "10.10.30.5"
    assert c.put("/api/security", json={"internal_networks": "kaputt"}).status_code == 400
    # would throw the admin who saves it out of the home network
    res = c.put("/api/security", json={"internal_networks": "192.168.1.0/24"})
    assert res.status_code == 400 and "10.10.30.5" in res.json()["detail"]
    res = c.put("/api/security", json={"internal_networks": "10.10.0.0/16\n203.0.113.0/24"})
    assert res.status_code == 200, res.text
    assert res.json()["internal_networks"] == "10.10.0.0/16, 203.0.113.0/24"
    # takes effect at once: that address counts as home now
    outside = TestClient(c.app, client=OUTSIDE)
    assert outside.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    assert outside.get("/api/me").json()["external"] is False
    # empty: back to the default ranges
    assert c.put("/api/security", json={"internal_networks": ""}).json()["internal_networks"] == ""
    assert TestClient(c.app, client=OUTSIDE).get("/api/setup").json()["home"] is False


def test_first_setup_page(settings: Settings):
    fresh = dataclasses.replace(settings, admin_password="")      # no account from the environment
    app = create_app(fresh, background=False)
    outside = TestClient(app, client=OUTSIDE)
    assert outside.get("/api/setup").json() == {"needed": True, "home": False}
    assert outside.post("/api/setup", json={"username": "anna", "password": "lang-genug-2026"}).status_code == 403
    home = TestClient(app, client=HOME)
    assert home.post("/api/setup", json={"username": "anna", "password": "kurz"}).status_code == 400
    res = home.post("/api/setup", json={"username": "Anna", "password": "lang-genug-2026", "display_name": "Anna R."})
    assert res.status_code == 201, res.text
    me = home.get("/api/me").json()                                  # signed in right away
    assert (me["name"], me["is_admin"]) == ("anna", True)
    assert home.get("/api/setup").json()["needed"] is False
    other = TestClient(app, client=HOME)
    assert other.post("/api/setup", json={"username": "mallory", "password": "lang-genug-2026"}).status_code == 409


def test_extractor_goes_to_worker_processes(settings: Settings, tmp_path):
    """Text extraction runs in a process pool: the extractor must survive pickling and follow the settings."""
    import pickle
    app = create_app(settings, background=False)
    app.state.system.update({"ocr_lang": "eng", "ocr_max_pages": 5})
    extractor = pickle.loads(pickle.dumps(app.state.make_extractor()))
    assert extractor.keywords == {"ocr": False, "lang": "eng", "max_ocr_pages": 5}
    app.state.index.scan()
    assert app.state.index.extract_pending(app.state.make_extractor(), workers=2) > 0
