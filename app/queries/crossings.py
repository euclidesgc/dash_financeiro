import sqlite3
from dataclasses import dataclass
from datetime import date

from app.queries.spending import SPENDING

_DEFINITION = "SELECT label, nature, essentiality FROM crossings WHERE slug = ?"
_DEFINITIONS = "SELECT slug, label, nature, essentiality FROM crossings ORDER BY position"

_ROWS = (
    "SELECT category AS key, sum(amount_cents) AS amount_cents, count(*) AS entries "
    f"FROM transactions WHERE {SPENDING} AND nature = ? AND essentiality = ? "
    "AND date >= ? AND date <= ? "
    "GROUP BY category ORDER BY amount_cents, key"
)


class UnknownCrossingError(LookupError):
    def __init__(self, slug: object) -> None:
        super().__init__(f"no crossing with slug {slug!r}: run the taxonomy seed first")
        self.slug = slug


@dataclass(frozen=True)
class Crossing:
    label: str
    rows: list[sqlite3.Row]
    total_cents: int
    monthly_average_cents: int


def crossing(conn: sqlite3.Connection, *, slug: str, start: str, end: str) -> Crossing:
    definition = conn.execute(_DEFINITION, (slug,)).fetchone()
    if definition is None:
        raise UnknownCrossingError(slug)
    rows = conn.execute(
        _ROWS, (definition["nature"], definition["essentiality"], start, end)
    ).fetchall()
    total = sum(row["amount_cents"] for row in rows)
    return Crossing(
        label=definition["label"],
        rows=rows,
        total_cents=total,
        # Reason: the monthly average is what sizes the reserve of item 007,
        # so it is read from the same rows as the total instead of being
        # divided again by each screen that shows the crossing.
        monthly_average_cents=round(total / _months(start, end)),
    )


def crossing_definitions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(_DEFINITIONS).fetchall()


# Reason: the candidates a crossing offers when no rule assigns its term are
# the crossing's own rows read under the fallback term — the same query, so
# the block the owner decides from and the block the decision fills never
# disagree on what a row is.
def candidates(
    conn: sqlite3.Connection, *, nature: str, term: str, start: str, end: str, limit: int
) -> list[sqlite3.Row]:
    return conn.execute(f"{_ROWS} LIMIT ?", (nature, term, start, end, limit)).fetchall()


def _months(start: str, end: str) -> int:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    return (last.year - first.year) * 12 + last.month - first.month + 1
