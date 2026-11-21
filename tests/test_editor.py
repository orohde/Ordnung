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
    client.post("/api/users", json={"name": "erika", "password": "erika-pass-2026",
                                    "areas": {"gemeinsam": "read"}})
    erika = TestClient(client.app)
    login(erika, "erika", "erika-pass-2026")
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


def test_edit_replaces_original_and_undo_works(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "kontoauszug")
    client.put(f"/api/documents/{doc['id']}/tags", json={"tags": ["steuer"]})
    pdf = make_pdf("Deutsche Kreditbank Kontoauszug Maerz BEZAHLT")
    res = client.post(f"/api/documents/{doc['id']}/edited", json={
        "pdf": base64.b64encode(pdf).decode(), "title": doc["title"], "date": doc["date"],
        "text": "BEZAHLT 21.11.2026", "replace": True, "add_tags": ["Bezahlt"]})
    assert res.status_code == 201, res.text
    out = res.json()
    assert not (settings.archive / doc["path"]).exists()        # original went to the trash …
    assert out["trash_path"].startswith(".papierkorb/")
    assert (settings.archive / out["trash_path"]).is_file()
    assert out["path"].startswith(f"oliver/Banken/DKB/{doc['date']}_{doc['title']}_")
    new = client.get(f"/api/documents/{out['id']}").json()
    assert sorted(new["tags"]) == ["Bezahlt", "steuer"]
    # … and comes back with "undo"
    assert client.post(f"/api/documents/{out['id']}/trash").status_code == 200
    back = client.post("/api/trash/restore", json={"trash_path": out["trash_path"]})
    assert back.status_code == 200, back.text
    assert (settings.archive / doc["path"]).is_file()


def test_edit_as_copy_keeps_original(client: TestClient, settings):
    login(client, "oliver", "geheim123")
    doc = _doc(client, "kontoauszug")
    res = client.post(f"/api/documents/{doc['id']}/edited", json={
        "pdf": base64.b64encode(make_pdf("Formular Dezember")).decode(), "title": "Formular (Kopie)",
        "replace": False})
    assert res.status_code == 201, res.text
    assert res.json()["trash_path"] is None
    assert (settings.archive / doc["path"]).is_file()


def test_stamp_templates_follow_the_account(client: TestClient):
    login(client, "oliver", "geheim123")
    assert client.get("/api/me/prefs").json()["stamps"] == []
    st = [{"text": "  Bezahlt ", "date": True, "extra": "per Überweisung", "color": "red"},
          {"text": "Bezahlt", "date": True, "extra": "per Überweisung", "color": "red"},   # same → once
          {"text": "Gebucht", "date": False, "color": "blue"}]
    res = client.put("/api/me/prefs", json={"stamps": st})
    assert res.status_code == 200, res.text
    assert res.json()["stamps"] == [
        {"text": "Bezahlt", "date": True, "extra": "per Überweisung", "color": "red"},
        {"text": "Gebucht", "date": False, "extra": "", "color": "blue"}]
    # size and spot on the page are kept when given
    res = client.put("/api/me/prefs", json={"stamps": [
        {"text": "Eingegangen", "date": True, "color": "blue", "size": 30.4, "fx": 0.81234567, "fy": 0.1}]})
    assert res.json()["stamps"] == [
        {"text": "Eingegangen", "date": True, "extra": "", "color": "blue", "size": 30, "fx": 0.8123, "fy": 0.1}]
    for bad in ({"size": 200}, {"size": True}, {"fx": 0.5}, {"fx": 1.5, "fy": 0.2}, {"fx": "a", "fy": 0.2}):
        assert client.put("/api/me/prefs", json={"stamps": [{"text": "x", **bad}]}).status_code == 400, bad
    assert client.put("/api/me/prefs", json={"stamps": [{"text": "x", "color": "pink"}]}).status_code == 400
    assert client.put("/api/me/prefs", json={"stamps": [{"text": ""}]}).status_code == 400
