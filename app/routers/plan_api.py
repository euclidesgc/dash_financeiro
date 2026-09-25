from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import connect
from app.plan.ceiling import InvalidCeilingError, read_ceiling, set_ceiling

router = APIRouter(prefix="/api/plan")

INVALID_CEILING = "O teto precisa ser maior que zero."


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
            raise HTTPException(status_code=422, detail=INVALID_CEILING) from error
        stored = read_ceiling(conn)
    finally:
        conn.close()
    return CeilingResponse(monthly_ceiling_cents=stored)
