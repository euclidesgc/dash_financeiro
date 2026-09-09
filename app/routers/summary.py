import sqlite3
from datetime import date
from typing import Any

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from app.commitments.calendar import WINDOW_DAYS
from app.db import connect
from app.projection.forecast import forecast
from app.projection.monthly import median_months, monthly
from app.projection.position import positions
from app.routers.reference import Reference, screen_date
from app.sync import (
    STALE_DAYS,
    MissingCredentialError,
    SyncOutcome,
    days_since,
    finished_on,
    last_runs,
    readable,
    synchronise,
)

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/"
SYNC = "/sincronizar"
DATE_FIELD = "data"
COMMAND = "python -m app.sync"

_COUNT = "SELECT COUNT(*) AS total FROM transactions"


@router.get(SCREEN)
def summary_screen(request: Request) -> Response:
    reference = screen_date(request.query_params.get(DATE_FIELD))
    conn = connect()
    try:
        return _answer(request, conn, reference, notice=reference.notice)
    finally:
        conn.close()


@router.post(SYNC)
def synchronise_now(request: Request) -> Response:
    reference = screen_date(request.query_params.get(DATE_FIELD))
    conn = connect()
    try:
        try:
            outcome = synchronise(conn, today=reference.date)
        except MissingCredentialError as refusal:
            return _answer(request, conn, reference, notice=str(refusal), status_code=400)
        return _answer(request, conn, reference, notice=_said(outcome))
    finally:
        conn.close()


def _said(outcome: SyncOutcome) -> str:
    if outcome.status != "ok":
        return f"A sincronização falhou: {readable(outcome.message)}"
    if not outcome.transactions:
        return "Sincronizado. Nenhum lançamento novo."
    return f"Sincronizado. {outcome.transactions} lançamento(s) novo(s)."


def _answer(
    request: Request,
    conn: sqlite3.Connection,
    reference: Reference,
    *,
    notice: str | None = None,
    status_code: int = 200,
) -> Response:
    context = _context(conn, reference.date)
    context.update(
        notice=notice,
        # Reason: the balances are always the current ones — no history of
        # them is kept, so the reference date moves the projection and
        # never the position. Saying "hoje" over a date the owner typed
        # would be the screen naming a day it is not describing.
        asked_today=not reference.asked,
    )
    return TEMPLATES.TemplateResponse(request, "resumo.html", context, status_code=status_code)


def _moving(days: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shown: list[dict[str, Any]] = []
    carried = 0
    for entry in days[1:]:
        carried += entry["variable_cents"]
        if not (entry["income_cents"] or entry["due_cents"]):
            continue
        shown.append(dict(entry, variable_cents=carried))
        carried = 0
    # Reason: the last day of the window closes the list whenever anything
    # is still carried, even a window with no income and no commitment at
    # all. Without it the undated spending is never handed to any row — the
    # list stops short of the balance the header announces — or disappears
    # while the header announces a fall, and the screen contradicts itself
    # in one panel.
    if carried or (shown and shown[-1]["date"] != days[-1]["date"]):
        shown.append(dict(days[-1], variable_cents=carried))
    return shown


def _context(conn: sqlite3.Connection, today: date) -> dict[str, Any]:
    line = forecast(conn, today=today)
    month = monthly(conn, today=today)
    return {
        "reference": today.isoformat(),
        "position": positions(conn),
        "month": month,
        "window_days": WINDOW_DAYS,
        "median_months": median_months(conn),
        "forecast": line,
        "start": line["days"][0],
        "end": line["days"][-1],
        # Reason: only the days where something happens — forty-six rows of
        # an almost unchanged balance would bury the three that decide the
        # month. The days left out still carry their share of the undated
        # spending, so each row shown gathers what was skipped since the
        # previous one — otherwise the figures on screen would not add up
        # to the balance beside them.
        "moving": _moving(line["days"]),
        "empty": conn.execute(_COUNT).fetchone()["total"] == 0,
        "sync": _sync(conn, today),
    }


def _sync(conn: sqlite3.Connection, today: date) -> dict[str, Any]:
    runs = last_runs(conn)
    age = days_since(runs["succeeded"], today)
    return {
        "latest": runs["latest"],
        "succeeded": runs["succeeded"],
        "succeeded_at": finished_on(runs["succeeded"]),
        "reason": readable(runs["latest"]["message"]) if runs["latest"] else None,
        "age_days": age,
        # Reason: the number the owner reads has an age, and the age is part
        # of the number — a panel showing a fortnight-old statement with the
        # face of a fresh one gets every decision wrong at once (RF-13).
        "stale": age is not None and age > STALE_DAYS,
        "failed": bool(runs["latest"] and runs["latest"]["status"] != "ok"),
        "action": SYNC,
        "command": COMMAND,
    }
