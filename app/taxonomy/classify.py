import re
import sqlite3

from app.db import connect
from app.ingest.normalize import normalize_description

MATCH_DESCRIPTION = "description"
MATCH_CATEGORY = "category"

# Money moved between the owner's own accounts, and money given back, never
# left the house; counting either as spending inflates the residue the panel
# offers for correction (invariant 25).
_SPENDING = "amount_cents < 0 AND is_transfer = 0 AND is_refund = 0 AND refunded_by IS NULL"


class MissingFallbackError(RuntimeError):
    def __init__(self, table: str) -> None:
        super().__init__(f"no fallback row in {table}: run the taxonomy seed first")
        self.table = table


def classify_all(conn: sqlite3.Connection) -> int:
    _fill_payees(conn)
    _record_categories(conn)
    fallback = _fallback(conn)
    expressions, categories = _rules(conn)
    updates = []
    for row in conn.execute(
        "SELECT id, payee, category, rule_id, group_id, nature, essentiality FROM transactions"
    ).fetchall():
        target = _match(row, expressions, categories) or fallback
        current = (row["rule_id"], row["group_id"], row["nature"], row["essentiality"])
        if current != target:
            updates.append((*target, row["id"]))
    conn.executemany(
        "UPDATE transactions SET rule_id = ?, group_id = ?, nature = ?, essentiality = ? "
        "WHERE id = ?",
        updates,
    )
    return len(updates)


def residue(conn: sqlite3.Connection, *, start: str, end: str) -> sqlite3.Row:
    return conn.execute(
        "SELECT count(*) AS entries, coalesce(sum(amount_cents), 0) AS amount_cents "
        f"FROM transactions WHERE rule_id IS NULL AND {_SPENDING} AND date >= ? AND date <= ?",
        (start, end),
    ).fetchone()


def _match(
    row: sqlite3.Row,
    expressions: list[tuple[re.Pattern[str], tuple]],
    categories: dict[str, tuple],
) -> tuple | None:
    payee = row["payee"] or ""
    for pattern, target in expressions:
        if pattern.search(payee):
            return target
    return categories.get(row["category"])


def _rules(
    conn: sqlite3.Connection,
) -> tuple[list[tuple[re.Pattern[str], tuple]], dict[str, tuple]]:
    expressions: list[tuple[re.Pattern[str], tuple]] = []
    categories: dict[str, tuple] = {}
    for rule in conn.execute(
        "SELECT id, match_kind, match_value, group_id, nature, essentiality "
        "FROM category_rules ORDER BY id"
    ):
        target = (rule["id"], rule["group_id"], rule["nature"], rule["essentiality"])
        if rule["match_kind"] == MATCH_DESCRIPTION:
            expressions.append((re.compile(rule["match_value"]), target))
        elif rule["match_kind"] == MATCH_CATEGORY:
            categories.setdefault(rule["match_value"], target)
    return expressions, categories


def _fallback(conn: sqlite3.Connection) -> tuple:
    group = conn.execute("SELECT id FROM category_groups WHERE is_fallback = 1").fetchone()
    nature = conn.execute("SELECT value FROM natures WHERE is_fallback = 1").fetchone()
    essentiality = conn.execute(
        "SELECT value FROM essentialities WHERE is_fallback = 1"
    ).fetchone()
    for table, row in (
        ("category_groups", group),
        ("natures", nature),
        ("essentialities", essentiality),
    ):
        if row is None:
            raise MissingFallbackError(table)
    return (None, group[0], nature[0], essentiality[0])


def _fill_payees(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id, description FROM transactions WHERE payee IS NULL OR payee = ''"
    ).fetchall()
    conn.executemany(
        "UPDATE transactions SET payee = ? WHERE id = ?",
        [(normalize_description(row["description"]), row["id"]) for row in rows],
    )


def _record_categories(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO categories (name) VALUES (?) ON CONFLICT (name) DO NOTHING",
        conn.execute(
            "SELECT DISTINCT category FROM transactions "
            "WHERE category IS NOT NULL AND category != ''"
        ).fetchall(),
    )


def main() -> int:
    conn = connect()
    try:
        changed = classify_all(conn)
        conn.commit()
        total = conn.execute("SELECT count(*) FROM transactions").fetchone()[0]
        unmatched = conn.execute(
            "SELECT count(*) FROM transactions WHERE rule_id IS NULL"
        ).fetchone()[0]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"classified {total}: changed={changed} without_rule={unmatched}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
