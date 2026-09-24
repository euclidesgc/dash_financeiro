import sqlite3

import pytest

from app.db import fold
from app.taxonomy.catalogue import create_category
from app.taxonomy.classify import classify_all, residue
from app.taxonomy.override import (
    NotAnOutflowError,
    UnknownCategoryError,
    UnknownTransactionError,
    clear_not_expense,
    restore_auto,
    set_manual,
    set_not_expense,
)
from app.taxonomy.seed import (
    UNCATEGORISED,
    pickable_categories,
    seed_labels,
    seed_taxonomy,
)
from tests.conftest import load, narrowed, transaction


def prepared(conn: sqlite3.Connection, seed: dict) -> int:
    load(
        conn,
        [
            transaction(
                "t-1", "2026-09-01", -10.0, descricao="LANCAMENTO UM", categoria="Healthcare"
            )
        ],
    )
    seed_taxonomy(conn, narrowed(seed, [r for r in seed["rules"] if r["match_kind"] == "category"]))
    classify_all(conn)
    conn.commit()
    row = conn.execute("SELECT id FROM transactions WHERE pluggy_id = ?", ("t-1",)).fetchone()
    return int(row["id"])


def reason_of(conn: sqlite3.Connection, id: int) -> str | None:
    row = conn.execute("SELECT not_expense_reason FROM transactions WHERE id = ?", (id,)).fetchone()
    return row["not_expense_reason"]


def state(conn: sqlite3.Connection, id: int) -> tuple[str | None, str | None, str, str]:
    row = conn.execute(
        "SELECT t.category, t.category_auto, t.category_source, g.name AS group_name "
        "FROM transactions AS t JOIN category_groups AS g ON g.id = t.group_id "
        "WHERE t.id = ?",
        (id,),
    ).fetchone()
    return (row["category"], row["category_auto"], row["category_source"], row["group_name"])


def test_pickable_categories_are_sorted_by_label_without_the_uncategorised_key(taxonomy_conn, seed):
    seed_taxonomy(taxonomy_conn, seed)

    categories = pickable_categories(taxonomy_conn)

    assert UNCATEGORISED not in [c.key for c in categories]
    assert len(categories) == len(seed_labels()) - 1
    sort_keys = [fold(c.label) for c in categories]
    assert sort_keys == sorted(sort_keys)
    assert all(c.is_system for c in categories)
    assert fold("Água") == "agua"


def test_set_manual_writes_the_category_marks_it_manual_and_reclassifies(tmp_path, seed):
    from app.db import connect
    from app.migrate import run_migrations

    path = str(tmp_path / "dash.sqlite")
    run_migrations(path)
    conn = connect(path)
    id = prepared(conn, seed)

    set_manual(conn, id, "Groceries")

    assert state(conn, id) == ("Groceries", "Healthcare", "manual", "Alimentação")
    conn.close()
    fresh = connect(path)
    row = fresh.execute(
        "SELECT category, category_auto, category_source FROM transactions WHERE id = ?", (id,)
    ).fetchone()
    fresh.close()
    assert (row["category"], row["category_auto"], row["category_source"]) == (
        "Groceries",
        "Healthcare",
        "manual",
    )


def test_set_manual_with_none_stores_null_as_manual(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)

    set_manual(taxonomy_conn, id, None)

    category, category_auto, category_source, _ = state(taxonomy_conn, id)
    assert category is None
    assert category_source == "manual"
    assert category_auto == "Healthcare"


def test_set_manual_refuses_a_key_outside_the_catalogue(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)
    before = state(taxonomy_conn, id)

    with pytest.raises(UnknownCategoryError):
        set_manual(taxonomy_conn, id, "Inexistente")

    assert state(taxonomy_conn, id) == before


def test_set_manual_refuses_the_uncategorised_key(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)
    before = state(taxonomy_conn, id)

    with pytest.raises(UnknownCategoryError):
        set_manual(taxonomy_conn, id, UNCATEGORISED)

    assert state(taxonomy_conn, id) == before


