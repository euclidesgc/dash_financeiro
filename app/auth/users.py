import sqlite3

CURRENT_EPOCH = "SELECT session_epoch FROM users WHERE login = ?"
BUMP_EPOCH = "UPDATE users SET session_epoch = session_epoch + 1 WHERE login = ?"


def session_epoch(conn: sqlite3.Connection, login: str) -> int | None:
    row = conn.execute(CURRENT_EPOCH, (login,)).fetchone()
    return None if row is None else int(row[0])


def bump_session_epoch(conn: sqlite3.Connection, login: str) -> None:
    conn.execute(BUMP_EPOCH, (login,))
    conn.commit()
