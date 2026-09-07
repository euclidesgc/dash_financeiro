import sqlite3
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect
from app.plan.whatif import (
    INCOME,
    KINDS,
    InvalidScenarioError,
    facts,
    impact,
    parse_move,
    parse_validity,
    save,
    saved,
)
from app.queries.period import InvalidPeriodError, day
from app.routers.plan import EARLIEST, LATEST

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/simulador"
FACT = f"{SCREEN}/fato"
DATE_FIELD = "data"


@router.get(SCREEN)
def simulator_screen(request: Request) -> Response:
    conn = connect()
    try:
        return _answer(request, conn, _reference(request.query_params.get(DATE_FIELD)))
    finally:
        conn.close()


@router.post(SCREEN)
def run(
    request: Request,
    tipo: Annotated[str, Form()] = INCOME,
    mensal: Annotated[str, Form()] = "",
    unico: Annotated[str, Form()] = "",
    prazo: Annotated[str, Form()] = "",
    nome: Annotated[str, Form()] = "",
    data: Annotated[str, Form()] = "",
) -> Response:
    today = _reference(data)
    conn = connect()
    try:
        try:
            move = parse_move(tipo, mensal, unico, prazo)
        except InvalidScenarioError as refusal:
            return _answer(request, conn, today, notice=str(refusal), status_code=400)
        answer = impact(conn, move, today=today)
        if nome.strip():
            save(conn, nome, move)
        return _answer(request, conn, today, answer=answer)
    finally:
        conn.close()


@router.post(FACT)
def store_fact(
    request: Request,
    nome: Annotated[str, Form()] = "",
    rotulo: Annotated[str, Form()] = "",
    valor: Annotated[str, Form()] = "",
    validade: Annotated[str, Form()] = "",
    data: Annotated[str, Form()] = "",
) -> Response:
    today = _reference(data)
    conn = connect()
    try:
        try:
            move = parse_move(INCOME, valor, "", "")
            until = parse_validity(validade)
        except InvalidScenarioError as refusal:
            return _answer(request, conn, today, notice=str(refusal), status_code=400)
        if not nome.strip():
            return _answer(
                request, conn, today, notice="O fato precisa de um nome.", status_code=400
            )
        conn.execute(
            "INSERT OR REPLACE INTO plan_facts "
            "(name, label, value_cents, unit, source, captured_at, valid_until) "
            "VALUES (?, ?, ?, 'centavos', 'humano', datetime('now'), ?)",
            (nome.strip(), rotulo.strip() or nome.strip(), move.monthly_cents, until),
        )
        conn.commit()
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
    answer: dict | None = None,
    status_code: int = 200,
) -> Response:
    context = _context(conn, today)
    context.update(notice=notice, answer=answer)
    return TEMPLATES.TemplateResponse(request, "simulador.html", context, status_code=status_code)


def _context(conn: sqlite3.Connection, today: date) -> dict[str, Any]:
    return {
        "reference": today.isoformat(),
        "kinds": KINDS,
        "scenarios": saved(conn),
        "facts": facts(conn, today=today),
        "fact_action": FACT,
        "action": SCREEN,
    }
