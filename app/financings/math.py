import calendar
from datetime import date

from app.financings.money import MONTHS_IN_YEAR, RATE_SCALE


def monthly_from_yearly_bp(yearly_pct: float) -> int:
    yearly = yearly_pct / 100
    monthly: float = (1 + yearly) ** (1 / MONTHS_IN_YEAR) - 1
    return round(monthly * RATE_SCALE)


def instalments_due(first_due: date, term_months: int, today: date) -> int:
    # Reason: date(year, month, first_due.day) raises ValueError past the
    # month's last day, and a contract due on the 31st crosses February
    # every year.
    year, month, day = first_due.year, first_due.month, first_due.day
    paid = 0
    for _ in range(term_months):
        last_day = calendar.monthrange(year, month)[1]
        if date(year, month, min(day, last_day)) <= today:
            paid += 1
        month += 1
        if month > MONTHS_IN_YEAR:
            month, year = 1, year + 1
    return paid


def remaining_months(first_due: date, term_months: int, today: date) -> int:
    # Reason: a floor at zero, not a negative count — with every instalment
    # due the contract is settled, not a debt with an inverted sign
    # (invariant 22).
    return max(term_months - instalments_due(first_due, term_months, today), 0)


def present_value_cents(payment_cents: int, monthly_rate_bp: int, left: int) -> int:
    if left <= 0:
        return 0
    if monthly_rate_bp == 0:
        # Reason: no interest, no annuity factor to divide by — the present
        # value of what is left is just the sum of the remaining instalments.
        return payment_cents * left
    rate = monthly_rate_bp / RATE_SCALE
    return round(payment_cents * (1 - (1 + rate) ** -left) / rate)
