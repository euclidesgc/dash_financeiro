import re

# Limitation: the grammar only recognises "R$" followed by a value and a
# number followed by "%" — a bare integer like "24" is not flagged. A
# wider grammar would flag "2026" and turn the guard into noise someone
# switches off in the first week (norm 23).
#
# Reason: the space and the decimal places are optional because the
# grammar that required "R$ " and exactly two decimal places did not
# recognise "R$987.654,32" or "R$ 202,4" as a figure at all — and what it
# does not recognise, it lets through. The guard failed open precisely on
# the forms a model varies on its own.
_MONEY = re.compile(r"R\$\s*\d+(?:\.\d{3})*(?:,\d{1,2})?")
_PERCENT = re.compile(r"\d+(?:,\d+)?\s*%")

CENTS_IN_UNIT = 100


def figures(text: str) -> list[str]:
    return _MONEY.findall(text) + _PERCENT.findall(text)


def _as_cents(figure: str) -> int:
    digits = figure.replace("R$", "").strip().replace(".", "")
    units, _, decimals = digits.partition(",")
    return int(units or 0) * CENTS_IN_UNIT + int((decimals or "0").ljust(2, "0"))


def _canonical(figure: str) -> tuple[str, str]:
    if "%" in figure:
        units, _, decimals = figure.replace("%", "").strip().partition(",")
        return ("%", f"{int(units)}.{decimals.rstrip('0') or '0'}")
    return ("R$", str(_as_cents(figure)))


def uncited(reading: str, context: str) -> list[str]:
    # Decision: the comparison is by the number, not by how it is written.
    # A figure rewritten — with no space, no thousands dot, one decimal
    # place instead of two — is the same figure, and discarding it would be
    # refusing a correct reading. A figure the context does not contain is
    # still flagged, whatever form the model wrote it in.
    seen = {_canonical(figure) for figure in figures(context)}
    return [figure for figure in figures(reading) if _canonical(figure) not in seen]
