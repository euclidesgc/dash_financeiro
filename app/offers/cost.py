import sqlite3
from typing import Any

from app.debts.ladder import ladder
from app.financings.money import RATE_SCALE
from app.offers.store import read_all


class InvalidCostInputError(ValueError):
    pass


def total_cost(
    released_cents: int,
    monthly_rate_bp: int,
    term_months: int,
    fee_cents: int = 0,
) -> int:
    # Invariant: with no route in front to block it first — the phase-2
    # comparison calls this function directly — a zero term divides by
    # zero and a negative rate returns a negative cost. The offer route
    # already refuses both; this function needs to refuse on its own too.
    if term_months <= 0:
        raise InvalidCostInputError("Prazo precisa ser maior que zero.")
    if monthly_rate_bp < 0:
        raise InvalidCostInputError("Taxa mensal não pode ser negativa.")
    if monthly_rate_bp == 0:
        return fee_cents
    rate = monthly_rate_bp / RATE_SCALE
    payment = round(released_cents * rate / (1 - (1 + rate) ** -term_months))
    return payment * term_months - released_cents + fee_cents


def compare(step: dict[str, Any] | None, offers: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    without_rate = []
    for offer in offers:
        if offer["monthly_rate_bp"] is None:
            without_rate.append(offer["name"])
            continue
        offer_cents = total_cost(
            offer["released_cents"],
            offer["monthly_rate_bp"],
            offer["term_months"],
            offer["fee_cents"],
        )
        stay_cents = None
        difference_cents = None
        cheaper = None
        if step is not None:
            # Decision: same amount released and same term as the offer,
            # at the current step's rate, and with no origination cost — it
            # is the only basis on which an overdraft, which has no
            # schedule of its own, has a cost to pay down to zero
            # (recorded in the plan as a gap in the brief).
            stay_cents = total_cost(
                offer["released_cents"], step["monthly_rate_bp"], offer["term_months"], 0
            )
            difference_cents = stay_cents - offer_cents
            cheaper = offer_cents < stay_cents
        rows.append(
            {
                "name": offer["name"],
                "monthly_rate_bp": offer["monthly_rate_bp"],
                "term_months": offer["term_months"],
                "released_cents": offer["released_cents"],
                "fee_cents": offer["fee_cents"],
                "offer_cents": offer_cents,
                "stay_cents": stay_cents,
                "difference_cents": difference_cents,
                "cheaper": cheaper,
            }
        )
    return {"step": step, "rows": rows, "without_rate": without_rate}


def comparison(conn: sqlite3.Connection) -> dict[str, Any]:
    steps = ladder(conn)
    return compare(steps[0] if steps else None, read_all(conn))
