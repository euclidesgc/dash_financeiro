from datetime import date

from app.settings.typed import InvalidValueError, parse_money, parse_months, parse_rate

NAME_MAX = 60


def read_form(typed: dict[str, str], *, today: date) -> dict:
    name = (typed.get("nome") or "").strip()
    if not name:
        raise InvalidValueError("Nome é obrigatório.")
    if len(name) > NAME_MAX:
        raise InvalidValueError(f"Nome muito longo: no máximo {NAME_MAX} caracteres.")
    rate = parse_rate(typed.get("taxa", ""), "Taxa mensal")
    term = parse_months(typed.get("prazo", ""), "Prazo em meses")
    if term is None:
        raise InvalidValueError("Prazo em meses é obrigatório.")
    released = parse_money(typed.get("liberado", ""), "Valor liberado")
    fee = parse_money(typed.get("contratacao", ""), "Custo de contratação", allow_zero=True)
    return {
        "name": name,
        "monthly_rate_bp": rate,
        "term_months": term,
        "released_cents": released,
        "fee_cents": fee,
        "captured_at": today.isoformat(),
    }