def test_set_manual_refuses_an_unknown_transaction(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)

    with pytest.raises(UnknownTransactionError):
        set_manual(taxonomy_conn, id + 1000, "Groceries")


def test_restore_auto_returns_to_category_auto_and_reclassifies(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)
    set_manual(taxonomy_conn, id, "Groceries")

    restore_auto(taxonomy_conn, id)

    assert state(taxonomy_conn, id) == ("Healthcare", "Healthcare", "auto", "Saúde")


def test_restore_auto_refuses_an_unknown_transaction(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)

    with pytest.raises(UnknownTransactionError):
        restore_auto(taxonomy_conn, id + 1000)


def test_set_manual_accepts_a_key_created_in_the_catalogue(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)
    key = create_category(taxonomy_conn, "Pet shop")

    set_manual(taxonomy_conn, id, key)

    category, _, source, _ = state(taxonomy_conn, id)
    assert category == "pet-shop"
    assert source == "manual"


def test_set_not_expense_writes_the_reason_and_reclassifies(tmp_path, seed):
    from app.db import connect
    from app.migrate import run_migrations

    path = str(tmp_path / "dash.sqlite")
    run_migrations(path)
    conn = connect(path)
    id = prepared(conn, seed)

    set_not_expense(conn, id, "refund")

    assert reason_of(conn, id) == "refund"
    assert state(conn, id)[3] == "Saúde"
    conn.close()
    fresh = connect(path)
    assert reason_of(fresh, id) == "refund"
    fresh.close()


def test_clear_not_expense_returns_to_null(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)
    set_not_expense(taxonomy_conn, id, "refund")

    clear_not_expense(taxonomy_conn, id)

    assert reason_of(taxonomy_conn, id) is None


def test_clear_not_expense_on_a_row_already_null_does_not_fail(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)

    clear_not_expense(taxonomy_conn, id)

    assert reason_of(taxonomy_conn, id) is None


def test_set_and_clear_not_expense_refuse_an_unknown_transaction(taxonomy_conn, seed):
    id = prepared(taxonomy_conn, seed)

    with pytest.raises(UnknownTransactionError):
        set_not_expense(taxonomy_conn, id + 1000, "other")

    with pytest.raises(UnknownTransactionError):
        clear_not_expense(taxonomy_conn, id + 1000)


def test_set_not_expense_refuses_a_transfer_a_refund_and_an_income(taxonomy_conn, seed):
    prepared(taxonomy_conn, seed)
    load(
        taxonomy_conn,
        [
            transaction("t-transfer", "2026-09-02", -20.0, eh_transferencia=True),
            transaction("t-refund", "2026-09-03", 20.0, eh_estorno=True),
            transaction("t-income", "2026-09-04", 100.0),
        ],
    )
    classify_all(taxonomy_conn)
    taxonomy_conn.commit()

    for pluggy_id in ("t-transfer", "t-refund", "t-income"):
        row = taxonomy_conn.execute(
            "SELECT id FROM transactions WHERE pluggy_id = ?", (pluggy_id,)
        ).fetchone()
        other_id = int(row["id"])

        with pytest.raises(NotAnOutflowError) as excinfo:
            set_not_expense(taxonomy_conn, other_id, "other")

        assert excinfo.value.transaction_id == other_id
        assert reason_of(taxonomy_conn, other_id) is None


def test_the_residue_stops_counting_a_row_marked_as_not_expense(taxonomy_conn, seed):
    prepared(taxonomy_conn, seed)
    load(
        taxonomy_conn,
        [transaction("t-2", "2026-09-02", -20.0, categoria="")],
    )
    classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    row = taxonomy_conn.execute(
        "SELECT id FROM transactions WHERE pluggy_id = ?", ("t-2",)
    ).fetchone()
    other_id = int(row["id"])

    result = residue(taxonomy_conn, start="2026-09-01", end="2026-09-30")
    assert result["entries"] == 1

    set_not_expense(taxonomy_conn, other_id, "other")

    result = residue(taxonomy_conn, start="2026-09-01", end="2026-09-30")
    assert result["entries"] == 0
    assert result["amount_cents"] == 0
