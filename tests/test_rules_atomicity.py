import pytest

from app.taxonomy import classify, rules
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction


@pytest.fixture
def rows():
    return [
        transaction("t-a", "2026-03-02", -10.00, descricao="Loja A", categoria="Compras"),
        transaction("t-b", "2026-03-03", -20.00, descricao="Loja B", categoria="Compras"),
        transaction("t-c", "2026-03-04", -30.00, descricao="Outra", categoria="Nada"),
    ]


@pytest.fixture
def base(taxonomy_conn, seed, rows):
    conn = load(taxonomy_conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify.classify_all(conn)
    conn.commit()
    return conn


def snapshot(conn):
    return [
        tuple(row)
        for row in conn.execute(
            "SELECT id, rule_id, group_id, nature, essentiality FROM transactions ORDER BY id"
        )
    ]


def half_written_then_broken(conn):
    conn.execute(
        "UPDATE transactions SET rule_id = NULL, group_id = NULL, nature = NULL, "
        "essentiality = NULL WHERE id = (SELECT min(id) FROM transactions)"
    )
    raise RuntimeError("reclassification broke halfway")


def test_a_failed_reclassification_leaves_no_row_changed(base, seed, monkeypatch):
    before_rules = base.execute("SELECT count(*) FROM category_rules").fetchone()[0]
    before_rows = snapshot(base)
    group_id = base.execute(
        "SELECT id FROM category_groups WHERE name = ?", (seed["groups"][0]["name"],)
    ).fetchone()[0]
    monkeypatch.setattr(classify, "classify_all", half_written_then_broken)
    with pytest.raises(RuntimeError):
        rules.create_rule(
            base,
            match_kind="category",
            match_value="Compras",
            group_id=group_id,
            nature=seed["natures"][0],
            essentiality=seed["essentialities"][0],
        )
    assert base.execute("SELECT count(*) FROM category_rules").fetchone()[0] == before_rules
    assert snapshot(base) == before_rows


def test_a_failed_reclassification_leaves_an_edit_undone(base, seed, monkeypatch):
    group_id = base.execute(
        "SELECT id FROM category_groups WHERE name = ?", (seed["groups"][0]["name"],)
    ).fetchone()[0]
    rules.create_rule(
        base,
        match_kind="category",
        match_value="Compras",
        group_id=group_id,
        nature=seed["natures"][0],
        essentiality=seed["essentialities"][0],
    )
    rule_id = base.execute(
        "SELECT id FROM category_rules WHERE match_value = ?", ("Compras",)
    ).fetchone()[0]
    before_rules = base.execute(
        "SELECT match_kind, match_value, group_id, nature, essentiality FROM category_rules"
    ).fetchall()
    before_rows = snapshot(base)
    monkeypatch.setattr(classify, "classify_all", half_written_then_broken)
    with pytest.raises(RuntimeError):
        rules.update_rule(base, rule_id, essentiality=seed["essentialities"][-1])
    after_rules = base.execute(
        "SELECT match_kind, match_value, group_id, nature, essentiality FROM category_rules"
    ).fetchall()
    assert [tuple(row) for row in after_rules] == [tuple(row) for row in before_rules]
    assert snapshot(base) == before_rows
