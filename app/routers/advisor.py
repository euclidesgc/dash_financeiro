import sqlite3
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.advisor.context import as_text, lines, snapshot
from app.advisor.gaps import (
    UnknownQuestionError,
    dismiss,
    next_question,
    pending,
    postponed,
)
from app.advisor.gemini import AdvisorUnavailableError, ask
from app.config import load_config
from app.db import connect
from app.queries.period import InvalidPeriodError, day
from app.routers.plan import EARLIEST, LATEST

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/consultor"
DISMISS = f"{SCREEN}/adiar"
DATE_FIELD = "data"
MAX_QUESTION = 500


@router.get(SCREEN)
def advisor_screen(request: Request) -> Response:
    conn = connect()
    try:
        return _answer(request, conn, _reference(request.query_params.get(DATE_FIELD)))
    finally:
        conn.close()


@router.post(SCREEN)
def consult(
    request: Request,
    pergunta: Annotated[str, Form()] = "",
    data: Annotated[str, Form()] = "",
) -> Response:
    today = _reference(data)
    asked = (pergunta or "").strip()
    conn = connect()
    try:
        if not asked:
            return _answer(request, conn, today, notice="Escreva a pergunta.", status_code=400)
        if len(asked) > MAX_QUESTION:
            return _answer(
                request,
                conn,
                today,
                notice=f"A pergunta passa de {MAX_QUESTION} caracteres.",
                status_code=400,
            )
        numbers = snapshot(conn, today=today)
        try:
            reading = ask(asked, as_text(numbers), api_key=load_config().gemini_api_key)
        except AdvisorUnavailableError as refusal:
            return _answer(request, conn, today, unavailable=str(refusal), asked=asked)
        return _answer(request, conn, today, reading=reading.text, asked=asked)
    finally:
        conn.close()


@router.post(DISMISS)
def postpone(
    request: Request,
    nome: Annotated[str, Form()] = "",
    data: Annotated[str, Form()] = "",
) -> Response:
    today = _reference(data)
    conn = connect()
    try:
        try:
            dismiss(conn, nome.strip())
        except UnknownQuestionError as refusal:
            return _answer(request, conn, today, notice=str(refusal), status_code=400)
        return _answer(request, conn, today)
    finally:
        conn.close()


def _reference(asked: object) -> date:
    try:
        asked_date = day(asked, DATE_FIELD)
    except InvalidPeriodError:
        return date.today()
    return asked_date if EARLIEST <= asked_date <= LATEST else date.today()


def _answer(
    request: Request,
    conn: sqlite3.Connection,
    today: date,
    *,
    notice: str | None = None,
    reading: str | None = None,
    unavailable: str | None = None,
    asked: str | None = None,
    status_code: int = 200,
) -> Response:
    context = _context(conn, today)
    context.update(notice=notice, reading=reading, unavailable=unavailable, asked=asked)
    return TEMPLATES.TemplateResponse(request, "consultor.html", context, status_code=status_code)


def _context(conn: sqlite3.Connection, today: date) -> dict[str, Any]:
    numbers = snapshot(conn, today=today)
    return {
        "reference": today.isoformat(),
        "numbers": numbers,
        "context_text": as_text(numbers),
        "context_lines": lines(numbers),
        "question": next_question(conn, today=today),
        "pending": pending(conn, today=today),
        # "Nothing to ask because everything is answered" and "nothing to ask
        # because you postponed everything" are different states, and only one of
        # them means the projection is running on fact.
        "postponed": postponed(conn) if not next_question(conn, today=today) else 0,
        "action": SCREEN,
        "dismiss_action": DISMISS,
        "has_key": bool(load_config().gemini_api_key),
    }
