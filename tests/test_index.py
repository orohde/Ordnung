import functools

import pytest

from ordnung.config import Settings
from ordnung.index import HL_START, Index, parse_name, shortest_unique_ids, split_path
from ordnung.textextract import extract


@pytest.fixture
def index(settings: Settings) -> Index:
    idx = Index(settings.db_path, settings.archive)
    idx.scan()
    return idx


@pytest.fixture
def full_index(index: Index) -> Index:
    index.extract_pending(functools.partial(extract, ocr=False))
    return index


def test_parse_name():
    assert parse_name("2026-10-01_Rezept_a3f9c1").title == "Rezept"
    assert parse_name("2026-10-01_Rezept_a3f9c1").doc_date == "2026-10-01"
    assert parse_name("2026-08-17_Zuzahlung – Diakonie").title == "Zuzahlung – Diakonie"
    assert parse_name("0000381").title == "0000381"
    assert parse_name("0000381").doc_date is None


def test_split_path():
    assert split_path("oliver/Banken/DKB/x.pdf") == ("oliver", "Banken/DKB")
    assert split_path("oliver/x.pdf") == ("oliver", "")
    assert split_path("x.pdf") == ("", "")


def test_short_ids_grow_on_collision():
    ids = shortest_unique_ids(["abcdef01" + "0" * 56, "abcdef02" + "0" * 56, "123456" + "0" * 58])
    assert ids["123456" + "0" * 58] == "123456"
    assert ids["abcdef01" + "0" * 56] == "abcdef01"


def test_scan_skips_hidden_and_counts(index: Index):
    assert index.meta()["total"] == 6
    assert {a["name"] for a in index.areas()} == {"", "oliver", "erika", "gemeinsam"}


def test_rescan_is_incremental(index: Index, settings: Settings):
    result = index.scan()
    assert result["hashed"] == 0 and result["removed"] == 0
    (settings.archive / "oliver/Banken/DKB/2026-03-01_Kontoauszug.pdf").unlink()
    assert index.scan()["removed"] == 1
    assert index.documents(["oliver"], recursive=True, query="kontoauszug")["total"] == 0


def test_schema_change_rebuilds(settings: Settings, index: Index):
    with index.connect() as con:
        con.execute("UPDATE meta SET value='1' WHERE key='schema'")
    again = Index(settings.db_path, settings.archive)
    assert again.meta()["total"] == 0
    again.scan()
    assert again.meta()["total"] == 6


def test_tree_merges_areas(index: Index):
    tree = index.tree(["oliver", "gemeinsam"])
    versicherungen = next(c for c in tree["children"] if c["name"] == "Versicherungen")
    assert versicherungen["count"] == 2
    assert versicherungen["areas"] == ["gemeinsam", "oliver"]


def test_search_path_and_title(index: Index):
    found = index.documents(["oliver", "erika", "gemeinsam"], recursive=True, query="contin wohng")
    assert found["total"] == 1
    assert found["items"][0]["title"] == "Versicherungsschein Wohngebäude"


def test_text_extraction(full_index: Index):
    status = full_index.text_status()
    assert status["done"] == status["total"] == 6
    assert status["errors"] == 0


def test_search_full_text_with_snippet(full_index: Index):
    found = full_index.documents(["erika"], recursive=True, query="ibuprof")
    assert found["total"] == 1
    assert HL_START in found["items"][0]["snippet"]


def test_search_ranks_title_over_body(full_index: Index):
    found = full_index.documents(["oliver", "erika", "gemeinsam"], recursive=True, query="rezept")
    assert found["total"] == 2


def test_area_restriction(full_index: Index):
    found = full_index.documents(["erika"], recursive=True, query="continentale")
    assert found["total"] == 0


def test_short_tokens_fall_back_to_like(full_index: Index):
    found = full_index.documents(["oliver"], recursive=True, query="dkb")
    assert found["total"] == 1
    found = full_index.documents(["oliver"], recursive=True, query="nr")
    assert found["total"] == 0  # path/title only for one- and two-letter words
