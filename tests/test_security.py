"""Sign-in security: every route behind the login, sessions, lockout, second factor."""

import time

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.config import Settings
from ordnung.security import Networks, totp_code, totp_match

PUBLIC = {("GET", "/api/version"), ("POST", "/api/login"), ("POST", "/api/logout"),
          ("GET", "/api/setup"), ("POST", "/api/setup")}   # setup refuses once an account exists
HOME = ("10.10.30.5", 50000)
OUTSIDE = ("203.0.113.7", 50000)


@pytest.fixture
def app(settings: Settings):
    app = create_app(settings, background=False)
    app.state.index.scan()
    return app


def client_at(app, where=HOME, https=False) -> TestClient:
    return TestClient(app, client=where, base_url="https://testserver" if https else "http://testserver")


def sign_in(c: TestClient, name="oliver", password="geheim123", code=None):
    body = {"username": name, "password": password}
    if code:
        body["code"] = code
    return c.post("/api/login", json=body)


def now_code(app, name="oliver") -> str:
    account = app.state.users.get(name)
    return totp_code(account.totp_secret or account.totp_pending, int(time.time() // 30))


def enable_totp(app, c: TestClient) -> list[str]:
    assert c.post("/api/me/totp/setup", json={"password": "geheim123"}).status_code == 200
    res = c.post("/api/me/totp/enable", json={"code": now_code(app)})
    assert res.status_code == 200, res.text
    return res.json()["recovery_codes"]


def test_every_route_needs_a_login(app):
    """A new route without the login check would be open on the internet."""
    c = client_at(app, OUTSIDE)
    checked = 0
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/"):
            continue
        if route.path in ("/api/docs", "/api/openapi.json"):
            continue
        path = route.path
        for param in route.param_convertors:
            path = path.replace("{" + param + "}", "x").replace("{" + param + ":path}", "x")
        for method in route.methods - {"HEAD", "OPTIONS"}:
            if (method, route.path) in PUBLIC:
                continue
            res = c.request(method, path, json={})
            assert res.status_code == 401, f"{method} {route.path} answers {res.status_code} without login"
            checked += 1
    assert checked > 80


def test_logout_ends_the_session_on_the_server(app):
    c = client_at(app)
    assert sign_in(c).status_code == 200
    stolen = dict(c.cookies)
    c.post("/api/logout")
    thief = client_at(app)
    thief.cookies.update(stolen)
    assert thief.get("/api/me").status_code == 401


def test_password_change_signs_out_other_devices(app):
    laptop, phone = client_at(app), client_at(app)
    sign_in(laptop), sign_in(phone)
    res = laptop.post("/api/me/password", json={"old": "geheim123", "new": "ein-langes-neues"})
    assert res.json()["signed_out"] == 1
    assert laptop.get("/api/me").status_code == 200
    assert phone.get("/api/me").status_code == 401


def test_session_list_and_revoke(app):
    laptop, phone = client_at(app), client_at(app, OUTSIDE)
    sign_in(laptop), sign_in(phone)
    sessions = laptop.get("/api/me/sessions").json()
    assert len(sessions) == 2
    other = next(s for s in sessions if not s["current"])
    assert other["external"] is True
    assert laptop.delete(f"/api/me/sessions/{other['id']}").status_code == 200
    assert phone.get("/api/me").status_code == 401
    assert laptop.delete("/api/me/sessions/nope").status_code == 404


def test_https_cookie_is_host_only_and_secure(app):
    c = client_at(app, https=True)
    res = sign_in(c)
    cookie = res.headers["set-cookie"]
    assert cookie.startswith("__Host-ordnung_session=")
    assert "Secure" in cookie and "HttpOnly" in cookie and "Path=/" in cookie and "Domain" not in cookie
    assert c.get("/api/me").status_code == 200


def test_cross_site_requests_are_refused(app):
    c = client_at(app)
    sign_in(c)
    body = {"old": "geheim123", "new": "ein-langes-neues"}
    assert c.post("/api/me/password", json=body, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert c.post("/api/me/password", json=body, headers={"Sec-Fetch-Site": "same-site"}).status_code == 403
    assert c.post("/api/me/password", json=body, headers={"Origin": "https://evil.example"}).status_code == 403
    assert c.post("/api/logout", headers={"Origin": "null"}).status_code == 403
    # reading stays possible, and the own page passes
    assert c.get("/api/me", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 200
    assert c.post("/api/me/password", json=body, headers={"Origin": "http://testserver"}).status_code == 200


def test_lockout_per_account_and_side(app, monkeypatch):
    monkeypatch.setattr("ordnung.app.time.sleep", lambda s: None)
    outside, home = client_at(app, OUTSIDE), client_at(app)
    for _ in range(5):
        assert sign_in(outside, password="falsch").status_code == 401
    res = sign_in(outside)
    assert res.status_code == 429 and int(res.headers["retry-after"]) > 0
    # the person at home is not locked out by the attacker outside
    assert sign_in(home).status_code == 200


def test_new_passwords_need_twelve_characters(app):
    c = client_at(app)
    sign_in(c)
    assert c.post("/api/users", json={"name": "kurz", "password": "elf-zeichen"}).status_code == 400
    assert c.post("/api/users", json={"name": "lang", "password": "zwoelf-zeich"}).status_code == 201


def test_totp_setup_and_sign_in(app, monkeypatch):
    monkeypatch.setattr("ordnung.app.time.sleep", lambda s: None)
    home = client_at(app)
    sign_in(home)
    assert home.post("/api/me/totp/setup", json={"password": "falsch"}).status_code == 403
    setup = home.post("/api/me/totp/setup", json={"password": "geheim123"}).json()
    assert setup["uri"].startswith("otpauth://totp/") and setup["qr"].startswith("data:image/svg+xml")
    assert home.post("/api/me/totp/enable", json={"code": "000000"}).status_code == 400
    codes = home.post("/api/me/totp/enable", json={"code": now_code(app)}).json()["recovery_codes"]
    assert len(codes) == 10
    assert home.get("/api/me").json()["totp"] is True
    assert "totp_secret" not in home.get("/api/users").json()[0]

    outside = client_at(app, OUTSIDE)
    assert sign_in(outside).json()["detail"] == "code required"
    assert sign_in(outside, code="123456").status_code == 401
    # the code of the last step was used at "enable" – the same one must not work twice
    used = app.state.users.get("oliver").totp_last_step
    assert totp_match(app.state.users.get("oliver").totp_secret, totp_code(app.state.users.get("oliver").totp_secret, used), used) is None
    # a recovery code works exactly once
    assert sign_in(outside, code=codes[0].upper()).status_code == 200
    assert sign_in(client_at(app, OUTSIDE), code=codes[0]).status_code == 401
    assert outside.get("/api/me").json()["recovery_left"] == 9
    # at home the password is enough unless policy asks for more
    assert sign_in(client_at(app)).status_code == 200


def test_home_session_without_code_does_not_work_outside(app):
    home = client_at(app)
    sign_in(home)
    enable_totp(app, home)
    later = client_at(app)
    sign_in(later)                       # at home, no code needed
    cookies = dict(later.cookies)
    travelling = client_at(app, OUTSIDE)
    travelling.cookies.update(cookies)
    assert travelling.get("/api/me").status_code == 401
    # the session that confirmed the code works everywhere
    away = client_at(app, OUTSIDE)
    away.cookies.update(dict(home.cookies))
    assert away.get("/api/me").status_code == 200


def test_policy_outside_only_with_second_factor(app):
    home = client_at(app)
    sign_in(home)
    home.post("/api/users", json={"name": "erika", "password": "erika-pass-2026"})
    # the admin cannot lock themselves out
    assert home.put("/api/security", json={"require_2fa_external": True}).status_code == 400
    enable_totp(app, home)
    res = home.put("/api/security", json={"require_2fa_external": True})
    assert res.status_code == 200 and res.json()["without_2fa"] == ["erika"]
    assert sign_in(client_at(app, OUTSIDE), "erika", "erika-pass-2026").json()["detail"] == "second factor required outside"
    assert sign_in(client_at(app), "erika", "erika-pass-2026").status_code == 200


def test_admin_resets_second_factor(app):
    home = client_at(app)
    sign_in(home)
    home.post("/api/users", json={"name": "erika", "password": "erika-pass-2026"})
    erika = client_at(app)
    sign_in(erika, "erika", "erika-pass-2026")
    assert erika.post("/api/me/totp/setup", json={"password": "erika-pass-2026"}).status_code == 200
    assert erika.post("/api/me/totp/enable", json={"code": now_code(app, "erika")}).status_code == 200
    res = home.patch("/api/users/erika", json={"reset_totp": True})
    assert res.json()["totp"] is False
    assert erika.get("/api/me").status_code == 401        # reset signs her out


def test_disable_needs_password_and_code(app):
    home = client_at(app)
    sign_in(home)
    codes = enable_totp(app, home)
    assert home.post("/api/me/totp/disable", json={"password": "geheim123", "code": "000000"}).status_code == 400
    assert home.post("/api/me/totp/disable", json={"password": "geheim123", "code": codes[1]}).status_code == 200
    assert home.get("/api/me").json()["totp"] is False


def test_security_settings_hide_the_token(app):
    home = client_at(app)
    sign_in(home)
    res = home.put("/api/security", json={"ntfy_url": "http://127.0.0.1:9/x", "ntfy_token": "tk_geheim"})
    assert res.status_code == 200 and res.json()["has_ntfy_token"] is True
    assert "tk_geheim" not in res.text
    assert home.put("/api/security", json={"ntfy_url": "ftp://x"}).status_code == 400
    assert home.post("/api/security/test").status_code == 400      # nothing listens on port 9


def test_networks():
    nets = Networks()
    assert nets.is_internal("10.10.20.50") and nets.is_internal("100.101.1.2") and nets.is_internal("::1")
    assert nets.is_internal("::ffff:192.168.1.4")
    assert not nets.is_internal("203.0.113.7") and not nets.is_internal("testclient")
    assert Networks("192.168.5.0/24").is_internal("192.168.5.9") and not Networks("192.168.5.0/24").is_internal("10.0.0.1")
