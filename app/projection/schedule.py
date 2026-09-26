import sqlite3
from dataclasses import dataclass, replace
from datetime import date

from app.commitments import INSTALLMENT
from app.commitments.live import charged, subscriptions
from app.commitments.schedule import end_month
from app.commitments.series import SAME_PURCHASE_DEVIATION
from app.financings import NAMES
from app.financings import store as financings_store
from app.queries.period import shift

CARD_INSTALLMENT = "card_installment"
FINANCING = "financing"
RECURRING_FIXED = "recurring"
SOURCES = (CARD_INSTALLMENT, FINANCING, RECURRING_FIXED)
DEFAULT_MONTHS = 6
MAX_MONTHS = 24


@dataclass(frozen=True)
class ScheduleLine:
    source: str
    description: str
    account: str | None
    amount_cents: int
    first_month: str
    last_month: str
    months_in_window: int
    window_total_cents: int
    first_installment: int | None
    last_installment: int | None
    installment_total: int | None
    end_month: str | None
    replaces: str | None = None


@dataclass(frozen=True)
class MonthSchedule:
    month: str
    by_source: dict[str, int]
    total_cents: int
    ending: list[str]


@dataclass(frozen=True)
class Unprojected:
    source: str
    description: str
    reason: str


@dataclass(frozen=True)
class Schedule:
    months: list[MonthSchedule]
    lines: list[ScheduleLine]
    unprojected: list[Unprojected]
    total_cents: int


def _label(day: date) -> str:
    return day.strftime("%Y-%m")


def _distance(later: str, earlier: str) -> int:
    return (int(later[:4]) - int(earlier[:4])) * 12 + int(later[5:7]) - int(earlier[5:7])


def _numbered_line(
    source: str,
    description: str,
    account: str | None,
    amount_cents: int,
    window: list[str],
    number_of: dict[str, int],
    total: int,
) -> ScheduleLine | None:
    covered = [month for month in window if 1 <= number_of[month] <= total]
    if not covered:
        return None
    first, last = covered[0], covered[-1]
    return ScheduleLine(
        source=source,
        description=description,
        account=account,
        amount_cents=amount_cents,
        first_month=first,
        last_month=last,
        months_in_window=len(covered),
        window_total_cents=amount_cents * len(covered),
        first_installment=number_of[first],
        last_installment=number_of[last],
        installment_total=total,
        end_month=_month_of_number(first, number_of[first], total),
    )


def _month_of_number(month: str, number: int, total: int) -> str:
    return end_month(month, total - number)


def _card_installments(
    conn: sqlite3.Connection, today: date, window: list[str]
) -> tuple[list[ScheduleLine], list[Unprojected]]:
    lines: list[ScheduleLine] = []
    unknown: list[Unprojected] = []
    for row in charged(conn, today=today):
        if row["kind"] != INSTALLMENT:
            continue
        if row["last_installment"] is None:
            unknown.append(
                Unprojected(
                    source=CARD_INSTALLMENT,
                    description=row["description"],
                    reason="o lançamento não diz qual parcela é, então o fim não é conhecido",
                )
            )
            continue
        # Reason: the number follows from the last charge seen, not from
        # installments_left — a card invoice posts every future instalment
        # at once, and the series with none left still has charges dated
        # inside the window.
        seen = row["last_seen_date"][:7]
        number_of = {month: row["last_installment"] + _distance(month, seen) for month in window}
        line = _numbered_line(
            CARD_INSTALLMENT,
            row["description"],
            row["account"],
            row["amount_cents"],
            window,
            number_of,
            row["installment_total"],
        )
        if line is not None:
            lines.append(line)
    return lines, unknown


