from datetime import date
from typing import Any

from app.financings import KINDS, MORTGAGE, VEHICLE
from app.settings.limits import MORTGAGE_MAX_RATE_BP, VEHICLE_MAX_RATE_BP
from app.settings.typed import (
    CENTS_IN_UNIT,
    InvalidValueError,
    parse_money,
    parse_months,
    parse_rate,
)

_RATE_CEILINGS = {MORTGAGE: MORTGAGE_MAX_RATE_BP, VEHICLE: VEHICLE_MAX_RATE_BP}


def parse_due_date(typed: str, field: str = "Primeiro vencimento") -> date:
    cleaned = (typed or "").strip()
    try:
        return date.fromisoformat(cleaned)
    except ValueError:
        raise InvalidValueError(f"{field} inválido: “{typed}”. Use a forma AAAA-MM-DD.") from None


def read_form(kind: str, typed: dict[str, str]) -> dict[str, Any]:
    if kind not in KINDS:
        raise InvalidValueError(f"Tipo de financiamento desconhecido: “{kind}”.")
    rate = parse_rate(typed.get("taxa", ""), "Taxa mensal")
    if rate is None:
        raise InvalidValueError("Taxa mensal é obrigatória.")
    if rate == 0:
        raise InvalidValueError("Taxa mensal precisa ser maior que zero.")
    ceiling = _RATE_CEILINGS[kind]
    if rate > ceiling:
        raise InvalidValueError(
            f"Taxa mensal fora da faixa: “{typed.get('taxa', '')}”. Use no máximo "
            f"{ceiling / CENTS_IN_UNIT:g}% ao mês."
        )
    term = parse_months(typed.get("prazo", ""), "Prazo em meses")
    if term is None:
        raise InvalidValueError("Prazo em meses é obrigatório.")
    if kind == MORTGAGE:
        balance = parse_money(typed.get("saldo", ""), "Saldo devedor")
        return {
            "kind": kind,
            "monthly_rate_bp": rate,
            "term_months": term,
            "balance_cents": -balance,
            "payment_cents": None,
            "first_due_date": None,
        }
    payment = parse_money(typed.get("parcela", ""), "Valor da parcela")
    due = parse_due_date(typed.get("vencimento", ""))
    return {
        "kind": kind,
        "monthly_rate_bp": rate,
        "term_months": term,
        "balance_cents": None,
        "payment_cents": -payment,
        "first_due_date": due.isoformat(),
    }
