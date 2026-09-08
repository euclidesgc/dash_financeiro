import sqlite3
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from app.commitments import INSTALLMENT
from app.commitments.live import charged, installments, subscriptions
from app.commitments.schedule import on_month
from app.commitments.series import installment_of
from app.queries.period import shift
from app.queries.spending import SPENDING

WINDOW_DAYS = 45
DUE_TOLERANCE_DAYS = 10

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
    recorded = _recorded_entries(conn, first, last, charged(conn, today=first))
    entries = recorded + _remaining_predictions(_predicted_entries(series, first, last), recorded)
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


def _live_series(conn: sqlite3.Connection, today: date) -> list[dict[str, Any]]:
    # A series that stopped being charged has no next due date to predict, and a
    # dismissed one is money the owner already took out of the total: both stay
    # off the prediction, and the screen says how many (RF-22 do 003).
    recurring = [
        row for row in subscriptions(conn, today=today) if row["live"] and not row["dismissed"]
    ]
    return recurring + installments(conn, today=today)


def _recorded_entries(
    conn: sqlite3.Connection, first: date, last: date, series: list[dict[str, Any]]
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


def _predicted_entries(series: list[dict[str, Any]], first: date, last: date) -> list[Entry]:
    entries = []
    for row in series:
        identity = _series_identity(row)
        for month in _months(first, last):
            if not _charges(row, month.strftime("%Y-%m")):
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


def _remaining_predictions(predictions: list[Entry], recorded: list[Entry]) -> list[Entry]:
    # A recorded charge replaces the prediction it realises, and that is the
    # nearest one of its own series — measured between whole dates, so a series
    # due on the 29th and charged on the 1st of the next month is two days away
    # and not twenty-eight (RF-13). Keyed by month instead, a stray charge on the
    # 5th would hide the due date on the 25th; matched by exact day, the median
    # being a day or two off would show the same money leaving twice (RF-10).
    left = list(predictions)
    for entry in recorded:
        when = date.fromisoformat(entry["date"])
        nearest, distance = None, None
        for candidate in left:
            if candidate["identity"] != entry["identity"]:
                continue
            apart = abs((date.fromisoformat(candidate["date"]) - when).days)
            if apart <= DUE_TOLERANCE_DAYS and (distance is None or apart < distance):
                nearest, distance = candidate, apart
        if nearest is not None:
            left.remove(nearest)
    return left


def _charges(row: dict[str, Any], month: str) -> bool:
    # An instalment stops at its last instalment, so the prediction runs only
    # over the months it still owes; a subscription has no end and is charged in
    # every month of the window.
    if row["due_day"] is None:
        return False
    if row["kind"] != INSTALLMENT:
        return True
    return bool(row["last_seen_date"][:7] < month <= (row["ends_month"] or ""))


def _months(first: date, last: date) -> list[date]:
    start, end = date(first.year, first.month, 1), date(last.year, last.month, 1)
    months = [start]
    while months[-1] < end:
        months.append(shift(months[-1], 1))
    return months


def _series_identity(row: dict[str, Any]) -> tuple[str, int, int]:
    if row["kind"] == INSTALLMENT:
        return row["series_key"], row["installment_total"], abs(row["amount_cents"])
    return row["series_key"], 0, 0


def _row_identity(
    row: sqlite3.Row, known: dict[tuple[str, int, int], dict[str, Any]]
) -> tuple[str, int, int]:
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
