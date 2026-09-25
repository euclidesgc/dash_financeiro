import re
import sqlite3

from app.db import connect
from app.queries.spending import SPENDING

MATCH_DESCRIPTION = "description"
MATCH_CATEGORY = "category"

# Reason: a bare tuple has no field names, so the order is written here
# once — rule_id (None only for the fallback), group_id, nature,
# essentiality.
_Target = tuple[int | None, int, str, str]


class MissingFallbackError(RuntimeError):
    def __init__(self, table: str) -> None:
        super().__init__(f"no fallback row in {table}: run the taxonomy seed first")
        self.table = table


def classify_all(conn: sqlite3.Connection) -> int:
    fallback = _fallback(conn)
    _record_categories(conn, fallback[1])
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
    row: sqlite3.Row = conn.execute(
        "SELECT count(*) AS entries, coalesce(sum(amount_cents), 0) AS amount_cents "
        f"FROM transactions WHERE rule_id IS NULL AND {SPENDING} AND date >= ? AND date <= ?",
        (start, end),
    ).fetchone()
    return row


def _match(
    row: sqlite3.Row,
    expressions: list[tuple[re.Pattern[str], _Target]],
    categories: dict[str, _Target],
) -> _Target | None:
    payee = row["payee"] or ""
    for pattern, target in expressions:
        if pattern.search(payee):
            return target
    return categories.get(row["category"])


def _rules(
    conn: sqlite3.Connection,
) -> tuple[list[tuple[re.Pattern[str], _Target]], dict[str, _Target]]:
    expressions: list[tuple[re.Pattern[str], _Target]] = []
    categories: dict[str, _Target] = {}
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


def _fallback(conn: sqlite3.Connection) -> _Target:
    group = conn.execute("SELECT id FROM category_groups WHERE is_fallback = 1").fetchone()
    nature = conn.execute("SELECT value FROM natures WHERE is_fallback = 1").fetchone()
    essentiality = conn.execute("SELECT value FROM essentialities WHERE is_fallback = 1").fetchone()
    for table, row in (
        ("category_groups", group),
        ("natures", nature),
        ("essentialities", essentiality),
    ):
        if row is None:
            raise MissingFallbackError(table)
    return (None, group[0], nature[0], essentiality[0])


def _record_categories(conn: sqlite3.Connection, fallback_group_id: int) -> None:
    rows = conn.execute(
        "SELECT DISTINCT category FROM transactions WHERE category IS NOT NULL AND category != ''"
    ).fetchall()
    conn.executemany(
        "INSERT INTO categories (name, group_id, label) VALUES (?, ?, ?) "
        "ON CONFLICT (name) DO NOTHING",
        [(row["category"], fallback_group_id, row["category"]) for row in rows],
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
