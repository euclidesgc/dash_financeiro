import sqlite3
from datetime import date
from typing import Any

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect
from app.plan.objective import RESERVE_MONTHS, floor_label, levers, survival_floor_cents
from app.plan.timeline import BASE, every_scenario, history, record
from app.queries.period import InvalidPeriodError, day

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/objetivo"
DATE_FIELD = "data"


@router.get(SCREEN)
def objective_screen(request: Request) -> Response:
    today = _reference(request.query_params.get(DATE_FIELD))
    conn = connect()
    try:
        runs = every_scenario(conn, today=today)
        # Every reading writes a snapshot, because "in March you projected 30
        # months, today you project 24" needs a March to compare against, and
        # nobody remembers to press a button for that.
        record(conn, runs, today=today)
        return TEMPLATES.TemplateResponse(request, "objetivo.html", _context(conn, runs, today))
    finally:
        conn.close()


def _reference(asked: object) -> date:
    try:
        return day(asked, DATE_FIELD)
    except InvalidPeriodError:
        return date.today()


def _context(conn: sqlite3.Connection, runs: list[dict], today: date) -> dict[str, Any]:
    return {
        "reference": today.isoformat(),
        "scenarios": runs,
        "base": next(run for run in runs if run["scenario"] == BASE),
        "floor_cents": survival_floor_cents(conn, today=today),
        "floor_label": floor_label(conn),
        "reserve_months": RESERVE_MONTHS,
        "levers": levers(conn, today=today),
        "history": history(conn),
        "reachable": any(run["months_to_objective"] is not None for run in runs),
    }
