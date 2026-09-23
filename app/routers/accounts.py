from fastapi import APIRouter
from pydantic import BaseModel

from app.db import connect
from app.queries.balances import list_balances

router = APIRouter(prefix="/api/accounts")


class AccountBalance(BaseModel):
    id: str
    name: str | None
    institution: str | None
    type: str | None
    subtype: str | None
    balance_cents: int
    updated_at: str | None


class BalancesResponse(BaseModel):
    accounts: list[AccountBalance]


@router.get("/balances")
def balances() -> BalancesResponse:
    conn = connect()
    try:
        rows = list_balances(conn)
    finally:
        conn.close()
    return BalancesResponse(accounts=[AccountBalance(**dict(row)) for row in rows])
