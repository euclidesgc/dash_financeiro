import sqlite3
from typing import Any

from app.accounts import CREDIT

# Motivo (D-006): GROUP BY a.name before the join with the series is what
# stops two accounts with the same name from doubling the curve while the
# total beside it stays right. c.due_day is left out on purpose: it is the
# day the series was charged, not the day the invoice is due, and the two
# share a name.
_CARD_SERIES = (
    "SELECT g.card_name, g.closing_day, g.due_day, c.series_key, c.description, "
    "c.amount_cents, c.installments_left, c.last_seen_date, c.ends_month "
    "  FROM (SELECT a.name AS card_name, MAX(k.closing_day) AS closing_day, "
    "               MAX(k.due_day) AS due_day "
    "          FROM accounts a LEFT JOIN cards k ON k.account_id = a.id "
    "         WHERE a.type = ? "
    "         GROUP BY a.name) g "
    "  LEFT JOIN commitments c "
    "    ON c.account = g.card_name AND c.kind = ? "
    "   AND c.installments_left > 0 AND c.last_seen_date >= ? "
    " ORDER BY g.card_name, c.amount_cents * c.installments_left, c.series_key"
)


def card_series(conn: sqlite3.Connection, *, kind: str, floor: str) -> list[dict[str, Any]]:
    rows = conn.execute(_CARD_SERIES, (CREDIT, kind, floor)).fetchall()
    return [dict(row) for row in rows]
