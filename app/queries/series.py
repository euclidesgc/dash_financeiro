import sqlite3
from datetime import date

from app.queries.period import month
from app.queries.spending import SPENDING

MONTHS = 13

_SERIES = (
    "WITH months(month) AS (VALUES {values}) "
    "SELECT months.month AS month, coalesce(sum(t.amount_cents), 0) AS amount_cents, "
    "count(t.id) AS entries "
    "FROM months LEFT JOIN transactions AS t "
    f"ON strftime('%Y-%m', t.date) = months.month AND {SPENDING} "
    "GROUP BY months.month ORDER BY months.month"
)


def monthly_series(
    conn: sqlite3.Connection, *, end_month: str, months: int = MONTHS
) -> list[sqlite3.Row]:
    labels = _labels(month(end_month), months)
    return conn.execute(_SERIES.format(values=", ".join(["(?)"] * len(labels))), labels).fetchall()


def _labels(last: date, months: int) -> list[str]:
    # Reason: a GROUP BY over the transactions returns only the months that
    # have a row, and an invisible hole in a time series lies about the trend
    # (RF-28) — the points are generated here and the aggregate is filled
    # into them.
    total = last.year * 12 + last.month - 1
    return [
        f"{(total - step) // 12:04d}-{(total - step) % 12 + 1:02d}"
        for step in range(months - 1, -1, -1)
    ]
