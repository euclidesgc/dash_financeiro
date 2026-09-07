import sqlite3
from datetime import date

from app.commitments import series
from app.commitments.live import live_floor
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

_INSERT = f"INSERT INTO commitments ({', '.join(_FIELDS)}) VALUES ({', '.join('?' * len(_FIELDS))})"


def recompute(conn: sqlite3.Connection, *, today: date | None = None) -> int:
    floor = live_floor(today)
    try:
        # Wiping and rewriting is what makes idempotence a property of
        # construction instead of a promise of upsert; a half recomputed base
        # keeps adding up and starts lying, which is worse than no base at all.
        conn.execute("DELETE FROM commitments")
        installments = series.installment_series(conn)
        recurring = series.recurring_series(conn)
        rows = recurring_after_precedence(recurring, installments, floor) + installments
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
    recurring: list[dict], installments: list[dict], floor: str
) -> list[dict]:
    # An instalment ends and a subscription does not, so a key that is both
    # counts once, as the instalment. The precedence looks only at the window,
    # never at what is still owed: in the month the last instalment falls the
    # series stops owing, the precedence would let go, and the recurring line —
    # built from those very charges — would resurrect a finished debt (RF-01).
    charged = {row["series_key"] for row in installments if row["last_seen_date"] >= floor}
    return [row for row in recurring if row["series_key"] not in charged]


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
