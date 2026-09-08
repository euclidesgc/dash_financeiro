import sqlite3
from collections.abc import Callable
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.commitments.calendar import WINDOW_DAYS, calendar, window
from app.commitments.invoice import invoice_curve
from app.commitments.live import installments, released_cash, subscriptions, totals
from app.commitments.mark import DismissRefusedError, dismiss, resume
from app.db import connect
from app.payees.names import labels as payee_labels
from app.routers.reference import screen_date

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/comprometido"
DISMISS = f"{SCREEN}/dispensar"
RESUME = f"{SCREEN}/retomar"

DATE_FIELD = "data"


@router.get(SCREEN)
def commitments_screen(request: Request) -> Response:
    reference = screen_date(request.query_params.get(DATE_FIELD))
    conn = connect()
    try:
        return _answer(request, conn, reference.date, notice=reference.notice)
    finally:
        conn.close()


@router.post(DISMISS)
def dismiss_series(
    request: Request,
    serie: Annotated[str, Form()] = "",
    data: Annotated[str, Form()] = "",
) -> Response:
    return _mark(request, dismiss, serie, data)


@router.post(RESUME)
def resume_series(
    request: Request,
    serie: Annotated[str, Form()] = "",
    data: Annotated[str, Form()] = "",
) -> Response:
    return _mark(request, resume, serie, data)


def _mark(
    request: Request,
    action: Callable[[sqlite3.Connection, str], None],
    series_key: str,
    asked: str,
) -> Response:
    today = screen_date(asked).date
    conn = connect()
    try:
        try:
            action(conn, series_key)
        except DismissRefusedError as refusal:
            return _answer(request, conn, today, notice=str(refusal), status_code=400)
        conn.commit()
        # The whole screen comes back from the write, totals included: asking for
        # a reload would take the number the owner just changed out of sight.
        return _answer(request, conn, today)
    finally:
        conn.close()


def _answer(
    request: Request,
    conn: sqlite3.Connection,
    today: date,
    *,
    notice: str | None = None,
    status_code: int = 200,
) -> Response:
    context = _context(conn, today)
    context.update(notice=notice)
    return TEMPLATES.TemplateResponse(
        request, "comprometido.html", context, status_code=status_code
    )


def _labels(conn: sqlite3.Connection, rows: list[dict]) -> dict[str, str]:
    # The reading name of a series is the description the source sent; a payee
    # the owner named, or one the Pluggy names, takes its place. Measured: the
    # 115 series keys of this base are payees that exist.
    resolved = payee_labels(conn)
    return {row["series_key"]: resolved.get(row["series_key"], row["description"]) for row in rows}


def _context(conn: sqlite3.Connection, today: date) -> dict[str, Any]:
    recurring = subscriptions(conn, today=today)
    live = installments(conn, today=today)
    first, last = window(today)
    context: dict[str, Any] = {
        "reference": today.isoformat(),
        "subscriptions": [row for row in recurring if not row["dismissed"]],
        "dismissed": [row for row in recurring if row["dismissed"]],
        "installments": live,
        "released": released_cash(conn, today=today),
        # Decisão: a rota chama a leitura de domínio pronta, do mesmo jeito que já
        # chama released_cash e calendar acima, sem montar junção nenhuma aqui.
        "invoice": invoice_curve(conn, today=today),
        "calendar": calendar(conn, today=today),
        "window_start": first.isoformat(),
        "window_end": last.isoformat(),
        "window_days": WINDOW_DAYS,
        # A short calendar reads as a quiet month, so the screen counts the
        # series it left out for lack of a recent charge instead of shrinking
        # in silence (RF-22).
        "stale": len([row for row in recurring if not row["live"]]),
        # The reading name of a series is the description the source sent; the key
        # underneath it is what the form posts back, and the two are shown by the
        # same macro the other screens use.
        "labels": _labels(conn, recurring + live),
        "screen": SCREEN,
        "dismiss_url": DISMISS,
        "resume_url": RESUME,
    }
    context.update(totals(conn, today=today))
    return context
