import math
import sqlite3
from datetime import UTC, datetime, timedelta

WINDOW_SECONDS = 900
MAX_FAILURES = 5

RECENT_FAILURES = (
    "SELECT occurred_at FROM login_attempts "
    "WHERE ip = ? AND success = 0 AND occurred_at >= ? "
    "ORDER BY occurred_at"
)


def _moment(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(UTC)
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC)
    return now


# Reason: every stamp is written with the same precision so that the window
# filter can compare them as text, which is what SQLite indexes.
def _stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="microseconds")


def _record(conn: sqlite3.Connection, ip: str, success: int, now: datetime | None) -> None:
    conn.execute(
        "INSERT INTO login_attempts (ip, occurred_at, success) VALUES (?, ?, ?)",
        (ip, _stamp(_moment(now)), success),
    )
    conn.commit()


def record_failure(conn: sqlite3.Connection, ip: str, *, now: datetime | None = None) -> None:
    _record(conn, ip, 0, now)


# Reason: the trail of who got in and when is what an incident asks for
# first; the block counter reads only the failures, so this row never
# changes what it decides.
def record_success(conn: sqlite3.Connection, ip: str, *, now: datetime | None = None) -> None:
    _record(conn, ip, 1, now)


def blocked_seconds(conn: sqlite3.Connection, ip: str, *, now: datetime | None = None) -> int:
    moment = _moment(now)
    window_start = _stamp(moment - timedelta(seconds=WINDOW_SECONDS))
    rows = conn.execute(RECENT_FAILURES, (ip, window_start)).fetchall()
    if len(rows) < MAX_FAILURES:
        return 0
    oldest_blocking = datetime.fromisoformat(rows[-MAX_FAILURES]["occurred_at"])
    remaining = WINDOW_SECONDS - (moment - oldest_blocking).total_seconds()
    return max(1, math.ceil(remaining))
