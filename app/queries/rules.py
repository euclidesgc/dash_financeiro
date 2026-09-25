import sqlite3

from app.queries.spending import SPENDING, date_window

__all__ = (
    "held_by_rule",
    "payee_samples",
    "residue",
    "rule",
    "rule_candidates",
    "rule_id_of",
    "rule_listing",
    "rules_carrying",
)

_LISTING = (
    "SELECT r.id AS id, r.match_kind AS match_kind, r.match_value AS match_value, "
    "r.group_id AS group_id, g.name AS group_name, r.nature AS nature, "
    "r.essentiality AS essentiality, count(t.id) AS entries, "
    f"coalesce(sum(CASE WHEN {SPENDING} THEN t.amount_cents END), 0) AS amount_cents "
    "FROM category_rules AS r JOIN category_groups AS g ON g.id = r.group_id "
    "LEFT JOIN transactions AS t ON t.rule_id = r.id "
    "GROUP BY r.id ORDER BY amount_cents, r.match_value"
)

_RULE = (
    "SELECT id, match_kind, match_value, group_id, nature, essentiality "
    "FROM category_rules WHERE id = ?"
)

_RULE_OF = "SELECT id FROM category_rules WHERE match_kind = ? AND match_value = ?"

_HELD = "SELECT count(*) FROM transactions WHERE rule_id = ?"

_CARRYING = "SELECT count(*) FROM category_rules WHERE essentiality = ?"

# Reason: the rules screen asks it over the whole base and the spending
# panel over its period; one template keeps both screens reading the same
# loose money.
_RESIDUE = (
    "SELECT count(*) AS entries, coalesce(sum(amount_cents), 0) AS amount_cents "
    f"FROM transactions WHERE rule_id IS NULL AND {SPENDING}"
)

# Reason: a rule is not bound to a period, so neither is what is missing
# one — the two readings of the same loose money — the category it carries
# and the payee it paid — are the two shapes a rule can take, and the money
# orders them.
_CANDIDATES = (
    "SELECT ? AS kind, category AS value, count(*) AS entries, "
    "sum(amount_cents) AS amount_cents FROM transactions "
    f"WHERE rule_id IS NULL AND {SPENDING} AND category IS NOT NULL AND category != '' "
    "GROUP BY category UNION ALL "
    "SELECT ? AS kind, payee AS value, count(*) AS entries, "
    "sum(amount_cents) AS amount_cents FROM transactions "
    f"WHERE rule_id IS NULL AND {SPENDING} AND payee IS NOT NULL AND payee != '' "
    "GROUP BY payee ORDER BY amount_cents LIMIT ?"
)

_SAMPLES = (
    "SELECT payee AS value FROM transactions WHERE payee IS NOT NULL AND payee != '' "
    "GROUP BY payee ORDER BY count(*) DESC, payee LIMIT ?"
)


def rule_listing(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(_LISTING).fetchall()


def rule(conn: sqlite3.Connection, rule_id: str | int) -> sqlite3.Row | None:
    row: sqlite3.Row | None = conn.execute(_RULE, (rule_id,)).fetchone()
    return row


def rule_id_of(conn: sqlite3.Connection, *, match_kind: str, match_value: str) -> int | None:
    row = conn.execute(_RULE_OF, (match_kind, match_value)).fetchone()
    return None if row is None else int(row["id"])


def held_by_rule(conn: sqlite3.Connection, rule_id: int) -> int:
    return int(conn.execute(_HELD, (rule_id,)).fetchone()[0])


def rules_carrying(conn: sqlite3.Connection, term: str) -> int:
    return int(conn.execute(_CARRYING, (term,)).fetchone()[0])


def residue(
    conn: sqlite3.Connection, *, start: str | None = None, end: str | None = None
) -> sqlite3.Row:
    window, params = date_window(start, end)
    row: sqlite3.Row = conn.execute(f"{_RESIDUE}{window}", params).fetchone()
    return row


def rule_candidates(
    conn: sqlite3.Connection, *, category_kind: str, payee_kind: str, limit: int
) -> list[sqlite3.Row]:
    return conn.execute(_CANDIDATES, (category_kind, payee_kind, limit)).fetchall()


def payee_samples(conn: sqlite3.Connection, limit: int) -> list[str]:
    return [row["value"] for row in conn.execute(_SAMPLES, (limit,))]
