from app.advisor.context import as_text, lines, snapshot
from app.offers.cost import compare
from tests.test_plan import REFERENCE, prepare, rent, salary

STEP = {"name": "Conta corrente", "monthly_rate_bp": 2000}
OFFER = {
    "name": "Banco Teste",
    "monthly_rate_bp": 1000,
    "term_months": 2,
    "released_cents": 100000,
    "fee_cents": 5000,
}
WITHOUT_RATE = {
    "name": "Banco Sem Taxa",
    "monthly_rate_bp": None,
    "term_months": 24,
    "released_cents": 100000,
    "fee_cents": 0,
}


def test_the_row_names_the_cheaper_path_against_the_current_step():
    found = compare(STEP, [OFFER])

    row = found["rows"][0]
    assert row["stay_cents"] == 30910
    assert row["offer_cents"] == 20238
    assert row["difference_cents"] == 10672
    assert row["cheaper"] is True
    assert found["without_rate"] == []


def test_an_offer_without_a_rate_is_excluded_from_rows_and_named_apart():
    found = compare(STEP, [OFFER, WITHOUT_RATE])

    assert [row["name"] for row in found["rows"]] == ["Banco Teste"]
    assert found["without_rate"] == ["Banco Sem Taxa"]


def test_a_null_step_leaves_the_staying_cost_and_the_difference_null():
    found = compare(None, [OFFER])

    row = found["rows"][0]
    assert row["offer_cents"] == 20238
    assert row["stay_cents"] is None
    assert row["difference_cents"] is None
    assert row["cheaper"] is None


def test_a_step_that_is_not_the_cheapest_path_is_named_the_cheaper_one():
    expensive_offer = {**OFFER, "monthly_rate_bp": 3000}
    found = compare(STEP, [expensive_offer])

    row = found["rows"][0]
    assert row["cheaper"] is False


def test_the_comparison_reaches_lines_and_as_text_by_membership(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    conn.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source) "
        "VALUES ('overdraft', 'Conta corrente', -500000, 2000, 'accounts')"
    )
    conn.execute(
        "INSERT INTO offers "
        "(name, monthly_rate_bp, term_months, released_cents, fee_cents, captured_at) "
        "VALUES ('Banco Teste', 1000, 2, 100000, 5000, '2026-09-01')"
    )
    conn.commit()

    numbers = snapshot(conn, today=REFERENCE)
    shown = lines(numbers)
    text = as_text(numbers)

    named = [line for line in shown if line["label"].startswith("Banco Teste")]
    assert len(named) == 3
    assert {line["value"] for line in named} == {"R$ 309,10", "R$ 202,38", "R$ 106,72"}
    for line in named:
        assert f"{line['label']}: {line['value']}." in text
