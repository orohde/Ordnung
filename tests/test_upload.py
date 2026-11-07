import base64
import io

import pypdfium2 as pdfium
from PIL import Image

from conftest import make_pdf
from test_inbox import env, process  # noqa: F401  (fixture)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _photo(fmt: str, size=(1200, 1600), orientation: int | None = None) -> bytes:
    img = Image.new("RGB", size, (250, 250, 245))
    for x in range(100, 1100):
        img.putpixel((x, 200), (0, 0, 0))
    buf = io.BytesIO()
    if fmt == "HEIF":
        import pillow_heif
        pillow_heif.register_heif_opener()
    kw = {}
    if orientation:
        exif = Image.Exif()
        exif[0x0112] = orientation
        kw["exif"] = exif.tobytes()
    img.save(buf, fmt, **kw)
    return buf.getvalue()


def _pages(path) -> list[tuple[float, float]]:
    pdf = pdfium.PdfDocument(str(path))
    return [tuple(round(v) for v in pdf[i].get_size()) for i in range(len(pdf))]


def test_upload_photo_heic_and_pdf(env):
    app, c, _inbox, _fresh = env
    up = app.state.settings.data / "hochgeladen"
    res = c.post("/api/inbox/upload", json={"files": [
        {"name": "IMG_0001.JPG", "data": _b64(_photo("JPEG", orientation=6))},     # taken sideways
        {"name": "IMG_0002.HEIC", "data": _b64(_photo("HEIF"))},
        {"name": "Rechnung.pdf", "data": _b64(make_pdf("Rechnung Hochgeladen 4711"))},
    ]})
    assert res.status_code == 201, res.text
    assert res.json()["names"] == ["IMG_0001.pdf", "IMG_0002.pdf", "Rechnung.pdf"]
    w, h = _pages(up / "IMG_0001.pdf")[0]
    assert w > h                                              # EXIF rotation applied
    process(app)
    items = c.get("/api/inbox").json()["items"]
    assert sorted(i["name"] for i in items) == ["IMG_0001.pdf", "IMG_0002.pdf", "Rechnung.pdf"]


def test_upload_combines_pages_into_one_document(env):
    app, c, _inbox, _fresh = env
    up = app.state.settings.data / "hochgeladen"
    res = c.post("/api/inbox/upload", json={"combine": True, "files": [
        {"name": "Brief Seite 1.jpg", "data": _b64(_photo("JPEG"))},
        {"name": "Brief Seite 2.png", "data": _b64(_photo("PNG"))},
        {"name": "Anlage.pdf", "data": _b64(make_pdf("Anlage"))},
    ]})
    assert res.json()["names"] == ["Brief Seite 1.pdf"]
    assert len(_pages(up / "Brief Seite 1.pdf")) == 3


def test_upload_refuses_junk_and_deletes_after_filing(env):
    app, c, _inbox, fresh = env
    assert c.post("/api/inbox/upload", json={"files": [{"name": "a.exe", "data": _b64(b"MZ")}]}).status_code == 400
    assert c.post("/api/inbox/upload", json={"files": [{"name": "a.pdf", "data": _b64(b"hallo")}]}).status_code == 400
    assert c.post("/api/inbox/upload", json={"files": [{"name": "a.jpg", "data": _b64(b"kein bild")}]}).status_code == 400
    c.post("/api/storage/switch", json={"archive_path": str(fresh)})
    c.post("/api/inbox/upload", json={"files": [{"name": "Beleg.pdf", "data": _b64(make_pdf("Beleg Upload"))}]})
    process(app)
    item = c.get("/api/inbox").json()["items"][0]
    res = c.post(f"/api/inbox/{item['key']}/file", json={
        "area": "oliver", "folder": "Belege", "title": "Beleg", "date": "2026-11-07"})
    assert res.status_code == 200, res.text
    assert not (app.state.settings.data / "hochgeladen" / "Beleg.pdf").exists()   # upload removed
    assert (fresh / "oliver" / "Belege").is_dir()
