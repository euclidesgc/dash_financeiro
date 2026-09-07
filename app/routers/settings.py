import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.config import reference_date
from app.db import connect
from app.projection.monthly import available_months
from app.settings import store
from app.settings.catalog import FACT, GOAL, MEDIAN
from app.settings.typed import InvalidValueError, parse_months

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/configuracao"

SAVED = "Salvo."


@router.get(SCREEN)
def settings_screen(request: Request) -> Response:
    conn = connect()
    try:
        return _answer(request, conn)
    finally:
        conn.close()


@router.post(SCREEN)
def store_value(
    request: Request,
    nome: Annotated[str, Form()] = "",
    valor: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        try:
            _refuse_window_the_base_cannot_fill(conn, _text(nome), _text(valor))
            store.write(conn, _text(nome), _text(valor))
        except InvalidValueError as refusal:
            return _answer(request, conn, notice=str(refusal), status_code=400)
        return _answer(request, conn, done=SAVED)
    finally:
        conn.close()


def _refuse_window_the_base_cannot_fill(conn: sqlite3.Connection, name: str, typed: str) -> None:
    # seen[-N:] truncates in silence: asking for twelve months over a base with
    # six would print twelve on the screen and compute six (RF-10a). The refusal
    # lives here because this is the only screen that writes a goal.
    if name != MEDIAN:
        return
    asked = parse_months(typed, "Meses da janela da mediana")
    seen = available_months(conn, today=reference_date())
    if asked is not None and asked > seen:
        raise InvalidValueError(
            f"A base tem {seen} {'mês fechado' if seen == 1 else 'meses fechados'}, "
            f"e a janela pedida é de {asked}. Informe no máximo {seen}."
        )


def _text(raw: str) -> str:
    # Starlette reads an urlencoded field as latin-1 before percent-decoding it,
    # so a body carrying raw UTF-8 bytes arrives mojibake and every accented
    # value is stored wrong. Reading those bytes back as UTF-8 is exact when it
    # succeeds and leaves the value untouched when it does not.
    try:
        return raw.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return raw


def _answer(
    request: Request,
    conn: sqlite3.Connection,
    *,
    notice: str | None = None,
    done: str | None = None,
    status_code: int = 200,
) -> Response:
    context = _context(conn)
    context.update(notice=notice, done=done)
    return TEMPLATES.TemplateResponse(
        request, "configuracao.html", context, status_code=status_code
    )


def _context(conn: sqlite3.Connection) -> dict[str, Any]:
    reading = store.read(conn, today=reference_date())
    return {
        "action": SCREEN,
        "facts": [item for item in reading if item["kind"] == FACT],
        "goals": [item for item in reading if item["kind"] == GOAL],
        "available_months": available_months(conn, today=reference_date()),
    }
