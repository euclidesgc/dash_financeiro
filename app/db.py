import sqlite3
from pathlib import Path

from app.config import load_config


def connect(path: str | None = None) -> sqlite3.Connection:
    target = path or load_config().db_path
    parent = Path(target).parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    # SQLite ships foreign key enforcement off, per connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
