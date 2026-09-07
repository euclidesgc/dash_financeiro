import sqlite3
from dataclasses import dataclass
from datetime import date, datetime

from app.commitments.engine import recompute
from app.config import PLUGGY_CREDENTIALS, load_config, reference_date
from app.db import connect
from app.debts.ladder import rebuild
from app.ingest.loader import IngestResult, ingest
from app.ingest.source import load_accounts, load_transactions
from app.taxonomy.classify import classify_all

FILE = "arquivo"
PLUGGY = "pluggy"
SOURCE = "DASH_SYNC_SOURCE"

STALE_DAYS = 1


class MissingCredentialError(RuntimeError):
    pass


@dataclass(frozen=True)
class SyncOutcome:
    status: str
    message: str
    transactions: int
    accounts: int


def synchronise(conn: sqlite3.Connection, *, today: date | None = None) -> SyncOutcome:
    # The command and the button call this same function: a sync that behaves
    # differently from the cron and from the screen is the defect that only shows
    # up on the day it matters (D4).
    config = load_config()
    if config.sync_source == PLUGGY:
        missing = [name for name in PLUGGY_CREDENTIALS if not config.pluggy.get(name)]
        if missing:
            # No run happened, so no run is recorded: a failure row here would
            # fill the history with failures that never occurred and make the
            # screen shout about configuration instead of synchronisation (D3).
            raise MissingCredentialError(
                "Sincronização com a Pluggy exige "
                + " e ".join(missing)
                + " no ambiente. Enquanto não houver, o painel lê o arquivo já consolidado."
            )
    result = ingest(
        conn,
        transactions=load_transactions(config.transactions_path),
        accounts=load_accounts(config.accounts_glob),
        source=config.transactions_path,
    )
    if result.status == "ok":
        _after(conn, today or reference_date())
    return _outcome(result)


def _after(conn: sqlite3.Connection, today: date) -> None:
    classify_all(conn)
    recompute(conn, today=today)
    rebuild(conn, today=today)


def _outcome(result: IngestResult) -> SyncOutcome:
    return SyncOutcome(
        status=result.status,
        message=result.message,
        transactions=result.transactions_written,
        accounts=result.accounts_written,
    )


def last_runs(conn: sqlite3.Connection) -> dict:
    # Two rows, not one: the last attempt says whether it failed, and the last
    # success says how old the data is. Showing only the attempt would hide the
    # age; showing only the success would hide the failure (RF-12).
    latest = conn.execute("SELECT * FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()
    succeeded = conn.execute(
        "SELECT * FROM sync_runs WHERE status = 'ok' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return {
        "latest": dict(latest) if latest else None,
        "succeeded": dict(succeeded) if succeeded else None,
    }


def days_since(run: dict | None, today: date) -> int | None:
    if not run or not run["finished_at"]:
        return None
    return (today - datetime.fromisoformat(run["finished_at"]).date()).days


def main() -> int:
    today = reference_date()
    conn = connect()
    try:
        outcome = synchronise(conn, today=today)
    except MissingCredentialError as refusal:
        print(f"sync recusado: {refusal}", flush=True)
        return 1
    finally:
        conn.close()
    print(
        f"sync {outcome.status}: inserted={outcome.transactions} "
        f"accounts={outcome.accounts} reference={today.isoformat()}",
        flush=True,
    )
    return 0 if outcome.status == "ok" else 1
