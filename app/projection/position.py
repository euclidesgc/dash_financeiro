import sqlite3

from app.accounts import BANK, CREDIT

_BY_TYPE = "SELECT type, COALESCE(SUM(balance_cents), 0) AS total FROM accounts GROUP BY type"


def positions(conn: sqlite3.Connection) -> dict:
    # Three numbers, never one. Of the consolidated position, the card share is
    # debt at ~51% a year and the bank share is what falls into the overdraft:
    # a screen showing only the sum hides which of the two is on fire (RF-04).
    totals = {row["type"]: row["total"] for row in conn.execute(_BY_TYPE)}
    cash = totals.get(BANK, 0)
    card = totals.get(CREDIT, 0)
    return {
        "cash_cents": cash,
        "card_cents": card,
        "consolidated_cents": cash + card,
    }
