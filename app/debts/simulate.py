from typing import Any, cast

from app.financings.money import RATE_SCALE
from app.settings.typed import InvalidValueError


class UnknownRateError(ValueError):
    pass


def simulate(debt: dict[str, Any], extra_cents: int) -> dict[str, Any]:
    if extra_cents <= 0:
        raise InvalidValueError("O aporte precisa ser maior que zero.")
    if not debt["monthly_rate_bp"]:
        # Answering R$ 0,00 here is not abstaining: it is the stronger claim that
        # the money saves nothing. The screen already says two sections above
        # that guessing a rate would be the panel deciding what it does not know.
        raise UnknownRateError(
            f"Sem a taxa de {debt['name']}, não dá para dizer o que o aporte economiza. "
            "Informe a taxa primeiro."
        )
    balance = abs(debt["balance_cents"])
    rate = (debt["monthly_rate_bp"] or 0) / RATE_SCALE
    if extra_cents >= balance:
        return _answer(
            debt,
            balance,
            debt["term_months"] or 0,
            _interest(debt, balance, rate),
            extra_cents - balance,
        )
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
    removed = left - remaining
    return _answer(debt, extra_cents, removed, removed * payment - extra_cents, 0)


def _months_for(present: int, payment: int, rate: float) -> int:
    months = 0
    owed: float = present
    while owed > 0 and months < _CEILING:
        owed = owed * (1 + rate) - payment
        months += 1
    return months


_CEILING = 1200


def _interest(debt: dict[str, Any], balance: int, rate: float) -> int:
    if debt["term_months"] and debt["payment_cents"]:
        return cast(int, debt["term_months"] * abs(debt["payment_cents"]) - balance)
    return round(balance * rate)


def _answer(
    debt: dict[str, Any], applied: int, instalments: int, interest: int, leftover: int
) -> dict[str, Any]:
    return {
        "debt_id": debt["id"],
        "name": debt["name"],
        "applied_cents": applied,
        "instalments_removed": instalments,
        "interest_saved_cents": max(interest, 0),
        "leftover_cents": leftover,
        "settles": leftover > 0 or applied >= abs(debt["balance_cents"]),
    }
