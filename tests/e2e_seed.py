import sqlite3
import sys

from app.auth.seed import seed_user
from app.db import connect
from app.ingest.loader import IngestResult, ingest
from app.ingest.source import load_accounts, load_transactions
from app.migrate import run_migrations
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import seed_taxonomy

LOGIN = "e2e"
PASSWORD = "senha-e2e-9k2"
TRANSACTIONS = "tests/data/e2e_transactions.json"
ACCOUNTS = "tests/data/e2e_accounts.json"


def seed(conn: sqlite3.Connection) -> IngestResult:
    seed_user(conn, LOGIN, PASSWORD)
    seed_taxonomy(conn)
    result = ingest(
        conn,
        transactions=load_transactions(TRANSACTIONS),
        accounts=load_accounts(ACCOUNTS),
        source="e2e",
    )
    if result.status != "ok":
        return result
    classify_all(conn)
    # Reason: the seed ingest is fixture furniture, not a real sync run; the
    # screen must start from "Nunca atualizado", not from this bootstrap row.
    conn.execute("DELETE FROM sync_runs")
    conn.commit()
    return result


def main() -> int:
    run_migrations()
    conn = connect()
    try:
        result = seed(conn)
    finally:
        conn.close()
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
