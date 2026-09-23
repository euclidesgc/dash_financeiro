from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import connect
from app.plan.ceiling import month_signal, read_ceiling
from app.queries.expenses import (
    Order,
    Sort,
    get_expense,
    list_expenses,
    sum_by_category,
    sum_expenses,
)
from app.queries.similar import count_similar
from app.taxonomy.limits import Scope, Signal, is_whole_month, signal_for
from app.taxonomy.override import (
    UnknownCategoryError,
    UnknownTransactionError,
    apply_to_similar,
    restore_auto,
    set_manual,
)

router = APIRouter(prefix="/api/transactions")

UNKNOWN_EXPENSE = "Gasto não encontrado."
UNKNOWN_CATEGORY = "Categoria desconhecida."


class Expense(BaseModel):
    id: int
    date: str
    description: str | None
    payee_name: str | None
    account_name: str | None
    account_institution: str | None
    account_type: Literal["BANK", "CREDIT"] | None
    category: str | None
    category_key: str | None
    category_source: Literal["auto", "manual"]
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
    limit_cents: int | None
    signal: Signal | None


class CategoryTotalsResponse(BaseModel):
    groups: list[CategoryGroup]
    total_cents: int
    over_limit_count: int
    signal_scope: Scope


class MonthSignalResponse(BaseModel):
    scope: Scope
    spent_cents: int
    ceiling_cents: int | None
    signal: Signal | None
    remaining_cents: int | None


class CategoryUpdate(BaseModel):
    mode: Literal["manual", "auto"]
    category: str | None = None


class SimilarResponse(BaseModel):
    count: int


class ApplyToSimilarBody(BaseModel):
    category: str | None


class ApplyToSimilarResponse(BaseModel):
    updated: int


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
    scope: Scope = "month" if is_whole_month(date_from, date_to) else "none"
    items = [
        CategoryGroup(
            category=g.category,
            label=g.label,
            count=g.count,
            total_cents=g.total_cents,
            limit_cents=g.limit_cents,
            signal=signal_for(abs(g.total_cents), g.limit_cents) if scope == "month" else None,
        )
        for g in groups
    ]
    return CategoryTotalsResponse(
        groups=items,
        total_cents=sum(g.total_cents for g in groups),
        over_limit_count=sum(1 for item in items if item.signal == "over"),
        signal_scope=scope,
    )


@router.get("/expenses/month-signal")
def month_signal_of_period(
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
) -> MonthSignalResponse:
    date_from, date_to = _date_bounds(from_, to)
    conn = connect()
    try:
        total = sum_expenses(conn, date_from=date_from, date_to=date_to)
        ceiling = read_ceiling(conn)
    finally:
        conn.close()
    result = month_signal(
        spent_cents=abs(total),
        ceiling_cents=ceiling,
        whole_month=is_whole_month(date_from, date_to),
    )
    return MonthSignalResponse(
        scope=result.scope,
        spent_cents=result.spent_cents,
        ceiling_cents=result.ceiling_cents,
        signal=result.signal,
        remaining_cents=result.remaining_cents,
    )


@router.patch("/{transaction_id}/category")
def update_category(transaction_id: int, body: CategoryUpdate) -> Expense:
    conn = connect()
    try:
        try:
            if body.mode == "manual":
                set_manual(conn, transaction_id, body.category)
            else:
                restore_auto(conn, transaction_id)
        except UnknownTransactionError as error:
            raise HTTPException(status_code=404, detail=UNKNOWN_EXPENSE) from error
        except UnknownCategoryError as error:
            raise HTTPException(status_code=422, detail=UNKNOWN_CATEGORY) from error
        item = get_expense(conn, transaction_id)
    finally:
        conn.close()
    if item is None:
        raise HTTPException(status_code=404, detail=UNKNOWN_EXPENSE)
    return Expense(**item)


@router.get("/{transaction_id}/similar")
def similar(transaction_id: int) -> SimilarResponse:
    conn = connect()
    try:
        if get_expense(conn, transaction_id) is None:
            raise HTTPException(status_code=404, detail=UNKNOWN_EXPENSE)
        count = count_similar(conn, transaction_id)
    finally:
        conn.close()
    return SimilarResponse(count=count)


@router.post("/{transaction_id}/category/apply-to-similar")
def apply_category_to_similar(
    transaction_id: int, body: ApplyToSimilarBody
) -> ApplyToSimilarResponse:
    conn = connect()
    try:
        try:
            updated = apply_to_similar(conn, transaction_id, body.category)
        except UnknownTransactionError as error:
            raise HTTPException(status_code=404, detail=UNKNOWN_EXPENSE) from error
        except UnknownCategoryError as error:
            raise HTTPException(status_code=422, detail=UNKNOWN_CATEGORY) from error
    finally:
        conn.close()
    return ApplyToSimilarResponse(updated=updated)
