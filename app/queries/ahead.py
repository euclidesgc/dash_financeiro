import sqlite3
from dataclasses import dataclass

from app.queries.spending import SPENDING

_AHEAD = (
    "SELECT count(*) AS entries, coalesce(sum(amount_cents), 0) AS amount_cents "
    f"FROM transactions WHERE {SPENDING} AND date > ? AND date <= ?"
)


@dataclass(frozen=True)
class Ahead:
    entries: int
    amount_cents: int


def posted_ahead(conn: sqlite3.Connection, *, after: str, until: str) -> Ahead:
    row = conn.execute(_AHEAD, (after, until)).fetchone()
    return Ahead(entries=row["entries"], amount_cents=row["amount_cents"])
