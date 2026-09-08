from datetime import date
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.settings.catalog import BASIS_POINTS, CENTS, MONTHS

TEMPLATES_FOLDER = Path(__file__).resolve().parents[1] / "templates"

TEMPLATES = Jinja2Templates(directory=str(TEMPLATES_FOLDER))

# U+2212, the mathematical minus. Colour is never the only sign a value is an
# outflow, so the glyph travels glued to the figure in every screen.
MINUS = "−"

CENTS_IN_REAL = 100


def brl(cents: int | None) -> str:
    value = cents or 0
    units, remainder = divmod(abs(value), CENTS_IN_REAL)
    grouped = f"{units:,}".replace(",", ".")
    return f"{MINUS if value < 0 else ''}R$ {grouped},{remainder:02d}"


def day(value: object) -> str:
    try:
        return date.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)


def month(value: object) -> str:
    try:
        return date.fromisoformat(f"{value}-01").strftime("%m/%Y")
    except ValueError:
        return str(value)


def rate(basis_points: int | None) -> str:
    if basis_points is None:
        return "—"
    units, remainder = divmod(basis_points, CENTS_IN_REAL)
    return f"{units},{remainder:02d}%"


def number(cents: int | None) -> str:
    value = cents or 0
    units, remainder = divmod(abs(value), CENTS_IN_REAL)
    return f"{units},{remainder:02d}"


def unit_value(value: int | None, unit: str) -> str:
    # A row of the store holds cents, basis points or months, and the unit is the
    # column that says which. Reading every row as money is how "6 meses" was
    # printed "R$ 0,06".
    if value is None:
        return "—"
    if unit == CENTS:
        return brl(value)
    if unit == BASIS_POINTS:
        return rate(value)
    if unit == MONTHS:
        return f"{value} {'mês' if value == 1 else 'meses'}"
    return str(value)


def unit_typed(value: int | None, unit: str) -> str:
    # What the owner types back into the field, in the grammar the reader of that
    # unit accepts — never the formatted figure, which no reader accepts.
    if value is None:
        return ""
    if unit == CENTS:
        # The grouped form, the same one the figure above the field shows: a
        # field that reads 35000,00 under a figure that reads R$ 35.000,00 makes
        # the owner check whether the panel understood the number.
        return brl(value).removeprefix(f"{MINUS}").removeprefix("R$ ")
    if unit == BASIS_POINTS:
        return rate(value).replace("%", "")
    return str(value)
