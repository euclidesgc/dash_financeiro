from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.cards import store
from app.cards.catalog import ACTION, CLEAR_ACTION
from app.db import connect
from app.routers.render import unit_value
from app.routers.settings import answer
from app.settings.typed import InvalidValueError

router = APIRouter()

SAVED = "{label} — valor salvo: {value}."
UNCHANGED = "{label} — em branco, valor mantido."
CLEARED = "{label} — valor apagado."


@router.post(ACTION)
def store_field(
    request: Request,
    cartao: Annotated[str, Form()] = "",
    campo: Annotated[str, Form()] = "",
    valor: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        try:
            value, changed = store.write(conn, cartao, campo, valor)
        except InvalidValueError as refusal:
            return answer(request, conn, notice=str(refusal), status_code=400)
        item = store.entry(campo)
        message = (
            SAVED.format(label=item["label"], value=unit_value(value, item["unit"]))
            if changed
            else UNCHANGED.format(label=item["label"])
        )
        return answer(request, conn, done=message)
    finally:
        conn.close()


@router.post(CLEAR_ACTION)
def clear_field(
    request: Request,
    cartao: Annotated[str, Form()] = "",
    campo: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        try:
            item = store.erase(conn, cartao, campo)
        except InvalidValueError as refusal:
            return answer(request, conn, notice=str(refusal), status_code=400)
        return answer(request, conn, done=CLEARED.format(label=item["label"]))
    finally:
        conn.close()
