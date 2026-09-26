#!/usr/bin/env bash
set -euo pipefail

E2E_DIR=${DASH_E2E_DIR:?set by playwright.config.ts}
trap 'rm -rf "$E2E_DIR"' EXIT
trap 'exit 143' TERM INT

export DASH_ENV_FILE=/dev/null
export DASH_DB_PATH="$E2E_DIR/dash.sqlite"
export SESSION_SECRET=e2e-secret
export DASH_TRANSACTIONS_PATH=tests/data/e2e_transactions.json
export DASH_ACCOUNTS_GLOB=tests/data/sync_accounts.json

uv run python -m tests.e2e_seed
# Reason: a sync cannot be undone through the API; e2e/restore-seeded-base.ts
# copies this snapshot back over the live database to start from the seed.
cp "$DASH_DB_PATH" "$E2E_DIR/seed.sqlite"

# Reason: the e2e app swaps the AI provider for an offline scripted one, so
# the chat journey runs the real tool against the seed without network.
# Reason: exec would replace the shell and the EXIT trap that removes the
# temporary database would never run.
uv run uvicorn tests.e2e_app:create_e2e_app --factory --host 127.0.0.1 --port 8000 &
wait $!
