import sys

from app.config import load_config
from app.db import connect
from app.ingest.loader import ingest
from app.ingest.source import load_accounts, load_transactions
from app.migrate import run_migrations


def main() -> int:
    config = load_config()
    run_migrations(config.db_path)
    transactions = load_transactions(config.transactions_path)
    accounts = load_accounts(config.accounts_glob)
    conn = connect(config.db_path)
    try:
        result = ingest(
            conn,
            transactions=transactions,
            accounts=accounts,
            source=config.transactions_path,
        )
    finally:
        conn.close()
    for rejection in result.rejections:
        print(
            f"rejected index={rejection.index} reason={rejection.reason} "
            f"description={rejection.description}",
            file=sys.stderr,
        )
    if result.status != "ok":
        print(f"ingest failed: {result.message}", file=sys.stderr)
        return 1
    print(f"ingested {result.message}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
