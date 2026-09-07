import sqlite3
from datetime import date

from app.commitments.live import released_cash
from app.commitments.live import totals as commitment_totals
from app.projection.monthly import MONTHS, complete_months, median
from app.queries.crossings import crossing
from app.queries.spending import SPENDING

FLOOR_SLUG = "piso"
CUT_SLUG = "corte"
RESERVE_MONTHS = 6

_LABEL = "SELECT label FROM crossings WHERE slug = ?"

_INCOME = (
    "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    "WHERE substr(date, 1, 7) = ? AND amount_cents > 0 AND is_transfer = 0 AND is_refund = 0"
)
_SPENDING = (
    f"SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    f"WHERE substr(date, 1, 7) = ? AND {SPENDING}"
)


def survival_floor_cents(conn: sqlite3.Connection, *, today: date) -> int:
    # The reserve is sized by what the household needs to survive a month, not by
    # what it usually spends: the crossing fixed × essential is that number, and
    # the item 002 already computes it.
    months = complete_months(conn, today=today)
    if not months:
        return 0
    found = crossing(
        conn, slug=FLOOR_SLUG, start=f"{months[0]}-01", end=_last_day(months[-1])
    )
    return abs(found.monthly_average_cents)


def floor_label(conn: sqlite3.Connection) -> str:
    # The name of the crossing lives in the taxonomy table, not in the template:
    # the vocabulary is data, and a screen that spells it out becomes a second
    # place to change when the owner renames it (RF do 002).
    found = conn.execute(_LABEL, (FLOOR_SLUG,)).fetchone()
    return found["label"] if found else FLOOR_SLUG


def reserve_target_cents(conn: sqlite3.Connection, *, today: date) -> int:
    return survival_floor_cents(conn, today=today) * RESERVE_MONTHS


def monthly_results(conn: sqlite3.Connection, *, today: date) -> list[int]:
    return [
        conn.execute(_INCOME, (month,)).fetchone()["total"]
        + conn.execute(_SPENDING, (month,)).fetchone()["total"]
        for month in complete_months(conn, today=today)
    ]


def levers(conn: sqlite3.Connection, *, today: date) -> dict[str, int]:
    # Every lever is money the product already identified, and each one names an
    # act the owner has to perform. A scenario built on a multiplier would be a
    # guess wearing the clothes of a plan.
    months = complete_months(conn, today=today)
    cut = 0
    if months:
        cut = abs(
            crossing(
                conn, slug=CUT_SLUG, start=f"{months[0]}-01", end=_last_day(months[-1])
            ).monthly_average_cents
        )
    return {
        "dismissed": commitment_totals(conn, today=today)["projected_savings_cents"],
        "cut": cut,
        "released": sum(row["amount_cents"] for row in released_cash(conn, today=today)),
    }


def _last_day(month: str) -> str:
    from calendar import monthrange

    year, index = int(month[:4]), int(month[5:7])
    return f"{month}-{monthrange(year, index)[1]:02d}"


def baseline_cents(conn: sqlite3.Connection, *, today: date) -> int:
    results = monthly_results(conn, today=today)
    return median(results) if results else 0


MEDIAN_MONTHS = MONTHS
