import sqlite3
from datetime import date

from app.offers.typed import read_form

_COLUMNS = "name, monthly_rate_bp, term_months, released_cents, fee_cents, captured_at"
_VALUES = ":name, :monthly_rate_bp, :term_months, :released_cents, :fee_cents, :captured_at"
_UPDATE_SET = (
    "monthly_rate_bp = excluded.monthly_rate_bp, term_months = excluded.term_months, "
    "released_cents = excluded.released_cents, fee_cents = excluded.fee_cents, "
    "captured_at = excluded.captured_at"
)
_UPSERT = (
    f"INSERT INTO offers ({_COLUMNS}) VALUES ({_VALUES}) "
    f"ON CONFLICT (name) DO UPDATE SET {_UPDATE_SET}"
)

ACTION = "/configuracao/proposta"
REMOVE_ACTION = f"{ACTION}/remover"


def read_all(conn: sqlite3.Connection) -> list[dict]:
    return [dict(row) for row in conn.execute(f"SELECT {_COLUMNS} FROM offers ORDER BY id")]


def write(conn: sqlite3.Connection, typed: dict[str, str], *, today: date) -> None:
    row = read_form(typed, today=today)
    conn.execute(_UPSERT, row)
    conn.commit()


def remove(conn: sqlite3.Connection, name: str) -> None:
    conn.execute("DELETE FROM offers WHERE name = ?", (name,))
    conn.commit()


def section(conn: sqlite3.Connection) -> dict:
    return {"action": ACTION, "remove_action": REMOVE_ACTION, "offers": read_all(conn)}
