import sqlite3

import pytest

from app.commitments.mark import dismiss, resume
from app.db import connect
from app.queries.crossings import candidates, crossing, crossing_definitions
from app.queries.payees import payee_cnpj, payee_known
from app.queries.reach import correction_target
from app.queries.rules import (
    held_by_rule,
    payee_samples,
    residue,
    rule,
    rule_candidates,
    rule_id_of,
    rule_listing,
    rules_carrying,
)
from app.queries.transactions import base_is_empty
from app.queries.vocabulary import fallback_term, group_name, groups, natures, terms
from app.taxonomy.classify import MATCH_CATEGORY, MATCH_DESCRIPTION, classify_all
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction
from tests.conftest import rule as rule_row

WINDOW = ("2026-03-01", "2026-03-31")


@pytest.fixture
def base(taxonomy_conn, seed):
    load(
        taxonomy_conn,
        [
            transaction("t-shop", "2026-03-02", -10.00, descricao="Loja", categoria="Compras"),
            transaction("t-shop-2", "2026-03-09", -15.00, descricao="Loja", categoria="Compras"),
            transaction(
                "t-clinic",
                "2026-03-03",
                -20.00,
                descricao="Clinica",
                categoria="Saude",
                cnpj="22.222.222/0001-22",
            ),
            transaction("t-orphan", "2026-03-04", -30.00, descricao="Avulso", categoria="Nada"),
            transaction("t-outside", "2026-01-07", -60.00, descricao="Fora", categoria="Nada"),
        ],
    )
    health = seed["groups"][5]["name"]
    seed_taxonomy(
        taxonomy_conn,
        narrowed(seed, [rule_row(MATCH_CATEGORY, "Saude", health, "fixa", "essencial")]),
    )
    classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    return taxonomy_conn


def payee_of(conn: sqlite3.Connection, pluggy_id: str) -> str:
    row = conn.execute("SELECT payee FROM transactions WHERE pluggy_id = ?", (pluggy_id,))
    return str(row.fetchone()[0])


def id_of(conn: sqlite3.Connection, pluggy_id: str) -> int:
    row = conn.execute("SELECT id FROM transactions WHERE pluggy_id = ?", (pluggy_id,))
    return int(row.fetchone()[0])


def test_the_vocabulary_comes_back_in_the_seed_order(base, seed):
    assert [row["name"] for row in groups(base)][:1] == [seed["groups"][0]["name"]]
    assert natures(base) == seed["natures"]
    assert terms(base) == seed["essentialities"]
    assert fallback_term(base) == seed["fallback_essentiality"]


def test_a_group_name_is_empty_for_an_unknown_group(base, seed):
    first = groups(base)[0]
    assert group_name(base, first["id"]) == first["name"]
    assert group_name(base, -1) == ""


def test_the_residue_over_the_whole_base_counts_what_the_window_leaves_out(base):
    whole = residue(base)
    window = residue(base, start=WINDOW[0], end=WINDOW[1])
    assert (window["entries"], window["amount_cents"]) == (3, -5500)
    assert (whole["entries"], whole["amount_cents"]) == (4, -11500)


def test_a_written_rule_is_found_by_its_match_and_reports_what_it_holds(base):
    found = rule_id_of(base, match_kind=MATCH_CATEGORY, match_value="Saude")
    assert found is not None
    assert held_by_rule(base, found) == 1
    assert rule(base, found)["match_value"] == "Saude"
    assert rule(base, str(found))["id"] == found
    assert rule_id_of(base, match_kind=MATCH_DESCRIPTION, match_value="Saude") is None
    assert rule(base, -1) is None


def test_the_rule_listing_carries_the_money_each_rule_holds(base):
    listed = rule_listing(base)
    assert [(row["match_value"], row["entries"], row["amount_cents"]) for row in listed] == [
        ("Saude", 1, -2000)
    ]
    assert rules_carrying(base, "essencial") == 1
    assert rules_carrying(base, "supérfluo") == 0


def test_rule_candidates_read_both_shapes_of_the_loose_money_and_stop_at_the_limit(base):
    found = rule_candidates(base, category_kind="c", payee_kind="p", limit=2)
    assert [(row["kind"], row["value"], row["amount_cents"]) for row in found] == [
        ("c", "Nada", -9000),
        ("p", payee_of(base, "t-outside"), -6000),
    ]


def test_payee_samples_order_the_most_frequent_payee_first(base):
    assert payee_samples(base, 1) == [payee_of(base, "t-shop")]


def test_a_payee_is_known_only_when_a_transaction_carries_it(base):
    assert payee_known(base, payee_of(base, "t-clinic"))
    assert not payee_known(base, "ninguém")


def test_the_cnpj_of_a_payee_is_read_from_its_transactions(base):
    assert payee_cnpj(base, payee_of(base, "t-clinic")) is not None
    assert payee_cnpj(base, payee_of(base, "t-shop")) is None
    assert payee_cnpj(base, "ninguém") is None


def test_an_empty_base_says_so(base):
    assert not base_is_empty(base)
    base.execute("DELETE FROM transactions")
    assert base_is_empty(base)


def test_the_correction_target_is_read_by_transaction_id(base):
    target = correction_target(base, id_of(base, "t-clinic"))
    assert target is not None
    assert target["category"] == "Saude"
    assert correction_target(base, -1) is None


def test_crossing_candidates_are_the_crossing_rows_under_the_fallback_term(base, seed):
    slugs = [row["slug"] for row in crossing_definitions(base)]
    assert slugs == [
        item["slug"] for item in sorted(seed["crossings"], key=lambda c: c["position"])
    ]
    nature, term = seed["fallback_nature"], seed["fallback_essentiality"]
    offered = candidates(base, nature=nature, term=term, start=WINDOW[0], end=WINDOW[1], limit=1)
    all_rows = candidates(base, nature=nature, term=term, start=WINDOW[0], end=WINDOW[1], limit=10)
    assert [row["key"] for row in offered] == [all_rows[0]["key"]]
    assert [row["amount_cents"] for row in all_rows] == sorted(
        row["amount_cents"] for row in all_rows
    )
    assert crossing(base, slug=slugs[0], start=WINDOW[0], end=WINDOW[1]).rows is not None


def test_dismissing_and_resuming_are_durable_without_a_commit_from_the_caller(base):
    base.execute(
        "INSERT INTO commitments (kind, series_key, description, amount_cents, last_seen_date) "
        "VALUES ('recurring', 's', 's', -100, '2026-03-01')"
    )
    base.commit()
    path = base.execute("PRAGMA database_list").fetchone()["file"]
    dismiss(base, "s")
    other = connect(path)
    try:
        assert other.execute("SELECT dismissed FROM commitments").fetchone()[0] == 1
        resume(base, "s")
        assert other.execute("SELECT dismissed FROM commitments").fetchone()[0] == 0
    finally:
        other.close()
