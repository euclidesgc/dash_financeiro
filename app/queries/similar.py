import sqlite3

from app.queries.spending import SPENDING

# Reason: the description branch only holds while the origin has no payee
# (a freshly ingested row not yet classified); SPENDING enters as an id IN
# (…) subquery because the string carries no alias (debt 025).
SIMILAR_IDS = (
    "SELECT s.id FROM transactions AS s "
    "JOIN transactions AS o ON o.id = ? "
    "WHERE s.id != o.id "
    f"AND s.id IN (SELECT id FROM transactions WHERE {SPENDING}) "
    "AND CASE WHEN o.payee IS NOT NULL AND o.payee != '' "
    "THEN s.payee = o.payee "
    "ELSE o.description IS NOT NULL AND fold(s.description) = fold(o.description) END"
)


def count_similar(conn: sqlite3.Connection, transaction_id: int) -> int:
    row = conn.execute(f"SELECT count(*) FROM ({SIMILAR_IDS})", (transaction_id,)).fetchone()
    return int(row[0])
