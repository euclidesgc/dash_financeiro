from datetime import date

import pytest

from app.plan.whatif import (
    EXPENSE,
    INCOME,
    InvalidScenarioError,
    Move,
    facts,
    impact,
    parse_move,
    save,
    saved,
    signed_monthly,
)
from tests.test_plan import REFERENCE, prepare, rent, salary


def base(conn, income=9000.0, cost=-1000.0):
    return prepare(conn, salary(income) + rent(cost))


def move(kind, monthly):
    return Move(kind=kind, monthly_cents=monthly, once_cents=0, months=None)


def test_income_adds_and_expense_subtracts():
    assert signed_monthly(move(INCOME, 50000)) == 50000
    assert signed_monthly(move(EXPENSE, 50000)) == -50000


def test_an_income_brings_the_objective_closer(taxonomy_conn):
    conn = base(taxonomy_conn)
    found = impact(conn, move(INCOME, 200000), today=REFERENCE)

    assert found["days_delta"] is not None
    assert found["days_delta"] < 0


def test_an_expense_pushes_the_objective_away(taxonomy_conn):
    conn = base(taxonomy_conn)
    found = impact(conn, move(EXPENSE, 100000), today=REFERENCE)

    assert found["days_delta"] is not None
    assert found["days_delta"] > 0


def test_turning_never_into_a_date_is_not_a_number_of_days(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(1000.0) + rent(-3000.0))
    found = impact(conn, move(INCOME, 900000), today=REFERENCE)

    assert found["reachable_before"] is False
    assert found["reachable_after"] is True
    assert found["days_delta"] is None


def test_the_simulator_uses_the_same_engine_as_the_objective(taxonomy_conn):
    conn = base(taxonomy_conn)
    found = impact(conn, move(INCOME, 0), today=REFERENCE)

    assert found["before"]["months_to_objective"] == found["after"]["months_to_objective"]
    assert found["days_delta"] == 0


def test_a_value_that_is_not_a_number_is_refused_by_field_name():
    with pytest.raises(InvalidScenarioError) as refusal:
        parse_move(INCOME, "abc", "", "")

    assert "Valor mensal inválido" in str(refusal.value)


def test_an_unknown_kind_is_refused():
    with pytest.raises(InvalidScenarioError) as refusal:
        parse_move("outra-coisa", "10,00", "", "")

    assert "outra-coisa" in str(refusal.value)


def test_a_term_that_is_not_whole_is_refused():
    with pytest.raises(InvalidScenarioError):
        parse_move(INCOME, "10,00", "", "meio ano")


def test_a_scenario_without_a_name_is_refused(taxonomy_conn):
    with pytest.raises(InvalidScenarioError):
        save(taxonomy_conn, "  ", move(INCOME, 1000))


def test_a_saved_scenario_comes_back_and_the_same_name_is_replaced(taxonomy_conn):
    save(taxonomy_conn, "Vender o carro", move(INCOME, 123533))
    save(taxonomy_conn, "Vender o carro", move(INCOME, 200000))

    assert [(row["name"], row["monthly_cents"]) for row in saved(taxonomy_conn)] == [
        ("Vender o carro", 200000)
    ]


def test_a_fact_past_its_date_is_marked_stale(taxonomy_conn):
    taxonomy_conn.execute(
        "INSERT INTO plan_facts (name, label, value_cents, unit, source, captured_at, valid_until) "
        "VALUES ('q', 'Quitação', 100, 'centavos', 'humano', '2026-01-01', '2026-08-01'), "
        "('t', 'Transporte', 200, 'centavos', 'humano', '2026-01-01', NULL)"
    )
    taxonomy_conn.commit()
    found = {row["name"]: row["stale"] for row in facts(taxonomy_conn, today=date(2026, 9, 5))}

    assert found == {"q": True, "t": False}


def test_a_value_with_a_dot_as_decimal_is_refused_and_not_read_as_thousands():
    with pytest.raises(InvalidScenarioError) as refusal:
        parse_move(INCOME, "5000.00", "", "")

    assert "1.234,56" in str(refusal.value)


def test_the_brazilian_forms_are_read_and_only_those():
    assert parse_move(INCOME, "5.000,00", "", "").monthly_cents == 500000
    assert parse_move(INCOME, "5000,00", "", "").monthly_cents == 500000
    assert parse_move(INCOME, "5000", "", "").monthly_cents == 500000
    for bad in ("inf", "nan", "Infinity", "1e3", "1_000", "5,001"):
        with pytest.raises(InvalidScenarioError):
            parse_move(INCOME, bad, "", "")


def test_a_value_that_rounds_to_zero_is_refused():
    with pytest.raises(InvalidScenarioError):
        parse_move(INCOME, "0,00", "", "")


def test_a_validity_that_is_not_a_date_is_refused():
    from app.plan.whatif import parse_validity

    assert parse_validity("") is None
    assert parse_validity("2026-08-01") == "2026-08-01"
    for bad in ("banana", "9999-99-99", "01/08/2026"):
        with pytest.raises(InvalidScenarioError):
            parse_validity(bad)


def test_a_term_stops_the_effect_and_a_one_off_lands_once(taxonomy_conn):
    conn = base(taxonomy_conn)
    forever = impact(conn, move(INCOME, 200000), today=REFERENCE)
    for_two = impact(
        conn, Move(kind=INCOME, monthly_cents=200000, once_cents=0, months=2), today=REFERENCE
    )
    with_once = impact(
        conn,
        Move(kind=INCOME, monthly_cents=200000, once_cents=5000000, months=None),
        today=REFERENCE,
    )

    assert for_two["after"]["months_to_objective"] > forever["after"]["months_to_objective"]
    assert with_once["after"]["months_to_objective"] < forever["after"]["months_to_objective"]
