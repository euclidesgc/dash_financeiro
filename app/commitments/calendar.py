import sqlite3
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from app.commitments import INSTALLMENT
from app.commitments.live import installments, subscriptions
from app.commitments.schedule import on_month
from app.commitments.series import installment_of
from app.queries.period import shift
from app.queries.spending import SPENDING

WINDOW_DAYS = 45

Entry = dict[str, Any]
Day = dict[str, Any]

_RECORDED = (
    "SELECT payee, date, description, amount_cents, installment_current, installment_total "
    f"FROM transactions WHERE {SPENDING} AND payee IS NOT NULL AND payee != '' "
    "AND date >= ? AND date <= ? ORDER BY date, id"
)


def window(today: date | None = None) -> tuple[date, date]:
    reference = today or date.today()
    return reference, reference + timedelta(days=WINDOW_DAYS)


def calendar(conn: sqlite3.Connection, *, today: date | None = None) -> list[Day]:
    first, last = window(today)
    series = _live_series(conn, first)
    entries = _recorded_entries(conn, first, last, series)
    booked = {(entry["identity"], entry["date"][:7]) for entry in entries}
    entries += _predicted_entries(series, first, last, booked)
    days: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        days[entry["date"]].append(entry)
    return [
        {
            "date": when,
            "total_cents": sum(entry["amount_cents"] for entry in days[when]),
            "entries": [_public(entry) for entry in sorted(days[when], key=_ordering)],
        }
        for when in sorted(days)
    ]


def _live_series(conn: sqlite3.Connection, today: date) -> list[dict]:
    # A series that stopped being charged has no next due date to predict, and a
    # dismissed one is money the owner already took out of the total: both stay
    # off the calendar, and the screen says how many (RF-22).
    recurring = [
        row
        for row in subscriptions(conn, today=today)
        if row["live"] and not row["dismissed"]
    ]
    return recurring + installments(conn, today=today)


def _recorded_entries(
    conn: sqlite3.Connection, first: date, last: date, series: list[dict]
) -> list[Entry]:
    known = {_series_identity(row): row for row in series}
    entries = []
    for row in conn.execute(_RECORDED, (first.isoformat(), last.isoformat())):
        identity = _row_identity(row, known)
        commitment = known.get(identity)
        if commitment is None:
            continue
        entries.append(
            {
                "identity": identity,
                "date": row["date"],
                "series_key": commitment["series_key"],
                "description": row["description"] or commitment["description"],
                "amount_cents": row["amount_cents"],
                "predicted": False,
            }
        )
    return entries


def _predicted_entries(
    series: list[dict], first: date, last: date, booked: set[tuple]
) -> list[Entry]:
    # A charge already recorded takes the whole month of its series, not just the
    # day it fell on: the median rarely lands on the exact day, and a prediction
    # a few days off the real line would show the same money leaving twice in the
    # same month (RF-23).
    entries = []
    for row in series:
        identity = _series_identity(row)
        for month in _months(first, last):
            label = month.strftime("%Y-%m")
            if (identity, label) in booked or not _charges(row, label):
                continue
            due = on_month(row["due_day"], month)
            if first <= due <= last:
                entries.append(
                    {
                        "identity": identity,
                        "date": due.isoformat(),
                        "series_key": row["series_key"],
                        "description": row["description"],
                        "amount_cents": row["amount_cents"],
                        "predicted": True,
                    }
                )
    return entries


def _charges(row: dict, month: str) -> bool:
    # An instalment stops at its last instalment, so the prediction runs only
    # over the months it still owes; a subscription has no end and is charged in
    # every month of the window.
    if row["due_day"] is None:
        return False
    if row["kind"] != INSTALLMENT:
        return True
    return row["last_seen_date"][:7] < month <= (row["ends_month"] or "")


def _months(first: date, last: date) -> list[date]:
    start, end = date(first.year, first.month, 1), date(last.year, last.month, 1)
    months = [start]
    while months[-1] < end:
        months.append(shift(months[-1], 1))
    return months


def _series_identity(row: dict) -> tuple[str, int, int]:
    if row["kind"] == INSTALLMENT:
        return row["series_key"], row["installment_total"], abs(row["amount_cents"])
    return row["series_key"], 0, 0


def _row_identity(row: sqlite3.Row, known: dict) -> tuple[str, int, int]:
    # The same identity the engine grouped by, read from the raw line: matching a
    # recorded occurrence to its series by payee alone would let one open
    # purchase of a store silence the prediction of another (RF-23). The marker
    # falls back to the recurring key because a subscription whose description
    # happens to carry one is still that subscription being charged.
    _, total = installment_of(row)
    marked = (row["payee"], total or 0, abs(row["amount_cents"]) if total else 0)
    return marked if marked in known else (row["payee"], 0, 0)


def _ordering(entry: Entry) -> tuple[int, str]:
    return entry["amount_cents"], entry["series_key"]


def _public(entry: Entry) -> Entry:
    return {name: value for name, value in entry.items() if name != "identity"}
