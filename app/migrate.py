import sys
from pathlib import Path

from app.db import connect
from app.migrations.runner import apply_migrations, reconcile_skipped

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


def reconcile(version: str, path: str | None = None) -> str:
    conn = connect(path)
    try:
        outcome = reconcile_skipped(conn, SQL_FOLDER, version)
    finally:
        conn.close()
    print(outcome, flush=True)
    return outcome


if __name__ == "__main__":
    # Decision: reconciliation is an explicit command and not an automatic
    # mode. It records a version as applied on a base that skipped it, and
    # that is a claim about the schema only someone who looked at the file
    # can make.
    if len(sys.argv) == 3 and sys.argv[1] == "--reconciliar":
        reconcile(sys.argv[2])
    else:
        run_migrations()
