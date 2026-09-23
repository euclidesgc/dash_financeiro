import sqlite3
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

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

_SELECT = f"""SELECT t.id, t.date, t.description, t.payee, t.category, t.amount_cents,
       a.name AS account_name, a.institution AS account_institution, a.type AS account_type
FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id
WHERE {SPENDING}"""

_TOTAL = f"SELECT count(*) FROM transactions WHERE {SPENDING}"


@dataclass(frozen=True)
class ExpensesPage:
    items: list[dict[str, Any]]
    total: int


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


def _page_sql(sort: Sort, order: Order) -> tuple[str, list[str | int]]:
    rank_sql, params = _category_rank_clause() if sort == "category" else ("", [])
    expression = _SORT_SQL[sort].format(order=_ORDER_SQL[order], rank=rank_sql)
    sql = f"{_SELECT} ORDER BY {expression}, t.id DESC LIMIT ? OFFSET ?"
    return sql, params


def list_expenses(
    conn: sqlite3.Connection,
    *,
    page: int,
    page_size: int,
    sort: Sort = "date",
    order: Order = "desc",
) -> ExpensesPage:
    offset = (page - 1) * page_size
    sql, order_params = _page_sql(sort, order)
    rows = conn.execute(sql, (*order_params, page_size, offset)).fetchall()
    total = conn.execute(_TOTAL).fetchone()[0]
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
            }
        )
    return ExpensesPage(items=items, total=total)
