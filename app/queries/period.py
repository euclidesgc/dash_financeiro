from datetime import date, timedelta

CLOSED_MONTHS = 6

START_FIELD = "inicio"
END_FIELD = "fim"

_INVALID_DATE = "data inválida: {field} ({value})"
_INVALID_PERIOD = "período inválido: {end_field} ({end}) anterior a {start_field} ({start})"


class InvalidPeriodError(ValueError):
    pass


def day(value: object, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise InvalidPeriodError(_INVALID_DATE.format(field=field, value=value)) from None


def month(value: object, field: str = END_FIELD) -> date:
    try:
        return date.fromisoformat(f"{value}-01")
    except (TypeError, ValueError):
        raise InvalidPeriodError(_INVALID_DATE.format(field=field, value=value)) from None


def check_period(start: object, end: object) -> tuple[date, date]:
    first, last = day(start, START_FIELD), day(end, END_FIELD)
    if last < first:
        raise InvalidPeriodError(
            _INVALID_PERIOD.format(
                end_field=END_FIELD, end=end, start_field=START_FIELD, start=start
            )
        )
    return first, last


def default_period(today: date, months: int = CLOSED_MONTHS) -> tuple[str, str]:
    # The running month would open the screen on a handful of days of data, so
    # the window ends on the last month already closed; `today` is a parameter
    # so the first load of the screen is verifiable without a fake clock.
    last = shift(date(today.year, today.month, 1), -1)
    first = shift(last, 1 - months)
    return first.isoformat(), (shift(last, 1) - timedelta(days=1)).isoformat()


def shift(anchor: date, months: int) -> date:
    total = anchor.year * 12 + anchor.month - 1 + months
    return date(total // 12, total % 12 + 1, 1)
