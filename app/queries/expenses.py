import sqlite3
from dataclasses import dataclass
from typing import Any, Literal

from app.db import fold
from app.queries.payees import RESOLVED_PAYEES
from app.queries.spending import EXCLUDED, INCOME, SPENDING, date_window

Sort = Literal["date", "amount", "category"]
Order = Literal["asc", "desc"]
View = Literal["expenses", "excluded", "income"]

_PREDICATE: dict[View, str] = {"expenses": SPENDING, "excluded": EXCLUDED, "income": INCOME}

_ORDER_SQL: dict[Order, str] = {"asc": "ASC", "desc": "DESC"}

_FROM = (
    "FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id"
    f" LEFT JOIN ({RESOLVED_PAYEES}) AS pn ON pn.payee = t.payee"
    " LEFT JOIN categories AS c ON c.name = t.category"
)
# Reason: categories.name is UNIQUE and RESOLVED_PAYEES has one row per
# payee, so neither join multiplies rows and _TOTAL stays correct.

_LABEL = "COALESCE(c.label, NULLIF(t.category, ''))"

_SORT_SQL: dict[Sort, str] = {
    "date": "t.date {order}",
    "amount": "abs(t.amount_cents) {order}",
    "category": (
        f"CASE WHEN {_LABEL} IS NULL THEN 1 ELSE 0 END, fold({_LABEL}) {{order}}, t.category"
    ),
}

_SELECT = f"""SELECT t.id, t.date, t.description, t.payee, t.category, t.category_source,
       {_LABEL} AS category_label,
       t.amount_cents, t.account_id, t.not_expense_reason, pn.name AS payee_name,
       a.name AS account_name, a.institution AS account_institution, a.type AS account_type
{_FROM}"""

_TOTAL = (
    "SELECT count(*), coalesce(sum(t.amount_cents), 0),"
    " coalesce(sum(CASE WHEN t.amount_cents < 0 THEN t.amount_cents END), 0),"
    " coalesce(sum(CASE WHEN t.amount_cents > 0 THEN t.amount_cents END), 0)"
    f" {_FROM}"
)
_BY_CATEGORY = (
    f"SELECT NULLIF(t.category, '') AS category, {_LABEL} AS label, count(*) AS count,"
    f" coalesce(sum(t.amount_cents), 0) AS total,"
    f" max(c.monthly_limit_cents) AS limit_cents {_FROM}"
)


@dataclass(frozen=True)
class ExpensesPage:
    items: list[dict[str, Any]]
    total: int
    total_cents: int
    outflow_cents: int
    inflow_cents: int


@dataclass(frozen=True)
class CategoryTotal:
    category: str | None
    label: str
    count: int
    total_cents: int
    limit_cents: int | None


@dataclass(frozen=True)
class MonthTotal:
    month: str
    income_cents: int
    spending_cents: int
    balance_cents: int


@dataclass(frozen=True)
class PeriodResult:
    income_cents: int
    spending_cents: int
    balance_cents: int


def _like_pattern(term: str) -> str:
    folded = fold(term) or ""
    escaped = folded.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _where(
    view: View,
    date_from: str | None,
    date_to: str | None,
    account_id: str | None,
    search: str | None,
    category: str | None = None,
) -> tuple[str, list[str]]:
    sql = f"WHERE {_PREDICATE[view]}"
    window, params = date_window(date_from, date_to, "t.date")
    sql += window
    if account_id is not None:
        sql += " AND t.account_id = ?"
        params.append(account_id)
    if search is not None:
        sql += " AND (fold(t.description) LIKE ? ESCAPE '\\' OR fold(pn.name) LIKE ? ESCAPE '\\')"
        pattern = _like_pattern(search)
        params.extend([pattern, pattern])
    if category is not None:
        sql += " AND t.category = ?"
        params.append(category)
    return sql, params


def _page_sql(sort: Sort, order: Order, where: str) -> str:
    expression = _SORT_SQL[sort].format(order=_ORDER_SQL[order])
    return f"{_SELECT} {where} ORDER BY {expression}, t.id DESC LIMIT ? OFFSET ?"


def _item(row: sqlite3.Row) -> dict[str, Any]:
    raw_category = row["category"]
    return {
        "id": row["id"],
        "date": row["date"],
        "description": row["description"],
        "payee_name": row["payee_name"],
        "account_name": row["account_name"],
        "account_institution": row["account_institution"],
        "account_type": row["account_type"],
        "category": row["category_label"],
        "category_key": raw_category or None,
        "category_source": row["category_source"],
        "amount_cents": row["amount_cents"],
        "account_id": row["account_id"],
        "not_expense_reason": row["not_expense_reason"],
    }


