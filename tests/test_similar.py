import sqlite3

import pytest

from app.queries.similar import count_similar
from app.taxonomy.classify import classify_all
from app.taxonomy.override import (
    UnknownCategoryError,
    UnknownTransactionError,
    apply_to_similar,
    set_manual,
)
from app.taxonomy.seed import UNCATEGORISED, seed_taxonomy
from tests.conftest import load, narrowed, transaction

BASE_ROWS = [
    transaction("o", "2026-09-01", -45.0, descricao="FARMACIA CENTRAL", categoria="Healthcare"),
    transaction("s1", "2026-08-15", -30.0, descricao="FARMACIA CENTRAL"),
    transaction("s2", "2026-07-08", -20.0, descricao="Farmácia Central"),
    transaction("x", "2026-09-02", -10.0, descricao="MERCADO"),
]


def prepared(
    conn: sqlite3.Connection, seed: dict, rows: list[dict], *, classify: bool
) -> sqlite3.Connection:
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, [r for r in seed["rules"] if r["match_kind"] == "category"]))
    if classify:
        classify_all(conn)
        conn.commit()
    return conn


def id_of(conn: sqlite3.Connection, pluggy_id: str) -> int:
    row = conn.execute("SELECT id FROM transactions WHERE pluggy_id = ?", (pluggy_id,)).fetchone()
    return int(row["id"])


def row_of(conn: sqlite3.Connection, id: int) -> tuple[str | None, str, str | None, str]:
    row = conn.execute(
        "SELECT t.category, t.category_source, t.payee, g.name AS group_name "
        "FROM transactions AS t LEFT JOIN category_groups AS g ON g.id = t.group_id "
        "WHERE t.id = ?",
        (id,),
    ).fetchone()
    return {
        "category": row["category"],
        "category_source": row["category_source"],
        "payee": row["payee"],
        "group_name": row["group_name"],
    }


def test_count_similar_matches_by_payee_after_classification_and_excludes_the_origin(
    taxonomy_conn, seed
):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    o = id_of(taxonomy_conn, "o")
    s1 = id_of(taxonomy_conn, "s1")

    assert row_of(taxonomy_conn, o)["payee"]
    assert count_similar(taxonomy_conn, o) == 2
    assert count_similar(taxonomy_conn, s1) == 2


def test_count_similar_falls_back_to_the_folded_description_when_the_payee_is_null(
    taxonomy_conn, seed
):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=False)
    o = id_of(taxonomy_conn, "o")

    assert not row_of(taxonomy_conn, o)["payee"]
    assert count_similar(taxonomy_conn, o) == 2


def test_count_similar_with_a_null_description_matches_nothing(taxonomy_conn, seed):
    rows = [
        transaction("n1", "2026-09-01", -10.0, descricao=None),
        transaction("n2", "2026-09-02", -10.0, descricao=None),
    ]
    prepared(taxonomy_conn, seed, rows, classify=False)
    n1 = id_of(taxonomy_conn, "n1")

    assert count_similar(taxonomy_conn, n1) == 0


def test_transfers_refunds_and_credits_of_the_same_payee_stay_out(taxonomy_conn, seed):
    rows = [
        *BASE_ROWS,
        transaction("t", "2026-09-03", -5.0, descricao="FARMACIA CENTRAL", eh_transferencia=True),
        transaction("r", "2026-09-04", -5.0, descricao="FARMACIA CENTRAL", eh_estorno=True),
        transaction("c", "2026-09-05", 5.0, descricao="FARMACIA CENTRAL", tipo="CREDIT"),
    ]
    prepared(taxonomy_conn, seed, rows, classify=True)
    o = id_of(taxonomy_conn, "o")

    assert count_similar(taxonomy_conn, o) == 2


def test_a_similar_row_already_manual_with_another_category_counts(taxonomy_conn, seed):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    o = id_of(taxonomy_conn, "o")
    s1 = id_of(taxonomy_conn, "s1")
    set_manual(taxonomy_conn, s1, "Housing")

    assert count_similar(taxonomy_conn, o) == 2


