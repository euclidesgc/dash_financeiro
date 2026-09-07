import pytest

from app.queries.period import InvalidPeriodError
from app.queries.series import MONTHS, monthly_series
from tests.conftest import load, transaction

END_MONTH = "2026-03"


def points(conn, end_month=END_MONTH, **extra):
    return {
        row["month"]: row["amount_cents"]
        for row in monthly_series(conn, end_month=end_month, **extra)
    }


@pytest.fixture
def conn(taxonomy_conn):
    return load(
        taxonomy_conn,
        [
            transaction("t-january", "2026-01-15", -10.00),
            transaction("t-march", "2026-03-10", -25.00),
            transaction("t-march-again", "2026-03-20", -5.00),
            transaction("t-income", "2026-02-10", 400.00),
            transaction("t-internal", "2026-02-11", -80.00, eh_transferencia=True),
            transaction("t-refund", "2026-02-12", 30.00, eh_estorno=True, estornada_por="t-debit"),
            transaction("t-debit", "2026-02-12", -30.00, estornada_por="t-refund"),
        ],
    )


def test_the_series_has_thirteen_points_ending_in_the_given_month(conn):
    series = monthly_series(conn, end_month=END_MONTH)
    assert len(series) == MONTHS == 13
    assert series[0]["month"] == "2025-03"
    assert series[-1]["month"] == END_MONTH


def test_a_month_without_spending_stays_in_the_series(conn):
    series = monthly_series(conn, end_month=END_MONTH)
    assert len(series) == 13
    month = {row["month"]: row for row in series}
    assert "2026-02" in month
    assert month["2026-02"]["amount_cents"] == 0
    assert month["2026-01"]["amount_cents"] == -1000
    assert month["2026-03"]["amount_cents"] == -3000


def test_the_months_come_out_in_order_and_without_a_hole(conn):
    months = [row["month"] for row in monthly_series(conn, end_month=END_MONTH)]
    assert months == sorted(months)
    assert months == [
        "2025-03",
        "2025-04",
        "2025-05",
        "2025-06",
        "2025-07",
        "2025-08",
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
    ]


def test_income_transfer_refund_and_refunded_debit_stay_out_of_the_point(conn):
    assert points(conn)["2026-02"] == 0
    assert sum(row["amount_cents"] for row in monthly_series(conn, end_month=END_MONTH)) == -4000


def test_each_point_counts_the_entries_that_built_it(conn):
    entries = {row["month"]: row["entries"] for row in monthly_series(conn, end_month=END_MONTH)}
    assert (entries["2026-01"], entries["2026-02"], entries["2026-03"]) == (1, 0, 2)


def test_the_series_crosses_the_turn_of_the_year(conn):
    assert [row["month"] for row in monthly_series(conn, end_month="2026-01", months=3)] == [
        "2025-11",
        "2025-12",
        "2026-01",
    ]


def test_a_month_that_is_not_a_month_is_refused_naming_the_field(conn):
    with pytest.raises(InvalidPeriodError) as refused:
        monthly_series(conn, end_month="2026-13")
    assert str(refused.value) == "data inválida: fim (2026-13)"
