import sqlite3
from calendar import monthrange
from datetime import date, timedelta

from app.commitments.calendar import calendar, window
from app.commitments.live import totals as committed_totals
from app.commitments.schedule import median_day
from app.projection.monthly import monthly
from app.projection.position import positions

_INCOME_DAYS = (
    "SELECT date FROM transactions "
    "WHERE amount_cents > 0 AND is_transfer = 0 AND is_refund = 0 AND date <= ?"
)


def forecast(conn: sqlite3.Connection, *, today: date | None = None) -> dict:
    first, last = window(today)
    month = monthly(conn, today=first)
    committed = committed_totals(conn, today=first)["committed_cents"]
    # The dated commitment is only the datable half of the spending. Projecting
    # the whole income against half the spending makes the line rise over a
    # window that reaches two salaries, and the panel would announce that the
    # deficit closes by itself (RF-13).
    variable = month["spending_cents"] - committed
    due = {day["date"]: day["total_cents"] for day in calendar(conn, today=first)}
    income_day = _income_day(conn, first)

    balance = positions(conn)["consolidated_cents"]
    days = [_day(first, balance, 0, 0, 0)]
    for step in range(1, (last - first).days + 1):
        when = first + timedelta(days=step)
        entering = month["income_cents"] if when.day == income_day else 0
        leaving = due.get(when.isoformat(), 0)
        spread = round(variable / monthrange(when.year, when.month)[1])
        balance += entering + leaving + spread
        days.append(_day(when, balance, entering, leaving, spread))

    worst = min(days, key=lambda day: day["balance_cents"])
    return {
        "days": days,
        "worst": worst,
        "delta_cents": days[-1]["balance_cents"] - days[0]["balance_cents"],
        "variable_cents": variable,
        "income_day": income_day,
    }


def _income_day(conn: sqlite3.Connection, today: date) -> int | None:
    days = [int(row["date"][8:10]) for row in conn.execute(_INCOME_DAYS, (today.isoformat(),))]
    return median_day(days) if days else None


def _day(when: date, balance: int, entering: int, leaving: int, spread: int) -> dict:
    return {
        "date": when.isoformat(),
        "balance_cents": balance,
        "income_cents": entering,
        "due_cents": leaving,
        "variable_cents": spread,
    }
