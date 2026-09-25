from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import connect
from app.queries.expenses import Order, Sort, list_expenses, sum_by_category

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
    account_id: str | None


class ExpensesResponse(BaseModel):
    items: list[Expense]
    page: int
    page_size: int
    total: int
    total_cents: int


class CategoryGroup(BaseModel):
    category: str | None
    label: str
    count: int
    total_cents: int


class CategoryTotalsResponse(BaseModel):
    groups: list[CategoryGroup]
    total_cents: int


def _date_bounds(from_: date | None, to: date | None) -> tuple[str | None, str | None]:
    if from_ is not None and to is not None and to < from_:
        raise HTTPException(
            status_code=422, detail="A data final precisa ser igual ou posterior à inicial."
        )
    return (from_.isoformat() if from_ else None, to.isoformat() if to else None)


def _search_term(q: str | None) -> str | None:
    term = q.strip() if q is not None else ""
    return term if len(term) >= 2 else None


@router.get("/expenses")
def expenses(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort: Annotated[Sort, Query()] = "date",
    order: Annotated[Order, Query()] = "desc",
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    account_id: Annotated[str | None, Query(min_length=1)] = None,
    q: Annotated[str | None, Query()] = None,
) -> ExpensesResponse:
    date_from, date_to = _date_bounds(from_, to)
    search = _search_term(q)
    conn = connect()
    try:
        found = list_expenses(
            conn,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            date_from=date_from,
            date_to=date_to,
            account_id=account_id,
            search=search,
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


@router.get("/expenses/by-category")
def expenses_by_category(
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    account_id: Annotated[str | None, Query(min_length=1)] = None,
    q: Annotated[str | None, Query()] = None,
) -> CategoryTotalsResponse:
    date_from, date_to = _date_bounds(from_, to)
    search = _search_term(q)
    conn = connect()
    try:
        groups = sum_by_category(
            conn,
            date_from=date_from,
            date_to=date_to,
            account_id=account_id,
            search=search,
        )
    finally:
        conn.close()
    return CategoryTotalsResponse(
        groups=[
            CategoryGroup(
                category=g.category, label=g.label, count=g.count, total_cents=g.total_cents
            )
            for g in groups
        ],
        total_cents=sum(g.total_cents for g in groups),
    )
