import sqlite3
from datetime import date

from app.commitments import INSTALLMENT, RECURRING
from app.commitments.schedule import months_before

LIVE_MONTHS = 1

_COLUMNS = (
    "id, kind, series_key, description, account, amount_cents, months_observed, "
    "months_consecutive, last_seen_date, due_day, last_installment, installment_total, "
    "installments_left, ends_month, dismissed"
)


def live_months(today: date | None = None) -> list[str]:
    return months_before((today or date.today()).strftime("%Y-%m"), LIVE_MONTHS)


def subscriptions(conn: sqlite3.Connection, *, today: date | None = None) -> list[dict]:
    # Every recurring series is listed, live or not: a series that stopped being
    # charged is shown marked, never hidden, because a short list reads as a
    # quiet month (RF-35).
    window = live_months(today)
    rows = conn.execute(
        f"SELECT {_COLUMNS} FROM commitments WHERE kind = ? ORDER BY amount_cents, series_key",
        (RECURRING,),
    ).fetchall()
    return [dict(row, live=row["last_seen_date"][:7] in window) for row in rows]


def installments(conn: sqlite3.Connection, *, today: date | None = None) -> list[dict]:
    # An instalment series is only a commitment while it still has an unpaid
    # instalment and was charged this month or the last one: without the window
    # the dead series still "owe" money that leaves no account (D1, RF-13).
    window = live_months(today)
    rows = conn.execute(
        f"SELECT {_COLUMNS} FROM commitments WHERE kind = ? AND installments_left > 0 "
        "ORDER BY amount_cents * installments_left, series_key",
        (INSTALLMENT,),
    ).fetchall()
    return [dict(row) for row in rows if row["last_seen_date"][:7] in window]


def released_cash(conn: sqlite3.Connection, *, today: date | None = None) -> list[dict]:
    # Money that stops leaving is money coming back, so it is counted positive:
    # written negative it would read as one more outflow.
    freed: dict[str, int] = {}
    for row in installments(conn, today=today):
        freed[row["ends_month"]] = freed.get(row["ends_month"], 0) - row["amount_cents"]
    return [{"month": month, "amount_cents": freed[month]} for month in sorted(freed)]


def totals(conn: sqlite3.Connection, *, today: date | None = None) -> dict:
    recurring = subscriptions(conn, today=today)
    live = installments(conn, today=today)
    committed = sum(row["amount_cents"] for row in recurring if not row["dismissed"])
    committed += sum(row["amount_cents"] for row in live)
    return {
        "committed_cents": committed,
        "projected_savings_cents": -sum(
            row["amount_cents"] for row in recurring if row["dismissed"]
        ),
        "released_cents": -sum(row["amount_cents"] for row in live),
    }
