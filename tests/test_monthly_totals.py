from app.queries.expenses import MonthTotal, monthly_totals, period_result
from tests.conftest import load, transaction


def _base(conn):
    load(
        conn,
        [
            transaction("jul-gasto", "2026-07-10", -40.00),
            transaction("jul-salario", "2026-07-05", 3000.00, tipo="CREDIT"),
            transaction("ago-gasto-1", "2026-08-04", -100.00),
            transaction("ago-gasto-2", "2026-08-31", -85.50),
            transaction("ago-salario", "2026-08-05", 5000.00, tipo="CREDIT"),
            transaction("ago-transf", "2026-08-06", -700.00, eh_transferencia=True),
            transaction("ago-estorno", "2026-08-07", 30.00, tipo="CREDIT", eh_estorno=True),
            transaction("ago-estornado", "2026-08-07", -30.00, estornada_por="ago-estorno"),
            transaction("set-gasto", "2026-09-02", -12.00),
            transaction("set-nao-gasto", "2026-09-03", -500.00),
        ],
    )
    conn.execute(
        "UPDATE transactions SET not_expense_reason = 'other' WHERE pluggy_id = 'set-nao-gasto'"
    )
    conn.commit()
    return conn


def test_each_month_sums_income_spending_and_balance(taxonomy_conn):
    months = monthly_totals(_base(taxonomy_conn))

    assert months == [
        MonthTotal("2026-07", 300000, -4000, 296000),
        MonthTotal("2026-08", 500000, -18550, 481450),
        MonthTotal("2026-09", 0, -1200, -1200),
    ]


def test_own_transfer_refund_and_not_an_expense_stay_out(taxonomy_conn):
    august = monthly_totals(_base(taxonomy_conn), date_from="2026-08-01", date_to="2026-08-31")

    assert august == [MonthTotal("2026-08", 500000, -18550, 481450)]


def test_months_add_up_to_the_period_result(taxonomy_conn):
    conn = _base(taxonomy_conn)
    months = monthly_totals(conn, date_from="2026-07-01", date_to="2026-09-30")
    whole = period_result(conn, date_from="2026-07-01", date_to="2026-09-30")

    assert sum(month.spending_cents for month in months) == whole.spending_cents
    assert sum(month.income_cents for month in months) == whole.income_cents


def test_account_filter_and_empty_window(taxonomy_conn):
    conn = _base(taxonomy_conn)

    assert monthly_totals(conn, account_id="outra-conta") == []
    assert monthly_totals(conn, date_from="2027-01-01") == []
    assert len(monthly_totals(conn, account_id="acc-1")) == 3
