import os
import sqlite3
from pathlib import Path

from app.config import load_config


def _restrict(target: str) -> None:
    # The file holds the password hash and the statement, and SQLite creates it
    # through the umask, at 0644. A missing file (":memory:") or a filesystem
    # that refuses chmod is not a reason to refuse the connection.
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
    # SQLite ships foreign key enforcement off, per connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
