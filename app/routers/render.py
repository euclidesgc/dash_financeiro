from datetime import date
from pathlib import Path

from fastapi.templating import Jinja2Templates

TEMPLATES_FOLDER = Path(__file__).resolve().parents[1] / "templates"

TEMPLATES = Jinja2Templates(directory=str(TEMPLATES_FOLDER))

# U+2212, the mathematical minus. Colour is never the only sign a value is an
# outflow, so the glyph travels glued to the figure in every screen.
MINUS = "−"

CENTS = 100


def brl(cents: object) -> str:
    value = int(cents or 0)
    units, remainder = divmod(abs(value), CENTS)
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


def rate(basis_points: object) -> str:
    if basis_points is None:
        return "—"
    units, remainder = divmod(int(basis_points), CENTS)
    return f"{units},{remainder:02d}%"


def number(cents: object) -> str:
    value = int(cents or 0)
    units, remainder = divmod(abs(value), CENTS)
    return f"{units},{remainder:02d}"
