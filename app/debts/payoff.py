import calendar
import sqlite3
from dataclasses import dataclass
from datetime import date

from app.commitments import INSTALLMENT
from app.commitments.live import charged
from app.debts.ladder import CARD, OVERDRAFT, ladder, without_rate
from app.financings import MORTGAGE, VEHICLE
from app.financings import store as financings_store
from app.financings.math import remaining_months
from app.queries.period import shift
from app.settings import store as settings_store
from app.settings.catalog import SETTLEMENT

CARD_INSTALLMENT = "card_installment"
KINDS = (OVERDRAFT, CARD, VEHICLE, MORTGAGE, CARD_INSTALLMENT)

INFORMED = "informed"
BALANCE = "balance"
NOMINAL = "nominal"

MAX_SAVING_MONTHS = 600
DEBT_KEY = "debt"
SERIES_KEY = "installment"


@dataclass(frozen=True)
class Debt:
    key: str
    kind: str
    name: str
    account: str | None
    balance_cents: int | None
    payment_cents: int | None
    first_due: date | None
    installment_total: int | None
    settlement_cents: int | None
    settlement_valid_until: str | None


@dataclass(frozen=True)
class Payoff:
    day: date
    payoff_cents: int | None
    nominal_cents: int | None
    installments_left: int | None
    end_month: str | None
    basis: str
    target_cents: int
    missing_settlement: bool


@dataclass(frozen=True)
class SavingPlan:
    payoff: Payoff
    months: int | None
    monthly_cents: int
    reached_month: str | None


class PastTargetError(ValueError):
    pass


class InvalidSavingError(ValueError):
    pass


def _month(day: date) -> str:
    return day.strftime("%Y-%m")


def _distance(later: date, earlier: date) -> int:
    return (later.year - earlier.year) * 12 + later.month - earlier.month


def _month_end(day: date) -> date:
    return date(day.year, day.month, calendar.monthrange(day.year, day.month)[1])


def _on_day(month: date, day: int) -> date:
    return date(month.year, month.month, min(day, calendar.monthrange(month.year, month.month)[1]))


def _settlement(conn: sqlite3.Connection, today: date) -> tuple[int | None, str | None]:
    found = next(
        (row for row in settings_store.stored(conn, today=today) if row["name"] == SETTLEMENT),
        None,
    )
    if found is None:
        return None, None
    return found["value"], found["valid_until"]


def _series_first_due(last_seen: str, last_installment: int) -> date:
    # Reason: the first instalment is dated back from the last one seen, so a
    # series whose invoice already posted every future charge is counted by
    # the same instalments_due as a financing contract.
    seen = date.fromisoformat(last_seen)
    return _on_day(shift(seen, 1 - last_installment), seen.day)


def list_debts(conn: sqlite3.Connection, *, today: date) -> list[Debt]:
    debts: list[Debt] = []
    settlement, valid_until = _settlement(conn, today)
    vehicle = financings_store.read(conn, VEHICLE)
    for row in ladder(conn) + without_rate(conn):
        key = f"{DEBT_KEY}-{row['id']}"
        if row["kind"] == VEHICLE:
            if vehicle is None or vehicle["first_due_date"] is None:
                continue
            first_due = date.fromisoformat(vehicle["first_due_date"])
            if remaining_months(first_due, vehicle["term_months"], today) <= 0:
                continue
            debts.append(
                Debt(
                    key=key,
                    kind=VEHICLE,
                    name=row["name"],
                    account=None,
                    balance_cents=None,
                    payment_cents=vehicle["payment_cents"],
                    first_due=first_due,
                    installment_total=vehicle["term_months"],
                    settlement_cents=settlement,
                    settlement_valid_until=valid_until,
                )
            )
            continue
        debts.append(
            Debt(
                key=key,
                kind=row["kind"],
                name=row["name"],
                account=None,
                balance_cents=row["balance_cents"],
                payment_cents=None,
                first_due=None,
                installment_total=row["term_months"] if row["kind"] == MORTGAGE else None,
                settlement_cents=None,
                settlement_valid_until=None,
            )
        )
    for row in charged(conn, today=today):
        if row["kind"] != INSTALLMENT or row["last_installment"] is None:
            continue
        debt = Debt(
            key=f"{SERIES_KEY}-{row['id']}",
            kind=CARD_INSTALLMENT,
            name=row["description"],
            account=row["account"],
            balance_cents=None,
            payment_cents=row["amount_cents"],
            first_due=_series_first_due(row["last_seen_date"], row["last_installment"]),
            installment_total=row["installment_total"],
            settlement_cents=None,
            settlement_valid_until=None,
        )
        if _left(debt, today):
            debts.append(debt)
    return debts


