"""Every answer carries the headers that keep the browser from guessing, framing and telling."""
from fastapi.testclient import TestClient

from ordnung.app import create_app


def test_security_headers_on_every_answer(settings):
    client = TestClient(create_app(settings, background=False))
    for path in ("/", "/api/version", "/api/documents"):
        res = client.get(path)
        assert res.headers["x-content-type-options"] == "nosniff", path
        assert res.headers["x-frame-options"] == "SAMEORIGIN", path
        assert res.headers["referrer-policy"] == "same-origin", path
        assert "frame-ancestors 'self'" in res.headers["content-security-policy"], path


def test_no_request_body_beyond_the_limit(settings):
    import dataclasses
    client = TestClient(create_app(dataclasses.replace(settings, max_upload_mb=1), background=False))
    assert client.post("/api/login", content=b"{" + b" " * (2 * 1024 * 1024) + b"}",
                       headers={"Content-Type": "application/json"}).status_code == 413

    def chunks():                                      # no length named: counted while it comes
        for _ in range(3):
            yield b" " * (1024 * 1024)
    assert client.post("/api/login", content=chunks(), headers={"Content-Type": "application/json"}).status_code == 413
    assert client.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
