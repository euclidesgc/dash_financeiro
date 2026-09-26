import sys

from app.commitments.engine import main as recompute_command
from app.config import load_config
from app.db import connect
from app.debts.ladder import main as debts_command
from app.ingest.loader import ingest
from app.ingest.source import load_accounts, load_discarded, load_transactions
from app.ingest.trigger import COMMAND
from app.migrate import run_migrations
from app.taxonomy.classify import main as classify_command
from app.taxonomy.seed import main as seed_command


def main() -> int:
    config = load_config()
    run_migrations(config.db_path)
    transactions = load_transactions(config.transactions_path)
    accounts = load_accounts(config.accounts_glob)
    discarded = load_discarded(config.transactions_path)
    conn = connect(config.db_path)
    try:
        result = ingest(
            conn,
            transactions=transactions,
            accounts=accounts,
            source=config.transactions_path,
            trigger=COMMAND,
            discarded=discarded,
            record=False,
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
    # Reason: a load that is not classified leaves every reader between two
    # commands looking at rows without group, nature or essentiality.
    status = seed_command()
    if status != 0:
        return status
    status = classify_command()
    if status != 0:
        return status
    # Reason: the recomputation is idempotent, so running it always costs
    # nothing, and a base loaded without commitments would leave the screen
    # empty between two commands.
    status = recompute_command()
    if status != 0:
        return status
    return debts_command()


if __name__ == "__main__":
    raise SystemExit(main())
