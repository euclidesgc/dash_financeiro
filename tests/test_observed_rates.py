from datetime import date

from app.debts.observed import MIN_BALANCE_CENTS, MIN_MONTHS, daily_balances, observed_rates
from tests.conftest import ACCOUNT, load, transaction

REFERENCE = date(2026, 9, 5)


def account(conn, balance):
    conn.execute("UPDATE accounts SET balance_cents = ?", (balance,))
    conn.commit()
    return conn


def month(prefix, when, spend, interest=None):
    rows = [transaction(f"{prefix}-{when}", f"{when}-01", spend, descricao="Compra")]
    if interest is not None:
        rows.append(
            transaction(f"{prefix}-j-{when}", f"{when}-28", interest, descricao="Saída JUROS LIMITE DA CONTA")
        )
    return rows


def test_the_balance_is_walked_backwards_from_the_reported_one(taxonomy_conn):
    conn = account(load(taxonomy_conn, month("a", "2026-08", -100.0)), -10000)
    days = daily_balances(conn, ACCOUNT["id"], -10000, REFERENCE)

    assert days["2026-09-05"] == -10000
    assert days["2026-08-01"] == -10000
    # The walk stops at the first movement: before it there is no history to
    # reconstruct, and inventing a zero there would invent days in the black.
    assert "2026-07-31" not in days
    assert min(days) == "2026-08-01"


def test_a_month_with_no_interest_charged_is_not_a_rate(taxonomy_conn):
    rows = []
    for when in ("2026-05", "2026-06", "2026-07"):
        rows += month("a", when, -1000.0)
    conn = account(load(taxonomy_conn, rows), -300000)

    assert observed_rates(conn, today=REFERENCE) == {}


def test_a_balance_too_small_is_a_minimum_fee_and_not_a_rate(taxonomy_conn):
    rows = []
    for when in ("2026-05", "2026-06", "2026-07", "2026-08"):
        rows += month("a", when, -1.0, interest=-0.30)
    conn = account(load(taxonomy_conn, rows), -400)

    assert abs(-400) < MIN_BALANCE_CENTS
    assert observed_rates(conn, today=REFERENCE) == {}


def test_fewer_months_than_the_floor_do_not_produce_a_suggestion(taxonomy_conn):
    rows = month("a", "2026-08", -5000.0, interest=-100.0)
    conn = account(load(taxonomy_conn, rows), -500000)

    assert MIN_MONTHS > 1
    assert observed_rates(conn, today=REFERENCE) == {}


def test_the_suggestion_is_the_median_and_the_range_is_shown(taxonomy_conn):
    rows = []
    for when, interest in (("2026-05", -50.0), ("2026-06", -100.0), ("2026-07", -150.0)):
        rows += month("a", when, -0.01, interest=interest)
    conn = account(load(taxonomy_conn, rows), -1000000)
    found = observed_rates(conn, today=REFERENCE)[ACCOUNT["id"]]

    assert found["months"] == 3
    assert found["lowest_bp"] < found["median_bp"] < found["highest_bp"]


def test_a_late_payment_fine_is_not_the_price_of_carrying_a_balance(taxonomy_conn):
    rows = []
    for when in ("2026-05", "2026-06", "2026-07"):
        rows += [
            transaction(f"m-{when}", f"{when}-01", -1000.0, descricao="Compra"),
            transaction(f"j-{when}", f"{when}-28", -50.0, descricao="JUROS DE MORA"),
        ]
    conn = account(load(taxonomy_conn, rows), -300000)

    assert observed_rates(conn, today=REFERENCE) == {}
