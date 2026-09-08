import json
import os
import sqlite3
from datetime import date
from pathlib import Path

from app.financings import KINDS, MORTGAGE, NAMES, VEHICLE
from app.financings.math import monthly_from_yearly_bp, present_value_cents, remaining_months
from app.financings.money import CENTS_IN_UNIT
from app.financings.typed import read_form

MANUAL_DIR = "DASH_MANUAL_DIR"
DEFAULT_MANUAL = "data/manual"
MORTGAGE_FILE = "financiamento_caixa.json"
VEHICLE_FILE = "cdc_safra_veiculo.json"

_COLUMNS = "kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date"
_VALUES = ":kind, :monthly_rate_bp, :term_months, :balance_cents, :payment_cents, :first_due_date"
_INSERT = f"INSERT OR IGNORE INTO financings ({_COLUMNS}) VALUES ({_VALUES})"
_UPSERT = f"INSERT OR REPLACE INTO financings ({_COLUMNS}) VALUES ({_VALUES})"


def manual_dir() -> Path:
    return Path(os.environ.get(MANUAL_DIR) or DEFAULT_MANUAL)


def read_all(conn: sqlite3.Connection) -> list[dict]:
    return [dict(row) for row in conn.execute(f"SELECT {_COLUMNS} FROM financings")]


def read(conn: sqlite3.Connection, kind: str) -> dict | None:
    row = conn.execute(f"SELECT {_COLUMNS} FROM financings WHERE kind = ?", (kind,)).fetchone()
    return dict(row) if row else None


def seed_from_manual(conn: sqlite3.Connection) -> int:
    # A non-empty table is a machine that already imported: the disk is not
    # opened again, and a contract removed after import cannot un-import.
    count = conn.execute("SELECT COUNT(*) FROM financings").fetchone()[0]
    if count > 0:
        return 0
    seeded = 0
    mortgage = _read(MORTGAGE_FILE)
    if mortgage:
        conn.execute(_INSERT, _mortgage_row(mortgage))
        seeded += 1
    vehicle = _read(VEHICLE_FILE)
    if vehicle:
        conn.execute(_INSERT, _vehicle_row(vehicle))
        seeded += 1
    if seeded:
        conn.commit()
    return seeded


def _read(name: str) -> dict | None:
    # data/ lives outside version control, so the panel has to boot on a
    # machine that never received the contracts. A missing file is a missing
    # financing, never a broken load (RF-04).
    path = manual_dir() / name
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def _mortgage_row(data: dict) -> dict:
    return {
        "kind": MORTGAGE,
        "monthly_rate_bp": monthly_from_yearly_bp(data["juros_efetivos_aa_pct"]),
        "term_months": data["prazo_restante_meses"],
        "balance_cents": -round(data["saldo_devedor"] * CENTS_IN_UNIT),
        "payment_cents": None,
        "first_due_date": None,
    }


def _vehicle_row(data: dict) -> dict:
    return {
        "kind": VEHICLE,
        "monthly_rate_bp": round(data["juros_efetivo_mensal_pct"] * CENTS_IN_UNIT),
        "term_months": data["prazo_meses"],
        "balance_cents": None,
        "payment_cents": -round(data["valor_parcela"] * CENTS_IN_UNIT),
        "first_due_date": data["primeiro_vencimento"],
    }


def write(conn: sqlite3.Connection, kind: str, typed: dict[str, str]) -> None:
    row = read_form(kind, typed)
    conn.execute(_UPSERT, row)
    conn.commit()


def section(conn: sqlite3.Connection, *, today: date) -> dict:
    rows = {row["kind"]: row for row in read_all(conn)}
    result: dict[str, dict] = {}
    for kind in KINDS:
        row = rows.get(kind)
        entry = {
            "label": NAMES[kind],
            "monthly_rate_bp": row["monthly_rate_bp"] if row else None,
            "term_months": row["term_months"] if row else None,
            "balance_cents": row["balance_cents"] if row else None,
            "payment_cents": row["payment_cents"] if row else None,
            "first_due_date": row["first_due_date"] if row else None,
        }
        if kind == VEHICLE:
            entry["remaining_months"], entry["balance_cents"] = _vehicle_balance(row, today)
        result[kind] = entry
    return result


def _vehicle_balance(row: dict | None, today: date) -> tuple[int | None, int | None]:
    if row is None or row["first_due_date"] is None:
        return None, None
    first_due = date.fromisoformat(row["first_due_date"])
    left = remaining_months(first_due, row["term_months"], today)
    if left <= 0:
        return left, None
    return left, present_value_cents(row["payment_cents"], row["monthly_rate_bp"], left)
