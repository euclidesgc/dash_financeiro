import sqlite3
from typing import Any

from app.debts.ladder import RATE_SCALE

BASIS_POINTS = 100


class InvalidAmountError(ValueError):
    pass


def simulate(debt: dict, extra_cents: int) -> dict[str, Any]:
    if extra_cents <= 0:
        raise InvalidAmountError("O aporte precisa ser maior que zero.")
    balance = abs(debt["balance_cents"])
    rate = (debt["monthly_rate_bp"] or 0) / RATE_SCALE
    if extra_cents >= balance:
        return _answer(debt, balance, debt["term_months"] or 0, _interest(debt, balance, rate), extra_cents - balance)
    if not debt["term_months"] or not debt["payment_cents"] or rate <= 0:
        # No term means no instalment to remove: an overdraft and a revolving
        # card are charged for as long as the balance is there, so the only true
        # answer is the interest the money stops costing every month (RF-17).
        return _answer(debt, extra_cents, 0, round(extra_cents * rate), 0)
    payment = abs(debt["payment_cents"])
    left = debt["term_months"]
    # The instalments that vanish are the last ones of the schedule, and each of
    # them carries a different amount of interest: dividing the extra payment by
    # the instalment would answer with a number that is never right.
    remaining = _months_for(balance - extra_cents, payment, rate)
    return _answer(debt, extra_cents, left - remaining, (left - remaining) * payment - extra_cents, 0)


def _months_for(present: int, payment: int, rate: float) -> int:
    months = 0
    owed = present
    while owed > 0 and months < _CEILING:
        owed = owed * (1 + rate) - payment
        months += 1
    return months


_CEILING = 1200


def _interest(debt: dict, balance: int, rate: float) -> int:
    if debt["term_months"] and debt["payment_cents"]:
        return debt["term_months"] * abs(debt["payment_cents"]) - balance
    return round(balance * rate)


def _answer(debt: dict, applied: int, instalments: int, interest: int, leftover: int) -> dict[str, Any]:
    return {
        "debt_id": debt["id"],
        "name": debt["name"],
        "applied_cents": applied,
        "instalments_removed": instalments,
        "interest_saved_cents": max(interest, 0),
        "leftover_cents": leftover,
        "settles": leftover > 0 or applied >= abs(debt["balance_cents"]),
    }


def parse_amount(typed: str) -> int:
    cleaned = (typed or "").strip().replace("R$", "").replace(".", "").replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        raise InvalidAmountError(f"Aporte inválido: {typed!r}.") from None
    if value <= 0:
        raise InvalidAmountError("O aporte precisa ser maior que zero.")
    return round(value * BASIS_POINTS)


def parameter(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute("SELECT value_cents FROM plan_parameters WHERE name = ?", (name,)).fetchone()
    return row["value_cents"] if row else None
