import pytest

from app.queries.reach import category_reach, holders, payee_reach, rule_reach
from app.taxonomy.classify import classify_all
from app.taxonomy.rules import create_rule, expression_for
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, rule, transaction

CATEGORY = "Categoria da fonte"
FINANCEIRO = "Financeiro"
PESSOAL = "Pessoal"


def group_id(conn, name):
    return conn.execute("SELECT id FROM category_groups WHERE name = ?", (name,)).fetchone()[0]


@pytest.fixture
def three_payments():
    return [
        transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria=CATEGORY),
        transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria=CATEGORY),
        transaction(
            "t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria=CATEGORY
        ),
    ]


@pytest.fixture
def base(taxonomy_conn, seed, three_payments):
    conn = load(taxonomy_conn, three_payments)
    seed_taxonomy(conn, narrowed(seed, []))
    classify_all(conn)
    conn.commit()
    return conn


def test_payee_reach_matches_exactly_and_category_reach_sums_every_source_of_the_category(base):
    exact = payee_reach(base, "mercado livre")
    sibling = payee_reach(base, "mercado livre pago")
    category = category_reach(base, CATEGORY)

    assert (exact["entries"], exact["amount_cents"]) == (2, -15000)
    assert (sibling["entries"], sibling["amount_cents"]) == (1, -2500)
    assert (category["entries"], category["amount_cents"]) == (3, -17500)


def test_a_transfer_and_a_refund_of_the_same_payee_never_enter_either_reach(
    taxonomy_conn, seed, three_payments
):
    rows = [
        *three_payments,
        transaction(
            "t-ml-transfer",
            "2026-09-05",
            -40.00,
            descricao="Mercado Livre",
            categoria=CATEGORY,
            eh_transferencia=True,
        ),
        transaction(
            "t-ml-refund",
            "2026-09-06",
            15.00,
            descricao="Mercado Livre",
            categoria=CATEGORY,
            eh_estorno=True,
            estornada_por="t-ml-debit",
        ),
        transaction(
            "t-ml-debit",
            "2026-09-06",
            -15.00,
            descricao="Mercado Livre",
            categoria=CATEGORY,
            estornada_por="t-ml-refund",
        ),
    ]
    conn = load(taxonomy_conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify_all(conn)
    conn.commit()

    exact = payee_reach(conn, "mercado livre")
    category = category_reach(conn, CATEGORY)

    assert (exact["entries"], exact["amount_cents"]) == (2, -15000)
    assert (category["entries"], category["amount_cents"]) == (3, -17500)


def test_rule_reach_counts_only_the_transactions_the_written_rule_actually_holds(base):
    reclassified = create_rule(
        base,
        match_kind="description",
        match_value=expression_for("mercado livre"),
        group_id=group_id(base, PESSOAL),
        nature="variável",
        essentiality="supérfluo",
    )
    assert reclassified == 2
    rule_id = base.execute(
        "SELECT id FROM category_rules WHERE match_value = ?", (expression_for("mercado livre"),)
    ).fetchone()[0]

    reach = rule_reach(base, rule_id)

    assert (reach["entries"], reach["amount_cents"]) == (2, -15000)


def test_holders_is_empty_when_no_other_rule_holds_the_payee(base):
    create_rule(
        base,
        match_kind="description",
        match_value=expression_for("mercado livre"),
        group_id=group_id(base, PESSOAL),
        nature="variável",
        essentiality="supérfluo",
    )
    rule_id = base.execute(
        "SELECT id FROM category_rules WHERE match_value = ?", (expression_for("mercado livre"),)
    ).fetchone()[0]

    assert holders(base, payee="mercado livre", rule_id=rule_id) == []


def test_holders_names_the_competing_rule_of_lower_id(taxonomy_conn, seed, three_payments):
    conn = load(taxonomy_conn, three_payments)
    seed_taxonomy(
        conn, narrowed(seed, [rule("description", "^mercado", FINANCEIRO, "fixa", "essencial")])
    )
    classify_all(conn)
    conn.commit()
    lower_id = conn.execute(
        "SELECT id FROM category_rules WHERE match_value = '^mercado'"
    ).fetchone()[0]

    create_rule(
        conn,
        match_kind="description",
        match_value=expression_for("mercado livre"),
        group_id=group_id(conn, PESSOAL),
        nature="variável",
        essentiality="supérfluo",
    )
    higher_id = conn.execute(
        "SELECT id FROM category_rules WHERE match_value = ?", (expression_for("mercado livre"),)
    ).fetchone()[0]

    found = holders(conn, payee="mercado livre", rule_id=higher_id)

    assert [(row["id"], row["match_value"]) for row in found] == [(lower_id, "^mercado")]


def test_payee_reach_and_holders_leave_manual_rows_out(taxonomy_conn, seed, three_payments):
    conn = load(taxonomy_conn, three_payments)
    seed_taxonomy(
        conn, narrowed(seed, [rule("description", "^mercado", FINANCEIRO, "fixa", "essencial")])
    )
    classify_all(conn)
    conn.execute(
        "UPDATE transactions SET category = NULL, category_source = 'manual' "
        "WHERE pluggy_id IN ('t-ml-1', 't-ml-2')"
    )
    classify_all(conn)
    conn.commit()

    exact = payee_reach(conn, "mercado livre")
    found = holders(conn, payee="mercado livre", rule_id=0)

    assert (exact["entries"], exact["amount_cents"]) == (0, 0)
    assert found == []
