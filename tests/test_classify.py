import pytest

from app.taxonomy.classify import MissingFallbackError, classify_all, residue
from app.taxonomy.rules import update_rule
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, rule, transaction

SHOP = "Loja do Bairro 12/03/2026"
CLINIC = "Clinica Central"


@pytest.fixture
def vocabulary(seed):
    groups = [group["name"] for group in seed["groups"]]
    return {
        "housing": groups[0],
        "health": groups[5],
        "fallback": next(group["name"] for group in seed["groups"] if group["is_fallback"]),
        "natures": seed["natures"],
        "essentialities": seed["essentialities"],
        "fallback_nature": seed["fallback_nature"],
        "fallback_essentiality": seed["fallback_essentiality"],
    }


@pytest.fixture
def rows():
    return [
        transaction("t-shop", "2026-03-02", -10.00, descricao=SHOP, categoria="Compras"),
        transaction("t-clinic", "2026-03-03", -20.00, descricao=CLINIC, categoria="Saude"),
        transaction("t-orphan", "2026-03-04", -30.00, descricao="Sem regra", categoria="Nada"),
        transaction("t-income", "2026-03-05", 40.00, descricao="Salario", categoria="Nada"),
        transaction(
            "t-internal",
            "2026-03-06",
            -50.00,
            descricao="Entre contas",
            categoria="Nada",
            eh_transferencia=True,
        ),
        transaction("t-outside", "2026-01-07", -60.00, descricao="Fora", categoria="Nada"),
    ]


def classified(conn, seed, vocabulary, rules):
    seed_taxonomy(conn, narrowed(seed, rules))
    classify_all(conn)
    conn.commit()
    return conn


def state(conn, pluggy_id):
    return conn.execute(
        "SELECT t.payee, g.name AS group_name, t.nature, t.essentiality, r.match_value "
        "FROM transactions t JOIN category_groups g ON g.id = t.group_id "
        "LEFT JOIN category_rules r ON r.id = t.rule_id WHERE t.pluggy_id = ?",
        (pluggy_id,),
    ).fetchone()


def test_the_payee_is_the_normalized_description(taxonomy_conn, seed, vocabulary, rows):
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, [])
    assert state(conn, "t-shop")["payee"] == "loja do bairro"


def test_a_transaction_no_rule_reaches_falls_into_the_declared_fallback(
    taxonomy_conn, seed, vocabulary, rows
):
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, [])
    row = state(conn, "t-orphan")
    assert row["group_name"] == vocabulary["fallback"]
    assert row["nature"] == vocabulary["fallback_nature"]
    assert row["essentiality"] == vocabulary["fallback_essentiality"]
    assert row["match_value"] is None


def test_a_category_rule_classifies_every_transaction_of_that_category(
    taxonomy_conn, seed, vocabulary, rows
):
    rules = [
        rule(
            "category",
            "Compras",
            vocabulary["housing"],
            vocabulary["natures"][0],
            vocabulary["essentialities"][0],
        )
    ]
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, rules)
    row = state(conn, "t-shop")
    assert row["group_name"] == vocabulary["housing"]
    assert row["nature"] == vocabulary["natures"][0]
    assert row["essentiality"] == vocabulary["essentialities"][0]
    assert row["match_value"] == "Compras"


def test_an_expression_rule_beats_the_category_rule_it_overlaps(
    taxonomy_conn, seed, vocabulary, rows
):
    rules = [
        rule(
            "description",
            "loja",
            vocabulary["health"],
            vocabulary["natures"][1],
            vocabulary["essentialities"][1],
        ),
        rule(
            "category",
            "Compras",
            vocabulary["housing"],
            vocabulary["natures"][0],
            vocabulary["essentialities"][0],
        ),
    ]
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, rules)
    row = state(conn, "t-shop")
    assert row["match_value"] == "loja"
    assert row["group_name"] == vocabulary["health"]


