import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionRow:
    item_id: str
    created_at: str


_SELECT = "SELECT item_id, created_at FROM pluggy_connections"


def _row(row: sqlite3.Row) -> ConnectionRow:
    return ConnectionRow(item_id=row["item_id"], created_at=row["created_at"])


def list_connections(conn: sqlite3.Connection) -> list[ConnectionRow]:
    rows = conn.execute(f"{_SELECT} ORDER BY created_at, item_id").fetchall()
    return [_row(row) for row in rows]


def get_connection(conn: sqlite3.Connection, item_id: str) -> ConnectionRow | None:
    row = conn.execute(f"{_SELECT} WHERE item_id = ?", (item_id,)).fetchone()
    return None if row is None else _row(row)


def list_item_ids(conn: sqlite3.Connection) -> list[str]:
    return [row.item_id for row in list_connections(conn)]
