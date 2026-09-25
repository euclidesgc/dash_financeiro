import sqlite3

__all__ = ("base_is_empty",)

_ANY = "SELECT 1 FROM transactions LIMIT 1"


def base_is_empty(conn: sqlite3.Connection) -> bool:
    return conn.execute(_ANY).fetchone() is None
