import unicodedata
from datetime import date

from app.settings.limits import NAME_MAX
from app.settings.typed import InvalidValueError, parse_money, parse_months, parse_rate

_REPLACEMENT_CHAR = "�"


def _has_illegible_byte(value: str) -> bool:
    # Motivo: app/offers/store.py writes with ON CONFLICT (name) DO UPDATE — the
    # name is the write key, and a byte the owner cannot retype is a row they
    # cannot overwrite.
    return _REPLACEMENT_CHAR in value or any(unicodedata.category(char) == "Cc" for char in value)


def read_form(typed: dict[str, str], *, today: date) -> dict:
    name = (typed.get("nome") or "").strip()
    if not name:
        raise InvalidValueError("Nome é obrigatório.")
    if len(name) > NAME_MAX:
        raise InvalidValueError(f"Nome muito longo: no máximo {NAME_MAX} caracteres.")
    if _has_illegible_byte(name):
        raise InvalidValueError(f"Nome com caractere ilegível: “{name}”.")
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
