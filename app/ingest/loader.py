import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import InvalidOperation

from app.accounts import CREDIT
from app.ingest.money import FractionalCentsError, to_cents

# SQLite caps host parameters per statement, so the source is compared against
# the database in chunks instead of one IN clause holding every identifier.
_ID_CHUNK = 500

_ACCOUNT_COLUMNS = (
    "id",
    "name",
    "type",
    "subtype",
    "institution",
    "balance_cents",
    "updated_at",
)

_TRANSACTION_COLUMNS = (
    "pluggy_id",
    "account_id",
    "date",
    "description",
    "amount_cents",
    "type",
    "category_pluggy",
    "category",
    "installment_current",
    "installment_total",
    "is_transfer",
    "transfer_reason",
    "is_refund",
    "refunded_by",
    "is_cash_withdrawal",
)

_REQUIRED_TRANSACTION_FIELDS = (
    ("id", "missing_pluggy_id"),
    ("conta_id", "missing_account_id"),
    ("data", "missing_date"),
)


@dataclass(frozen=True)
class Rejection:
    index: int
    reason: str
    description: str


@dataclass(frozen=True)
class IngestResult:
    status: str
    message: str
    rejections: tuple[Rejection, ...]
    transactions_accepted: int
    transactions_written: int
    accounts_accepted: int
    accounts_written: int


def ingest(
    conn: sqlite3.Connection,
    *,
    transactions: list[dict],
    accounts: list[dict],
    source: str,
    now: datetime | None = None,
) -> IngestResult:
    started = now or datetime.now(UTC)
    account_rows, rejections = _map(accounts, _account_row)
    transaction_rows, transaction_rejections = _map(transactions, _transaction_row)
    rejections.extend(transaction_rejections)

    if rejections:
        message = f"rejected={len(rejections)}"
        return _fail(
            conn,
            started=started,
            now=now,
            source=source,
            message=message,
            rejections=tuple(rejections),
            transactions_accepted=len(transaction_rows),
            transactions_written=0,
            accounts_accepted=len(account_rows),
            accounts_written=0,
        )

    try:
        # Counted before the upsert: after it, everything is present, and
        # "how many rows are there" is not the same question as "how many
        # entered" (RF-01).
        accounts_before = _count_present(
            conn, "accounts", "id", [row["id"] for row in account_rows]
        )
        transactions_before = _count_present(
            conn, "transactions", "pluggy_id", [row["pluggy_id"] for row in transaction_rows]
        )
        conn.executemany(
            _upsert("accounts", _ACCOUNT_COLUMNS, "id"),
            [tuple(row[column] for column in _ACCOUNT_COLUMNS) for row in account_rows],
        )
        conn.executemany(
            _upsert("transactions", _TRANSACTION_COLUMNS, "pluggy_id"),
            [tuple(row[column] for column in _TRANSACTION_COLUMNS) for row in transaction_rows],
        )
        accounts_present = _count_present(
            conn, "accounts", "id", [row["id"] for row in account_rows]
        )
        transactions_present = _count_present(
            conn, "transactions", "pluggy_id", [row["pluggy_id"] for row in transaction_rows]
        )
        accounts_written = accounts_present - accounts_before
        transactions_written = transactions_present - transactions_before
    except Exception:
        conn.rollback()
        raise

    if transactions_present != len(transaction_rows) or accounts_present != len(account_rows):
        return _fail(
            conn,
            started=started,
            now=now,
            source=source,
            message=(
                f"transactions accepted={len(transaction_rows)} present={transactions_present} "
                f"accounts accepted={len(account_rows)} present={accounts_present}"
            ),
            rejections=(),
            transactions_accepted=len(transaction_rows),
            transactions_written=transactions_written,
            accounts_accepted=len(account_rows),
            accounts_written=accounts_written,
            transactions_present=transactions_present,
            accounts_present=accounts_present,
        )

    message = f"transactions={transactions_written} accounts={accounts_written}"
    _record_run(
        conn,
        started=started,
        finished=now or datetime.now(UTC),
        source=source,
        status="ok",
        transactions_count=transactions_written,
        accounts_count=accounts_written,
        transactions_present=transactions_present,
        accounts_present=accounts_present,
        message=message,
    )
    conn.commit()
    return IngestResult(
        status="ok",
        message=message,
        rejections=(),
        transactions_accepted=len(transaction_rows),
        transactions_written=transactions_written,
        accounts_accepted=len(account_rows),
        accounts_written=accounts_written,
    )


