import sqlite3

from app.accounts import CREDIT
from app.cards.catalog import BY_NAME, FIELDS
from app.cards.typed import parse
from app.settings.typed import InvalidValueError

_RECONCILE = "INSERT OR IGNORE INTO cards (account_id) SELECT id FROM accounts WHERE type = ?"
_READ = (
    "SELECT c.account_id, a.name, a.institution, a.balance_cents, "
    + ", ".join(f"c.{field['column']}" for field in FIELDS)
    + " FROM cards c JOIN accounts a ON a.id = c.account_id ORDER BY c.account_id"
)


def reconcile(conn: sqlite3.Connection) -> int:
    return conn.execute(_RECONCILE, (CREDIT,)).rowcount


def read(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(_READ).fetchall()
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


def entry(name: str) -> dict:
    item = BY_NAME.get(name)
    if item is None:
        raise InvalidValueError(f"Campo desconhecido: “{name}”.")
    return item


def write(conn: sqlite3.Connection, account_id: str, field: str, typed: str) -> int | None:
    item = entry(field)
    value = parse(item["unit"], typed, item["label"])
    try:
        conn.execute(
            f"INSERT INTO cards (account_id, {item['column']}) VALUES (?, ?) "
            f"ON CONFLICT(account_id) DO UPDATE SET {item['column']} = excluded.{item['column']}",
            (account_id, value),
        )
    except sqlite3.IntegrityError:
        # The FK on cards.account_id is the check: an id that names no account
        # fails here, and the owner sees the id back, not "FOREIGN KEY
        # constraint failed".
        raise InvalidValueError(f"Cartão não encontrado: “{account_id}”.") from None
    conn.commit()
    return value
