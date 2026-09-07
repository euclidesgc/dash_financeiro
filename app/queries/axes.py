import json
import sqlite3
from pathlib import Path

from app.queries.period import InvalidPeriodError, check_period
from app.queries.spending import SPENDING

__all__ = (
    "AXES",
    "PAYEE_AXIS",
    "InvalidPeriodError",
    "UnknownAxisError",
    "aggregate",
    "transactions_of",
)

AXES_PATH = Path(__file__).resolve().parent / "axes.json"

# The five axis names are interface vocabulary, and no code file of app/ may
# carry one as a literal (RF-08), so they live in data next to the mapping to
# the column each one partitions.
_COLUMNS: dict[str, str] = json.loads(AXES_PATH.read_text(encoding="utf-8"))["axes"]

AXES: tuple[str, ...] = tuple(_COLUMNS)

# Derived from the data, never spelled out: the axis names are interface
# vocabulary and no file of app/ may carry one as a literal.
PAYEE_AXIS = next(name for name, column in _COLUMNS.items() if column == "payee")

_UNKNOWN_AXIS = "eixo inválido: {value}. Eixos aceitos: {axes}"

_KEYS = {
    "group": "coalesce(g.name, '')",
    "category": "coalesce(t.category, '')",
    "payee": "coalesce(t.payee, '')",
    "nature": "coalesce(t.nature, '')",
    "essentiality": "coalesce(t.essentiality, '')",
}

# A left join keeps every spending row in every axis: an inner join would drop
# whatever a broken classification left without a group, and that axis would
# stop matching the other four without saying so (RF-20).
_FROM = "FROM transactions AS t LEFT JOIN category_groups AS g ON g.id = t.group_id"

_WINDOW = f"WHERE {SPENDING} AND t.date >= ? AND t.date <= ?"


class UnknownAxisError(LookupError):
    def __init__(self, value: object) -> None:
        super().__init__(_UNKNOWN_AXIS.format(value=value, axes=", ".join(AXES)))
        self.value = value


def aggregate(
    conn: sqlite3.Connection, *, axis: str, start: str, end: str
) -> list[sqlite3.Row]:
    key = _key(axis)
    check_period(start, end)
    return conn.execute(
        f"SELECT {key} AS key, sum(t.amount_cents) AS amount_cents, count(*) AS entries "
        f"{_FROM} {_WINDOW} GROUP BY {key} ORDER BY amount_cents, key",
        (start, end),
    ).fetchall()


def transactions_of(
    conn: sqlite3.Connection, *, axis: str, key: str, start: str, end: str
) -> list[sqlite3.Row]:
    column = _key(axis)
    check_period(start, end)
    return conn.execute(
        "SELECT t.date AS date, t.description AS description, "
        "coalesce(a.name, a.institution, t.account_id) AS account, "
        "t.amount_cents AS amount_cents "
        f"{_FROM} LEFT JOIN accounts AS a ON a.id = t.account_id "
        f"{_WINDOW} AND {column} = ? ORDER BY t.date, t.id",
        (start, end, key),
    ).fetchall()


def _key(axis: str) -> str:
    # The axis reaches SQL as a GROUP BY target, so it is resolved against the
    # declared set before touching the statement: interpolated straight, it is
    # an injection.
    if axis not in _COLUMNS:
        raise UnknownAxisError(axis)
    return _KEYS[_COLUMNS[axis]]
