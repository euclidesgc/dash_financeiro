# Reason: U+2212, the mathematical minus. Colour is never the only sign a
# value is an outflow, so the glyph travels glued to the figure in every
# screen.
MINUS = "−"

CENTS_IN_REAL = 100


def brl(cents: int | None) -> str:
    value = cents or 0
    units, remainder = divmod(abs(value), CENTS_IN_REAL)
    grouped = f"{units:,}".replace(",", ".")
    return f"{MINUS if value < 0 else ''}R$ {grouped},{remainder:02d}"
