import re
import sqlite3
from dataclasses import dataclass
from datetime import date

from app.plan.timeline import BASE, simulate

DAYS_IN_MONTH = 30
INCOME = "receita"
EXPENSE = "despesa"
KINDS = (INCOME, EXPENSE)


class InvalidScenarioError(ValueError):
    pass


@dataclass(frozen=True)
class Move:
    kind: str
    monthly_cents: int
    once_cents: int
    months: int | None


def signed_monthly(move: Move) -> int:
    return move.monthly_cents if move.kind == INCOME else -move.monthly_cents


def impact(conn: sqlite3.Connection, move: Move, *, today: date) -> dict:
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
        raise InvalidScenarioError(f"Validade inválida: “{typed}”. Use AAAA-MM-DD.")
    try:
        date.fromisoformat(cleaned)
    except ValueError:
        raise InvalidScenarioError(f"Validade inválida: “{typed}”. Use AAAA-MM-DD.") from None
    return cleaned


def parse_move(kind: str, monthly: str, once: str, months: str) -> Move:
    if kind not in KINDS:
        raise InvalidScenarioError(f"Tipo desconhecido: “{kind}”. Use receita ou despesa.")
    return Move(
        kind=kind,
        monthly_cents=_cents(monthly, "Valor mensal"),
        once_cents=_cents(once, "Valor único", allow_zero=True),
        months=_whole(months),
    )


# A ceiling, not a nicety: past three hundred digits float() returns inf and
# round(inf) raises, which is a 500 on a money field — the very class of defect
# the strict reading exists to close. Twelve digits is more money than this
# panel will ever be asked about.
MAX_DIGITS = 12

_MONEY = re.compile(r"^\d{1,3}(\.\d{3})*(,\d{1,2})?$|^\d+(,\d{1,2})?$")


def _cents(typed: str, field: str, *, allow_zero: bool = False) -> int:
    # Read strictly in the Brazilian form. Stripping every dot as a thousands
    # separator turned "5000.00" into five hundred thousand reais, accepted,
    # displayed and stored without a word — on a screen that decides money
    # (RF-14). Anything that is not the written form is refused by name.
    cleaned = (typed or "").strip().replace("R$", "").replace(" ", "")
    if not cleaned and allow_zero:
        return 0
    if not _MONEY.match(cleaned) or len(cleaned.replace(".", "").replace(",", "")) > MAX_DIGITS:
        raise InvalidScenarioError(
            f"{field} inválido: “{typed}”. Escreva na forma 1.234,56, "
            f"com no máximo {MAX_DIGITS} algarismos."
        )
    units, _, decimals = cleaned.replace(".", "").partition(",")
    # Integer cents from integer parts: float would stop being exact long before
    # the ceiling above, and the invariant of this base is integer cents.
    cents = int(units or 0) * 100 + int((decimals or "0").ljust(2, "0"))
    if cents == 0 and not allow_zero:
        raise InvalidScenarioError(f"{field} precisa ser maior que zero.")
    return cents


def _whole(typed: str) -> int | None:
    cleaned = (typed or "").strip()
    if not cleaned:
        return None
    try:
        value = int(cleaned)
    except ValueError:
        raise InvalidScenarioError(f"Prazo inválido: “{typed}”. Use um número de meses.") from None
    if value <= 0:
        raise InvalidScenarioError("O prazo precisa ser maior que zero.")
    return value


def save(conn: sqlite3.Connection, name: str, move: Move) -> None:
    if not (name or "").strip():
        raise InvalidScenarioError("O cenário precisa de um nome.")
    conn.execute(
        "INSERT OR REPLACE INTO scenarios "
        "(name, created_at, kind, monthly_cents, once_cents, months) "
        "VALUES (?, datetime('now'), ?, ?, ?, ?)",
        (name.strip(), move.kind, move.monthly_cents, move.once_cents, move.months),
    )
    conn.commit()


def saved(conn: sqlite3.Connection) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM scenarios ORDER BY name")]


def facts(conn: sqlite3.Connection, *, today: date) -> list[dict]:
    rows = [dict(row) for row in conn.execute("SELECT * FROM plan_facts ORDER BY label")]
    for row in rows:
        row["stale"] = bool(row["valid_until"] and row["valid_until"] < today.isoformat())
    return rows
