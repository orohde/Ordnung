"""The brake on failed sign-ins holds also when many tries come at once."""
import threading
import time

import pytest
from fastapi.testclient import TestClient

from ordnung.app import create_app
from ordnung.security import LoginGuard


@pytest.fixture
def app(settings):
    app = create_app(settings, background=False)
    app.state.index.scan()
    return app


@pytest.fixture
def admin_ready(app):
    return app


def test_tries_sent_together_cannot_slip_past_the_lock(app, admin_ready):
    real = app.state.users.authenticate

    def slow(name, password):                      # the password check takes its time, as scrypt does
        time.sleep(0.05)
        return real(name, password)
    app.state.users.authenticate = slow
    answers, start = [], threading.Barrier(30)

    def one():
        client = TestClient(app, client=("203.0.113.7", 50000))
        start.wait()
        answers.append(client.post("/api/login", json={"username": "oliver", "password": "falsch-falsch"}).status_code)
    threads = [threading.Thread(target=one) for _ in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert answers.count(401) <= 5 and set(answers) <= {401, 429}, answers


def test_the_guard_forgets_but_never_endlessly():
    guard = LoginGuard()
    guard.KEEP = 100
    for n in range(5):
        guard.fail("oliver", True)
    for n in range(500):
        guard.fail(f"niemand{n}", True)
    assert len(guard._state) <= guard.KEEP + 1
    assert guard.locked_for("oliver", True) > 0                   # the locked account is not forgotten
    assert guard.begin("niemand499", True) == 0 and guard.begin("niemand499", True) == 1
    guard.end("niemand499", True)
    assert guard.begin("niemand499", True) == 0


def test_password_asked_again_has_the_same_brake(app):
    client = TestClient(app, client=("10.10.30.5", 50000))
    assert client.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    for _ in range(5):
        assert client.post("/api/me/password", json={"old": "falsch-falsch", "new": "x" * 14}).status_code == 403
    assert client.post("/api/me/password", json={"old": "geheim123", "new": "x" * 14}).status_code == 429
    assert client.post("/api/me/totp/setup", json={"password": "geheim123"}).status_code == 429


def test_names_the_app_acts_under_are_not_for_people(app):
    client = TestClient(app, client=("10.10.30.5", 50000))
    assert client.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    for name in ("api", "upload", "API"):
        assert client.post("/api/users", json={"name": name, "password": "geheim1234567"}).status_code == 400, name
