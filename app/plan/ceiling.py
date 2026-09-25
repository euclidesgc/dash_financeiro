import sqlite3
from dataclasses import dataclass

from app.settings import store
from app.settings.catalog import MONTHLY_CEILING
from app.settings.limits import MAX_CENTS
from app.taxonomy.limits import Scope, Signal, signal_for


class InvalidCeilingError(ValueError):
    def __init__(self, cents: int) -> None:
        self.cents = cents
        super().__init__(f"Teto inválido: {cents}")


def read_ceiling(conn: sqlite3.Connection) -> int | None:
    return store.value(conn, MONTHLY_CEILING)


def set_ceiling(conn: sqlite3.Connection, cents: int | None) -> None:
    if cents is not None and not 0 < cents <= MAX_CENTS:
        raise InvalidCeilingError(cents)
    store.put(conn, MONTHLY_CEILING, cents)


@dataclass(frozen=True)
class MonthSignal:
    scope: Scope
    spent_cents: int
    ceiling_cents: int | None
    signal: Signal | None
    remaining_cents: int | None


def month_signal(*, spent_cents: int, ceiling_cents: int | None, whole_month: bool) -> MonthSignal:
    scope: Scope = "month" if whole_month else "none"
    signal = signal_for(spent_cents, ceiling_cents) if scope == "month" else None
    remaining = (
        ceiling_cents - spent_cents if scope == "month" and ceiling_cents is not None else None
    )
    return MonthSignal(
        scope=scope,
        spent_cents=spent_cents,
        ceiling_cents=ceiling_cents,
        signal=signal,
        remaining_cents=remaining,
    )
