import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.db import connect
from app.migrate import run_migrations

_ITEM_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

_INSERT = "INSERT INTO pluggy_connections (item_id, created_at) VALUES (?, ?)"
_INSERT_MISSING = "INSERT OR IGNORE INTO pluggy_connections (item_id, created_at) VALUES (?, ?)"


class PluggyConnectionError(Exception):
    pass


class InvalidItemIdError(PluggyConnectionError):
    pass


class DuplicateConnectionError(PluggyConnectionError):
    pass


class ConnectionNotFoundError(PluggyConnectionError):
    pass


def normalise(raw: str) -> str:
    item_id = raw.strip().lower()
    if not _ITEM_ID.fullmatch(item_id):
        raise InvalidItemIdError(raw)
    return item_id


def _now() -> str:
    return datetime.now(UTC).isoformat()


def add_connection(conn: sqlite3.Connection, raw: str) -> str:
    item_id = normalise(raw)
    try:
        conn.execute(_INSERT, (item_id, _now()))
    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise DuplicateConnectionError(item_id) from error
    conn.commit()
    return item_id


def remove_connection(conn: sqlite3.Connection, item_id: str) -> None:
    removed = conn.execute(
        "DELETE FROM pluggy_connections WHERE item_id = ?", (item_id.strip().lower(),)
    ).rowcount
    if removed == 0:
        conn.rollback()
        raise ConnectionNotFoundError(item_id)
    conn.commit()


def import_file(conn: sqlite3.Connection, path: Path) -> int:
    added = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item_id = normalise(line)
        except InvalidItemIdError:
            continue
        added += conn.execute(_INSERT_MISSING, (item_id, _now())).rowcount
    conn.commit()
    return added


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("uso: python -m app.sync.connections <arquivo com um id por linha>", file=sys.stderr)
        return 1
    run_migrations()
    conn = connect()
    try:
        added = import_file(conn, Path(argv[0]))
    finally:
        conn.close()
    print(f"conexões importadas: {added}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
