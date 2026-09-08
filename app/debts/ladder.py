import sqlite3
from datetime import date
from typing import Any

from app.accounts import BANK, CREDIT
from app.cards import store
from app.cards.catalog import RATE
from app.db import connect
from app.financings import MORTGAGE, NAMES, VEHICLE
from app.financings import store as financings_store
from app.financings.math import present_value_cents, remaining_months
from app.financings.money import RATE_SCALE
from app.settings.typed import parse_rate

OVERDRAFT = "overdraft"
CARD = "card"

_STEPS = (
    "SELECT d.id, d.kind, d.name, d.balance_cents, "
    "COALESCE(c.monthly_rate_bp, d.monthly_rate_bp) AS monthly_rate_bp, "
    "d.term_months, d.payment_cents, d.source, d.account_id "
    "FROM debts d LEFT JOIN cards c ON c.account_id = d.account_id AND d.kind = 'card'"
)
_INSERT = (
    "INSERT OR REPLACE INTO debts "
    "(kind, name, balance_cents, monthly_rate_bp, term_months, payment_cents, source, account_id) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)


def rebuild(conn: sqlite3.Connection, *, today: date | None = None) -> int:
    store.reconcile(conn)
    # Wiped and rewritten, like the commitments: a half rebuilt ladder keeps
    # adding up and starts lying about where the next real earns most.
    rates = {
        (row["kind"], row["name"]): row["monthly_rate_bp"]
        for row in conn.execute("SELECT kind, name, monthly_rate_bp FROM debts")
    }
    conn.execute("DELETE FROM debts")
    rows = _from_accounts(conn) + _from_financings(conn, today or date.today())
    conn.executemany(
        _INSERT,
        [
            (
                row["kind"],
                row["name"],
                row["balance_cents"],
                # A rate the owner typed only survives the reload when nothing
                # recomputed one: a financing's rate always comes back from its
                # own row, and only a step no source reproduces — an overdraft,
                # a card — falls back to what was there.
                row["monthly_rate_bp"]
                if row["monthly_rate_bp"] is not None
                else rates.get((row["kind"], row["name"])),
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


def _from_accounts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
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


def _from_financings(conn: sqlite3.Connection, today: date) -> list[dict[str, Any]]:
    financings_store.seed_from_manual(conn)
    rows = []
    for row in financings_store.read_all(conn):
        if row["kind"] == MORTGAGE:
            rows.append(
                {
                    "kind": MORTGAGE,
                    "name": NAMES[MORTGAGE],
                    "balance_cents": row["balance_cents"],
                    "monthly_rate_bp": row["monthly_rate_bp"],
                    "term_months": row["term_months"],
                    "payment_cents": None,
                    "source": "financings",
                    "account_id": None,
                }
            )
        elif row["kind"] == VEHICLE:
            first_due = date.fromisoformat(row["first_due_date"])
            left = remaining_months(first_due, row["term_months"], today)
            if left <= 0:
                # Every instalment due settles the contract: it is not a step
                # with a balance of inverted sign (invariant 22).
                continue
            rows.append(
                {
                    "kind": VEHICLE,
                    "name": NAMES[VEHICLE],
                    # The balance of a Price loan is the present value of the
                    # instalments not yet due, discounted at the contract rate:
                    # it is what the law makes the bank offer on early
                    # settlement, and copying a figure would freeze it.
                    "balance_cents": present_value_cents(
                        row["payment_cents"], row["monthly_rate_bp"], left
                    ),
                    "monthly_rate_bp": row["monthly_rate_bp"],
                    "term_months": left,
                    "payment_cents": row["payment_cents"],
                    "source": "financings",
                    "account_id": None,
                }
            )
    return rows


def ladder(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in conn.execute(
            f"SELECT * FROM ({_STEPS}) WHERE monthly_rate_bp IS NOT NULL "
            "ORDER BY monthly_rate_bp DESC, balance_cents"
        )
    ]


def without_rate(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    # A step with no rate has no place on the ladder, and guessing one would be
    # the panel deciding what it does not know. It is shown apart, saying what is
    # missing (RF-08).
    return [
        dict(row)
        for row in conn.execute(
            f"SELECT * FROM ({_STEPS}) WHERE monthly_rate_bp IS NULL ORDER BY balance_cents"
        )
    ]


def step(conn: sqlite3.Connection, debt_id: int) -> dict[str, Any] | None:
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


def monthly_interest_cents(row: dict[str, Any]) -> int:
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
