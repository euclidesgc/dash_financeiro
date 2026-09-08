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
    # Invariante: sem rota na frente para barrar antes — a comparação da fase
    # 2 chama esta função direto —, prazo zero divide por zero e taxa negativa
    # devolve custo negativo. A rota de proposta já recusa os dois; esta função
    # precisa recusar sozinha também.
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
            # Decisão: mesmo valor liberado e mesmo prazo da proposta, à taxa do
            # degrau atual, e sem custo de contratação — é a única base em que um
            # cheque especial, que não tem cronograma próprio, tem custo até
            # zerar (registrado no plano como lacuna do brief).
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
