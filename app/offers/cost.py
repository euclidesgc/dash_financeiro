from app.financings.money import RATE_SCALE


def total_cost(
    released_cents: int,
    monthly_rate_bp: int,
    term_months: int,
    fee_cents: int = 0,
) -> int:
    if monthly_rate_bp == 0:
        return fee_cents
    rate = monthly_rate_bp / RATE_SCALE
    payment = round(released_cents * rate / (1 - (1 + rate) ** -term_months))
    return payment * term_months - released_cents + fee_cents