def sum_expenses(
    conn: sqlite3.Connection,
    *,
    view: View = "expenses",
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
    search: str | None = None,
    category: str | None = None,
) -> int:
    where, params = _where(view, date_from, date_to, account_id, search, category)
    _, total_cents, _, _ = conn.execute(f"{_TOTAL} {where}", params).fetchone()
    return int(total_cents)


def list_expenses(
    conn: sqlite3.Connection,
    *,
    page: int,
    page_size: int,
    sort: Sort = "date",
    order: Order = "desc",
    view: View = "expenses",
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
    search: str | None = None,
    category: str | None = None,
) -> ExpensesPage:
    offset = (page - 1) * page_size
    where, where_params = _where(view, date_from, date_to, account_id, search, category)
    sql = _page_sql(sort, order, where)
    rows = conn.execute(sql, (*where_params, page_size, offset)).fetchall()
    total, total_cents, outflow_cents, inflow_cents = conn.execute(
        f"{_TOTAL} {where}", where_params
    ).fetchone()
    items = [_item(row) for row in rows]
    return ExpensesPage(
        items=items,
        total=total,
        total_cents=int(total_cents),
        outflow_cents=int(outflow_cents),
        inflow_cents=int(inflow_cents),
    )


def get_expense(conn: sqlite3.Connection, transaction_id: int) -> dict[str, Any] | None:
    row = conn.execute(f"{_SELECT} WHERE t.id = ?", (transaction_id,)).fetchone()
    if row is None:
        return None
    # Reason: no SPENDING filter here — this reads a single transaction by
    # id, not a page of gastos.
    return _item(row)


def sum_by_category(
    conn: sqlite3.Connection,
    *,
    view: View = "expenses",
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
    search: str | None = None,
) -> list[CategoryTotal]:
    where, params = _where(view, date_from, date_to, account_id, search)
    sql = (
        f"{_BY_CATEGORY} {where} GROUP BY NULLIF(t.category, '')"
        " ORDER BY abs(total) DESC,"
        " CASE WHEN NULLIF(t.category, '') IS NULL THEN 1 ELSE 0 END,"
        " NULLIF(t.category, '')"
    )
    rows = conn.execute(sql, params).fetchall()
    result = []
    for row in rows:
        category = row["category"]
        label = "Sem categoria" if category is None else row["label"]
        result.append(
            CategoryTotal(
                category=category,
                label=label,
                count=row["count"],
                total_cents=int(row["total"]),
                limit_cents=None if row["limit_cents"] is None else int(row["limit_cents"]),
            )
        )
    return result


def period_result(
    conn: sqlite3.Connection,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
    search: str | None = None,
) -> PeriodResult:
    income = sum_expenses(
        conn,
        view="income",
        date_from=date_from,
        date_to=date_to,
        account_id=account_id,
        search=search,
    )
    spending = sum_expenses(
        conn,
        view="expenses",
        date_from=date_from,
        date_to=date_to,
        account_id=account_id,
        search=search,
    )
    return PeriodResult(
        income_cents=income, spending_cents=spending, balance_cents=income + spending
    )


_MONTHLY = (
    "SELECT substr(t.date, 1, 7) AS month,"
    f" coalesce(sum(CASE WHEN {INCOME} THEN t.amount_cents END), 0) AS income,"
    f" coalesce(sum(CASE WHEN {SPENDING} THEN t.amount_cents END), 0) AS spending"
    f" FROM transactions AS t WHERE (({INCOME}) OR ({SPENDING}))"
)


def monthly_totals(
    conn: sqlite3.Connection,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
) -> list[MonthTotal]:
    window, params = date_window(date_from, date_to, "t.date")
    sql = f"{_MONTHLY}{window}"
    if account_id is not None:
        sql += " AND t.account_id = ?"
        params.append(account_id)
    rows = conn.execute(f"{sql} GROUP BY month ORDER BY month", params).fetchall()
    return [
        MonthTotal(
            month=row["month"],
            income_cents=int(row["income"]),
            spending_cents=int(row["spending"]),
            balance_cents=int(row["income"]) + int(row["spending"]),
        )
        for row in rows
    ]
