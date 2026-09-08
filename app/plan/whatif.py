import re
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.plan.timeline import BASE, simulate
from app.settings.store import stored
from app.settings.typed import InvalidValueError, parse_money, parse_months

DAYS_IN_MONTH = 30
INCOME = "receita"
EXPENSE = "despesa"
KINDS = (INCOME, EXPENSE)


@dataclass(frozen=True)
class Move:
    kind: str
    monthly_cents: int
    once_cents: int
    months: int | None


def signed_monthly(move: Move) -> int:
    return move.monthly_cents if move.kind == INCOME else -move.monthly_cents


def impact(conn: sqlite3.Connection, move: Move, *, today: date) -> dict[str, Any]:
    # The answer is in days because the unit of this product is days until the
    # objective. Reais are the input; the output is distance.
    before = simulate(conn, BASE, today=today)
    after = simulate(
        conn,
        BASE,
        today=today,
        extra_monthly_cents=signed_monthly(move),
        extra_months=move.months,
        extra_once_cents=move.once_cents if move.kind == INCOME else -move.once_cents,
    )
    return {
        "months": move.months,
        "once_cents": move.once_cents,
        "before": before,
        "after": after,
        "monthly_delta_cents": signed_monthly(move),
        "days_delta": _days_between(before["months_to_objective"], after["months_to_objective"]),
        "reachable_before": before["months_to_objective"] is not None,
        "reachable_after": after["months_to_objective"] is not None,
    }


def _days_between(before: int | None, after: int | None) -> int | None:
    # No number at all when either side has no date: a scenario that turns
    # "never" into "eleven years" moved the world, and calling that a difference
    # of N days would be inventing an arithmetic that has no first term.
    if before is None or after is None:
        return None
    return (after - before) * DAYS_IN_MONTH


VALID_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_validity(typed: str) -> str | None:
    # Stored raw, the staleness of a fact was decided by comparing strings:
    # "banana" is never less than a date, so a validity typed wrong left the fact
    # looking fresh forever — which is exactly what the field exists to prevent.
    cleaned = (typed or "").strip()
    if not cleaned:
        return None
    if not VALID_DATE.match(cleaned):
        raise InvalidValueError(f"Validade inválida: “{typed}”. Use AAAA-MM-DD.")
    try:
        date.fromisoformat(cleaned)
    except ValueError:
        raise InvalidValueError(f"Validade inválida: “{typed}”. Use AAAA-MM-DD.") from None
    return cleaned


def parse_move(kind: str, monthly: str, once: str, months: str) -> Move:
    if kind not in KINDS:
        raise InvalidValueError(f"Tipo desconhecido: “{kind}”. Use receita ou despesa.")
    return Move(
        kind=kind,
        monthly_cents=parse_money(monthly, "Valor mensal"),
        once_cents=parse_money(once, "Valor único", allow_zero=True),
        months=parse_months(months, "Prazo"),
    )


def save(conn: sqlite3.Connection, name: str, move: Move) -> None:
    if not (name or "").strip():
        raise InvalidValueError("O cenário precisa de um nome.")
    conn.execute(
        "INSERT OR REPLACE INTO scenarios "
        "(name, created_at, kind, monthly_cents, once_cents, months) "
        "VALUES (?, datetime('now'), ?, ?, ?, ?)",
        (name.strip(), move.kind, move.monthly_cents, move.once_cents, move.months),
    )
    conn.commit()


def saved(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM scenarios ORDER BY name")]


def facts(conn: sqlite3.Connection, *, today: date) -> list[dict[str, Any]]:
    return stored(conn, today=today)
