from datetime import date

import pytest

from app.projection.schedule import (
    CARD_INSTALLMENT,
    FINANCING,
    RECURRING_FIXED,
    schedule_by_month,
)

TODAY = date(2026, 9, 26)

_COMMITMENT = (
    "INSERT INTO commitments (kind, series_key, description, account, amount_cents, "
    "last_seen_date, last_installment, installment_total, installments_left, ends_month, "
    "dismissed) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_FINANCING = (
    "INSERT INTO financings (kind, monthly_rate_bp, term_months, balance_cents, payment_cents, "
    "first_due_date) VALUES (?, ?, ?, ?, ?, ?)"
)


def installment(conn, key, amount, seen, last, total, *, left=None, ends=None):
    conn.execute(
        _COMMITMENT,
        ("installment", key, key.upper(), "Cartão", amount, seen, last, total, left, ends, 0),
    )


def recurring(conn, key, amount, seen, *, dismissed=0):
    conn.execute(
        _COMMITMENT,
        ("recurring", key, key.upper(), "Conta", amount, seen, None, 0, None, None, dismissed),
    )


@pytest.fixture
def conn(taxonomy_conn):
    return taxonomy_conn


def test_no_data_projects_zero_months_with_the_asked_window(conn):
    schedule = schedule_by_month(conn, today=TODAY, months=3)

    assert [row.month for row in schedule.months] == ["2026-10", "2026-11", "2026-12"]
    assert all(row.total_cents == 0 and row.ending == [] for row in schedule.months)
    assert schedule.lines == []
    assert schedule.unprojected == []
    assert schedule.total_cents == 0


def test_an_installment_ending_mid_window_counts_only_until_its_last_month(conn):
    installment(conn, "loja", -10000, "2026-09-11", 3, 5, left=2, ends="2026-11")
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY, months=4)

    totals = {row.month: row.by_source[CARD_INSTALLMENT] for row in schedule.months}
    assert totals == {"2026-10": -10000, "2026-11": -10000, "2026-12": 0, "2027-01": 0}
    assert schedule.months[1].ending == ["LOJA"]
    [line] = schedule.lines
    assert (line.first_installment, line.last_installment, line.installment_total) == (4, 5, 5)
    assert (line.first_month, line.last_month, line.end_month) == ("2026-10", "2026-11", "2026-11")
    assert line.window_total_cents == -20000
    assert schedule.total_cents == -20000


def test_an_invoice_that_already_posted_future_installments_is_numbered_back(conn):
    installment(conn, "otica", -55800, "2027-02-10", 10, 10, left=0, ends="2027-02")
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY, months=6)

    [line] = schedule.lines
    assert (line.first_installment, line.last_installment) == (6, 10)
    assert line.months_in_window == 5
    assert [row.by_source[CARD_INSTALLMENT] for row in schedule.months] == [-55800] * 5 + [0]
    assert schedule.months[4].ending == ["OTICA"]


def test_a_finished_or_stale_installment_leaves_nothing_in_the_window(conn):
    installment(conn, "acabou", -5000, "2026-09-06", 4, 4, left=0, ends="2026-09")
    installment(conn, "antiga", -7000, "2026-03-06", 1, 12, left=11, ends="2027-02")
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY)

    assert schedule.lines == []
    assert schedule.total_cents == 0


def test_an_installment_without_number_is_reported_instead_of_guessed(conn):
    installment(conn, "sem numero", -3000, "2026-09-06", None, 6)
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY)

    assert schedule.lines == []
    [item] = schedule.unprojected
    assert (item.source, item.description) == (CARD_INSTALLMENT, "SEM NUMERO")


def test_a_financing_projects_from_its_contract_and_stops_at_the_last_payment(conn):
    conn.execute(_FINANCING, ("vehicle", 163, 3, None, -123533, "2026-10-11"))
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY, months=4)

    [line] = schedule.lines
    assert line.source == FINANCING
    assert line.description == "CDC do veículo"
    assert (line.first_installment, line.last_installment, line.installment_total) == (1, 3, 3)
    assert line.end_month == "2026-12"
    assert [row.by_source[FINANCING] for row in schedule.months] == [-123533] * 3 + [0]


def test_a_financing_without_payment_is_reported_not_derived(conn):
    conn.execute(_FINANCING, ("mortgage", 72, 370, -23858518, None, None))
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY)

    assert schedule.lines == []
    [item] = schedule.unprojected
    assert (item.source, item.description) == (FINANCING, "Financiamento imobiliário")


def test_the_bill_that_pays_a_financing_is_counted_once_as_the_financing(conn):
    conn.execute(_FINANCING, ("vehicle", 163, 60, None, -123533, "2025-06-11"))
    recurring(conn, "safra", -125298, "2026-09-11")
    recurring(conn, "luz", -18317, "2026-09-24")
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY, months=2)

    by_source = schedule.months[0].by_source
    assert by_source == {CARD_INSTALLMENT: 0, FINANCING: -123533, RECURRING_FIXED: -18317}
    financing = next(line for line in schedule.lines if line.source == FINANCING)
    assert financing.replaces == "SAFRA"
    assert (financing.first_installment, financing.installment_total) == (17, 60)
    assert financing.end_month == "2030-05"


def test_recurring_counts_every_month_only_while_live_and_not_dismissed(conn):
    recurring(conn, "viva", -9699, "2026-09-03")
    recurring(conn, "parada", -2990, "2026-07-27")
    recurring(conn, "cancelada", -10900, "2026-09-03", dismissed=1)
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY, months=3)

    assert [row.total_cents for row in schedule.months] == [-9699] * 3
    [line] = schedule.lines
    assert line.end_month is None and line.months_in_window == 3


def test_months_total_is_the_sum_of_the_sources(conn):
    installment(conn, "loja", -10000, "2026-09-11", 3, 5, left=2, ends="2026-11")
    conn.execute(_FINANCING, ("vehicle", 163, 60, None, -123533, "2025-06-11"))
    recurring(conn, "luz", -18317, "2026-09-24")
    conn.commit()

    schedule = schedule_by_month(conn, today=TODAY, months=3)

    assert [row.total_cents for row in schedule.months] == [-151850, -151850, -141850]
    assert schedule.total_cents == -445550


@pytest.mark.parametrize("months", [0, 25])
def test_a_window_outside_one_to_twenty_four_months_is_refused(conn, months):
    with pytest.raises(ValueError):
        schedule_by_month(conn, today=TODAY, months=months)
