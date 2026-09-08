import sqlite3
from datetime import date
from typing import Any

from app.commitments import INSTALLMENT, RECURRING
from app.queries.period import shift

LIVE_MONTHS = 1

_COLUMNS = (
    "id, kind, series_key, description, account, amount_cents, months_observed, "
    "months_consecutive, last_seen_date, due_day, last_installment, installment_total, "
    "installments_left, ends_month, dismissed"
)


def live_floor(today: date | None = None) -> str:
    # Reason: this is a floor, not a set of month labels — a card invoice
    # arrives with instalments dated months ahead, and a set of the current
    # and previous month reads those future charges as a series that
    # stopped (RF-23). A floor lets the future in and keeps the remote past
    # out with one comparison.
    reference = today or date.today()
    return shift(date(reference.year, reference.month, 1), -LIVE_MONTHS).isoformat()


def subscriptions(conn: sqlite3.Connection, *, today: date | None = None) -> list[dict[str, Any]]:
    # Reason: every recurring series is listed, live or not — a series that
    # stopped being charged is shown marked, never hidden, because a short
    # list reads as a quiet month (RF-35 from item 003).
    floor = live_floor(today)
    rows = conn.execute(
        f"SELECT {_COLUMNS} FROM commitments WHERE kind = ? ORDER BY amount_cents, series_key",
        (RECURRING,),
    ).fetchall()
    return [dict(row, live=row["last_seen_date"] >= floor) for row in rows]


def installments(conn: sqlite3.Connection, *, today: date | None = None) -> list[dict[str, Any]]:
    # Reason: an instalment series is only a commitment while it still has
    # an unpaid instalment and was charged recently enough — without the
    # window the dead series still "owe" money that leaves no account (D1,
    # RF-13 from item 003).
    floor = live_floor(today)
    rows = conn.execute(
        f"SELECT {_COLUMNS} FROM commitments WHERE kind = ? AND installments_left > 0 "
        "ORDER BY amount_cents * installments_left, series_key",
        (INSTALLMENT,),
    ).fetchall()
    return [dict(row) for row in rows if row["last_seen_date"] >= floor]


def charged(conn: sqlite3.Connection, *, today: date | None = None) -> list[dict[str, Any]]:
    # Reason: every series with a charge inside the window, owing more
    # instalments or not — an instalment already posted for a future date is
    # money leaving the account, and dropping it because the series stopped
    # owing would hide a charge the owner can already see on the invoice
    # (RF-15).
    rows = conn.execute(
        f"SELECT {_COLUMNS} FROM commitments WHERE last_seen_date >= ? AND dismissed = 0",
        (live_floor(today),),
    ).fetchall()
    return [dict(row) for row in rows]


def released_cash(conn: sqlite3.Connection, *, today: date | None = None) -> list[dict[str, Any]]:
    # Reason: money that stops leaving is money coming back, so it is
    # counted positive — written negative it would read as one more outflow.
    freed: dict[str, int] = {}
    for row in installments(conn, today=today):
        freed[row["ends_month"]] = freed.get(row["ends_month"], 0) - row["amount_cents"]
    return [{"month": month, "amount_cents": freed[month]} for month in sorted(freed)]


def totals(conn: sqlite3.Connection, *, today: date | None = None) -> dict[str, int]:
    # Reason: only a live series counts — a subscription last charged nine
    # months ago is the same defect the instalment window already fixed,
    # and it inflates the one number the owner reads first (RF-24).
    recurring = [row for row in subscriptions(conn, today=today) if row["live"]]
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
