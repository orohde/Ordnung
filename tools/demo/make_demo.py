"""Build a demo installation of Ordnung! with an invented family – for screenshots and trying it out.

    python tools/demo/make_demo.py /tmp/ordnung-demo --lang de     # or --lang en

creates ``archiv/`` (documents), ``eingang/`` (a scanner inbox with new post) and
``data/`` next to each other. Start Ordnung! on it with

    ORDNUNG_ARCHIVE=/tmp/ordnung-demo/archiv ORDNUNG_DATA=/tmp/ordnung-demo/data \\
    ORDNUNG_ADMIN_USER=demo ORDNUNG_ADMIN_PASSWORD=demo1234 python -m ordnung

and afterwards run ``python tools/demo/make_demo.py /tmp/ordnung-demo --lang de --setup http://localhost:8000``
once to add areas, a second account, tags, collections and rules through the API.

Everything is invented: the "Muster" family, every company, every address and number.
The senders use the reserved top-level domain ``.test``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

# --------------------------------------------------------------------------- PDF


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def letter_pdf(sender: str, sender_line: str, recipient: list[str], place_date: str,
               subject: str, body: list[str], footer: str) -> bytes:
    """A one-page A4 letter with a real text layer (Helvetica, WinAnsi)."""
    ops = []

    def text(x, y, s, size=10.5, bold=False, gray=0.0):
        font = "F2" if bold else "F1"
        ops.append(f"BT {gray:.2f} g /{font} {size} Tf {x} {y} Td ({_esc(s)}) Tj ET")

    # letterhead
    ops.append("0.11 0.30 0.62 rg 0 800 595 42 re f")
    text(56, 815, sender, 16, True, 1.0)
    text(56, 785, sender_line, 8, gray=0.35)
    for i, line in enumerate(recipient):
        text(56, 730 - i * 14, line)
    text(400, 660, place_date, 10)
    text(56, 620, subject, 12, True)
    y = 590
    for line in body:
        text(56, y, line)
        y -= 16 if line else 10
    ops.append("0.8 G 0.5 w 56 70 m 539 70 l S")
    text(56, 56, footer, 7.5, gray=0.45)
    content = "\n".join(ops).encode("cp1252", "replace")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
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


# --------------------------------------------------------------------------- data

AREAS = {
    "de": {"max": "Max", "erika": "Erika", "familie": "Familie", "haus": "Haus Lindenweg"},
    "en": {"max": "Max", "erika": "Erika", "familie": "Family", "haus": "House Linden Lane"},
}
PEOPLE = {"max": "Max Muster", "erika": "Erika Muster", "familie": "Familie Muster", "haus": "Familie Muster"}
ADDR = {"de": ["Lindenweg 5", "12345 Musterstadt"], "en": ["5 Linden Lane", "Sampletown AB1 2CD"]}
CITY = {"de": "Musterstadt", "en": "Sampletown"}

# (area, folder de, folder en, date, sender, domain, subject de, subject en, body de, body en, tags)
DOCS = [
    ("haus", "Versicherungen/Nordlicht/Wohngebäude", "Insurance/Nordlicht/Buildings", "2026-01-12",
     "Nordlicht Versicherung", "nordlicht-versicherung.test",
     "Versicherungsschein Wohngebäude", "Buildings insurance policy",
     ["Versicherungsschein Nr. WG-4471-2026", "Versicherungsort: Lindenweg 5, 12345 Musterstadt",
      "Versicherte Gefahren: Feuer, Leitungswasser, Sturm/Hagel, Elementar", "Jahresbeitrag: 612,40 EUR"],
     ["Policy no. WG-4471-2026", "Insured property: 5 Linden Lane, Sampletown",
      "Covered: fire, burst pipes, storm and hail, natural hazards", "Annual premium: EUR 612.40"], ["Steuer 2026"]),
    ("haus", "Versicherungen/Nordlicht/Wohngebäude", "Insurance/Nordlicht/Buildings", "2026-02-03",
     "Nordlicht Versicherung", "nordlicht-versicherung.test", "Beitragsrechnung 2026", "Premium invoice 2026",
     ["Versicherungsschein Nr. WG-4471-2026", "Fälliger Beitrag 01.03.2026: 612,40 EUR",
      "Der Betrag wird von Ihrem Konto abgebucht."],
     ["Policy no. WG-4471-2026", "Premium due 1 March 2026: EUR 612.40", "We will collect the amount by direct debit."],
     ["Steuer 2026"]),
    ("haus", "Wohnen/Handwerker", "Home/Tradespeople", "2026-03-18", "Sanitär Krause", "sanitaer-krause.test",
     "Rechnung 2026-117 Austausch Eckventile", "Invoice 2026-117 valve replacement",
     ["Arbeiten am 16.03.2026: Eckventile Bad und Küche getauscht", "Material 48,30 EUR, Arbeitszeit 1,5 h",
      "Rechnungsbetrag: 214,90 EUR inkl. MwSt.", "Davon Lohnkosten (§35a EStG): 142,80 EUR"],
     ["Work on 16 March 2026: replaced angle valves in bathroom and kitchen", "Material EUR 48.30, labour 1.5 h",
      "Total: EUR 214.90 incl. VAT", "Of which labour costs: EUR 142.80"], ["Steuer 2026"]),
    ("haus", "Wohnen/Energie", "Home/Energy", "2026-04-02", "Stadtwerke Musterstadt", "stadtwerke-musterstadt.test",
     "Jahresabrechnung Strom 2025", "Annual electricity statement 2025",
     ["Zählernummer 1ABC0012345678", "Verbrauch 01.01.–31.12.2025: 3.412 kWh", "Gutschrift: 86,20 EUR",
      "Neuer Abschlag ab Mai: 92,00 EUR"],
     ["Meter no. 1ABC0012345678", "Consumption 1 Jan – 31 Dec 2025: 3,412 kWh", "Credit: EUR 86.20",
      "New monthly payment from May: EUR 92.00"], []),
    ("familie", "Banken/Sparkasse Musterstadt/Kontoauszüge", "Banking/Sample Savings Bank/Statements", "2026-03-31",
     "Sparkasse Musterstadt", "sparkasse-musterstadt.test", "Kontoauszug März 2026", "Account statement March 2026",
     ["Girokonto DE12 3456 7890 1234 5678 90", "Alter Kontostand 2.481,17 EUR", "Neuer Kontostand 2.903,55 EUR"],
     ["Current account DE12 3456 7890 1234 5678 90", "Opening balance EUR 2,481.17",
      "Closing balance EUR 2,903.55"], []),
    ("familie", "Banken/Sparkasse Musterstadt/Kontoauszüge", "Banking/Sample Savings Bank/Statements", "2026-04-30",
     "Sparkasse Musterstadt", "sparkasse-musterstadt.test", "Kontoauszug April 2026", "Account statement April 2026",
     ["Girokonto DE12 3456 7890 1234 5678 90", "Alter Kontostand 2.903,55 EUR", "Neuer Kontostand 3.118,02 EUR"],
     ["Current account DE12 3456 7890 1234 5678 90", "Opening balance EUR 2,903.55",
      "Closing balance EUR 3,118.02"], []),
    ("familie", "Versicherungen/Nordlicht/Hausrat", "Insurance/Nordlicht/Contents", "2026-01-12",
     "Nordlicht Versicherung", "nordlicht-versicherung.test", "Versicherungsschein Hausrat", "Contents insurance policy",
     ["Versicherungsschein Nr. HR-2290-2026", "Versicherungssumme: 65.000 EUR", "Jahresbeitrag: 138,60 EUR"],
     ["Policy no. HR-2290-2026", "Sum insured: EUR 65,000", "Annual premium: EUR 138.60"], []),
    ("familie", "Versicherungen/Rechtsschutz", "Insurance/Legal expenses", "2025-11-20", "Justitia Rechtsschutz",
     "justitia-rechtsschutz.test", "Beitragsanpassung 2026", "Premium adjustment 2026",
     ["Vertrag RS-55102", "Ab 01.01.2026 beträgt Ihr Monatsbeitrag 24,90 EUR."],
     ["Contract RS-55102", "From 1 January 2026 your monthly premium is EUR 24.90."], []),
    ("familie", "Steuern/2025", "Taxes/2025", "2026-06-24", "Finanzamt Musterstadt", "finanzamt-musterstadt.test",
     "Einkommensteuerbescheid 2025", "Income tax assessment 2025",
     ["Steuernummer 123/456/78901", "Festgesetzte Einkommensteuer: 8.912,00 EUR", "Erstattung: 1.204,37 EUR"],
     ["Tax number 123/456/78901", "Income tax assessed: EUR 8,912.00", "Refund: EUR 1,204.37"], []),
    ("max", "Auto/Kombi", "Car/Estate", "2026-05-08", "Autohaus Berger", "autohaus-berger.test",
     "Rechnung Inspektion", "Service invoice",
     ["Fahrzeug: Kombi, Kennzeichen MU-ST 123", "Inspektion 60.000 km, Bremsflüssigkeit, Pollenfilter",
      "Rechnungsbetrag: 486,12 EUR"],
     ["Vehicle: estate car, registration MU-ST 123", "60,000 km service, brake fluid, cabin filter",
      "Total: EUR 486.12"], []),
    ("max", "Versicherungen/Kraftfahrt", "Insurance/Motor", "2025-12-01", "Kompass Kfz-Versicherung",
     "kompass-kfz.test", "Beitragsrechnung Kfz 2026", "Motor insurance premium 2026",
     ["Vertrag KF-778120, Kennzeichen MU-ST 123", "Haftpflicht und Vollkasko, SF 18", "Jahresbeitrag: 534,00 EUR"],
     ["Contract KF-778120, registration MU-ST 123", "Liability and comprehensive, no-claims class 18",
      "Annual premium: EUR 534.00"], ["Steuer 2026"]),
    ("max", "Arbeit/Gehalt", "Work/Pay", "2026-04-30", "Beispiel GmbH", "beispiel-gmbh.test",
     "Entgeltabrechnung April 2026", "Payslip April 2026",
     ["Personalnummer 004711", "Brutto 4.850,00 EUR, Netto 3.012,44 EUR"],
     ["Employee no. 004711", "Gross EUR 4,850.00, net EUR 3,012.44"], []),
    ("max", "Gesundheit/Ärzte", "Health/Doctors", "2026-02-14", "Praxis Dr. Sommer", "praxis-sommer.test",
     "Privatrechnung", "Private invoice",
     ["Behandlung am 06.02.2026", "Rechnungsbetrag nach GOÄ: 96,48 EUR"],
     ["Treatment on 6 February 2026", "Total: EUR 96.48"], ["Steuer 2026"]),
    ("erika", "Gesundheit/Krankenkasse", "Health/Health insurer", "2026-01-05", "Gesund & Fit Krankenkasse",
     "gesundundfit.test", "Bescheinigung Beiträge 2025", "Certificate of contributions 2025",
     ["Versichertennummer A123456789", "Gezahlte Beiträge 2025: 5.311,20 EUR"],
     ["Member no. A123456789", "Contributions paid in 2025: EUR 5,311.20"], ["Steuer 2026"]),
    ("erika", "Gesundheit/Ärzte", "Health/Doctors", "2026-03-09", "Zahnarztpraxis Weiss", "zahnarzt-weiss.test",
     "Heil- und Kostenplan", "Treatment and cost plan",
     ["Geplante Behandlung: Krone Zahn 26", "Voraussichtlicher Eigenanteil: 412,00 EUR"],
     ["Planned treatment: crown on tooth 26", "Expected own share: EUR 412.00"], []),
    ("erika", "Arbeit/Gehalt", "Work/Pay", "2026-04-30", "Stadtbibliothek Musterstadt", "stadtbibliothek.test",
     "Entgeltabrechnung April 2026", "Payslip April 2026",
     ["Personalnummer 2207", "Brutto 2.960,00 EUR, Netto 2.041,18 EUR"],
     ["Employee no. 2207", "Gross EUR 2,960.00, net EUR 2,041.18"], []),
    ("erika", "Ausweise", "ID documents", "2024-09-02", "Bürgeramt Musterstadt", "musterstadt.test",
     "Abholbenachrichtigung Personalausweis", "ID card ready for collection",
     ["Ihr neuer Personalausweis liegt zur Abholung bereit.", "Bitte bringen Sie den alten Ausweis mit."],
     ["Your new ID card is ready for collection.", "Please bring your old card."], []),
]

INBOX = [
    ("Nordlicht Versicherung", "nordlicht-versicherung.test", "2026-11-03",
     "Nachtrag zum Versicherungsschein", "Endorsement to your policy",
     ["Versicherungsschein Nr. WG-4471-2026", "Wir haben die Wohnfläche auf 142 m² angepasst."],
     ["Policy no. WG-4471-2026", "We have updated the living area to 142 m²."]),
    ("Sanitär Krause", "sanitaer-krause.test", "2026-11-05", "Angebot Badsanierung", "Quote bathroom refit",
     ["Angebot Nr. A-2026-088", "Badsanierung komplett: 14.860,00 EUR"],
     ["Quote no. A-2026-088", "Complete bathroom refit: EUR 14,860.00"]),
    ("Praxis Dr. Sommer", "praxis-sommer.test", "2026-11-06", "Privatrechnung", "Private invoice",
     ["Behandlung am 29.10.2026", "Rechnungsbetrag nach GOÄ: 54,12 EUR"],
     ["Treatment on 29 October 2026", "Total: EUR 54.12"]),
]


def _letter(lang, area, sender, domain, date, subject, body):
    y, m, d = date.split("-")
    when = f"{CITY[lang]}, {d}.{m}.{y}" if lang == "de" else f"{CITY[lang]}, {int(d)} {_month(int(m))} {y}"
    greet = ("Sehr geehrte Damen und Herren," if area in ("familie", "haus") else "Guten Tag,") if lang == "de" \
        else "Dear Sir or Madam,"
    bye = ["Mit freundlichen Grüßen", sender] if lang == "de" else ["Kind regards", sender]
    return letter_pdf(
        sender, f"{sender} · www.{domain} · info@{domain}",
        [PEOPLE[area], *ADDR[lang]], when, subject, [greet, "", *body, "", *bye],
        f"{sender} · www.{domain} · " + ("Dieses Dokument ist frei erfunden (Demo)." if lang == "de"
                                          else "This document is invented (demo)."))


def _month(m: int) -> str:
    return ["January", "February", "March", "April", "May", "June", "July", "August", "September",
            "October", "November", "December"][m - 1]


def build(root: Path, lang: str) -> None:
    archive, inbox = root / "archiv", root / "eingang" / ("scanner" if lang == "de" else "scanner")
    for p in (archive, inbox, root / "data"):
        p.mkdir(parents=True, exist_ok=True)
    for area in AREAS[lang]:
        (archive / area).mkdir(exist_ok=True)
    for area, f_de, f_en, date, sender, domain, s_de, s_en, b_de, b_en, _tags in DOCS:
        subject, body, folder = (s_de, b_de, f_de) if lang == "de" else (s_en, b_en, f_en)
        pdf = _letter(lang, area, sender, domain, date, subject, body)
        sid = hashlib.sha256(pdf).hexdigest()[:6]
        target = archive / area / folder
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{date}_{subject}_{sid}.pdf").write_bytes(pdf)
    for i, (sender, domain, date, s_de, s_en, b_de, b_en) in enumerate(INBOX, 1):
        subject, body = (s_de, b_de) if lang == "de" else (s_en, b_en)
        pdf = _letter(lang, "haus" if i == 1 else ("familie" if i == 2 else "max"), sender, domain, date,
                      subject, body)
        path = inbox / f"scan_{date.replace('-', '')}_{i:03d}.pdf"
        path.write_bytes(pdf)
        old = time.time() - 3600
        os.utime(path, (old, old))
    print(f"demo ({lang}) written to {root}")


# --------------------------------------------------------------------------- setup via API


def setup(root: Path, lang: str, base: str, user: str, password: str) -> None:
    import http.cookiejar
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(method, path, body=None):
        req = urllib.request.Request(base.rstrip("/") + "/api/" + path, method=method,
                                     data=None if body is None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with opener.open(req) as res:
            return json.loads(res.read() or b"null")

    call("POST", "login", {"username": user, "password": password})
    call("PUT", "storage", {
        "area_labels": AREAS[lang],
        "inboxes": [{"name": "Scanner", "path": str(root / "eingang" / "scanner"), "enabled": True,
                     "after_import": "move"}],
        "trash_days": 30,
    })
    call("POST", "rescan")
    for _ in range(60):                                  # wait for the first scan
        if call("GET", "status")["total"] >= len(DOCS):
            break
        time.sleep(1)
    call("PUT", "me/prefs", {"language": lang})
    # only the folders that hold documents – the shipped starter template is German and long
    for f in sorted((f for f in call("GET", "folders")["folders"] if f["template_only"]),
                    key=lambda f: -f["path"].count("/")):
        try:
            call("DELETE", "folders?path=" + urllib.parse.quote(f["path"]))
        except Exception:  # noqa: BLE001 – a parent goes with its children
            pass
    call("PATCH", f"users/{user}", {"display_name": "Max Muster"})
    try:
        call("POST", "users", {"name": "erika", "password": "erika-demo-2026", "display_name": "Erika Muster",
                               "areas": {"erika": "write", "familie": "write", "haus": "write"}})
    except Exception:  # noqa: BLE001 – already there
        pass
    # tags and a collection "tax return 2026"
    mappe = "Steuererklärung 2026" if lang == "de" else "Tax return 2026"
    try:
        call("POST", "mappen", {"name": mappe, "area": "familie"})
    except Exception:  # noqa: BLE001
        pass
    docs = call("GET", "documents?recursive=true&limit=500")["items"]
    by_subject = {d["title"]: d["id"] for d in docs}
    for area, f_de, f_en, date, sender, domain, s_de, s_en, b_de, b_en, tags in DOCS:
        title = s_de if lang == "de" else s_en
        if tags and title in by_subject:
            call("POST", "tags/change", {"ids": [by_subject[title]], "add": [mappe]})
    extra = {"Heil- und Kostenplan": "Zahnersatz", "Treatment and cost plan": "Dental work",
             "Rechnung 2026-117 Austausch Eckventile": "Bad", "Invoice 2026-117 valve replacement": "Bathroom"}
    for title, tag in extra.items():
        if title in by_subject:
            call("POST", "tags/change", {"ids": [by_subject[title]], "add": [tag]})
    # rules learned from the archive (no AI involved)
    try:
        call("POST", "rules/generate")
    except Exception:  # noqa: BLE001
        pass
    print("demo set up:", base)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--lang", choices=("de", "en"), default="de")
    ap.add_argument("--setup", metavar="URL")
    ap.add_argument("--user", default="demo")
    ap.add_argument("--password", default="demo1234")
    a = ap.parse_args()
    if a.setup:
        setup(a.root, a.lang, a.setup, a.user, a.password)
    else:
        build(a.root, a.lang)


if __name__ == "__main__":
    main()
