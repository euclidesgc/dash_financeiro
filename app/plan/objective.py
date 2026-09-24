import sqlite3
from datetime import date

from app.commitments.live import released_cash
from app.commitments.live import totals as commitment_totals
from app.projection.monthly import complete_months, median
from app.queries.crossings import crossing
from app.queries.spending import INCOME, SPENDING
from app.settings.catalog import RESERVE, RESERVE_MONTHS
from app.settings.store import value

FLOOR_SLUG = "piso"
CUT_SLUG = "corte"

_LABEL = "SELECT label FROM crossings WHERE slug = ?"

_INCOME = (
    f"SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    f"WHERE substr(date, 1, 7) = ? AND {INCOME}"
)
_SPENDING = (
    f"SELECT COALESCE(SUM(amount_cents), 0) AS total FROM transactions "
    f"WHERE substr(date, 1, 7) = ? AND {SPENDING}"
)


def survival_floor_cents(conn: sqlite3.Connection, *, today: date) -> int:
    # Reason: the reserve is sized by what the household needs to survive a
    # month, not by what it usually spends — the crossing fixed × essential
    # is that number, and item 002 already computes it.
    months = complete_months(conn, today=today)
    if not months:
        return 0
    found = crossing(conn, slug=FLOOR_SLUG, start=f"{months[0]}-01", end=_last_day(months[-1]))
    return abs(found.monthly_average_cents)


def floor_label(conn: sqlite3.Connection) -> str:
    # Reason: the name of the crossing lives in the taxonomy table, not in
    # the template — the vocabulary is data, and a screen that spells it out
    # becomes a second place to change when the owner renames it (the RF
    # from item 002).
    found = conn.execute(_LABEL, (FLOOR_SLUG,)).fetchone()
    return found["label"] if found else "o piso de sobrevivência"


def reserve_months(conn: sqlite3.Connection) -> int:
    # Reason: the constant is the premise the panel declares while the owner
    # has not decided, never the answer (RF-09).
    chosen = value(conn, RESERVE)
    return RESERVE_MONTHS if chosen is None else chosen


def reserve_target_cents(conn: sqlite3.Connection, *, today: date) -> int:
    return survival_floor_cents(conn, today=today) * reserve_months(conn)


def monthly_results(conn: sqlite3.Connection, *, today: date) -> list[int]:
    return [
        conn.execute(_INCOME, (month,)).fetchone()["total"]
        + conn.execute(_SPENDING, (month,)).fetchone()["total"]
        for month in complete_months(conn, today=today)
    ]


def levers(conn: sqlite3.Connection, *, today: date) -> dict[str, int]:
    # Reason: every lever is money the product already identified, and each
    # one names an act the owner has to perform. A scenario built on a
    # multiplier would be a guess wearing the clothes of a plan.
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
