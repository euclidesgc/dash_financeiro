import re

from app.cards.catalog import DAY
from app.settings.catalog import BASIS_POINTS, CENTS
from app.settings.limits import MAX_DAY, MIN_DAY
from app.settings.typed import InvalidValueError, parse_money, parse_rate

_WHOLE = re.compile(r"^\d+$")


def parse_day(typed: str, field: str = "Dia") -> int | None:
    cleaned = (typed or "").strip()
    if not cleaned:
        return None
    if not _WHOLE.match(cleaned) or not (MIN_DAY <= int(cleaned) <= MAX_DAY):
        raise InvalidValueError(f"{field} inválido: “{typed}”. Use um dia do mês, de 1 a 31.")
    return int(cleaned)


_READERS = {CENTS: parse_money, BASIS_POINTS: parse_rate, DAY: parse_day}


def parse(unit: str, typed: str, field: str) -> int | None:
    if not (typed or "").strip():
        return None
    reader = _READERS.get(unit)
    if reader is None:
        raise InvalidValueError(f"Unidade desconhecida: “{unit}”.")
    return reader(typed, field)
