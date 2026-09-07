import sqlite3
from datetime import date
from typing import Any

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from app.commitments.calendar import WINDOW_DAYS
from app.db import connect
from app.projection.forecast import forecast
from app.projection.monthly import MONTHS, monthly
from app.projection.position import positions
from app.queries.period import InvalidPeriodError, day

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/"
DATE_FIELD = "data"


@router.get(SCREEN)
def summary_screen(request: Request) -> Response:
    conn = connect()
    try:
        return TEMPLATES.TemplateResponse(
            request, "resumo.html", _context(conn, _reference(request.query_params.get(DATE_FIELD)))
        )
    finally:
        conn.close()


def _reference(asked: object) -> date:
    # Reached by hand-typed URL as often as by its own links, so a date it cannot
    # read falls back to today instead of a 500.
    try:
        return day(asked, DATE_FIELD)
    except InvalidPeriodError:
        return date.today()


def _moving(days: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shown: list[dict[str, Any]] = []
    carried = 0
    for entry in days[1:]:
        carried += entry["variable_cents"]
        if not (entry["income_cents"] or entry["due_cents"]):
            continue
        shown.append(dict(entry, variable_cents=carried))
        carried = 0
    return shown


def _context(conn: sqlite3.Connection, today: date) -> dict[str, Any]:
    line = forecast(conn, today=today)
    month = monthly(conn, today=today)
    return {
        "reference": today.isoformat(),
        "position": positions(conn),
        "month": month,
        "window_days": WINDOW_DAYS,
        "median_months": MONTHS,
        "forecast": line,
        "start": line["days"][0],
        "end": line["days"][-1],
        # Only the days where something happens: forty-six rows of an almost
        # unchanged balance would bury the three that decide the month. The days
        # left out still carry their share of the undated spending, so each row
        # shown gathers what was skipped since the previous one — otherwise the
        # figures on screen would not add up to the balance beside them.
        "moving": _moving(line["days"]),
        "empty": conn.execute("SELECT COUNT(*) AS total FROM transactions").fetchone()["total"] == 0,
    }
