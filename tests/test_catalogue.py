import sqlite3

import pytest

from app.db import connect
from app.taxonomy.catalogue import (
    CategoryInUseError,
    CategoryNotFoundError,
    DuplicateLabelError,
    InvalidLabelError,
    SystemCategoryError,
    create_category,
    delete_category,
    rename_category,
    slugify,
)
from app.taxonomy.seed import UNCATEGORISED, seed_taxonomy
from tests.conftest import load, transaction


def row(conn: sqlite3.Connection, key: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT name, label, is_system, group_id FROM categories WHERE name = ?", (key,)
    ).fetchone()


@pytest.fixture
def seeded(taxonomy_conn: sqlite3.Connection, seed: dict) -> sqlite3.Connection:
    seed_taxonomy(taxonomy_conn, seed)
    return taxonomy_conn


def test_slugify_folds_accents_and_joins_runs_with_a_dash():
    assert slugify("Pet shop") == "pet-shop"
    assert slugify("Água & Luz") == "agua-luz"
    assert slugify("!!!") == "categoria"
    assert slugify("  Lazer  ") == "lazer"


def test_create_category_writes_a_non_system_row_in_the_fallback_group(seeded, tmp_path):
    key = create_category(seeded, " Pet shop ")

    assert key == "pet-shop"
    created = row(seeded, key)
    assert created["label"] == "Pet shop"
    assert created["is_system"] == 0
    fallback = seeded.execute("SELECT id FROM category_groups WHERE is_fallback = 1").fetchone()
    assert created["group_id"] == fallback["id"]

    fresh = connect(seeded.execute("PRAGMA database_list").fetchone()["file"])
    try:
        assert row(fresh, key) is not None
    finally:
        fresh.close()


def test_create_category_makes_the_key_unique_with_a_numeric_suffix(seeded):
    create_category(seeded, "Pet shop")
    rename_category(seeded, "pet-shop", "Bicho")

    second = create_category(seeded, "Pet shop")
    assert second == "pet-shop-2"

    third = create_category(seeded, "Pet-Shop")
    assert third == "pet-shop-3"


def test_create_category_refuses_an_empty_or_blank_label(seeded):
    before = seeded.execute("SELECT count(*) FROM categories").fetchone()[0]

    with pytest.raises(InvalidLabelError):
        create_category(seeded, "")
    with pytest.raises(InvalidLabelError):
        create_category(seeded, "   ")

    after = seeded.execute("SELECT count(*) FROM categories").fetchone()[0]
    assert after == before


def test_create_category_refuses_a_label_that_only_differs_in_case_or_accent(seeded):
    with pytest.raises(DuplicateLabelError):
        create_category(seeded, "supermercado")
    with pytest.raises(DuplicateLabelError):
        create_category(seeded, "SUPERMERCADO")
    with pytest.raises(DuplicateLabelError):
        create_category(seeded, "Supermercádo")
    with pytest.raises(DuplicateLabelError):
        create_category(seeded, "sem categoria")


def test_rename_category_changes_only_the_label(seeded):
    rename_category(seeded, "Groceries", "Mercado")

    updated = row(seeded, "Groceries")
    assert updated["label"] == "Mercado"
    assert updated["is_system"] == 1
    assert updated["name"] == "Groceries"


def test_rename_category_accepts_its_own_label_in_another_case(seeded):
    create_category(seeded, "Pet shop")

    rename_category(seeded, "pet-shop", "PET SHOP")

    assert row(seeded, "pet-shop")["label"] == "PET SHOP"


def test_rename_category_refuses_a_duplicate_of_another_category(seeded):
    with pytest.raises(DuplicateLabelError):
        rename_category(seeded, "Groceries", "casa")

    assert row(seeded, "Groceries")["label"] != "casa"


def test_rename_category_refuses_the_uncategorised_key_and_an_unknown_key(seeded):
    with pytest.raises(CategoryNotFoundError):
        rename_category(seeded, UNCATEGORISED, "Novo Rotulo")
    with pytest.raises(CategoryNotFoundError):
        rename_category(seeded, "nao-existe", "Novo Rotulo")


def test_delete_category_refuses_a_system_category(seeded):
    with pytest.raises(SystemCategoryError):
        delete_category(seeded, "Groceries")

    assert row(seeded, "Groceries") is not None


def test_delete_category_refuses_a_category_in_use_and_reports_the_count(seeded):
    create_category(seeded, "Pet shop")
    load(
        seeded,
        [
            transaction("t-1", "2026-09-01", -10.0, categoria="pet-shop"),
            transaction("t-2", "2026-09-02", -5.0, categoria="pet-shop"),
        ],
    )

    with pytest.raises(CategoryInUseError) as excinfo:
        delete_category(seeded, "pet-shop")

    assert excinfo.value.usage_count == 2
    assert row(seeded, "pet-shop") is not None


def test_delete_category_removes_a_free_category_of_the_owner(seeded):
    create_category(seeded, "Pet shop")

    delete_category(seeded, "pet-shop")

    assert row(seeded, "pet-shop") is None
    fresh = connect(seeded.execute("PRAGMA database_list").fetchone()["file"])
    try:
        assert row(fresh, "pet-shop") is None
    finally:
        fresh.close()


def test_delete_category_refuses_the_uncategorised_key_and_an_unknown_key(seeded):
    with pytest.raises(CategoryNotFoundError):
        delete_category(seeded, UNCATEGORISED)
    with pytest.raises(CategoryNotFoundError):
        delete_category(seeded, "nao-existe")
