import sqlite3
from calendar import monthrange
from datetime import date, timedelta
from typing import Any

from app.accounts import BANK

# Reason: this is what the bank actually charged, not what the contract
# says. The description is the only marker the source gives, and "mora" is
# a late-payment fine on a single bill, not the price of carrying a
# negative balance.
_INTEREST = "lower(description) LIKE '%juros%' AND lower(description) NOT LIKE '%mora%'"
_MOVES = (
    "SELECT date, SUM(amount_cents) AS total FROM transactions WHERE account_id = ? GROUP BY date"
)
_CHARGED = (
    f"SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    f"WHERE account_id = ? AND substr(date, 1, 7) = ? AND {_INTEREST}"
)
_POSTING_DAYS = (
    f"SELECT CAST(substr(date, 9, 2) AS INTEGER) AS day FROM transactions "
    f"WHERE account_id = ? AND {_INTEREST} ORDER BY day"
)

# Reason: an account whose interest lands in the first third of the month
# is charging in arrears. A fixed cut in days cannot decide this — one
# account of this base posts on the 1st and another on the 6th, and a cut
# that reaches only the first threw away 31% of the second account's
# interest — the largest single charge of the series, for a month the
# account spent entirely in the black.
EARLY_DAYS = 10

# Reason: below this, a fixed minimum fee dominates the charge and the
# ratio stops being a rate — one month of this base shows 81% over an
# average balance of R$ 38.
MIN_BALANCE_CENTS = 50000
MIN_MONTHS = 3
# Reason: below this share of the month in the red, the ratio stops
# describing a rate.
MIN_NEGATIVE_SHARE = 0.5
RATE_SCALE = 10000


def daily_balances(
    conn: sqlite3.Connection, account_id: str, balance: int, today: date
) -> dict[str, int]:
    # Reason: walked backwards from the balance the source reports —
    # interest is charged on the daily negative balance, and a monthly
    # average hides the days the account spent in the black.
    moves = {row["date"]: row["total"] for row in conn.execute(_MOVES, (account_id,))}
    if not moves:
        return {}
    first = min(moves)
    days: dict[str, int] = {}
    running, when = balance, today
    while when.isoformat() >= first:
        days[when.isoformat()] = running
        running -= moves.get(when.isoformat(), 0)
        when -= timedelta(days=1)
    return days


def observed_rates(conn: sqlite3.Connection, *, today: date) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for account in conn.execute(
        "SELECT id, name, balance_cents FROM accounts WHERE type = ? AND balance_cents < 0",
        (BANK,),
    ):
        days = daily_balances(conn, account["id"], account["balance_cents"], today)
        rates = _monthly_rates(conn, account["id"], days, today)
        if len(rates) < MIN_MONTHS:
            continue
        ordered = sorted(rate for _, rate in rates)
        found[account["id"]] = {
            "name": account["name"],
            "months": len(ordered),
            "median_bp": _median(ordered),
            "lowest_bp": ordered[0],
            "highest_bp": ordered[-1],
        }
    return found


def _monthly_rates(
    conn: sqlite3.Connection, account_id: str, days: dict[str, int], today: date
) -> list[tuple[str, int]]:
    arrears = posts_in_arrears(conn, account_id)
    # Reason: the month in progress is left out — five days of balance
    # under a whole month of interest reads as a rate three times the real
    # one, and it was that partial month producing the widest end of the
    # range shown to the owner.
    current = f"{today.year:04d}-{today.month:02d}"
    rates = []
    for month in sorted({when[:7] for when in days}):
        if month >= current:
            continue
        charged = _charged_for(conn, account_id, month, arrears)
        if not charged:
            continue
        negative = [value for when, value in days.items() if when[:7] == month and value < 0]
        # Reason: measured against the days of the calendar month, not
        # against the days the reconstruction happens to hold. The oldest
        # month is truncated by construction — the walk stops at the first
        # movement — so comparing it to its own truncated self lets it
        # through: 14 of 26 reconstructed days passes, 14 of 31 real days
        # does not. That is the same partial-month distortion the month in
        # progress caused, surviving at the other end.
        if len(negative) < _days_in(month) * MIN_NEGATIVE_SHARE:
            continue
        average = sum(negative) / len(negative)
        if abs(average) < MIN_BALANCE_CENTS:
            continue
        rates.append((month, round(abs(charged) / abs(average) * RATE_SCALE)))
    return rates


def posts_in_arrears(conn: sqlite3.Connection, account_id: str) -> bool:
    # Reason: decided per account, from the account's own postings, because
    # the day is a property of the bank and not of this program.
    days = [row["day"] for row in conn.execute(_POSTING_DAYS, (account_id,))]
    return bool(days) and _median(days) <= EARLY_DAYS


def _days_in(month: str) -> int:
    return monthrange(int(month[:4]), int(month[5:7]))[1]


def _charged_for(conn: sqlite3.Connection, account_id: str, month: str, arrears: bool) -> int:
    # Reason: the bank charges in arrears — the interest posted early in a
    # month is the price of the month before. Matching the posting to the
    # month it was posted in, instead of the month it remunerates, turned a
    # contracted rate that barely moves into a range three times wider than
    # the real one.
    wanted = _next(month) if arrears else month
    charged = conn.execute(_CHARGED, (account_id, wanted)).fetchone()["total"]
    # Reason: only money that left. A month whose interest line nets
    # positive — a refund larger than the charge — is not a month the bank
    # charged for, and taking its absolute value would read a credit as a
    # rate.
    return charged if charged < 0 else 0


def _next(month: str) -> str:
    year, index = int(month[:4]), int(month[5:7])
    return f"{year + index // 12:04d}-{index % 12 + 1:02d}"


def _median(values: list[int]) -> int:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    # Reason: rounded, not truncated — an even count used to answer one
    # basis point below the middle of the two.
    return round((ordered[middle - 1] + ordered[middle]) / 2)
