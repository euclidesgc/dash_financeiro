import sqlite3
from dataclasses import dataclass
from typing import Any

from app.payees.names import labels
from app.queries.spending import SPENDING
from app.taxonomy.seed import category_labels

_PAGE = f"""SELECT t.id, t.date, t.description, t.payee, t.category, t.amount_cents,
       a.name AS account_name, a.institution AS account_institution, a.type AS account_type
FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id
WHERE {SPENDING} ORDER BY t.date DESC, t.id DESC LIMIT ? OFFSET ?"""

_TOTAL = f"SELECT count(*) FROM transactions WHERE {SPENDING}"


@dataclass(frozen=True)
class ExpensesPage:
    items: list[dict[str, Any]]
    total: int


def list_expenses(conn: sqlite3.Connection, *, page: int, page_size: int) -> ExpensesPage:
    offset = (page - 1) * page_size
    rows = conn.execute(_PAGE, (page_size, offset)).fetchall()
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
