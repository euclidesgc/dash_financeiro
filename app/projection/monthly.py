import sqlite3
from datetime import date

from app.queries.spending import SPENDING
from app.settings.catalog import MEDIAN_MONTHS

_MONTHS_SEEN = (
    "SELECT DISTINCT substr(date, 1, 7) AS month FROM transactions "
    "WHERE substr(date, 1, 7) < ? ORDER BY month"
)
_INCOME = (
    "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    "WHERE substr(date, 1, 7) = ? AND amount_cents > 0 AND is_transfer = 0 AND is_refund = 0"
)
_SPENDING = (
    f"SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    f"WHERE substr(date, 1, 7) = ? AND {SPENDING}"
)


def monthly(conn: sqlite3.Connection, *, today: date | None = None) -> dict:
    months = complete_months(conn, today=today)
    income = median([_total(conn, _INCOME, month) for month in months])
    spending = median([_total(conn, _SPENDING, month) for month in months])
    return {
        "months": months,
        "income_cents": income,
        "spending_cents": spending,
        "leftover_cents": income + spending,
    }


def complete_months(conn: sqlite3.Connection, *, today: date | None = None) -> list[str]:
    # The month of the reference date is still running, so counting it would
    # compare a fraction of a month against whole ones.
    current = (today or date.today()).strftime("%Y-%m")
    seen = [row["month"] for row in conn.execute(_MONTHS_SEEN, (current,))]
    return seen[-MEDIAN_MONTHS:]


def median(values: list[int]) -> int:
    # The median, not the mean: one month of this base carries an atypical credit
    # of R$ 42 thousand, and the mean would project an income that does not
    # exist. The median neutralises it without anyone deciding by hand which
    # month is atypical (RF-06).
    if not values:
        return 0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) // 2


def _total(conn: sqlite3.Connection, query: str, month: str) -> int:
    return conn.execute(query, (month,)).fetchone()["total"]
