from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.cards import store
from app.cards.catalog import ACTION
from app.db import connect
from app.routers.settings import SAVED, answer
from app.settings.typed import InvalidValueError

router = APIRouter()

CLEARED = "Apagado."


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
            value = store.write(conn, cartao, campo, valor)
        except InvalidValueError as refusal:
            return answer(request, conn, notice=str(refusal), status_code=400)
        return answer(request, conn, done=SAVED if value is not None else CLEARED)
    finally:
        conn.close()
