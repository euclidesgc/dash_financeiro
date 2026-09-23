import os
import sqlite3
import unicodedata
from pathlib import Path

from app.config import load_config


def fold(value: str | None) -> str | None:
    if value is None:
        return None
    return "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    ).casefold()


def _restrict(target: str) -> None:
    # Reason: the file holds the password hash and the statement, and SQLite
    # creates it through the umask, at 0644. A missing file (":memory:") or a
    # filesystem that refuses chmod is not a reason to refuse the connection.
    try:
        os.chmod(target, 0o600)
    except OSError:
        return


def connect(path: str | None = None) -> sqlite3.Connection:
    target = path or load_config().db_path
    parent = Path(target).parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    _restrict(target)
    conn.row_factory = sqlite3.Row
    # Reason: SQLite ships foreign key enforcement off, per connection.
    conn.execute("PRAGMA foreign_keys = ON")
    # Reason: expense search compares both sides in SQL, so fold must exist
    # on every connection, including tests and e2e.
    conn.create_function("fold", 1, fold, deterministic=True)
    return conn
