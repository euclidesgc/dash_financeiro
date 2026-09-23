#!/usr/bin/env bash
set -euo pipefail

E2E_DIR=$(mktemp -d)
trap 'rm -rf "$E2E_DIR"' EXIT
trap 'exit 143' TERM INT

export DASH_ENV_FILE=/dev/null
export DASH_DB_PATH="$E2E_DIR/dash.sqlite"
export SESSION_SECRET=e2e-secret
export DASH_TRANSACTIONS_PATH=tests/data/e2e_transactions.json
export DASH_ACCOUNTS_GLOB=tests/data/sync_accounts.json

uv run python -c '
import sys

from app.auth.seed import seed_user
from app.db import connect
from app.ingest.loader import ingest
from app.ingest.source import load_accounts, load_transactions
from app.migrate import run_migrations
from app.taxonomy.seed import seed_taxonomy

run_migrations()
conn = connect()
try:
    seed_user(conn, "e2e", "senha-e2e-9k2")
    seed_taxonomy(conn)
    result = ingest(
        conn,
        transactions=load_transactions("tests/data/e2e_transactions.json"),
        accounts=load_accounts("tests/data/e2e_accounts.json"),
        source="e2e",
    )
    # Reason: the seed ingest is fixture furniture, not a real sync run; the
    # screen must start from "Nunca atualizado", not from this bootstrap row.
    conn.execute("DELETE FROM sync_runs")
    conn.commit()
finally:
    conn.close()
if result.status != "ok":
    sys.exit(1)
'

# Reason: exec would replace the shell and the EXIT trap that removes the
# temporary database would never run.
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 &
wait $!
