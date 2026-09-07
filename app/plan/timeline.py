import sqlite3
from datetime import date

from app.debts.ladder import MORTGAGE, ladder
from app.plan.objective import baseline_cents, levers, reserve_target_cents
from app.projection.position import positions

CONSERVATIVE = "conservador"
BASE = "base"
OPTIMISTIC = "otimista"
SCENARIOS = (CONSERVATIVE, BASE, OPTIMISTIC)

EXPENSIVE_RATE_BP = 100
HORIZON_MONTHS = 360

LABELS = {
    CONSERVATIVE: "nada muda",
    BASE: "as assinaturas marcadas caem e a lista de corte é cortada",
    OPTIMISTIC: "o do meio, mais o caixa que os parcelamentos liberam ao acabar",
}


def monthly_result_cents(conn: sqlite3.Connection, scenario: str, *, today: date) -> int:
    # Three scenarios, and none of them is a multiplier over the other: each adds
    # a lever the product already identified and that the owner has to actually
    # pull. A number invented by percentage would be a guess wearing the clothes
    # of a plan.
    gained = levers(conn, today=today)
    result = baseline_cents(conn, today=today)
    if scenario in (BASE, OPTIMISTIC):
        result += gained["dismissed"] + gained["cut"]
    if scenario == OPTIMISTIC:
        result += gained["released"]
    return result


def expensive_debts(conn: sqlite3.Connection) -> list[dict]:
    # The mortgage stays out: at the bottom of the ladder it is the cheapest debt
    # there is, and paying it down before having a reserve trades safety for a
    # rate that is not hurting.
    return [
        row
        for row in ladder(conn)
        if row["kind"] != MORTGAGE and (row["monthly_rate_bp"] or 0) > EXPENSIVE_RATE_BP
    ]


def simulate(conn: sqlite3.Connection, scenario: str, *, today: date) -> dict:
    result = monthly_result_cents(conn, scenario, today=today)
    target = reserve_target_cents(conn, today=today)
    owed = [abs(row["balance_cents"]) for row in expensive_debts(conn)]
    rates = [(row["monthly_rate_bp"] or 0) / 10000 for row in expensive_debts(conn)]
    cash = positions(conn)["cash_cents"]

    milestones: dict[str, int | None] = {"resultado": None, "dividas": None, "reserva": None}
    if result >= 0:
        milestones["resultado"] = 0
    reserve = 0
    for month in range(1, HORIZON_MONTHS + 1):
        if result <= 0:
            # A month that ends in the red cannot pay anything down, and the debt
            # grows at its own rate: saying "in N months" here would be inventing
            # a date out of a trend that points the other way.
            break
        spare = result
        for index, balance in enumerate(owed):
            if balance <= 0:
                continue
            owed[index] = round(balance * (1 + rates[index])) - spare
            spare = max(-owed[index], 0)
            owed[index] = max(owed[index], 0)
            if spare <= 0:
                break
        if milestones["dividas"] is None and not any(owed):
            milestones["dividas"] = month
        if not any(owed):
            reserve += spare if spare else result
            if milestones["reserva"] is None and reserve >= target:
                milestones["reserva"] = month
                break
    return {
        "scenario": scenario,
        "label": LABELS[scenario],
        "monthly_result_cents": result,
        "reserve_target_cents": target,
        "cash_cents": cash,
        "expensive_cents": -sum(abs(row["balance_cents"]) for row in expensive_debts(conn)),
        "milestones": milestones,
        "months_to_objective": milestones["reserva"],
        # Without a date, the only useful number left is how far the monthly
        # result is from zero: that is the distance between "never" and "a date
        # exists", and it is the one thing the owner can act on.
        "missing_cents": -result if result < 0 else 0,
    }


def every_scenario(conn: sqlite3.Connection, *, today: date) -> list[dict]:
    return [simulate(conn, scenario, today=today) for scenario in SCENARIOS]


def record(conn: sqlite3.Connection, runs: list[dict], *, today: date) -> None:
    # A snapshot per recalculation is the only progress signal this product
    # accepts: "in March you projected 30 months, today you project 24" needs a
    # March to compare against.
    conn.executemany(
        "INSERT OR REPLACE INTO plan_snapshots (taken_at, reference_date, scenario, "
        "monthly_result_cents, reserve_target_cents, months_to_objective) "
        "VALUES (datetime('now'), ?, ?, ?, ?, ?)",
        [
            (
                today.isoformat(),
                run["scenario"],
                run["monthly_result_cents"],
                run["reserve_target_cents"],
                run["months_to_objective"],
            )
            for run in runs
        ],
    )
    conn.commit()


def history(conn: sqlite3.Connection, scenario: str = BASE) -> list[dict]:
    return [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM plan_snapshots WHERE scenario = ? ORDER BY reference_date",
            (scenario,),
        )
    ]
