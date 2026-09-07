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
            transaction(
                f"{prefix}-j-{when}",
                f"{when}-28",
                interest,
                descricao="Saída JUROS LIMITE DA CONTA",
            )
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


def charges(conn, day):
    from app.debts.observed import _charged_for, posts_in_arrears

    arrears = posts_in_arrears(conn, ACCOUNT["id"])
    return arrears, {
        month: _charged_for(conn, ACCOUNT["id"], month, arrears)
        for month in ("2026-05", "2026-06", "2026-07")
    }


def posted_on(day):
    return [
        transaction("c", "2026-06-01", -1000.0, descricao="Compra"),
        transaction("j", f"2026-07-{day}", -60.0, descricao="COBRANCA DE JUROS"),
    ]


def test_an_account_that_posts_early_is_charging_in_arrears(taxonomy_conn):
    conn = account(load(taxonomy_conn, posted_on("02")), -100000)
    arrears, found = charges(conn, "02")

    assert arrears is True
    assert found["2026-06"] == -6000
    assert found["2026-07"] == 0


def test_the_boundary_is_the_account_posting_day_and_not_a_fixed_cut(taxonomy_conn):
    # The day the real base posts on, and the day a fixed cut of five missed.
    conn = account(load(taxonomy_conn, posted_on("06")), -100000)
    arrears, found = charges(conn, "06")

    assert arrears is True
    assert found["2026-06"] == -6000


def test_an_account_that_posts_late_is_not_charging_in_arrears(taxonomy_conn):
    rows = [
        transaction("c", "2026-06-01", -1000.0, descricao="Compra"),
        transaction("j", "2026-06-28", -60.0, descricao="Saída JUROS LIMITE DA CONTA"),
    ]
    conn = account(load(taxonomy_conn, rows), -100000)
    arrears, found = charges(conn, "28")

    assert arrears is False
    assert found["2026-06"] == -6000
    assert found["2026-05"] == 0


def test_the_median_of_an_even_count_is_rounded_and_not_truncated():
    from app.debts.observed import _median

    assert _median([1, 2]) == 2  # 1,5 arredonda para 2
    assert _median([1, 2, 3, 4]) == 2  # 2,5 arredonda para o par, como o Python faz
    assert _median([100, 300]) == 200


def test_the_month_in_progress_is_left_out(taxonomy_conn):
    from app.debts.observed import _monthly_rates, daily_balances

    rows = []
    for when in ("2026-06", "2026-07", "2026-08", "2026-09"):
        rows += month("a", when, -1000.0, interest=-80.0)
    conn = account(load(taxonomy_conn, rows), -400000)
    days = daily_balances(conn, ACCOUNT["id"], -400000, REFERENCE)
    months = [when for when, _ in _monthly_rates(conn, ACCOUNT["id"], days, REFERENCE)]

    assert "2026-09" not in months
    assert months


def test_a_truncated_oldest_month_is_measured_against_the_calendar(taxonomy_conn):
    from app.debts.observed import _monthly_rates, daily_balances

    # The walk starts here, so June holds 26 reconstructed days, not 30.
    rows = [transaction("c", "2026-06-05", -3000.0, descricao="Compra")]
    rows += [
        transaction(f"p-{day}", f"2026-06-{day}", 3000.0, descricao="Deposito") for day in ("20",)
    ]
    rows += [transaction("j", "2026-07-02", -100.0, descricao="COBRANCA DE JUROS")]
    for when in ("2026-07", "2026-08"):
        rows += month("b", when, -3000.0, interest=-100.0)
    conn = account(load(taxonomy_conn, rows), -300000)
    days = daily_balances(conn, ACCOUNT["id"], -300000, REFERENCE)
    months = [when for when, _ in _monthly_rates(conn, ACCOUNT["id"], days, REFERENCE)]

    # 15 negative days of 30 in the calendar is under half, even though it is
    # over half of the 26 days the reconstruction holds.
    assert "2026-06" not in months


def test_a_month_whose_interest_nets_positive_is_not_a_month_the_bank_charged(taxonomy_conn):
    from app.debts.observed import _charged_for

    rows = [
        transaction("c", "2026-06-01", -1000.0, descricao="Compra"),
        transaction("j", "2026-06-28", -200.0, descricao="Saída JUROS LIMITE DA CONTA"),
        transaction("e", "2026-06-29", 500.0, descricao="CREDITO JUROS"),
    ]
    conn = account(load(taxonomy_conn, rows), -100000)

    assert _charged_for(conn, ACCOUNT["id"], "2026-06", arrears=False) == 0
