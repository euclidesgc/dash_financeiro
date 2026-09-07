import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime

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
    try:
        transactions = load_transactions(config.transactions_path)
        accounts = load_accounts(config.accounts_glob)
    except (OSError, ValueError) as failure:
        # The source file not being there is the most likely accident of the day,
        # and it used to raise before any row reached sync_runs: the sync failed,
        # left no trace, and the screen went on announcing the last success
        # (RF-20).
        return _record_failure(conn, config.transactions_path, failure)
    result = ingest(
        conn,
        transactions=transactions,
        accounts=accounts,
        source=config.transactions_path,
    )
    if result.status != "ok":
        return _outcome(result)
    try:
        _after(conn, today or reference_date())
    except Exception as failure:
        # The ok row is already committed by the load. If the reclassification,
        # the commitment recomputation or the ladder rebuild blows up here, that
        # row goes on claiming success with the derived tables frozen — a lying
        # success, which is the opposite of what item 006 delivered (RF-21).
        return _demote(conn, result.run_id, failure)
    return _outcome(result)


def _demote(conn: sqlite3.Connection, run_id: int | None, failure: Exception) -> SyncOutcome:
    # The row of this run, named. Aiming at the largest id assumes nobody writes
    # in between, and that assumption has no owner.
    message = f"pós-carga falhou: {type(failure).__name__}"
    conn.execute(
        "UPDATE sync_runs SET status = 'failed', message = ? WHERE id = ?",
        (message, run_id),
    )
    conn.commit()
    return SyncOutcome(status="failed", message=message, transactions=0, accounts=0)


def _record_failure(conn: sqlite3.Connection, source: str, failure: Exception) -> SyncOutcome:
    now = datetime.now(UTC).isoformat()
    message = f"fonte ilegível: {type(failure).__name__}"
    conn.execute(
        "INSERT INTO sync_runs (started_at, finished_at, source, status, message) "
        "VALUES (?, ?, ?, 'failed', ?)",
        (now, now, source, message),
    )
    conn.commit()
    return SyncOutcome(status="failed", message=message, transactions=0, accounts=0)


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


def finished_on(run: dict | None) -> datetime | None:
    # Written in UTC and read against a local reference date. Without the
    # conversion a load run after nine at night shows tomorrow's date and the age
    # comes out a day short — the very number this item exists to make honest
    # (RF-19).
    if not run or not run["finished_at"]:
        return None
    stamp = datetime.fromisoformat(run["finished_at"])
    return stamp.astimezone() if stamp.tzinfo else stamp


def days_since(run: dict | None, today: date) -> int | None:
    when = finished_on(run)
    return None if when is None else (today - when.date()).days


_REJECTED = re.compile(r"rejected=(\d+)")
_PRESENT = re.compile(r"accepted=(\d+) present=(\d+)")
_WRITE = re.compile(r"erro de escrita: (\w+)")
_SOURCE = re.compile(r"fonte ilegível: (\w+)")
_AFTER = re.compile(r"pós-carga falhou: (\w+)")


def readable(message: str | None) -> str:
    # The loader speaks to the log, in English and in its own terms. The owner is
    # the one who has to decide what to do about the failure (RF-18).
    if not message:
        return "sem detalhe registrado."
    rejected = _REJECTED.search(message)
    if rejected:
        count = int(rejected.group(1))
        return f"a fonte trouxe {count} lançamento(s) que o painel não conseguiu ler."
    present = _PRESENT.search(message)
    if present:
        missing = int(present.group(1)) - int(present.group(2))
        return f"{missing} lançamento(s) aceito(s) não chegaram à tabela; nada foi gravado."
    write = _WRITE.search(message)
    if write:
        return f"a escrita no banco foi recusada ({write.group(1)}); nada foi gravado."
    after = _AFTER.search(message)
    if after:
        # Not "the screens show the previous state": the three steps commit as
        # they go, so a failure in the second or third leaves the base partly
        # updated. Promising more than the code delivers is the same defect this
        # item exists to kill, one sentence smaller.
        return (
            f"os lançamentos entraram, mas a classificação e os compromissos não foram "
            f"recalculados até o fim ({after.group(1)}). Parte das telas pode estar "
            "desatualizada; sincronize de novo."
        )
    unreadable = _SOURCE.search(message)
    if unreadable:
        return (
            f"o arquivo de origem não pôde ser lido ({unreadable.group(1)}). "
            "Rode o consolidador antes de sincronizar."
        )
    return message


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
