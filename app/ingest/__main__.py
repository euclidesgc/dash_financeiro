import sys

from app.commitments.engine import main as recompute_command
from app.config import load_config
from app.db import connect
from app.ingest.loader import ingest
from app.ingest.source import load_accounts, load_transactions
from app.migrate import run_migrations
from app.taxonomy.classify import main as classify_command
from app.taxonomy.seed import main as seed_command


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
    # A load that is not classified leaves every reader between two commands
    # looking at rows without group, nature or essentiality.
    status = seed_command()
    if status != 0:
        return status
    status = classify_command()
    if status != 0:
        return status
    # The recomputation is idempotent, so running it always costs nothing, and a
    # base loaded without commitments would leave the screen empty between two
    # commands.
    return recompute_command()


if __name__ == "__main__":
    raise SystemExit(main())
