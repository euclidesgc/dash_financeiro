import sqlite3
from datetime import date
from typing import Any

from app.settings.catalog import BY_NAME, CATALOG
from app.settings.typed import InvalidValueError, parse

# Reason: None is a real argument here — it clears the deadline of a fact —
# so the absence of an argument needs a token of its own, or writing a value
# from a screen without a validity field would erase the validity typed in
# another.
UNCHANGED = object()

HUMAN = "humano"

_ALL = "SELECT name, label, value, unit, kind, source, captured_at, valid_until FROM plan_facts"
_ONE = "SELECT value FROM plan_facts WHERE name = ?"
_UPSERT = (
    "INSERT INTO plan_facts (name, label, value, unit, kind, source, captured_at, valid_until) "
    "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?) "
    "ON CONFLICT(name) DO UPDATE SET label = excluded.label, value = excluded.value, "
    "unit = excluded.unit, kind = excluded.kind, source = excluded.source, "
    "captured_at = excluded.captured_at, valid_until = excluded.valid_until"
)


def _stale(valid_until: str | None, today: date) -> bool:
    return bool(valid_until and valid_until < today.isoformat())


def stored(conn: sqlite3.Connection, *, today: date) -> list[dict[str, Any]]:
    rows = [dict(row) for row in conn.execute(f"{_ALL} ORDER BY label")]
    for row in rows:
        row["stale"] = _stale(row["valid_until"], today)
    return rows


def read(conn: sqlite3.Connection, *, today: date) -> list[dict[str, Any]]:
    known = {row["name"]: row for row in stored(conn, today=today)}
    answer = []
    for item in CATALOG:
        row = known.get(item["name"])
        answer.append(
            dict(
                item,
                value=row["value"] if row else None,
                captured_at=row["captured_at"] if row else None,
                valid_until=row["valid_until"] if row else None,
                stale=bool(row and row["stale"]),
            )
        )
    return answer


def value(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute(_ONE, (name,)).fetchone()
    return row["value"] if row else None


def entry(name: str) -> dict[str, Any]:
    # Reason: the same refusal as the classification rules of item 002 — a
    # name the catalogue does not declare is named back to the owner, never
    # written.
    item = BY_NAME.get(name)
    if item is None:
        raise InvalidValueError(f"Valor desconhecido: “{name}”.")
    if not item["stored"]:
        raise InvalidValueError(f"“{item['label']}” não é uma linha de valor: {item['help']}")
    return item


def write(
    conn: sqlite3.Connection,
    name: str,
    typed: str,
    *,
    valid_until: object = UNCHANGED,
) -> int:
    item = entry(name)
    read_value = parse(item["unit"], typed, item["label"])
    if read_value is None:
        raise InvalidValueError(f"{item['label']} precisa de um valor.")
    if valid_until is UNCHANGED:
        row = conn.execute("SELECT valid_until FROM plan_facts WHERE name = ?", (name,)).fetchone()
        valid_until = row["valid_until"] if row else None
    conn.execute(
        _UPSERT,
        (
            name,
            item["label"],
            read_value,
            item["unit"],
            item["kind"],
            HUMAN,
            valid_until,
        ),
    )
    conn.commit()
    return read_value
