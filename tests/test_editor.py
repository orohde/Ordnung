import base64
import io

from fastapi.testclient import TestClient
from PIL import Image

from conftest import make_pdf
from test_api import client, login  # noqa: F401  (fixture)


def _doc(client, q):
    return client.get("/api/documents", params={"recursive": True, "q": q}).json()["items"][0]


def test_save_edited_pdf_beside_original(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "kontoauszug")
    client.put(f"/api/documents/{doc['id']}/tags", json={"tags": ["steuer"]})
    pdf = make_pdf("Deutsche Kreditbank Kontoauszug Maerz unterschrieben")
    res = client.post(f"/api/documents/{doc['id']}/edited", json={
        "pdf": base64.b64encode(pdf).decode(), "title": "Kontoauszug (unterschrieben)",
        "text": "Max Muster, Musterstadt"})
    assert res.status_code == 201, res.text
    out = res.json()
    assert out["path"].startswith("oliver/Banken/DKB/2026-03-01_Kontoauszug (unterschrieben)_")
    assert (settings.archive / doc["path"]).is_file()          # original untouched
    new = client.get(f"/api/documents/{out['id']}").json()
    assert new["tags"] == ["steuer"]
    assert "Musterstadt" in client.get(f"/api/documents/{out['id']}/text").text
    # same bytes again → refused, not a second copy
    again = client.post(f"/api/documents/{doc['id']}/edited", json={
        "pdf": base64.b64encode(pdf).decode(), "title": "Nochmal"})
    assert again.status_code == 409


def test_edited_refuses_junk_and_readers(client: TestClient):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "rechtsschutz")
    bad = client.post(f"/api/documents/{doc['id']}/edited",
                      json={"pdf": base64.b64encode(b"hallo").decode(), "title": "x"})
    assert bad.status_code == 400
    client.post("/api/users", json={"name": "erika", "password": "erika-pass",
                                    "areas": {"gemeinsam": "read"}})
    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass")
    assert erika.get("/api/me").json()["write_areas"] == []
    res = erika.post(f"/api/documents/{doc['id']}/edited",
                     json={"pdf": base64.b64encode(make_pdf("x")).decode(), "title": "x"})
    assert res.status_code == 403


def test_signature_roundtrip(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.get("/api/me/signature").status_code == 404
    img = Image.new("RGBA", (300, 120), (0, 0, 0, 0))
    for x in range(50, 250):
        img.putpixel((x, 60), (0, 0, 80, 255))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    assert client.put("/api/me/signature", content=buf.getvalue()).status_code == 200
    assert client.get("/api/me").json()["signature"] is True
    got = Image.open(io.BytesIO(client.get("/api/me/signature").content))
    assert got.size == (200, 1)                                 # cropped to the strokes
    assert client.put("/api/me/signature", content=b"kein bild").status_code == 400
    assert client.delete("/api/me/signature").status_code == 200
    assert client.get("/api/me/signature").status_code == 404
