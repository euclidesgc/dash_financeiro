import sqlite3
from dataclasses import dataclass
from typing import Any, Literal

from app.db import fold
from app.payees.names import labels
from app.queries.spending import SPENDING

Sort = Literal["date", "amount", "category"]
Order = Literal["asc", "desc"]

_ORDER_SQL: dict[Order, str] = {"asc": "ASC", "desc": "DESC"}

_FROM = (
    "FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id"
    " LEFT JOIN payee_names AS own ON own.payee = t.payee AND own.source = 'dono'"
    " LEFT JOIN payee_names AS lk ON lk.payee = t.payee AND lk.source = 'cnpj'"
    " LEFT JOIN categories AS c ON c.name = t.category"
)
# Reason: categories.name is UNIQUE, so the join doesn't multiply rows and
# _TOTAL stays correct.

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
       t.amount_cents, t.account_id,
       a.name AS account_name, a.institution AS account_institution, a.type AS account_type
{_FROM}"""

_TOTAL = f"SELECT count(*), coalesce(sum(t.amount_cents), 0) {_FROM}"
_BY_CATEGORY = (
    f"SELECT NULLIF(t.category, '') AS category, {_LABEL} AS label, count(*) AS count,"
    f" coalesce(sum(t.amount_cents), 0) AS total,"
    f" max(c.monthly_limit_cents) AS limit_cents {_FROM}"
)

# Reason: reproduces app.payees.names._chosen's precedence row by row (debt
# tracked in the SPEC).
_PAYEE_NAME_SQL = (
    "CASE WHEN t.payee IS NULL THEN NULL ELSE COALESCE("
    "NULLIF(own.name, ''), NULLIF(t.merchant_name, ''), NULLIF(lk.name, ''), "
    "NULLIF(t.merchant_legal_name, ''), NULLIF(t.receiver_name, '')) END"
)


@dataclass(frozen=True)
class ExpensesPage:
    items: list[dict[str, Any]]
    total: int
    total_cents: int


@dataclass(frozen=True)
class CategoryTotal:
    category: str | None
    label: str
    count: int
    total_cents: int
    limit_cents: int | None


def _like_pattern(term: str) -> str:
    folded = fold(term) or ""
    escaped = folded.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _where(
    date_from: str | None, date_to: str | None, account_id: str | None, search: str | None
) -> tuple[str, list[str]]:
    sql = f"WHERE {SPENDING}"
    params: list[str] = []
    if date_from is not None:
        sql += " AND t.date >= ?"
        params.append(date_from)
    if date_to is not None:
        sql += " AND t.date <= ?"
        params.append(date_to)
    if account_id is not None:
        sql += " AND t.account_id = ?"
        params.append(account_id)
    if search is not None:
        sql += (
            " AND (fold(t.description) LIKE ? ESCAPE '\\'"
            f" OR fold({_PAYEE_NAME_SQL}) LIKE ? ESCAPE '\\')"
        )
        pattern = _like_pattern(search)
        params.extend([pattern, pattern])
    return sql, params


def _page_sql(sort: Sort, order: Order, where: str) -> str:
    expression = _SORT_SQL[sort].format(order=_ORDER_SQL[order])
    return f"{_SELECT} {where} ORDER BY {expression}, t.id DESC LIMIT ? OFFSET ?"


def _item(row: sqlite3.Row, names: dict[str, str]) -> dict[str, Any]:
    raw_category = row["category"]
    return {
        "id": row["id"],
        "date": row["date"],
        "description": row["description"],
        "payee_name": names.get(row["payee"]),
        "account_name": row["account_name"],
        "account_institution": row["account_institution"],
        "account_type": row["account_type"],
        "category": row["category_label"],
        "category_key": raw_category or None,
        "category_source": row["category_source"],
        "amount_cents": row["amount_cents"],
        "account_id": row["account_id"],
    }


def sum_expenses(
    conn: sqlite3.Connection,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
    search: str | None = None,
) -> int:
    where, params = _where(date_from, date_to, account_id, search)
    _, total_cents = conn.execute(f"{_TOTAL} {where}", params).fetchone()
    return int(total_cents)


def list_expenses(
    conn: sqlite3.Connection,
    *,
    page: int,
    page_size: int,
    sort: Sort = "date",
    order: Order = "desc",
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
    search: str | None = None,
) -> ExpensesPage:
    offset = (page - 1) * page_size
    where, where_params = _where(date_from, date_to, account_id, search)
    sql = _page_sql(sort, order, where)
    rows = conn.execute(sql, (*where_params, page_size, offset)).fetchall()
    total, _ = conn.execute(f"{_TOTAL} {where}", where_params).fetchone()
    total_cents = sum_expenses(
        conn,
        date_from=date_from,
        date_to=date_to,
        account_id=account_id,
        search=search,
    )
    # Reason: the payee's display name is a precedence already tested in
    # app.payees.names — resolving it here keeps the SQL free of duplicated
    # logic.
    names = labels(conn)
    items = [_item(row, names) for row in rows]
    return ExpensesPage(items=items, total=total, total_cents=int(total_cents))


def get_expense(conn: sqlite3.Connection, transaction_id: int) -> dict[str, Any] | None:
    row = conn.execute(f"{_SELECT} WHERE t.id = ?", (transaction_id,)).fetchone()
    if row is None:
        return None
    # Reason: no SPENDING filter here — this reads a single transaction by
    # id, not a page of gastos.
    return _item(row, labels(conn))


def sum_by_category(
    conn: sqlite3.Connection,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
    search: str | None = None,
) -> list[CategoryTotal]:
    where, params = _where(date_from, date_to, account_id, search)
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
