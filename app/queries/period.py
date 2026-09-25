import calendar
from datetime import date

START_FIELD = "inicio"
END_FIELD = "fim"

INVALID_DATE = "data inválida: {field} ({value})"
_INVALID_PERIOD = "período inválido: {end_field} ({end}) anterior a {start_field} ({start})"


class InvalidPeriodError(ValueError):
    pass


def day(value: object, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise InvalidPeriodError(INVALID_DATE.format(field=field, value=value)) from None


def month(value: object, field: str = END_FIELD) -> date:
    try:
        return date.fromisoformat(f"{value}-01")
    except (TypeError, ValueError):
        raise InvalidPeriodError(INVALID_DATE.format(field=field, value=value)) from None


def check_period(start: object, end: object) -> tuple[date, date]:
    first, last = day(start, START_FIELD), day(end, END_FIELD)
    if last < first:
        raise InvalidPeriodError(
            _INVALID_PERIOD.format(
                end_field=END_FIELD, end=end, start_field=START_FIELD, start=start
            )
        )
    return first, last


def default_period(today: date) -> tuple[str, str]:
    # Reason: the window ends on the reference date, not on the last day of
    # the month — the screen answers "how much left", and summing an
    # instalment already posted for a future date would answer a different
    # question.
    return date(today.year, today.month, 1).isoformat(), today.isoformat()


def month_end(anchor: date) -> date:
    # Reason: stepping into the next month and back one day has no next
    # month to step into in December 9999, the last one date can hold.
    return date(anchor.year, anchor.month, calendar.monthrange(anchor.year, anchor.month)[1])


def covers_whole_months(start: str, end: str) -> bool:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    return first.day == 1 and last == month_end(last)


def shift(anchor: date, months: int) -> date:
    total = anchor.year * 12 + anchor.month - 1 + months
    return date(total // 12, total % 12 + 1, 1)