def test_an_origin_that_is_not_spending_still_counts_the_similar_spending(taxonomy_conn, seed):
    rows = [
        *BASE_ROWS,
        transaction("c", "2026-09-05", 5.0, descricao="FARMACIA CENTRAL", tipo="CREDIT"),
    ]
    prepared(taxonomy_conn, seed, rows, classify=True)
    c = id_of(taxonomy_conn, "c")

    assert count_similar(taxonomy_conn, c) == 3


def test_apply_to_similar_writes_the_category_as_manual_on_every_similar_row_and_returns_the_count(
    taxonomy_conn, seed, tmp_path
):
    from app.db import connect

    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    o = id_of(taxonomy_conn, "o")
    s1 = id_of(taxonomy_conn, "s1")
    s2 = id_of(taxonomy_conn, "s2")
    x = id_of(taxonomy_conn, "x")
    path = taxonomy_conn.execute("PRAGMA database_list").fetchone()["file"]

    updated = apply_to_similar(taxonomy_conn, o, "Groceries")

    assert updated == 2
    assert (
        row_of(taxonomy_conn, s1)["category"],
        row_of(taxonomy_conn, s1)["category_source"],
    ) == (
        "Groceries",
        "manual",
    )
    assert (
        row_of(taxonomy_conn, s2)["category"],
        row_of(taxonomy_conn, s2)["category_source"],
    ) == (
        "Groceries",
        "manual",
    )
    assert row_of(taxonomy_conn, x)["category_source"] != "manual"
    fresh = connect(path)
    row = fresh.execute(
        "SELECT category, category_source FROM transactions WHERE id = ?", (s1,)
    ).fetchone()
    fresh.close()
    assert (row["category"], row["category_source"]) == ("Groceries", "manual")


def test_apply_to_similar_does_not_touch_the_origin(taxonomy_conn, seed):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    o = id_of(taxonomy_conn, "o")

    apply_to_similar(taxonomy_conn, o, "Groceries")

    result = row_of(taxonomy_conn, o)
    assert result["category"] == "Healthcare"
    assert result["category_source"] == "auto"


def test_apply_to_similar_reclassifies_the_group(taxonomy_conn, seed):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    o = id_of(taxonomy_conn, "o")
    s1 = id_of(taxonomy_conn, "s1")

    apply_to_similar(taxonomy_conn, o, "Groceries")

    assert row_of(taxonomy_conn, s1)["group_name"] == "Alimentação"


def test_apply_to_similar_with_none_stores_null_as_manual(taxonomy_conn, seed):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    o = id_of(taxonomy_conn, "o")
    s1 = id_of(taxonomy_conn, "s1")

    updated = apply_to_similar(taxonomy_conn, o, None)

    assert updated == 2
    result = row_of(taxonomy_conn, s1)
    assert result["category"] is None
    assert result["category_source"] == "manual"


def test_apply_to_similar_refuses_an_unknown_key_and_the_uncategorised_key_without_writing(
    taxonomy_conn, seed
):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    o = id_of(taxonomy_conn, "o")
    s1 = id_of(taxonomy_conn, "s1")
    before = row_of(taxonomy_conn, s1)

    with pytest.raises(UnknownCategoryError):
        apply_to_similar(taxonomy_conn, o, "Inexistente")
    with pytest.raises(UnknownCategoryError):
        apply_to_similar(taxonomy_conn, o, UNCATEGORISED)

    assert row_of(taxonomy_conn, s1) == before


def test_apply_to_similar_refuses_an_unknown_transaction(taxonomy_conn, seed):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    o = id_of(taxonomy_conn, "o")

    with pytest.raises(UnknownTransactionError):
        apply_to_similar(taxonomy_conn, o + 1000, "Groceries")


def test_apply_to_similar_without_similar_rows_returns_zero(taxonomy_conn, seed):
    prepared(taxonomy_conn, seed, BASE_ROWS, classify=True)
    x = id_of(taxonomy_conn, "x")

    assert apply_to_similar(taxonomy_conn, x, "Groceries") == 0
