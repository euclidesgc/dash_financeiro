import math
import re

from app.settings.catalog import BASIS_POINTS, CENTS, MONTHS

# A ceiling, not a nicety: past three hundred digits float() returns inf and
# round(inf) raises, which is a 500 on a money field. Twelve digits is more money
# than this panel will ever be asked about.
MAX_DIGITS = 12
CENTS_IN_UNIT = 100
MAX_RATE_BP = 100 * CENTS_IN_UNIT

_MONEY = re.compile(r"^\d{1,3}(\.\d{3})*(,\d{1,2})?$|^\d+(,\d{1,2})?$")
_WHOLE = re.compile(r"^\d+$")


class InvalidValueError(ValueError):
    pass


def parse_money(typed: str, field: str = "Valor", *, allow_zero: bool = False) -> int:
    # Read strictly in the Brazilian form. Stripping every dot as a thousands
    # separator turned "5000.00" into five hundred thousand reais, accepted,
    # displayed and stored without a word — on a screen that decides money.
    cleaned = (typed or "").strip().replace("R$", "").replace(" ", "")
    if not cleaned and allow_zero:
        return 0
    if not _MONEY.match(cleaned) or len(cleaned.replace(".", "").replace(",", "")) > MAX_DIGITS:
        raise InvalidValueError(
            f"{field} inválido: “{typed}”. Escreva na forma 1.234,56, "
            f"com no máximo {MAX_DIGITS} algarismos."
        )
    units, _, decimals = cleaned.replace(".", "").partition(",")
    # Integer cents from integer parts: float would stop being exact long before
    # the ceiling above, and the invariant of this base is integer cents.
    cents = int(units or 0) * CENTS_IN_UNIT + int((decimals or "0").ljust(2, "0"))
    if cents == 0 and not allow_zero:
        raise InvalidValueError(f"{field} precisa ser maior que zero.")
    return cents


def parse_rate(typed: str, field: str = "Taxa") -> int | None:
    # A rate is written with a decimal point as often as with a comma, and it is
    # bounded above: the strict money grammar would refuse the dotted form and
    # accept a rate of two hundred per cent a month.
    cleaned = (typed or "").strip().replace("%", "").replace(",", ".")
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        raise InvalidValueError(f"{field} inválida: “{typed}”.") from None
    # nan compares false against every bound, so it walked through the range
    # check and died inside round() — an HTTP 500 on a rate field.
    if not math.isfinite(value):
        raise InvalidValueError(f"{field} inválida: “{typed}”.")
    if value < 0 or value * CENTS_IN_UNIT > MAX_RATE_BP:
        raise InvalidValueError(f"{field} fora da faixa: “{typed}”. Use de 0 a 100% ao mês.")
    return round(value * CENTS_IN_UNIT)


def parse_months(typed: str, field: str = "Prazo") -> int | None:
    cleaned = (typed or "").strip()
    if not cleaned:
        return None
    # Motivo: SQLite's INTEGER column overflows past nineteen digits, and
    # int() alone would pass a term straight through to that 500 — the same
    # failure parse_money already guards against, proven twice now: on the
    # offer's prazo and on the goal's reserve months.
    if not _WHOLE.match(cleaned) or len(cleaned) > MAX_DIGITS:
        raise InvalidValueError(
            f"{field} inválido: “{typed}”. Use um número inteiro de meses, "
            f"com no máximo {MAX_DIGITS} algarismos."
        )
    value = int(cleaned)
    if value <= 0:
        raise InvalidValueError(f"{field} precisa ser maior que zero.")
    return value


_READERS = {CENTS: parse_money, BASIS_POINTS: parse_rate, MONTHS: parse_months}


def parse(unit: str, typed: str, field: str) -> int | None:
    reader = _READERS.get(unit)
    if reader is None:
        raise InvalidValueError(f"Unidade desconhecida: “{unit}”.")
    return reader(typed, field)
