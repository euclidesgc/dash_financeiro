from calendar import monthrange
from typing import Literal

Signal = Literal["within", "warning", "over"]
Scope = Literal["month", "none"]


def signal_for(spent_cents: int, limit_cents: int | None) -> Signal | None:
    if limit_cents is None:
        return None
    if spent_cents > limit_cents:
        return "over"
    if spent_cents * 5 >= limit_cents * 4:
        return "warning"
    return "within"


def is_whole_month(date_from: str | None, date_to: str | None) -> bool:
    if date_from is None or date_to is None:
        return False
    if not date_from.endswith("-01"):
        return False
    year, month = int(date_from[:4]), int(date_from[5:7])
    return date_to == f"{date_from[:7]}-{monthrange(year, month)[1]:02d}"
