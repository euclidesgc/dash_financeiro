import sqlite3
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.advisor import config
from app.advisor.cited import uncited
from app.advisor.context import as_text, lines, snapshot
from app.advisor.gaps import (
    UnknownQuestionError,
    dismiss,
    next_question,
    pending,
    postponed,
)
from app.advisor.gemini import AdvisorUnavailableError, ask
from app.db import connect
from app.routers.reference import screen_date
from app.settings.limits import MAX_QUESTION

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/consultor"
DISMISS = f"{SCREEN}/adiar"
DATE_FIELD = "data"
UNCHECKED = (
    "A leitura da IA citou um número que não está no contexto enviado, e por isso "
    "o painel não a mostra. Os números da tela são os mesmos."
)


@router.get(SCREEN)
def advisor_screen(request: Request) -> Response:
    reference = screen_date(request.query_params.get(DATE_FIELD))
    conn = connect()
    try:
        return _answer(request, conn, reference.date, notice=reference.notice)
    finally:
        conn.close()


@router.post(SCREEN)
def consult(
    request: Request,
    pergunta: Annotated[str, Form()] = "",
    data: Annotated[str, Form()] = "",
) -> Response:
    today = screen_date(data).date
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
        context_text = as_text(numbers)
        setup = config.current(conn)
        try:
            reading = ask(asked, context_text, api_key=setup.api_key, model=setup.model)
        except AdvisorUnavailableError as refusal:
            return _answer(request, conn, today, unavailable=str(refusal), asked=asked)
        if uncited(reading.text, context_text):
            # Decisão: a leitura inteira é descartada, e não só marcada — exibir a
            # frase com a cifra inventada dentro é o dano que a norma 23 existe
            # para impedir. A mensagem não repete a cifra recusada.
            return _answer(request, conn, today, unchecked=UNCHECKED, asked=asked)
        return _answer(request, conn, today, reading=reading.text, asked=asked)
    finally:
        conn.close()


@router.post(DISMISS)
def postpone(
    request: Request,
    nome: Annotated[str, Form()] = "",
    data: Annotated[str, Form()] = "",
) -> Response:
    today = screen_date(data).date
    conn = connect()
    try:
        try:
            dismiss(conn, nome.strip())
        except UnknownQuestionError as refusal:
            return _answer(request, conn, today, notice=str(refusal), status_code=400)
        return _answer(request, conn, today)
    finally:
        conn.close()


def _answer(
    request: Request,
    conn: sqlite3.Connection,
    today: date,
    *,
    notice: str | None = None,
    reading: str | None = None,
    unavailable: str | None = None,
    unchecked: str | None = None,
    asked: str | None = None,
    status_code: int = 200,
) -> Response:
    context = _context(conn, today)
    context.update(
        notice=notice, reading=reading, unavailable=unavailable, unchecked=unchecked, asked=asked
    )
    return TEMPLATES.TemplateResponse(request, "consultor.html", context, status_code=status_code)


def _context(conn: sqlite3.Connection, today: date) -> dict[str, Any]:
    numbers = snapshot(conn, today=today)
    setup = config.current(conn)
    return {
        "reference": today.isoformat(),
        "numbers": numbers,
        "context_text": as_text(numbers),
        "context_lines": lines(numbers),
        "comparison": numbers["comparison"],
        "question": next_question(conn, today=today),
        "pending": pending(conn, today=today),
        # Reason: "nothing to ask because everything is answered" and
        # "nothing to ask because you postponed everything" are different
        # states, and only one of them means the projection is running on fact.
        "postponed": postponed(conn) if not next_question(conn, today=today) else 0,
        "action": SCREEN,
        "dismiss_action": DISMISS,
        "has_key": bool(setup.api_key),
    }
