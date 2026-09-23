import sqlite3
from dataclasses import dataclass

from app.taxonomy.seed import UNCATEGORISED

_SELECT = (
    "SELECT c.name, c.label, c.is_system, c.monthly_limit_cents, count(t.id) AS usage_count "
    "FROM categories AS c LEFT JOIN transactions AS t ON t.category = c.name"
)


@dataclass(frozen=True)
class CategoryRow:
    key: str
    label: str
    is_system: bool
    usage_count: int
    monthly_limit_cents: int | None


def _row(row: sqlite3.Row) -> CategoryRow:
    return CategoryRow(
        key=row["name"],
        label=row["label"],
        is_system=bool(row["is_system"]),
        usage_count=int(row["usage_count"]),
        monthly_limit_cents=None
        if row["monthly_limit_cents"] is None
        else int(row["monthly_limit_cents"]),
    )


def list_categories(conn: sqlite3.Connection) -> list[CategoryRow]:
    rows = conn.execute(
        f"{_SELECT} WHERE c.name != ? GROUP BY c.id ORDER BY fold(c.label), c.name",
        (UNCATEGORISED,),
    ).fetchall()
    return [_row(row) for row in rows]


# Reason: usage_count counts every transaction with the key, not just
# spending — deleting a category a transfer still uses would leave an
# orphan key.
def get_category(conn: sqlite3.Connection, key: str) -> CategoryRow | None:
    row = conn.execute(f"{_SELECT} WHERE c.name = ? GROUP BY c.id", (key,)).fetchone()
    return None if row is None else _row(row)
