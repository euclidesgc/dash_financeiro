from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.config import reference_date
from app.db import connect
from app.debts.ladder import rebuild
from app.financings import store
from app.routers.settings import answer, text
from app.settings.typed import InvalidValueError

router = APIRouter()

SCREEN = "/configuracao"
FINANCING = f"{SCREEN}/financiamento"


@router.post(FINANCING)
def store_financing(
    request: Request,
    tipo: Annotated[str, Form()] = "",
    saldo: Annotated[str, Form()] = "",
    taxa: Annotated[str, Form()] = "",
    parcela: Annotated[str, Form()] = "",
    prazo: Annotated[str, Form()] = "",
    vencimento: Annotated[str, Form()] = "",
) -> Response:
    conn = connect()
    try:
        typed = {
            "saldo": text(saldo),
            "taxa": text(taxa),
            "parcela": text(parcela),
            "prazo": text(prazo),
            "vencimento": text(vencimento),
        }
        try:
            store.write(conn, text(tipo), typed)
        except InvalidValueError as refusal:
            return answer(request, conn, notice=str(refusal), status_code=400)
        rebuild(conn, today=reference_date())
        return answer(request, conn, done="Salvo.")
    finally:
        conn.close()
