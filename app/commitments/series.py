import re
import sqlite3
from collections import defaultdict

from app.commitments import INSTALLMENT, RECURRING
from app.commitments.schedule import consecutive_run, end_month, median_day
from app.queries.spending import SPENDING

MIN_MONTHS = 3
MIN_CONSECUTIVE_MONTHS = 3
MAX_RELATIVE_DEVIATION = 0.35
MAX_INSTALLMENTS = 48

_MARKER = re.compile(r"(?<!\d)(\d{1,2})\s*(?:/|\s+de\s+)\s*(\d{1,2})(?!\d)")

_OCCURRENCES = (
    "SELECT t.payee, t.date, t.description, t.amount_cents, t.installment_current, "
    "t.installment_total, a.name AS account "
    "FROM transactions t LEFT JOIN accounts a ON a.id = t.account_id "
    f"WHERE {SPENDING} AND t.payee IS NOT NULL AND t.payee != '' AND t.date IS NOT NULL "
    "ORDER BY t.date, t.id"
)


def recurring_series(conn: sqlite3.Connection) -> list[dict]:
    groups: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in conn.execute(_OCCURRENCES):
        groups[row["payee"]].append(row)
    detected = []
    for key, occurrences in groups.items():
        months = _months(occurrences)
        if len(months) < MIN_MONTHS:
            continue
        consecutive = consecutive_run(sorted(months))
        if consecutive < MIN_CONSECUTIVE_MONTHS:
            continue
        average = _average(occurrences)
        if average is None:
            continue
        last = occurrences[-1]
        detected.append(
            {
                "kind": RECURRING,
                "series_key": key,
                "description": last["description"] or key,
                "account": last["account"],
                "amount_cents": -average,
                "months_observed": len(months),
                "months_consecutive": consecutive,
                "last_seen_date": last["date"],
                "due_day": median_day(_days(occurrences)),
                "last_installment": None,
                "installment_total": 0,
                "installments_left": None,
                "ends_month": None,
            }
        )
    return detected


def installment_series(conn: sqlite3.Connection) -> list[dict]:
    groups: dict[tuple, list[tuple[sqlite3.Row, int | None]]] = defaultdict(list)
    for row in conn.execute(_OCCURRENCES):
        current, total = installment_of(row)
        if not total:
            continue
        # The same store shows up with several open purchases at once, so the
        # instalment count and the instalment value are part of the series key.
        groups[(row["payee"], total, abs(row["amount_cents"]))].append((row, current))
    detected = []
    for (key, total, amount), items in groups.items():
        occurrences = [row for row, _ in items]
        seen = sorted({current for _, current in items if current})
        last_installment = max(seen) if seen else None
        left = total - last_installment if last_installment is not None else None
        last = occurrences[-1]
        months = _months(occurrences)
        detected.append(
            {
                "kind": INSTALLMENT,
                "series_key": key,
                "description": last["description"] or key,
                "account": last["account"],
                "amount_cents": -amount,
                "months_observed": len(months),
                "months_consecutive": consecutive_run(sorted(months)),
                "last_seen_date": last["date"],
                "due_day": median_day(_days(occurrences)),
                "last_installment": last_installment,
                "installment_total": total,
                "installments_left": left,
                "ends_month": end_month(last["date"][:7], left) if left is not None else None,
            }
        )
    return detected


def installment_of(row: sqlite3.Row) -> tuple[int | None, int | None]:
    current, total = row["installment_current"], row["installment_total"]
    if current and total:
        return int(current), int(total)
    found = _MARKER.search(row["description"] or "")
    if not found:
        return None, None
    current, total = int(found.group(1)), int(found.group(2))
    if 1 <= current <= total <= MAX_INSTALLMENTS and total > 1:
        return current, total
    return None, None


def _months(occurrences: list[sqlite3.Row]) -> dict[str, list[int]]:
    months: dict[str, list[int]] = defaultdict(list)
    for row in occurrences:
        months[row["date"][:7]].append(abs(row["amount_cents"]))
    return months


def _days(occurrences: list[sqlite3.Row]) -> list[int]:
    return [int(row["date"][8:10]) for row in occurrences]


def _average(occurrences: list[sqlite3.Row]) -> int | None:
    # A series whose value swings has no "average value" that predicts anything,
    # and the three cuts together are what separate a live commitment from a
    # coincidence of three months (RF-09).
    values = [abs(row["amount_cents"]) for row in occurrences]
    mean = sum(values) / len(values)
    if mean == 0:
        return None
    if max(abs(value - mean) / mean for value in values) > MAX_RELATIVE_DEVIATION:
        return None
    return round(mean)