def _fail(
    conn: sqlite3.Connection,
    *,
    started: datetime,
    now: datetime | None,
    source: str,
    message: str,
    rejections: tuple[Rejection, ...],
    transactions_accepted: int,
    transactions_written: int,
    accounts_accepted: int,
    accounts_written: int,
    transactions_present: int = 0,
    accounts_present: int = 0,
) -> IngestResult:
    # The failure row has to outlive the rollback it describes, so it is written
    # after the rollback, in a transaction of its own.
    conn.rollback()
    _record_run(
        conn,
        started=started,
        finished=now or datetime.now(UTC),
        source=source,
        status="failed",
        transactions_count=transactions_written,
        accounts_count=accounts_written,
        transactions_present=transactions_present,
        accounts_present=accounts_present,
        message=message,
    )
    conn.commit()
    return IngestResult(
        status="failed",
        message=message,
        rejections=rejections,
        transactions_accepted=transactions_accepted,
        transactions_written=transactions_written,
        accounts_accepted=accounts_accepted,
        accounts_written=accounts_written,
    )


def _record_run(
    conn: sqlite3.Connection,
    *,
    started: datetime,
    finished: datetime,
    source: str,
    status: str,
    transactions_count: int,
    accounts_count: int,
    transactions_present: int,
    accounts_present: int,
    message: str,
) -> None:
    conn.execute(
        "INSERT INTO sync_runs (started_at, finished_at, source, status, transactions_count, "
        "accounts_count, transactions_present, accounts_present, message) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            started.isoformat(),
            finished.isoformat(),
            source,
            status,
            transactions_count,
            accounts_count,
            transactions_present,
            accounts_present,
            message,
        ),
    )


def _map(rows: list[dict], mapper) -> tuple[list[dict], list[Rejection]]:
    mapped: list[dict] = []
    rejections: list[Rejection] = []
    for index, raw in enumerate(rows):
        row, rejection = mapper(index, raw)
        if rejection is not None:
            rejections.append(rejection)
        else:
            mapped.append(row)
    return mapped, rejections


def _account_row(index: int, raw: dict) -> tuple[dict | None, Rejection | None]:
    label = str(raw.get("name") or "")
    if not raw.get("id"):
        return None, Rejection(index, "missing_account_id", label)
    if raw.get("balance") is None:
        return None, Rejection(index, "missing_balance", label)
    try:
        balance = to_cents(raw["balance"])
    except FractionalCentsError:
        return None, Rejection(index, "fractional_cents", label)
    except InvalidOperation:
        return None, Rejection(index, "invalid_balance", label)
    # Pluggy reports a card balance as a positive number, and a card balance is
    # debt: negative is money leaving, in any kind of account (invariant 22).
    if raw.get("type") == CREDIT:
        balance = -balance
    return {
        "id": raw["id"],
        "name": raw.get("name"),
        "type": raw.get("type"),
        "subtype": raw.get("subtype"),
        "institution": raw.get("marketingName") or raw.get("institutionName") or raw.get("name"),
        "balance_cents": balance,
        "updated_at": raw.get("updatedAt"),
    }, None


def _transaction_row(index: int, raw: dict) -> tuple[dict | None, Rejection | None]:
    label = str(raw.get("descricao") or "")
    for field, reason in _REQUIRED_TRANSACTION_FIELDS:
        if not raw.get(field):
            return None, Rejection(index, reason, label)
    if raw.get("valor") is None:
        return None, Rejection(index, "missing_amount", label)
    try:
        # The consolidator already flipped the sign for credit cards; flipping it
        # again here would turn a card purchase into income (invariant 22).
        amount = to_cents(raw["valor"])
    except FractionalCentsError:
        return None, Rejection(index, "fractional_cents", label)
    except InvalidOperation:
        return None, Rejection(index, "invalid_amount", label)
    return {
        "pluggy_id": raw["id"],
        "account_id": raw["conta_id"],
        "date": raw["data"],
        "description": raw.get("descricao"),
        "amount_cents": amount,
        "type": raw.get("tipo"),
        "category_pluggy": raw.get("categoria_pluggy"),
        "category": raw.get("categoria"),
        "installment_current": raw.get("parcela_atual"),
        "installment_total": raw.get("parcela_total"),
        "is_transfer": int(bool(raw.get("eh_transferencia"))),
        "transfer_reason": raw.get("motivo_transferencia") or "",
        "is_refund": int(bool(raw.get("eh_estorno"))),
        "refunded_by": raw.get("estornada_por") or None,
        "is_cash_withdrawal": int(bool(raw.get("eh_saque"))),
    }, None


def _upsert(table: str, columns: tuple[str, ...], key: str) -> str:
    placeholders = ", ".join("?" * len(columns))
    updates = ", ".join(f"{column} = excluded.{column}" for column in columns if column != key)
    return (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT({key}) DO UPDATE SET {updates}"
    )


def _count_present(conn: sqlite3.Connection, table: str, key: str, values: list[str]) -> int:
    unique = list(dict.fromkeys(values))
    total = 0
    for start in range(0, len(unique), _ID_CHUNK):
        chunk = unique[start : start + _ID_CHUNK]
        placeholders = ", ".join("?" * len(chunk))
        total += conn.execute(
            f"SELECT count(*) FROM {table} WHERE {key} IN ({placeholders})", chunk
        ).fetchone()[0]
    return total
