import functools
from pathlib import Path

import pytest

from ordnung.index import Index
from ordnung.rules import RuleService
from ordnung.senders import SenderBook, SenderService, describe, detect, grade, pretty
from ordnung.textextract import extract

from conftest import make_pdf

EXTRACT = functools.partial(extract, ocr=False)

DOCS = {
    # Cosmos Direkt only ever writes about the car
    "oliver/Versicherungen/Cosmos/KFZ/2024-01-01_Beitrag_aaaa11.pdf":
        "CosmosDirekt www.cosmosdirekt.de Beitragsrechnung Kfz-Versicherung Kennzeichen XX-AB 123",
    "oliver/Versicherungen/Cosmos/KFZ/2025-01-01_Beitrag_aaaa22.pdf":
        "CosmosDirekt www.cosmosdirekt.de Nachtrag Kfz-Versicherung Kennzeichen XX-AB 123",
    # the DKB writes about cards and accounts: the sender alone is not enough
    "oliver/Banken/DKB/Kreditkarten/2026-01-05_Abrechnung_bbbb11.pdf":
        "DKB AG www.dkb.de Kreditkartenabrechnung Januar Visa",
    "oliver/Banken/DKB/Kreditkarten/2026-02-05_Abrechnung_bbbb22.pdf":
        "DKB AG www.dkb.de Kreditkartenabrechnung Februar Visa",
    "oliver/Banken/DKB/Kontoauszüge/2026-01-31_Auszug_cccc11.pdf":
        "DKB AG www.dkb.de Kontoauszug Girokonto Januar Lastschrift amazon.de",
    # own address on a letter we wrote ourselves
    "oliver/Sonstiges/2026-03-01_Brief_dddd11.pdf": "Max Muster max@example.org Kündigung des Vertrags",
}


@pytest.fixture
def svc(tmp_path: Path) -> SenderService:
    archive = tmp_path / "archiv"
    for rel, text in DOCS.items():
        p = archive / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(make_pdf(text))
    index = Index(tmp_path / "ordnung.db", archive)
    index.scan()
    index.extract_pending(EXTRACT)
    rules = RuleService(tmp_path / "rules.json", index)
    book = SenderBook(tmp_path / "senders.json")
    book.set_own("example.org", True)
    return SenderService(book, rules)


def test_detect_and_names():
    text = "Kontoauszug\\nDKB AG · www.dkb.de\\n" + "x " * 2000 + "Lastschrift amazon.de amazon.de"
    assert detect(text, set()) == "dkb.de"              # the letterhead counts more than payees
    assert detect("Mail an max@example.org", {"example.org"}) is None
    assert detect("gesendet von gmail.com", set()) is None   # mail providers are no senders
    assert pretty("cosmosdirekt.de") == "Cosmosdirekt" and pretty("dkb.de") == "DKB"
    assert pretty("dr-mustermann.de") == "Dr Mustermann" and pretty("bad-musterstadt.de") == "Bad Musterstadt"
    assert grade(9, 10) == "green" and grade(6, 10) == "yellow" and grade(1, 10) == "red"


def test_describe_in_plain_words():
    names = {"cosmosdirekt.de": "Cosmos Direkt"}.get
    assert describe([{"type": "contains", "value": "cosmosdirekt.de"}], names) == "Post von Cosmos Direkt"
    assert describe([{"type": "contains", "value": "dkb.de"}, {"type": "contains", "value": "visa"}],
                    lambda d: "DKB") == "Post von DKB, in der „visa“ vorkommt"
    assert describe([{"type": "id", "value": "4711"}], names) == "Schreiben mit der Nummer 4711"


def test_propose_sender_alone(svc: SenderService):
    text = "CosmosDirekt www.cosmosdirekt.de Abrechnung der Kfz-Versicherung 2026"
    p = svc.propose(text, "Versicherungen/Cosmos/KFZ")
    assert p["kind"] == "sender" and p["conditions"] == [{"type": "contains", "value": "cosmosdirekt.de"}]
    assert p["label"] == "Post von Cosmosdirekt" and p["inside"] == 2 and len(p["examples"]) == 2
    # once the rule exists, nobody is asked again
    svc.rules.create(p["folder"], p["conditions"], source="learned", label=p["label"])
    assert svc.propose(text, "Versicherungen/Cosmos/KFZ") is None


def test_propose_sender_plus_word(svc: SenderService):
    text = "DKB AG www.dkb.de Kreditkartenabrechnung März Visa"
    p = svc.propose(text, "Banken/DKB/Kreditkarten")
    assert p["kind"] == "sender+word" and p["conditions"][0] == {"type": "contains", "value": "dkb.de"}
    assert p["conditions"][1]["value"] in ("Kreditkartenabrechnung", "Visa")   # as written in the letter
    assert p["label"].startswith("Post von DKB, in der „") and p["inside"] == 2
    # declined: not asked again for this sender and folder
    svc.book.decline("dkb.de", "Banken/DKB/Kreditkarten")
    assert svc.propose(text, "Banken/DKB/Kreditkarten") is None


def test_overview(svc: SenderService):
    rows = {r["domain"]: r for r in svc.overview()}
    assert set(rows) == {"cosmosdirekt.de", "dkb.de"}           # own address and payees left out
    dkb = rows["dkb.de"]
    assert dkb["docs"] == 3 and dkb["grade"] == "red" and dkb["none"] == 3
    assert [f["folder"] for f in dkb["folders"]] == ["Banken/DKB/Kreditkarten", "Banken/DKB/Kontoauszüge"]
    svc.rules.create("Banken/DKB/Kreditkarten", [{"type": "contains", "value": "kreditkartenabrechnung"}])
    dkb = {r["domain"]: r for r in svc.overview()}["dkb.de"]
    assert dkb["ok"] == 2 and dkb["folders"][0]["grade"] == "green"
    assert [d["title"] for d in svc.documents("dkb.de", "Banken/DKB/Kreditkarten")] == ["Abrechnung", "Abrechnung"]
