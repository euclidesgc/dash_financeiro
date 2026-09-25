from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import connect
from app.queries.expenses import Order, Sort, list_expenses

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
    total_cents: int


@router.get("/expenses")
def expenses(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort: Annotated[Sort, Query()] = "date",
    order: Annotated[Order, Query()] = "desc",
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
) -> ExpensesResponse:
    if from_ is not None and to is not None and to < from_:
        raise HTTPException(
            status_code=422, detail="A data final precisa ser igual ou posterior à inicial."
        )
    conn = connect()
    try:
        found = list_expenses(
            conn,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            date_from=from_.isoformat() if from_ else None,
            date_to=to.isoformat() if to else None,
        )
    finally:
        conn.close()
    return ExpensesResponse(
        items=[Expense(**item) for item in found.items],
        page=page,
        page_size=page_size,
        total=found.total,
        total_cents=found.total_cents,
    )
