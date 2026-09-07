import sqlite3
from datetime import date
from typing import Any

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect
from app.debts.ladder import without_rate
from app.plan.objective import RESERVE_MONTHS, floor_label, levers, survival_floor_cents
from app.plan.timeline import BASE, every_scenario, history, record
from app.queries.period import InvalidPeriodError, day

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/objetivo"
DATE_FIELD = "data"


@router.get(SCREEN)
def objective_screen(request: Request) -> Response:
    today, accepted = _reference(request.query_params.get(DATE_FIELD))
    conn = connect()
    try:
        runs = every_scenario(conn, today=today)
        # Every accepted reading writes a snapshot, because "in March you
        # projected 30 months, today you project 24" needs a March to compare
        # against, and nobody remembers to press a button for that. A refused
        # date does not: a typo in the URL would inject a point that cannot be
        # told apart from a real reading afterwards (RF-02).
        if accepted:
            record(conn, runs, today=today)
        context = _context(conn, runs, today)
        context["refused"] = not accepted
        return TEMPLATES.TemplateResponse(request, "objetivo.html", context)
    finally:
        conn.close()


EARLIEST = date(2000, 1, 1)
LATEST = date(2100, 12, 31)


def _reference(asked: object) -> tuple[date, bool]:
    # Every reading of this screen writes a point in a permanent series keyed by
    # this date, and the twelve-month window behind it does date arithmetic that
    # falls off the edge of the calendar: `0001-01-01` is valid ISO and took the
    # route down with a 500 (RF-15).
    # No parameter is not a refused date: it is the normal way into this screen,
    # from the two links the product itself carries. Treating it as a refusal
    # made the timeline stop growing through ordinary navigation, and printed
    # "the date asked was not accepted" over a request that asked for none.
    if asked is None or not str(asked).strip():
        return date.today(), True
    try:
        asked_date = day(asked, DATE_FIELD)
    except InvalidPeriodError:
        return date.today(), False
    if EARLIEST <= asked_date <= LATEST:
        return asked_date, True
    return date.today(), False


def _context(conn: sqlite3.Connection, runs: list[dict], today: date) -> dict[str, Any]:
    gained = levers(conn, today=today)
    return {
        "reference": today.isoformat(),
        "scenarios": runs,
        "base": next(run for run in runs if run["scenario"] == BASE),
        "floor_cents": survival_floor_cents(conn, today=today),
        "floor_label": floor_label(conn),
        "reserve_months": RESERVE_MONTHS,
        "levers": gained,
        "history": history(conn),
        "reachable": any(run["months_to_objective"] is not None for run in runs),
        # A lever the owner has not pulled yet renders as R$ 0,00 under a label
        # promising an act, and the screen used to leave the reader to guess why.
        # It names the empty list instead (RF-01).
        "empty_levers": [
            name
            for name, value in (
                ("as assinaturas marcadas como “não uso mais”", gained["dismissed"]),
                ("a lista de corte", gained["cut"]),
            )
            if not value
        ],
        # base == conservador only when both lists are empty: base adds both
        # levers, conservador adds neither. Saying it over one empty list would
        # contradict the two different numbers in the table beside it.
        "base_equals_conservative": not gained["dismissed"] and not gained["cut"],
        # The ladder of the objective only sees debts with a rate. Six of them
        # have none, and they are not small: leaving them out in silence would
        # make the milestone true over a fraction of the real debt (RF-18).
        "unrated": without_rate(conn),
        "unrated_cents": sum(row["balance_cents"] for row in without_rate(conn)),
    }
