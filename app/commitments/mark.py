import sqlite3
from datetime import datetime, timezone

from app.commitments import RECURRING

REFUSAL_MESSAGE = "Parcelamento contratado não para com um clique."


class DismissRefusedError(ValueError):
    def __init__(self, series_key: str) -> None:
        super().__init__(REFUSAL_MESSAGE)
        self.series_key = series_key


def dismiss(conn: sqlite3.Connection, series_key: str) -> None:
    # A contracted instalment keeps leaving the account after the click, so the
    # refusal is a product rule and lives here, not in the route (RF-27).
    if not _is_recurring(conn, series_key):
        raise DismissRefusedError(series_key)
    conn.execute(
        "INSERT INTO commitment_dismissals (series_key, dismissed_at) VALUES (?, ?) "
        "ON CONFLICT (series_key) DO NOTHING",
        (series_key, datetime.now(timezone.utc).isoformat()),
    )
    _apply(conn, series_key, 1)


def resume(conn: sqlite3.Connection, series_key: str) -> None:
    conn.execute("DELETE FROM commitment_dismissals WHERE series_key = ?", (series_key,))
    _apply(conn, series_key, 0)


def dismissed_keys(conn: sqlite3.Connection) -> set[str]:
    return {row[0] for row in conn.execute("SELECT series_key FROM commitment_dismissals")}


def _apply(conn: sqlite3.Connection, series_key: str, value: int) -> None:
    conn.execute(
        "UPDATE commitments SET dismissed = ? WHERE series_key = ? AND kind = ?",
        (value, series_key, RECURRING),
    )


def _is_recurring(conn: sqlite3.Connection, series_key: str) -> bool:
    found = conn.execute(
        "SELECT 1 FROM commitments WHERE series_key = ? AND kind = ?",
        (series_key, RECURRING),
    ).fetchone()
    return found is not None
