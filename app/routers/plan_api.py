from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import connect
from app.plan.ceiling import InvalidCeilingError, read_ceiling, set_ceiling
from app.routers.render import brl
from app.settings.limits import MAX_CENTS

router = APIRouter(prefix="/api/plan")

INVALID_CEILING = "O teto precisa ser maior que zero."
CEILING_TOO_LARGE = f"O teto passa do maior valor aceito, {brl(MAX_CENTS)}."


class CeilingBody(BaseModel):
    monthly_ceiling_cents: int | None


class CeilingResponse(BaseModel):
    monthly_ceiling_cents: int | None


@router.get("/ceiling")
def get_ceiling() -> CeilingResponse:
    conn = connect()
    try:
        ceiling = read_ceiling(conn)
    finally:
        conn.close()
    return CeilingResponse(monthly_ceiling_cents=ceiling)


@router.put("/ceiling")
def put_ceiling(body: CeilingBody) -> CeilingResponse:
    conn = connect()
    try:
        try:
            set_ceiling(conn, body.monthly_ceiling_cents)
        except InvalidCeilingError as error:
            detail = CEILING_TOO_LARGE if error.cents > 0 else INVALID_CEILING
            raise HTTPException(status_code=422, detail=detail) from error
        stored = read_ceiling(conn)
    finally:
        conn.close()
    return CeilingResponse(monthly_ceiling_cents=stored)
