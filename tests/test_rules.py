import pytest

from app.taxonomy.classify import classify_all
from app.taxonomy.rules import (
    InvalidExpressionError,
    InvalidTermError,
    UnknownRuleError,
    create_rule,
    delete_rule,
    update_rule,
)
from app.taxonomy.seed import message, seed_taxonomy
from tests.conftest import load, narrowed, transaction

UNKNOWN_GROUP = 9999
BROKEN_EXPRESSION = "[a-"


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
    classify_all(conn)
    conn.commit()
    return conn


@pytest.fixture
def terms(seed):
    return {
        "group": seed["groups"][0]["name"],
        "nature": seed["natures"][0],
        "essentiality": seed["essentialities"][0],
    }


def group_id(conn, name):
    return conn.execute("SELECT id FROM category_groups WHERE name = ?", (name,)).fetchone()[0]


def snapshot(conn):
    return [
        tuple(row)
        for row in conn.execute(
            "SELECT id, rule_id, group_id, nature, essentiality FROM transactions ORDER BY id"
        )
    ]


def test_a_new_category_rule_reports_how_many_transactions_it_reclassified(base, terms):
    reclassified = create_rule(
        base,
        match_kind="category",
        match_value="Compras",
        group_id=group_id(base, terms["group"]),
        nature=terms["nature"],
        essentiality=terms["essentiality"],
    )
    assert reclassified == 2


def test_editing_and_removing_report_the_same_reach(base, terms, seed):
    create_rule(
        base,
        match_kind="category",
        match_value="Compras",
        group_id=group_id(base, terms["group"]),
        nature=terms["nature"],
        essentiality=terms["essentiality"],
    )
    rule_id = base.execute(
        "SELECT id FROM category_rules WHERE match_value = ?", ("Compras",)
    ).fetchone()[0]
    assert update_rule(base, rule_id, essentiality=seed["essentialities"][-1]) == 2
    assert delete_rule(base, rule_id) == 2
    assert base.execute("SELECT count(*) FROM category_rules").fetchone()[0] == 0


def test_a_group_outside_the_table_is_refused_by_name(base, terms, seed):
    with pytest.raises(InvalidTermError) as raised:
        create_rule(
            base,
            match_kind="category",
            match_value="Zzz",
            group_id=UNKNOWN_GROUP,
            nature=terms["nature"],
            essentiality=terms["essentiality"],
        )
    assert str(raised.value) == message("invalid_group", UNKNOWN_GROUP, seed)


def test_a_nature_outside_the_vocabulary_is_refused_by_name(base, terms, seed):
    with pytest.raises(InvalidTermError) as raised:
        create_rule(
            base,
            match_kind="category",
            match_value="Zzz",
            group_id=group_id(base, terms["group"]),
            nature="zzz",
            essentiality=terms["essentiality"],
        )
    assert str(raised.value) == message("invalid_nature", "zzz", seed)


def test_an_essentiality_outside_the_vocabulary_is_refused_by_name(base, terms, seed):
    with pytest.raises(InvalidTermError) as raised:
        create_rule(
            base,
            match_kind="category",
            match_value="Zzz",
            group_id=group_id(base, terms["group"]),
            nature=terms["nature"],
            essentiality="zzz",
        )
    assert str(raised.value) == message("invalid_essentiality", "zzz", seed)


def test_an_expression_that_does_not_compile_is_refused_by_value(base, terms, seed):
    with pytest.raises(InvalidExpressionError) as raised:
        create_rule(
            base,
            match_kind="description",
            match_value=BROKEN_EXPRESSION,
            group_id=group_id(base, terms["group"]),
            nature=terms["nature"],
            essentiality=terms["essentiality"],
        )
    assert str(raised.value) == message("invalid_expression", BROKEN_EXPRESSION, seed)


def test_a_refusal_leaves_no_rule_and_no_transaction_changed(base, terms):
    before = (base.execute("SELECT count(*) FROM category_rules").fetchone()[0], snapshot(base))
    for kwargs in (
        {"match_kind": "category", "match_value": "Zzz", "group_id": UNKNOWN_GROUP},
        {"match_kind": "description", "match_value": BROKEN_EXPRESSION},
    ):
        arguments = {
            "group_id": group_id(base, terms["group"]),
            "nature": terms["nature"],
            "essentiality": terms["essentiality"],
        }
        arguments.update(kwargs)
        with pytest.raises((InvalidTermError, InvalidExpressionError)):
            create_rule(base, **arguments)
    assert (
        base.execute("SELECT count(*) FROM category_rules").fetchone()[0],
        snapshot(base),
    ) == before


def test_an_expression_rule_matches_the_normalized_description(base, terms):
    reclassified = create_rule(
        base,
        match_kind="description",
        match_value="^loja",
        group_id=group_id(base, terms["group"]),
        nature=terms["nature"],
        essentiality=terms["essentiality"],
    )
    assert reclassified == 2


def test_a_rule_that_does_not_exist_is_refused_by_id(base, seed):
    with pytest.raises(UnknownRuleError) as raised:
        delete_rule(base, UNKNOWN_GROUP)
    assert str(raised.value) == message("unknown_rule", UNKNOWN_GROUP, seed)
    with pytest.raises(UnknownRuleError):
        update_rule(base, UNKNOWN_GROUP, nature=seed["natures"][0])
