import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.advisor import config as advisor_config
from app.config import reference_date
from app.db import connect
from app.payees import names
from app.payees.lookup import InvalidCnpjError, LookupUnavailableError, enabled, trade_name
from app.projection.monthly import available_months
from app.settings import store
from app.settings.catalog import FACT, GOAL, MEDIAN
from app.settings.typed import InvalidValueError, parse_months

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/configuracao"
PAYEE = f"{SCREEN}/beneficiario"
CNPJ = f"{SCREEN}/cnpj"
IA = f"{SCREEN}/ia"
IA_FORGET = f"{IA}/esquecer"

# How many payees the screen offers to name. A product decision, not a
# measurement of this base: these cover more than half the money, and naming
# them one by one is an evening of work rather than a project. What was measured
# — how many payees exist and how much they cover — lives in
# tests/test_frozen_numbers.py, never in this file.
PAYEES = 30

SAVED = "Salvo."
NAMED = "Nome guardado."
FORGOTTEN = "Apelido apagado. O nome volta a ser o anterior."
KEY_FORGOTTEN = "Chave apagada."
LOOKUP_OFF = "A consulta por CNPJ está desligada. Ligue DASH_CNPJ_LOOKUP no ambiente para usá-la."
NO_CNPJ = "Este beneficiário não tem CNPJ na base."
UNKNOWN_PAYEE = "Beneficiário desconhecido: “{payee}”."


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


@router.post(PAYEE)
def name_payee(
    request: Request,
    beneficiario: Annotated[str, Form()] = "",
    nome: Annotated[str, Form()] = "",
) -> Response:
    payee = _text(beneficiario)
    conn = connect()
    try:
        if not _known(conn, payee):
            return _answer(request, conn, notice=UNKNOWN_PAYEE.format(payee=payee), status_code=400)
        given = _text(nome).strip()
        if given:
            names.name_it(conn, payee, given, names.OWNER)
            return _answer(request, conn, done=NAMED)
        # An empty field is the owner deleting the nickname, and RF-24 says the
        # name then falls back to what was there before — never to the raw
        # description, if a looked-up name is still stored.
        names.forget(conn, payee, names.OWNER)
        return _answer(request, conn, done=FORGOTTEN)
    finally:
        conn.close()


@router.post(CNPJ)
def look_up_cnpj(
    request: Request,
    beneficiario: Annotated[str, Form()] = "",
) -> Response:
    payee = _text(beneficiario)
    conn = connect()
    try:
        if not enabled():
            return _answer(request, conn, notice=LOOKUP_OFF)
        cnpj = _cnpj_of(conn, payee)
        if cnpj is None:
            return _answer(request, conn, notice=NO_CNPJ)
        try:
            found = trade_name(cnpj)
        except (InvalidCnpjError, LookupUnavailableError) as refusal:
            # Degrades with 200 and says what happened in Portuguese, and the
            # name already there stays: the same ruler as the advisor of 009.
            return _answer(request, conn, notice=str(refusal))
        names.name_it(conn, payee, found, names.LOOKUP)
        return _answer(request, conn, done=f"Nome consultado: {found}.")
    finally:
        conn.close()


@router.post(IA)
def store_ia(
    request: Request,
    chave: Annotated[str, Form()] = "",
    modelo: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        try:
            advisor_config.save(conn, api_key=_text(chave), model=_text(modelo))
        except advisor_config.UnknownModelError as refusal:
            return _answer(request, conn, notice=str(refusal), status_code=400)
        return _answer(request, conn, done=SAVED)
    finally:
        conn.close()


@router.post(IA_FORGET)
def forget_ia(request: Request) -> Response:
    conn = connect()
    try:
        advisor_config.forget(conn)
        return _answer(request, conn, done=KEY_FORGOTTEN)
    finally:
        conn.close()


def _known(conn: sqlite3.Connection, payee: str) -> bool:
    found = conn.execute("SELECT 1 FROM transactions WHERE payee = ? LIMIT 1", (payee,)).fetchone()
    return found is not None


def _cnpj_of(conn: sqlite3.Connection, payee: str) -> str | None:
    found = conn.execute(
        "SELECT MIN(merchant_cnpj) AS cnpj FROM transactions "
        "WHERE payee = ? AND merchant_cnpj IS NOT NULL",
        (payee,),
    ).fetchone()
    return found["cnpj"] if found else None


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
    context["ia"] = advisor_config.view(conn)
    context["ia_action"] = IA
    context["ia_forget_action"] = IA_FORGET
    return TEMPLATES.TemplateResponse(
        request, "configuracao.html", context, status_code=status_code
    )


def _context(conn: sqlite3.Connection) -> dict[str, Any]:
    reading = store.read(conn, today=reference_date())
    listed = names.ranked(conn, PAYEES)
    return {
        "action": SCREEN,
        "payee_action": PAYEE,
        "cnpj_action": CNPJ,
        "facts": [item for item in reading if item["kind"] == FACT],
        "goals": [item for item in reading if item["kind"] == GOAL],
        "available_months": available_months(conn, today=reference_date()),
        "payees": listed["payees"],
        "payees_total": listed["total_payees"],
        "payees_shown": PAYEES,
        "payees_covered_permille": listed["covered_permille"],
        "origins": names.ORIGINS,
        "lookup_on": enabled(),
    }