def test_the_lower_id_wins_between_two_rules_of_the_same_kind(
    taxonomy_conn, seed, vocabulary, rows
):
    rules = [
        rule(
            "description",
            "loja",
            vocabulary["health"],
            vocabulary["natures"][1],
            vocabulary["essentialities"][1],
        ),
        rule(
            "description",
            "bairro",
            vocabulary["housing"],
            vocabulary["natures"][0],
            vocabulary["essentialities"][0],
        ),
    ]
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, rules)
    assert state(conn, "t-shop")["match_value"] == "loja"


def test_reclassifying_the_same_base_changes_nothing(taxonomy_conn, seed, vocabulary, rows):
    rules = [
        rule(
            "category",
            "Compras",
            vocabulary["housing"],
            vocabulary["natures"][0],
            vocabulary["essentialities"][0],
        )
    ]
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, rules)
    before = conn.execute(
        "SELECT id, rule_id, group_id, nature, essentiality FROM transactions ORDER BY id"
    ).fetchall()
    assert classify_all(conn) == 0
    after = conn.execute(
        "SELECT id, rule_id, group_id, nature, essentiality FROM transactions ORDER BY id"
    ).fetchall()
    assert [tuple(row) for row in after] == [tuple(row) for row in before]


def test_the_observed_categories_are_recorded(taxonomy_conn, seed, vocabulary, rows):
    # `seed_taxonomy` also seeds the known tree (77 categories), so a category
    # the data observes is asserted as present, not as the whole table.
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, [])
    names = {row[0] for row in conn.execute("SELECT name FROM categories")}
    assert {"Compras", "Saude", "Nada"} <= names


def test_the_residue_counts_only_spending_without_a_rule_inside_the_window(
    taxonomy_conn, seed, vocabulary, rows
):
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, [])
    line = residue(conn, start="2026-03-01", end="2026-03-31")
    assert (line["entries"], line["amount_cents"]) == (3, -6000)


def test_a_rule_that_covers_the_residue_empties_it(taxonomy_conn, seed, vocabulary, rows):
    rules = [
        rule(
            "category",
            "Nada",
            vocabulary["housing"],
            vocabulary["natures"][0],
            vocabulary["essentialities"][0],
        ),
        rule(
            "category",
            "Compras",
            vocabulary["housing"],
            vocabulary["natures"][0],
            vocabulary["essentialities"][0],
        ),
        rule(
            "category",
            "Saude",
            vocabulary["health"],
            vocabulary["natures"][1],
            vocabulary["essentialities"][1],
        ),
    ]
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, rules)
    line = residue(conn, start="2026-03-01", end="2026-03-31")
    assert (line["entries"], line["amount_cents"]) == (0, 0)


def test_editing_a_rule_moves_its_transactions_without_reingestion(
    taxonomy_conn, seed, vocabulary, rows
):
    rules = [
        rule(
            "category",
            "Compras",
            vocabulary["housing"],
            vocabulary["natures"][0],
            vocabulary["essentialities"][0],
        )
    ]
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, rules)
    rule_id = conn.execute(
        "SELECT id FROM category_rules WHERE match_value = ?", ("Compras",)
    ).fetchone()[0]
    moved = update_rule(conn, rule_id, essentiality=vocabulary["essentialities"][-1])
    assert moved == 1
    assert state(conn, "t-shop")["essentiality"] == vocabulary["essentialities"][-1]


def test_classifying_before_the_seed_says_which_vocabulary_is_missing(taxonomy_conn, rows):
    conn = load(taxonomy_conn, rows)
    with pytest.raises(MissingFallbackError) as raised:
        classify_all(conn)
    assert raised.value.table == "category_groups"


def test_removing_a_rule_row_drops_its_transactions_into_the_residue(
    taxonomy_conn, seed, vocabulary, rows
):
    rules = [
        rule(
            "category",
            "Compras",
            vocabulary["housing"],
            vocabulary["natures"][0],
            vocabulary["essentialities"][0],
        )
    ]
    conn = classified(load(taxonomy_conn, rows), seed, vocabulary, rules)
    conn.execute("DELETE FROM category_rules WHERE match_value = ?", ("Compras",))
    assert classify_all(conn) == 1
    row = state(conn, "t-shop")
    assert row["match_value"] is None
    assert row["group_name"] == vocabulary["fallback"]
