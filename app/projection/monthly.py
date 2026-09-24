import sqlite3
from datetime import date
from typing import Any, cast

from app.queries.spending import INCOME, SPENDING
from app.settings.catalog import MEDIAN, MEDIAN_MONTHS
from app.settings.store import value

_MONTHS_SEEN = (
    "SELECT DISTINCT substr(date, 1, 7) AS month FROM transactions "
    "WHERE substr(date, 1, 7) < ? ORDER BY month"
)
_INCOME = (
    f"SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    f"WHERE substr(date, 1, 7) = ? AND {INCOME}"
)
_SPENDING = (
    f"SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    f"WHERE substr(date, 1, 7) = ? AND {SPENDING}"
)


def monthly(conn: sqlite3.Connection, *, today: date | None = None) -> dict[str, Any]:
    months = complete_months(conn, today=today)
    income = median([_total(conn, _INCOME, month) for month in months])
    spending = median([_total(conn, _SPENDING, month) for month in months])
    return {
        "months": months,
        "income_cents": income,
        "spending_cents": spending,
        "leftover_cents": income + spending,
    }


def median_months(conn: sqlite3.Connection) -> int:
    # Reason: the constant is the premise the panel declares while the owner
    # has not decided, never the answer (RF-09).
    chosen = value(conn, MEDIAN)
    return MEDIAN_MONTHS if chosen is None else chosen


def _seen(conn: sqlite3.Connection, today: date | None) -> list[str]:
    # Reason: the month of the reference date is still running, so counting
    # it would compare a fraction of a month against whole ones.
    current = (today or date.today()).strftime("%Y-%m")
    return [row["month"] for row in conn.execute(_MONTHS_SEEN, (current,))]


def available_months(conn: sqlite3.Connection, *, today: date | None = None) -> int:
    return len(_seen(conn, today))


def complete_months(conn: sqlite3.Connection, *, today: date | None = None) -> list[str]:
    return _seen(conn, today)[-median_months(conn) :]


def median(values: list[int]) -> int:
    # Reason: the median, not the mean — one month of this base carries an
    # atypical credit of R$ 42 thousand, and the mean would project an income
    # that does not exist. The median neutralises it without anyone deciding
    # by hand which month is atypical (RF-06).
    if not values:
        return 0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) // 2


def _total(conn: sqlite3.Connection, query: str, month: str) -> int:
    return cast(int, conn.execute(query, (month,)).fetchone()["total"])
