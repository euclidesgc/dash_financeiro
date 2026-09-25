import sqlite3

from app.queries.spending import SPENDING

__all__ = ("category_reach", "correction_target", "holders", "payee_reach", "rule_reach")

# Reason: the preview a screen shows before writing and the reach the
# write measures after it share this one template — two different SQL
# strings for the same question drift apart at the first edit, and the
# panel starts promising a number and delivering another (RF-02).
_REACH = (
    "SELECT count(*) AS entries, coalesce(sum(amount_cents), 0) AS amount_cents "
    f"FROM transactions WHERE {SPENDING} AND {{filtro}}"
)

_HOLDERS = (
    "SELECT DISTINCT r.id AS id, r.match_value AS match_value "
    "FROM transactions AS t JOIN category_rules AS r ON r.id = t.rule_id "
    "WHERE t.payee = ? AND t.category_source = 'auto' AND r.id != ? ORDER BY r.id"
)

_TARGET = (
    "SELECT id, payee, category, group_id, nature, essentiality FROM transactions WHERE id = ?"
)


# Reason: a row whose category the owner chose by hand is classified by
# that category alone (app/taxonomy/classify.py:_match), so no payee rule
# ever moves it — counting it would promise the correction a reach it
# cannot deliver.
def payee_reach(conn: sqlite3.Connection, payee: str) -> sqlite3.Row:
    row: sqlite3.Row = conn.execute(
        _REACH.format(filtro="payee = ? AND category_source = 'auto'"), (payee,)
    ).fetchone()
    return row


def category_reach(conn: sqlite3.Connection, category: str) -> sqlite3.Row:
    row: sqlite3.Row = conn.execute(_REACH.format(filtro="category = ?"), (category,)).fetchone()
    return row


def rule_reach(conn: sqlite3.Connection, rule_id: int) -> sqlite3.Row:
    row: sqlite3.Row = conn.execute(_REACH.format(filtro="rule_id = ?"), (rule_id,)).fetchone()
    return row


def holders(conn: sqlite3.Connection, *, payee: str, rule_id: int) -> list[sqlite3.Row]:
    return conn.execute(_HOLDERS, (payee, rule_id)).fetchall()


def correction_target(conn: sqlite3.Connection, transaction_id: int) -> sqlite3.Row | None:
    row: sqlite3.Row | None = conn.execute(_TARGET, (transaction_id,)).fetchone()
    return row
