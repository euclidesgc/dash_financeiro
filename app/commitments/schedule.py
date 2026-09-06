from calendar import monthrange
from datetime import date

MONTHS_IN_YEAR = 12


def median_day(days: list[int]) -> int:
    # With an even count the lower of the two middle days wins, so the predicted
    # day stays a day the series actually had: the average of two middle days
    # would announce a date that never happened (RF-19).
    ordered = sorted(days)
    return ordered[(len(ordered) - 1) // 2]


def on_month(day: int, month: date) -> date:
    # Day 31 does not exist in November, and an invalid date would take the whole
    # calendar down instead of being one day off (RF-20).
    last = monthrange(month.year, month.month)[1]
    return date(month.year, month.month, min(day, last))


def end_month(last_month: str, remaining: int) -> str:
    index = _index(last_month) + remaining
    return f"{index // MONTHS_IN_YEAR:04d}-{index % MONTHS_IN_YEAR + 1:02d}"


def months_before(month: str, count: int) -> list[str]:
    index = _index(month)
    return [_month(index - step) for step in range(count, -1, -1)]


def consecutive_run(months: list[str]) -> int:
    longest = run = 1
    for earlier, later in zip(months, months[1:]):
        run = run + 1 if _index(later) - _index(earlier) == 1 else 1
        longest = max(longest, run)
    return longest


def _index(month: str) -> int:
    return int(month[:4]) * MONTHS_IN_YEAR + int(month[5:7]) - 1


def _month(index: int) -> str:
    return f"{index // MONTHS_IN_YEAR:04d}-{index % MONTHS_IN_YEAR + 1:02d}"
