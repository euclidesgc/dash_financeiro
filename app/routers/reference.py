from dataclasses import dataclass
from datetime import date

from app.config import reference_date
from app.queries.period import INVALID_DATE, InvalidPeriodError, day

EARLIEST = date(2000, 1, 1)
LATEST = date(2100, 12, 31)

DATE_FIELD = "data"


@dataclass(frozen=True)
class Reference:
    date: date
    asked: bool
    notice: str | None


def screen_date(asked: object) -> Reference:
    if asked is None or not str(asked).strip():
        return Reference(reference_date(), False, None)
    try:
        asked_date = day(asked, DATE_FIELD)
    except InvalidPeriodError as error:
        return Reference(reference_date(), False, str(error))
    if EARLIEST <= asked_date <= LATEST:
        return Reference(asked_date, True, None)
    return Reference(reference_date(), False, INVALID_DATE.format(field=DATE_FIELD, value=asked))
