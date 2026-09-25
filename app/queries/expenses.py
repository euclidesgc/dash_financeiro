import sqlite3
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

from app.db import fold
from app.payees.names import labels
from app.queries.spending import SPENDING
from app.taxonomy.seed import category_labels

Sort = Literal["date", "amount", "category"]
Order = Literal["asc", "desc"]

_ORDER_SQL: dict[Order, str] = {"asc": "ASC", "desc": "DESC"}

_SORT_SQL: dict[Sort, str] = {
    "date": "t.date {order}",
    "amount": "abs(t.amount_cents) {order}",
    "category": (
        "CASE WHEN t.category IS NULL OR t.category = '' THEN 1 ELSE 0 END, "
        "{rank} {order}, t.category"
    ),
}

_FROM = (
    "FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id"
    " LEFT JOIN payee_names AS own ON own.payee = t.payee AND own.source = 'dono'"
    " LEFT JOIN payee_names AS lk ON lk.payee = t.payee AND lk.source = 'cnpj'"
)

_SELECT = f"""SELECT t.id, t.date, t.description, t.payee, t.category, t.amount_cents,
       t.account_id,
       a.name AS account_name, a.institution AS account_institution, a.type AS account_type
{_FROM}"""

# Reason: the primary key (payee, source) guarantees at most one row per
# join, so count and sum don't multiply.
_TOTAL = f"SELECT count(*), coalesce(sum(t.amount_cents), 0) {_FROM}"
_BY_CATEGORY = (
    f"SELECT NULLIF(t.category, '') AS category, count(*) AS count,"
    f" coalesce(sum(t.amount_cents), 0) AS total {_FROM}"
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


def _category_rank_clause() -> tuple[str, list[str | int]]:
    # Reason: the pt-BR label doesn't live in the database (debt 023), and
    # SQLite's BINARY collation would put "Água" after "Z"; normalizing to
    # the base letter here keeps the sort matching what the user reads.
    labels_by_key = category_labels()
    keys = sorted(
        labels_by_key,
        key=lambda key: (
            unicodedata.normalize("NFKD", labels_by_key[key])
            .encode("ascii", "ignore")
            .decode("ascii")
            .casefold()
        ),
    )
    params: list[str | int] = []
    for position, key in enumerate(keys):
        params.append(key)
        params.append(position)
    params.append(len(keys))
    sql = "CASE t.category " + "WHEN ? THEN ? " * len(keys) + "ELSE ? END"
    return sql, params


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


def _page_sql(sort: Sort, order: Order, where: str) -> tuple[str, list[str | int]]:
    rank_sql, params = _category_rank_clause() if sort == "category" else ("", [])
    expression = _SORT_SQL[sort].format(order=_ORDER_SQL[order], rank=rank_sql)
    sql = f"{_SELECT} {where} ORDER BY {expression}, t.id DESC LIMIT ? OFFSET ?"
    return sql, params


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
    sql, order_params = _page_sql(sort, order, where)
    rows = conn.execute(sql, (*where_params, *order_params, page_size, offset)).fetchall()
    total, total_cents = conn.execute(f"{_TOTAL} {where}", where_params).fetchone()
    # Reason: the pt-BR category label lives only in the taxonomy seed, not
    # in the database, and the payee's display name is a precedence already
    # tested in app.payees.names — resolving both here keeps the SQL free of
    # duplicated logic.
    names = labels(conn)
    categories = category_labels()
    items = []
    for row in rows:
        raw_category = row["category"]
        items.append(
            {
                "id": row["id"],
                "date": row["date"],
                "description": row["description"],
                "payee_name": names.get(row["payee"]),
                "account_name": row["account_name"],
                "account_institution": row["account_institution"],
                "account_type": row["account_type"],
                "category": categories.get(raw_category, raw_category) if raw_category else None,
                "amount_cents": row["amount_cents"],
                "account_id": row["account_id"],
            }
        )
    return ExpensesPage(items=items, total=total, total_cents=int(total_cents))


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
    categories = category_labels()
    result = []
    for row in rows:
        category = row["category"]
        label = "Sem categoria" if category is None else categories.get(category, category)
        result.append(
            CategoryTotal(
                category=category,
                label=label,
                count=row["count"],
                total_cents=int(row["total"]),
            )
        )
    return result
