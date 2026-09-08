import sqlite3
from typing import Any

from app.accounts import CREDIT
from app.cards.catalog import ACTION, BY_NAME, CLEAR_ACTION, FIELDS
from app.cards.typed import parse
from app.settings.typed import InvalidValueError

_RECONCILE = "INSERT OR IGNORE INTO cards (account_id) SELECT id FROM accounts WHERE type = ?"
_READ = (
    "SELECT c.account_id, a.name, a.institution, a.balance_cents, "
    + ", ".join(f"c.{field['column']}" for field in FIELDS)
    + " FROM cards c JOIN accounts a ON a.id = c.account_id WHERE a.type = ? ORDER BY c.account_id"
)
_ACCOUNT_TYPE = "SELECT type FROM accounts WHERE id = ?"


def reconcile(conn: sqlite3.Connection) -> int:
    return conn.execute(_RECONCILE, (CREDIT,)).rowcount


def screen(conn: sqlite3.Connection) -> dict[str, Any]:
    return {"action": ACTION, "clear_action": CLEAR_ACTION, "cards": read(conn)}


def read(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(_READ, (CREDIT,)).fetchall()
    return [
        {
            "account_id": row["account_id"],
            "name": row["name"],
            "institution": row["institution"],
            "balance_cents": row["balance_cents"],
            "fields": [
                {
                    "name": field["name"],
                    "label": field["label"],
                    "unit": field["unit"],
                    "value": row[field["column"]],
                }
                for field in FIELDS
            ],
        }
        for row in rows
    ]


def entry(name: str) -> dict[str, Any]:
    item = BY_NAME.get(name)
    if item is None:
        raise InvalidValueError(f"Campo desconhecido: “{name}”.")
    return item


def _refuse_unless_credit_account(conn: sqlite3.Connection, account_id: str) -> None:
    row = conn.execute(_ACCOUNT_TYPE, (account_id,)).fetchone()
    if row is None or row["type"] != CREDIT:
        raise InvalidValueError(f"Cartão não encontrado: “{account_id}”.")


def _upsert(conn: sqlite3.Connection, account_id: str, column: str, value: int | None) -> None:
    conn.execute(
        f"INSERT INTO cards (account_id, {column}) VALUES (?, ?) "
        f"ON CONFLICT(account_id) DO UPDATE SET {column} = excluded.{column}",
        (account_id, value),
    )
    conn.commit()


def write(
    conn: sqlite3.Connection, account_id: str, field: str, typed: str
) -> tuple[int | None, bool]:
    item = entry(field)
    _refuse_unless_credit_account(conn, account_id)
    # Decisão: a blank field means "leave it alone" (RF-01), never "erase it";
    # the erase gesture is the only path that writes NULL from here on.
    if not (typed or "").strip():
        return None, False
    value = parse(item["unit"], typed, item["label"])
    if value is None:
        raise InvalidValueError(f"{item['label']} inválido: “{typed}”.")
    _upsert(conn, account_id, item["column"], value)
    return value, True


def erase(conn: sqlite3.Connection, account_id: str, field: str) -> dict[str, Any]:
    item = entry(field)
    _refuse_unless_credit_account(conn, account_id)
    _upsert(conn, account_id, item["column"], None)
    return item
