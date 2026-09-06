import sqlite3
from datetime import date

from app.commitments import series
from app.commitments.live import live_months
from app.config import reference_date
from app.db import connect

_FIELDS = (
    "kind",
    "series_key",
    "description",
    "account",
    "amount_cents",
    "months_observed",
    "months_consecutive",
    "last_seen_date",
    "due_day",
    "last_installment",
    "installment_total",
    "installments_left",
    "ends_month",
)

_INSERT = (
    f"INSERT INTO commitments ({', '.join(_FIELDS)}) "
    f"VALUES ({', '.join('?' * len(_FIELDS))})"
)


def recompute(conn: sqlite3.Connection, *, today: date | None = None) -> int:
    window = live_months(today)
    try:
        # Wiping and rewriting is what makes idempotence a property of
        # construction instead of a promise of upsert; a half recomputed base
        # keeps adding up and starts lying, which is worse than no base at all.
        conn.execute("DELETE FROM commitments")
        installments = series.installment_series(conn)
        recurring = series.recurring_series(conn)
        rows = recurring_after_precedence(recurring, installments, window) + installments
        conn.executemany(_INSERT, [tuple(row[field] for field in _FIELDS) for row in rows])
        conn.execute(
            "UPDATE commitments SET dismissed = 1 WHERE series_key IN "
            "(SELECT series_key FROM commitment_dismissals)"
        )
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return len(rows)


def recurring_after_precedence(
    recurring: list[dict], installments: list[dict], window: list[str]
) -> list[dict]:
    # An instalment ends and a subscription does not, so a key that is both
    # counts once, as the instalment. The precedence runs against the live
    # instalment because that is the only one inside the total, and it is there
    # that counting twice costs money (D3, RF-17).
    live = {
        row["series_key"]
        for row in installments
        if (row["installments_left"] or 0) > 0 and row["last_seen_date"][:7] in window
    }
    return [row for row in recurring if row["series_key"] not in live]


def main() -> int:
    today = reference_date()
    conn = connect()
    try:
        written = recompute(conn, today=today)
    finally:
        conn.close()
    print(f"commitments recomputed: {written} reference={today.isoformat()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
