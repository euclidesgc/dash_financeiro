import json
import os
import sqlite3
from pathlib import Path

from app.financings import MORTGAGE, VEHICLE
from app.financings.math import monthly_from_yearly_bp
from app.financings.money import CENTS_IN_UNIT

MANUAL_DIR = "DASH_MANUAL_DIR"
DEFAULT_MANUAL = "data/manual"
MORTGAGE_FILE = "financiamento_caixa.json"
VEHICLE_FILE = "cdc_safra_veiculo.json"

_COLUMNS = "kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date"
_INSERT = (
    "INSERT OR IGNORE INTO financings "
    f"({_COLUMNS}) VALUES "
    "(:kind, :monthly_rate_bp, :term_months, :balance_cents, :payment_cents, :first_due_date)"
)


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
