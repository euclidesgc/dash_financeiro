from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.config import reference_date
from app.db import connect
from app.offers import store
from app.offers.store import ACTION as OFFER
from app.offers.store import REMOVE_ACTION as OFFER_REMOVE
from app.routers.settings import SAVED, answer, text
from app.settings.typed import InvalidValueError

router = APIRouter()


@router.post(OFFER)
def store_offer(
    request: Request,
    nome: Annotated[str, Form()] = "",
    taxa: Annotated[str, Form()] = "",
    prazo: Annotated[str, Form()] = "",
    liberado: Annotated[str, Form()] = "",
    contratacao: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        typed = {
            "nome": text(nome),
            "taxa": text(taxa),
            "prazo": text(prazo),
            "liberado": text(liberado),
            "contratacao": text(contratacao),
        }
        try:
            store.write(conn, typed, today=reference_date())
        except InvalidValueError as refusal:
            return answer(request, conn, notice=str(refusal), status_code=400)
        return answer(request, conn, done=SAVED)
    finally:
        conn.close()


@router.post(OFFER_REMOVE)
def remove_offer(
    request: Request,
    nome: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        store.remove(conn, text(nome))
        return answer(request, conn, done=SAVED)
    finally:
        conn.close()
