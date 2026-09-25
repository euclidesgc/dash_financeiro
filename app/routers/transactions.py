from typing import Annotated, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.db import connect
from app.queries.expenses import list_expenses

router = APIRouter(prefix="/api/transactions")


class Expense(BaseModel):
    id: int
    date: str
    description: str | None
    payee_name: str | None
    account_name: str | None
    account_institution: str | None
    account_type: Literal["BANK", "CREDIT"] | None
    category: str | None
    amount_cents: int


class ExpensesResponse(BaseModel):
    items: list[Expense]
    page: int
    page_size: int
    total: int


@router.get("/expenses")
def expenses(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ExpensesResponse:
    conn = connect()
    try:
        found = list_expenses(conn, page=page, page_size=page_size)
    finally:
        conn.close()
    return ExpensesResponse(
        items=[Expense(**item) for item in found.items],
        page=page,
        page_size=page_size,
        total=found.total,
    )
