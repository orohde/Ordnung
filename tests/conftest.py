from pathlib import Path

import pytest

from ordnung.config import Settings


def make_pdf(text: str) -> bytes:
    """Minimal one-page PDF with a text layer."""
    content = f"BT /F1 12 Tf 40 780 Td ({text}) Tj ET".encode("latin-1", "replace")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return out


FILES = {
    "oliver/Versicherungen/Continentale/Wohngebäude/2024-01-15_Versicherungsschein Wohngebäude.pdf":
        "Continentale Versicherung Wohngebaeudeversicherung Schein Nr 4711",
    "oliver/Banken/DKB/2026-03-01_Kontoauszug.pdf": "Deutsche Kreditbank Kontoauszug Maerz",
    "erika/Gesundheit/Rezepte/2026-10-01_Rezept_a3f9c1.pdf": "Rezept Ibuprofen 600 Dr. Fichtel",
    "erika/Gesundheit/Rezepte/2026-10-01_Rezept_7be204.pdf": "Rezept Amoxicillin Dr. Fichtel",
    "gemeinsam/Versicherungen/ARAG/2025-05-05_Rechtsschutz.pdf": "ARAG Rechtsschutz Police",
    "0000381.pdf": "Unsortiertes Schreiben",
}


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    archive = tmp_path / "archiv"
    for rel, text in FILES.items():
        path = archive / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(make_pdf(text))
    hidden = archive / "oliver/.hidden/secret.pdf"
    hidden.parent.mkdir(parents=True)
    hidden.write_bytes(b"x")
    data = tmp_path / "data"
    data.mkdir()
    return Settings(
        archive=archive, data=data, readonly=True, admin_user="oliver",
        admin_password="geheim123", api_token="tok", rescan_minutes=0, secret="s" * 32,
        ocr=False, starter=False,
    )