def unnumbered(conn: sqlite3.Connection, *, today: date) -> list[str]:
    return [
        row["description"]
        for row in charged(conn, today=today)
        if row["kind"] == INSTALLMENT and row["last_installment"] is None
    ]


def _left(debt: Debt, day: date) -> int:
    if debt.first_due is None or debt.installment_total is None:
        return 0
    return remaining_months(debt.first_due, debt.installment_total, day)


def _last_month(debt: Debt) -> str | None:
    if debt.first_due is None or debt.installment_total is None:
        return None
    return _month(shift(debt.first_due, debt.installment_total - 1))


def _informed_applies(debt: Debt, day: date, today: date) -> bool:
    # Reason: the bank quotes the settlement for now. Months ahead the
    # instalments paid meanwhile have already lowered it, and reusing the
    # quote would ask the owner to save for money he no longer owes.
    if debt.settlement_cents is None or _month(day) != _month(today):
        return False
    return debt.settlement_valid_until is None or debt.settlement_valid_until >= day.isoformat()


def payoff_at(debt: Debt, day: date, *, today: date) -> Payoff:
    if debt.first_due is None:
        balance = abs(debt.balance_cents or 0)
        return Payoff(
            day=day,
            payoff_cents=balance,
            nominal_cents=None,
            installments_left=debt.installment_total,
            end_month=None,
            basis=BALANCE,
            target_cents=balance,
            missing_settlement=False,
        )
    left = _left(debt, day)
    nominal = abs(debt.payment_cents or 0) * left
    ends = _last_month(debt) if left else None
    if debt.kind == CARD_INSTALLMENT:
        # Decision: an instalment purchase settles at its nominal remainder.
        # The discount for paying ahead is the issuer's to quote, and the
        # panel does not invent it.
        return Payoff(day, nominal, nominal, left, ends, NOMINAL, nominal, False)
    if _informed_applies(debt, day, today) and left:
        informed = abs(debt.settlement_cents or 0)
        return Payoff(day, informed, nominal, left, ends, INFORMED, informed, False)
    # Reason: without the bank's quote the payoff is unknown (invariant 26).
    # The nominal remainder is the ceiling the owner can save for, never a
    # payoff the panel made up with a discount of its own.
    return Payoff(day, None, nominal, left, ends, NOMINAL, nominal, bool(left))


def _ceil_div(amount: int, parts: int) -> int:
    return -(-amount // parts)


def saving_plan(
    debt: Debt,
    *,
    today: date,
    target_date: date | None = None,
    monthly_saving_cents: int | None = None,
) -> SavingPlan:
    if (target_date is None) == (monthly_saving_cents is None):
        raise ValueError("pass either target_date or monthly_saving_cents")
    if target_date is not None:
        if target_date < today:
            raise PastTargetError("A data para quitar já passou. Use uma data de hoje em diante.")
        payoff = payoff_at(debt, target_date, today=today)
        months = _distance(target_date, today)
        if payoff.target_cents == 0:
            return SavingPlan(payoff, months, 0, _month(target_date))
        if months == 0:
            # Reason: a date inside the running month leaves no month to save
            # in — the whole amount is needed now, not split in a fraction of
            # a deposit.
            return SavingPlan(payoff, 0, payoff.target_cents, _month(target_date))
        return SavingPlan(
            payoff, months, _ceil_div(payoff.target_cents, months), _month(target_date)
        )
    saving = monthly_saving_cents or 0
    if saving <= 0:
        raise InvalidSavingError("O valor guardado por mês precisa ser maior que zero.")
    for months in range(1, MAX_SAVING_MONTHS + 1):
        day = _month_end(shift(today, months))
        # Reason: the target moves while he saves — every instalment paid in
        # the meantime lowers what is left to settle, so the month he gets
        # there is the first one where the savings cover that month's payoff.
        payoff = payoff_at(debt, day, today=today)
        if saving * months >= payoff.target_cents:
            return SavingPlan(payoff, months, saving, _month(day))
    last = _month_end(shift(today, MAX_SAVING_MONTHS))
    return SavingPlan(payoff_at(debt, last, today=today), None, saving, None)
