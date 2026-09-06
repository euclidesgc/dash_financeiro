import sqlite3

# Money moved between the owner's own accounts, and money given back, never
# left the house: counting it as spending makes the total report an outflow
# that never happened (invariant 25).
_TOTAL_SPENDING = (
    "SELECT coalesce(sum(amount_cents), 0) FROM transactions "
    "WHERE amount_cents < 0 AND is_transfer = 0 AND is_refund = 0 AND refunded_by IS NULL"
)


def total_spending_cents(
    conn: sqlite3.Connection, start: str | None = None, end: str | None = None
) -> int:
    sql = _TOTAL_SPENDING
    params: list[str] = []
    if start is not None:
        sql += " AND date >= ?"
        params.append(start)
    if end is not None:
        sql += " AND date <= ?"
        params.append(end)
    return int(conn.execute(sql, params).fetchone()[0])
