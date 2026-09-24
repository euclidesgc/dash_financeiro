import sqlite3

# Reason: money moved between the owner's own accounts, and money given
# back, never left the house — counting it as spending makes the total
# report an outflow that never happened (invariant 25). Every spending query
# reads this one string — repeated per query, it gets forgotten in one of
# them, and the panel then lies on a single axis, which is the most
# expensive way to be wrong.
_CLEAN = "is_transfer = 0 AND is_refund = 0 AND refunded_by IS NULL"
OUTFLOW = f"amount_cents < 0 AND {_CLEAN}"
INFLOW = f"amount_cents > 0 AND {_CLEAN}"
SPENDING = f"{OUTFLOW} AND not_expense_reason IS NULL"
INCOME = f"{INFLOW} AND not_expense_reason IS NULL"
EXCLUDED = f"amount_cents <> 0 AND {_CLEAN} AND not_expense_reason IS NOT NULL"

_TOTAL_SPENDING = f"SELECT coalesce(sum(amount_cents), 0) FROM transactions WHERE {SPENDING}"


def date_window(
    date_from: str | None, date_to: str | None, column: str = "date"
) -> tuple[str, list[str]]:
    sql = ""
    params: list[str] = []
    if date_from is not None:
        sql += f" AND {column} >= ?"
        params.append(date_from)
    if date_to is not None:
        sql += f" AND {column} <= ?"
        params.append(date_to)
    return sql, params


def total_spending_cents(
    conn: sqlite3.Connection, start: str | None = None, end: str | None = None
) -> int:
    window, params = date_window(start, end)
    sql = f"{_TOTAL_SPENDING}{window}"
    return int(conn.execute(sql, params).fetchone()[0])
