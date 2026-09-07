from pathlib import Path

from app.db import connect
from app.migrations.runner import apply_migrations

SQL_FOLDER = Path(__file__).resolve().parent / "migrations" / "sql"


def run_migrations(path: str | None = None) -> list[str]:
    conn = connect(path)
    try:
        applied = apply_migrations(conn, SQL_FOLDER)
    finally:
        conn.close()
    for name in applied:
        print(f"applied {name}", flush=True)
    print(f"migrations applied: {len(applied)}", flush=True)
    return applied


if __name__ == "__main__":
    run_migrations()
