import json
import os
import sqlite3
from datetime import date
from pathlib import Path

from app.accounts import BANK, CREDIT
from app.cards import store
from app.cards.catalog import RATE
from app.db import connect
from app.settings.typed import parse_rate

OVERDRAFT = "overdraft"
CARD = "card"
MORTGAGE = "mortgage"
VEHICLE = "vehicle"

RATE_SCALE = 10000
BASIS_POINTS = 100
MONTHS_IN_YEAR = 12

MANUAL_DIR = "DASH_MANUAL_DIR"
DEFAULT_MANUAL = "data/manual"
MORTGAGE_FILE = "financiamento_caixa.json"
VEHICLE_FILE = "cdc_safra_veiculo.json"

_STEPS = (
    "SELECT d.id, d.kind, d.name, d.balance_cents, "
    "COALESCE(c.monthly_rate_bp, d.monthly_rate_bp) AS monthly_rate_bp, "
    "d.term_months, d.payment_cents, d.source, d.account_id "
    "FROM debts d LEFT JOIN cards c ON c.account_id = d.account_id"
)
_INSERT = (
    "INSERT OR REPLACE INTO debts "
    "(kind, name, balance_cents, monthly_rate_bp, term_months, payment_cents, source, account_id) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)


def manual_dir() -> Path:
    return Path(os.environ.get(MANUAL_DIR) or DEFAULT_MANUAL)


def rebuild(conn: sqlite3.Connection, *, today: date | None = None) -> int:
    store.reconcile(conn)
    # Wiped and rewritten, like the commitments: a half rebuilt ladder keeps
    # adding up and starts lying about where the next real earns most.
    rates = {
        (row["kind"], row["name"]): row["monthly_rate_bp"]
        for row in conn.execute("SELECT kind, name, monthly_rate_bp FROM debts")
    }
    conn.execute("DELETE FROM debts")
    rows = _from_accounts(conn) + _from_contracts(today or date.today())
    conn.executemany(
        _INSERT,
        [
            (
                row["kind"],
                row["name"],
                row["balance_cents"],
                # A rate the owner typed survives the reload: it is the one thing
                # on this screen that no source can produce again.
                rates.get((row["kind"], row["name"]), row["monthly_rate_bp"]),
                row["term_months"],
                row["payment_cents"],
                row["source"],
                row["account_id"],
            )
            for row in rows
        ],
    )
    conn.commit()
    return len(rows)


def _from_accounts(conn: sqlite3.Connection) -> list[dict]:
    # One step per account, not one per kind: the accounts have different limits
    # and different rates, and the rate is a field of the step.
    found = conn.execute(
        "SELECT id, name, type, balance_cents FROM accounts "
        "WHERE balance_cents < 0 AND type IN (?, ?) ORDER BY balance_cents",
        (BANK, CREDIT),
    )
    return [
        {
            "kind": OVERDRAFT if row["type"] == BANK else CARD,
            "name": row["name"],
            "balance_cents": row["balance_cents"],
            "monthly_rate_bp": None,
            "term_months": None,
            "payment_cents": None,
            "source": "accounts",
            "account_id": row["id"],
        }
        for row in found
    ]


def _from_contracts(today: date) -> list[dict]:
    rows = []
    mortgage = _read(MORTGAGE_FILE)
    if mortgage:
        rows.append(_mortgage(mortgage))
    vehicle = _read(VEHICLE_FILE)
    if vehicle:
        rows.append(_vehicle(vehicle, today))
    return rows


def _read(name: str) -> dict | None:
    # data/ lives outside version control, so the panel has to boot on a machine
    # that never received the contracts. A missing file is a missing step, never
    # a broken load (RF-05).
    path = manual_dir() / name
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def _mortgage(data: dict) -> dict:
    yearly = data["juros_efetivos_aa_pct"] / 100
    monthly = (1 + yearly) ** (1 / MONTHS_IN_YEAR) - 1
    return {
        "kind": MORTGAGE,
        "name": "Financiamento imobiliário",
        "balance_cents": -_cents(data["saldo_devedor"]),
        "monthly_rate_bp": round(monthly * RATE_SCALE),
        "term_months": data["prazo_restante_meses"],
        "payment_cents": None,
        "source": MORTGAGE_FILE,
        "account_id": None,
    }


def _vehicle(data: dict, today: date) -> dict:
    rate = data["juros_efetivo_mensal_pct"] / 100
    payment = data["valor_parcela"]
    left = data["prazo_meses"] - _paid(data, today)
    return {
        "kind": VEHICLE,
        "name": "CDC do veículo",
        # The balance of a Price loan is the present value of the instalments not
        # yet due, discounted at the contract rate: it is what the law makes the
        # bank offer on early settlement, and copying a figure would freeze it.
        "balance_cents": -round(payment * (1 - (1 + rate) ** -left) / rate * BASIS_POINTS),
        "monthly_rate_bp": round(rate * RATE_SCALE),
        "term_months": left,
        "payment_cents": -_cents(payment),
        "source": VEHICLE_FILE,
        "account_id": None,
    }


def _paid(data: dict, today: date) -> int:
    first = date.fromisoformat(data["primeiro_vencimento"])
    year, month, paid = first.year, first.month, 0
    for _ in range(data["prazo_meses"]):
        if date(year, month, first.day) <= today:
            paid += 1
        month += 1
        if month > MONTHS_IN_YEAR:
            month, year = 1, year + 1
    return paid


def _cents(value: float) -> int:
    return round(value * BASIS_POINTS)


def ladder(conn: sqlite3.Connection) -> list[dict]:
    return [
        dict(row)
        for row in conn.execute(
            f"SELECT * FROM ({_STEPS}) WHERE monthly_rate_bp IS NOT NULL "
            "ORDER BY monthly_rate_bp DESC, balance_cents"
        )
    ]


def without_rate(conn: sqlite3.Connection) -> list[dict]:
    # A step with no rate has no place on the ladder, and guessing one would be
    # the panel deciding what it does not know. It is shown apart, saying what is
    # missing (RF-08).
    return [
        dict(row)
        for row in conn.execute(
            f"SELECT * FROM ({_STEPS}) WHERE monthly_rate_bp IS NULL ORDER BY balance_cents"
        )
    ]


def step(conn: sqlite3.Connection, debt_id: int) -> dict | None:
    row = conn.execute(f"SELECT * FROM ({_STEPS}) WHERE id = ?", (debt_id,)).fetchone()
    return dict(row) if row else None


class DebtNotFoundError(LookupError):
    pass


def set_rate(conn: sqlite3.Connection, debt_id: int, typed: str) -> None:
    found = conn.execute("SELECT kind, account_id FROM debts WHERE id = ?", (debt_id,)).fetchone()
    if found is None:
        raise DebtNotFoundError("Dívida não encontrada.")
    if found["kind"] == CARD and found["account_id"] is not None:
        store.write(conn, found["account_id"], RATE, typed)
        return
    # A write that touches no row and answers 200 shows the owner a screen that
    # reloads as if it had saved.
    changed = conn.execute(
        "UPDATE debts SET monthly_rate_bp = ? WHERE id = ?", (parse_rate(typed), debt_id)
    ).rowcount
    if not changed:
        raise DebtNotFoundError("Dívida não encontrada.")
    conn.commit()


def monthly_interest_cents(row: dict) -> int:
    if row["monthly_rate_bp"] is None:
        return 0
    return -round(abs(row["balance_cents"]) * row["monthly_rate_bp"] / RATE_SCALE)


def main() -> int:
    from app.config import reference_date

    today = reference_date()
    conn = connect()
    try:
        written = rebuild(conn, today=today)
    finally:
        conn.close()
    print(f"debts rebuilt: {written} reference={today.isoformat()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
