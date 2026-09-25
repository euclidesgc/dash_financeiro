import sqlite3

BALANCES = (
    "SELECT id, name, institution, type, subtype, balance_cents, updated_at "
    "FROM accounts ORDER BY type, name"
)


def list_balances(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(BALANCES).fetchall()