def _financings(
    conn: sqlite3.Connection, window: list[str]
) -> tuple[list[ScheduleLine], list[Unprojected]]:
    lines: list[ScheduleLine] = []
    unknown: list[Unprojected] = []
    for row in financings_store.read_all(conn):
        name = NAMES.get(row["kind"], row["kind"])
        if row["payment_cents"] is None or row["first_due_date"] is None:
            # Reason: the contract has no instalment value, and deriving one
            # from balance and rate would pick an amortisation system the
            # panel does not know. The payment keeps showing among the fixed
            # bills when it leaves an account every month.
            unknown.append(
                Unprojected(
                    source=FINANCING,
                    description=name,
                    reason=(
                        "o contrato não tem valor de parcela cadastrado; se ela sai todo mês de "
                        "uma conta, aparece nas contas recorrentes"
                    ),
                )
            )
            continue
        first_due = row["first_due_date"][:7]
        number_of = {month: _distance(month, first_due) + 1 for month in window}
        line = _numbered_line(
            FINANCING, name, None, row["payment_cents"], window, number_of, row["term_months"]
        )
        if line is not None:
            lines.append(line)
    return lines, unknown


def _same_payment(recurring_cents: int, payment_cents: int) -> bool:
    larger = max(abs(recurring_cents), abs(payment_cents))
    return abs(abs(recurring_cents) - abs(payment_cents)) / larger <= SAME_PURCHASE_DEVIATION


def _recurring(
    conn: sqlite3.Connection, today: date, window: list[str], financings: list[ScheduleLine]
) -> tuple[list[ScheduleLine], list[ScheduleLine]]:
    lines: list[ScheduleLine] = []
    claimed: dict[int, str] = {}
    for row in subscriptions(conn, today=today):
        if not row["live"] or row["dismissed"]:
            continue
        # Decision: the bill that pays a financing is detected as a fixed
        # bill too; the contract line wins because it knows when the payments
        # end, and the bill is dropped so the month does not count it twice.
        payer = next(
            (
                index
                for index, financing in enumerate(financings)
                if index not in claimed
                and _same_payment(row["amount_cents"], financing.amount_cents)
            ),
            None,
        )
        if payer is not None:
            claimed[payer] = row["description"]
            continue
        lines.append(
            ScheduleLine(
                source=RECURRING_FIXED,
                description=row["description"],
                account=row["account"],
                amount_cents=row["amount_cents"],
                first_month=window[0],
                last_month=window[-1],
                months_in_window=len(window),
                window_total_cents=row["amount_cents"] * len(window),
                first_installment=None,
                last_installment=None,
                installment_total=None,
                end_month=None,
            )
        )
    tagged = [
        replace(line, replaces=claimed[index]) if index in claimed else line
        for index, line in enumerate(financings)
    ]
    return lines, tagged


def schedule_by_month(
    conn: sqlite3.Connection, *, today: date, months: int = DEFAULT_MONTHS
) -> Schedule:
    if not 1 <= months <= MAX_MONTHS:
        raise ValueError(f"months must be between 1 and {MAX_MONTHS}")
    # Reason: the window starts on the month after the reference date — the
    # running month is already half paid, and counting it whole would show
    # charges that already left.
    window = [_label(shift(today, step)) for step in range(1, months + 1)]
    cards, unknown_cards = _card_installments(conn, today, window)
    contracts, unknown_contracts = _financings(conn, window)
    recurring, financings = _recurring(conn, today, window, contracts)
    lines = sorted(
        cards + financings + recurring,
        key=lambda line: (SOURCES.index(line.source), line.amount_cents, line.description),
    )
    rows = []
    for month in window:
        by_source = dict.fromkeys(SOURCES, 0)
        ending = []
        for line in lines:
            if line.first_month <= month <= line.last_month:
                by_source[line.source] += line.amount_cents
                if line.end_month == month:
                    ending.append(line.description)
        rows.append(
            MonthSchedule(
                month=month,
                by_source=by_source,
                total_cents=sum(by_source.values()),
                ending=ending,
            )
        )
    return Schedule(
        months=rows,
        lines=lines,
        unprojected=unknown_cards + unknown_contracts,
        total_cents=sum(row.total_cents for row in rows),
    )
