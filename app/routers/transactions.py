from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import SQLITE_INTEGER_MAX, connect
from app.plan.ceiling import month_signal, read_ceiling
from app.queries.expenses import (
    Order,
    Sort,
    View,
    get_expense,
    list_expenses,
    period_result,
    sum_by_category,
    sum_expenses,
)
from app.queries.similar import count_similar
from app.routers.row_id import RowId
from app.taxonomy.limits import Scope, Signal, is_whole_month, signal_for
from app.taxonomy.override import (
    NotCountableError,
    UnknownCategoryError,
    UnknownTransactionError,
    apply_to_similar,
    clear_not_expense,
    restore_auto,
    set_manual,
    set_not_expense,
)

router = APIRouter(prefix="/api/transactions")

MAX_PAGE_SIZE = 100
# Reason: the query skips (page - 1) * page_size rows, and SQLite refuses an
# offset past its INTEGER range; bounded by the largest page size, the rule
# does not depend on the size asked for.
MAX_PAGE = SQLITE_INTEGER_MAX // MAX_PAGE_SIZE

UNKNOWN_EXPENSE = "Gasto não encontrado."
UNKNOWN_CATEGORY = "Categoria desconhecida."
NOT_COUNTABLE = "Só um lançamento que conta como gasto ou como entrada pode ser marcado."


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
    not_expense_reason: Literal["own_transfer", "refund", "other"] | None


class ExpensesResponse(BaseModel):
    items: list[Expense]
    page: int
    page_size: int
    total: int
    total_cents: int
    outflow_cents: int
    inflow_cents: int


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


class PeriodResultResponse(BaseModel):
    income_cents: int
    spending_cents: int
    balance_cents: int


class CategoryUpdate(BaseModel):
    mode: Literal["manual", "auto"]
    category: str | None = None


class SimilarResponse(BaseModel):
    count: int


class ApplyToSimilarBody(BaseModel):
    category: str | None


class ApplyToSimilarResponse(BaseModel):
    updated: int


class NotExpenseBody(BaseModel):
    reason: Literal["own_transfer", "refund", "other"]


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
    page: Annotated[int, Query(ge=1, le=MAX_PAGE)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
    sort: Annotated[Sort, Query()] = "date",
    order: Annotated[Order, Query()] = "desc",
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    account_id: Annotated[str | None, Query(min_length=1)] = None,
    q: Annotated[str | None, Query()] = None,
    view: Annotated[View, Query()] = "expenses",
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
            view=view,
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
        outflow_cents=found.outflow_cents,
        inflow_cents=found.inflow_cents,
    )


@router.get("/expenses/by-category")
def expenses_by_category(
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    account_id: Annotated[str | None, Query(min_length=1)] = None,
    q: Annotated[str | None, Query()] = None,
    view: Annotated[View, Query()] = "expenses",
) -> CategoryTotalsResponse:
    date_from, date_to = _date_bounds(from_, to)
    search = _search_term(q)
    conn = connect()
    try:
        groups = sum_by_category(
            conn,
            view=view,
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


@router.get("/expenses/period-result")
def period_result_of_period(
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    account_id: Annotated[str | None, Query(min_length=1)] = None,
    q: Annotated[str | None, Query()] = None,
) -> PeriodResultResponse:
    date_from, date_to = _date_bounds(from_, to)
    search = _search_term(q)
    conn = connect()
    try:
        found = period_result(
            conn, date_from=date_from, date_to=date_to, account_id=account_id, search=search
        )
    finally:
        conn.close()
    return PeriodResultResponse(
        income_cents=found.income_cents,
        spending_cents=found.spending_cents,
        balance_cents=found.balance_cents,
    )


@router.patch("/{transaction_id}/category")
def update_category(transaction_id: RowId, body: CategoryUpdate) -> Expense:
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


@router.put("/{transaction_id}/not-expense")
def set_not_expense_of(transaction_id: RowId, body: NotExpenseBody) -> Expense:
    conn = connect()
    try:
        try:
            set_not_expense(conn, transaction_id, body.reason)
        except UnknownTransactionError as error:
            raise HTTPException(status_code=404, detail=UNKNOWN_EXPENSE) from error
        except NotCountableError as error:
            raise HTTPException(status_code=422, detail=NOT_COUNTABLE) from error
        item = get_expense(conn, transaction_id)
    finally:
        conn.close()
    if item is None:
        raise HTTPException(status_code=404, detail=UNKNOWN_EXPENSE)
    return Expense(**item)


@router.delete("/{transaction_id}/not-expense")
def clear_not_expense_of(transaction_id: RowId) -> Expense:
    conn = connect()
    try:
        try:
            clear_not_expense(conn, transaction_id)
        except UnknownTransactionError as error:
            raise HTTPException(status_code=404, detail=UNKNOWN_EXPENSE) from error
        item = get_expense(conn, transaction_id)
    finally:
        conn.close()
    if item is None:
        raise HTTPException(status_code=404, detail=UNKNOWN_EXPENSE)
    return Expense(**item)


@router.get("/{transaction_id}/similar")
def similar(transaction_id: RowId) -> SimilarResponse:
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
    transaction_id: RowId, body: ApplyToSimilarBody
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
