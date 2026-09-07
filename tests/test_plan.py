from datetime import date

from app.commitments import engine
from app.debts.ladder import rebuild
from app.plan.objective import RESERVE_MONTHS, reserve_target_cents, survival_floor_cents
from app.plan.timeline import (
    BASE,
    CONSERVATIVE,
    OPTIMISTIC,
    every_scenario,
    expensive_debts,
    history,
    record,
    simulate,
)
from app.taxonomy import classify
from app.taxonomy.seed import load_seed, seed_taxonomy
from tests.conftest import load, transaction

REFERENCE = date(2026, 9, 5)
MONTHS = ("2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08")


def prepare(conn, rows):
    load(conn, rows)
    seed_taxonomy(conn, load_seed())
    classify.classify_all(conn)
    conn.commit()
    engine.recompute(conn, today=REFERENCE)
    rebuild(conn, today=REFERENCE)
    return conn


def salary(value):
    return [
        transaction(f"in-{month}", f"{month}-05", value, descricao="Salario", categoria="Salary")
        for month in MONTHS
    ]


def rent(value):
    return [
        transaction(f"out-{month}", f"{month}-10", value, descricao="Moradia", categoria="Housing")
        for month in MONTHS
    ]


def test_the_reserve_is_six_months_of_the_survival_floor(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    floor = survival_floor_cents(conn, today=REFERENCE)

    assert floor > 0
    assert reserve_target_cents(conn, today=REFERENCE) == floor * RESERVE_MONTHS


def test_a_month_that_ends_in_the_red_never_reaches_the_objective(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(1000.0) + rent(-3000.0))
    found = simulate(conn, CONSERVATIVE, today=REFERENCE)

    assert found["monthly_result_cents"] < 0
    assert found["months_to_objective"] is None
    assert found["milestones"] == {"resultado": None, "dividas": None, "reserva": None}
    assert found["missing_cents"] == -found["monthly_result_cents"]


def test_a_month_in_the_black_reaches_the_objective_and_says_when(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(9000.0) + rent(-1000.0))
    found = simulate(conn, CONSERVATIVE, today=REFERENCE)

    assert found["monthly_result_cents"] > 0
    assert found["milestones"]["resultado"] == 0
    assert found["months_to_objective"] is not None
    assert found["missing_cents"] == 0


def test_the_mortgage_never_enters_the_expensive_ladder(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    conn.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source) "
        "VALUES ('mortgage', 'Imovel', -20000000, 200, 'teste'), "
        "('card', 'Cartao', -500000, 900, 'teste')"
    )
    conn.commit()

    kinds = [row["kind"] for row in expensive_debts(conn)]

    assert "card" in kinds
    assert "mortgage" not in kinds


def test_the_three_scenarios_never_get_worse_from_left_to_right(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    runs = {run["scenario"]: run["monthly_result_cents"] for run in every_scenario(conn, today=REFERENCE)}

    assert runs[CONSERVATIVE] <= runs[BASE] <= runs[OPTIMISTIC]


def test_every_reading_writes_a_point_and_the_same_day_writes_only_one(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    runs = every_scenario(conn, today=REFERENCE)
    record(conn, runs, today=REFERENCE)
    record(conn, runs, today=REFERENCE)
    record(conn, runs, today=date(2026, 10, 5))

    assert [point["reference_date"] for point in history(conn)] == ["2026-09-05", "2026-10-05"]


def test_a_ladder_already_clear_was_cleared_in_month_zero(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(9000.0) + rent(-1000.0))
    conn.execute("DELETE FROM debts")
    conn.commit()
    found = simulate(conn, CONSERVATIVE, today=REFERENCE)

    assert found["milestones"]["dividas"] == 0


def test_a_month_that_goes_entirely_to_the_debt_does_not_feed_the_reserve(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(9000.0) + rent(-1000.0))
    conn.execute("DELETE FROM debts")
    conn.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source) "
        "VALUES ('card', 'Cartao', ?, 900, 'teste')",
        (-simulate(conn, CONSERVATIVE, today=REFERENCE)["monthly_result_cents"] * 100 // 109,),
    )
    conn.commit()
    found = simulate(conn, CONSERVATIVE, today=REFERENCE)

    assert found["milestones"]["dividas"] == 1
    assert found["milestones"]["reserva"] != 1


def test_the_freed_cash_arrives_when_the_instalment_ends_and_can_create_a_date(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-5100.0))
    conn.execute("DELETE FROM debts")
    conn.execute(
        "INSERT INTO commitments (kind, series_key, description, amount_cents, "
        "last_seen_date, installment_total, installments_left, ends_month, due_day) "
        "VALUES ('installment', 'loja', 'Loja', -50000, '2026-09-01', 6, 2, '2026-12', 10)"
    )
    conn.commit()
    conservative = simulate(conn, CONSERVATIVE, today=REFERENCE)
    optimistic = simulate(conn, OPTIMISTIC, today=REFERENCE)

    assert conservative["monthly_result_cents"] < optimistic["monthly_result_cents"]
    assert conservative["months_to_objective"] is None
    assert optimistic["milestones"]["resultado"] == 3


def test_an_instalment_ending_this_month_is_already_in_the_path(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-5000.0))
    conn.execute("DELETE FROM debts")
    conn.execute(
        "INSERT INTO commitments (kind, series_key, description, amount_cents, "
        "last_seen_date, installment_total, installments_left, ends_month, due_day) "
        "VALUES ('installment', 'loja', 'Loja', -50000, '2026-09-01', 6, 1, '2026-09', 10)"
    )
    conn.commit()
    found = simulate(conn, OPTIMISTIC, today=REFERENCE)

    assert found["monthly_result_cents"] == 50000
    assert found["milestones"]["resultado"] == 0
    assert found["months_to_objective"] is not None
