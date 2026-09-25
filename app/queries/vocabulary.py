import sqlite3

__all__ = ("fallback_term", "group_name", "groups", "natures", "terms")

_GROUPS = "SELECT id, name FROM category_groups ORDER BY position, name"
_GROUP_NAME = "SELECT name FROM category_groups WHERE id = ?"
_NATURES = "SELECT value FROM natures ORDER BY position"
_TERMS = "SELECT value FROM essentialities ORDER BY position"
_FALLBACK_TERM = "SELECT value FROM essentialities WHERE is_fallback = 1"


def groups(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(_GROUPS).fetchall()


def group_name(conn: sqlite3.Connection, group_id: int) -> str:
    row = conn.execute(_GROUP_NAME, (group_id,)).fetchone()
    return str(row["name"]) if row is not None else ""


def natures(conn: sqlite3.Connection) -> list[str]:
    return [row["value"] for row in conn.execute(_NATURES)]


def terms(conn: sqlite3.Connection) -> list[str]:
    return [row["value"] for row in conn.execute(_TERMS)]


def fallback_term(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(_FALLBACK_TERM).fetchone()
    return None if row is None else str(row["value"])
