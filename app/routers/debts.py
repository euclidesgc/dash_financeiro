import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect
from app.debts.ladder import (
    VEHICLE,
    DebtNotFoundError,
    InvalidRateError,
    ladder,
    monthly_interest_cents,
    set_rate,
    without_rate,
)
from app.debts.simulate import (
    InvalidAmountError,
    UnknownRateError,
    parameter,
    parse_amount,
    simulate,
)

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/dividas"
RATE = f"{SCREEN}/taxa"
SIMULATE = f"{SCREEN}/simular"
PARAMETER = f"{SCREEN}/parametro"

# The kind is a key in the schema and a word on the screen, and the screen is in
# pt-BR (norm 16). The map is here and not in the template so the vocabulary has
# one home.
KIND_LABELS = {
    "overdraft": "conta em cheque especial",
    "card": "cartão de crédito",
    "vehicle": "financiamento de veículo",
    "mortgage": "financiamento imobiliário",
}

SETTLEMENT = "quitacao"
TRANSPORT = "transporte"
PARAMETERS = {
    SETTLEMENT: "Saldo de quitação",
    TRANSPORT: "Custo de transporte",
}

NOT_FOUND = "Dívida não encontrada."


@router.get(SCREEN)
def debts_screen(request: Request) -> Response:
    conn = connect()
    try:
        return _answer(request, conn)
    finally:
        conn.close()


@router.post(RATE)
def rate(
    request: Request,
    degrau: Annotated[str, Form()] = "",
    taxa: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        try:
            set_rate(conn, _identifier(degrau), taxa)
        except (InvalidRateError, DebtNotFoundError) as refusal:
            return _answer(request, conn, notice=str(refusal), status_code=400)
        return _answer(request, conn)
    finally:
        conn.close()


@router.post(SIMULATE)
def simulation(
    request: Request,
    degrau: Annotated[str, Form()] = "",
    aporte: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        debt = _debt(conn, degrau)
        if debt is None:
            return _answer(request, conn, notice=NOT_FOUND, status_code=400)
        try:
            return _answer(request, conn, simulation=simulate(debt, parse_amount(aporte)))
        except (InvalidAmountError, UnknownRateError) as refusal:
            return _answer(request, conn, notice=str(refusal), status_code=400)
    finally:
        conn.close()


@router.post(PARAMETER)
def store_parameter(
    request: Request,
    nome: Annotated[str, Form()] = "",
    valor: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        if nome not in PARAMETERS:
            return _answer(
                request, conn, notice=f"Parâmetro desconhecido: “{nome}”.", status_code=400
            )
        try:
            cents = parse_amount(valor, PARAMETERS[nome])
        except InvalidAmountError as refusal:
            return _answer(request, conn, notice=str(refusal), status_code=400)
        conn.execute(
            "INSERT OR REPLACE INTO plan_parameters (name, value_cents, updated_at) "
            "VALUES (?, ?, datetime('now'))",
            (nome, cents),
        )
        conn.commit()
        return _answer(request, conn)
    finally:
        conn.close()


def _identifier(asked: str) -> int:
    # A key that is not a number is a debt that does not exist, and the reader
    # says so in pt-BR instead of letting the interpreter answer in English.
    try:
        return int(asked)
    except ValueError:
        raise DebtNotFoundError(NOT_FOUND) from None


def _debt(conn: sqlite3.Connection, asked: str) -> dict | None:
    try:
        found = conn.execute("SELECT * FROM debts WHERE id = ?", (_identifier(asked),)).fetchone()
    except DebtNotFoundError:
        return None
    return dict(found) if found else None


def _answer(
    request: Request,
    conn: sqlite3.Connection,
    *,
    notice: str | None = None,
    simulation: dict | None = None,
    status_code: int = 200,
) -> Response:
    context = _context(conn)
    context.update(notice=notice, simulation=simulation)
    return TEMPLATES.TemplateResponse(request, "dividas.html", context, status_code=status_code)


def _context(conn: sqlite3.Connection) -> dict[str, Any]:
    steps = ladder(conn)
    missing = without_rate(conn)
    vehicle = next((row for row in steps + missing if row["kind"] == VEHICLE), None)
    settlement = parameter(conn, SETTLEMENT)
    return {
        "rate_action": RATE,
        "simulate_action": SIMULATE,
        "parameter_action": PARAMETER,
        "ladder": [dict(row, interest_cents=monthly_interest_cents(row)) for row in steps],
        "without_rate": missing,
        "empty": not steps and not missing,
        "kind_labels": KIND_LABELS,
        "vehicle": vehicle,
        "settlement_cents": settlement,
        "transport_cents": parameter(conn, TRANSPORT),
        # The difference between what the schedule is worth and what the bank
        # actually charges to end it. It is a discount only when it is positive:
        # banks often quote settlement above the strict present value, and
        # calling that a discount — in the colour of a gain — would be the screen
        # lying in favour of a thirty-nine thousand real decision.
        "discount_cents": (
            abs(vehicle["balance_cents"]) - settlement
            if vehicle and settlement is not None
            else None
        ),
    }
