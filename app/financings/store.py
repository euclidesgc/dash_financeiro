import json
import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any, cast

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
_UPDATE_SET = (
    "monthly_rate_bp = excluded.monthly_rate_bp, term_months = excluded.term_months, "
    "balance_cents = excluded.balance_cents, payment_cents = excluded.payment_cents, "
    "first_due_date = excluded.first_due_date"
)
# A true UPDATE on conflict, not INSERT OR REPLACE: the latter deletes and
# reinserts the row, which moves it to the end of the table and reshuffles
# every id the ladder assigns by insertion order on the next rebuild.
_UPSERT = (
    f"INSERT INTO financings ({_COLUMNS}) VALUES ({_VALUES}) "
    f"ON CONFLICT (kind) DO UPDATE SET {_UPDATE_SET}"
)


def manual_dir() -> Path:
    return Path(os.environ.get(MANUAL_DIR) or DEFAULT_MANUAL)


def read_all(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(f"SELECT {_COLUMNS} FROM financings")]


def read(conn: sqlite3.Connection, kind: str) -> dict[str, Any] | None:
    row = conn.execute(f"SELECT {_COLUMNS} FROM financings WHERE kind = ?", (kind,)).fetchone()
    return dict(row) if row else None


def seed_from_manual(conn: sqlite3.Connection) -> int:
    # Decisão: o guarda é por tipo de contrato, não por a tabela estar vazia.
    # Contando a tabela inteira, a primeira gravação de um financiamento pela
    # tela dava a importação por encerrada e o outro contrato nunca mais era
    # semeado — o degrau sumia da escada de dívidas sem uma palavra. Quem já
    # está na tabela continua intocado, que é a razão original do guarda.
    present = {row[0] for row in conn.execute("SELECT kind FROM financings")}
    seeded = 0
    for kind, path, to_row in (
        (MORTGAGE, MORTGAGE_FILE, _mortgage_row),
        (VEHICLE, VEHICLE_FILE, _vehicle_row),
    ):
        if kind in present:
            continue
        contract = _read(path)
        if contract:
            conn.execute(_INSERT, to_row(contract))
            seeded += 1
    if seeded:
        conn.commit()
    return seeded


def _read(name: str) -> dict[str, Any] | None:
    # data/ lives outside version control, so the panel has to boot on a
    # machine that never received the contracts. A missing file is a missing
    # financing, never a broken load (RF-04).
    path = manual_dir() / name
    if not path.is_file():
        return None
    return cast(dict[str, Any], json.loads(path.read_text()))


def _mortgage_row(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": MORTGAGE,
        "monthly_rate_bp": monthly_from_yearly_bp(data["juros_efetivos_aa_pct"]),
        "term_months": data["prazo_restante_meses"],
        "balance_cents": -round(data["saldo_devedor"] * CENTS_IN_UNIT),
        "payment_cents": None,
        "first_due_date": None,
    }


def _vehicle_row(data: dict[str, Any]) -> dict[str, Any]:
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


def section(conn: sqlite3.Connection, *, today: date) -> dict[str, Any]:
    rows = {row["kind"]: row for row in read_all(conn)}
    result: dict[str, dict[str, Any]] = {}
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


def _vehicle_balance(row: dict[str, Any] | None, today: date) -> tuple[int | None, int | None]:
    if row is None or row["first_due_date"] is None:
        return None, None
    first_due = date.fromisoformat(row["first_due_date"])
    left = remaining_months(first_due, row["term_months"], today)
    if left <= 0:
        return left, None
    return left, present_value_cents(row["payment_cents"], row["monthly_rate_bp"], left)
