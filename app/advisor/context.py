import sqlite3
from datetime import date

from app.commitments.live import totals as commitment_totals
from app.plan.objective import reserve_target_cents
from app.plan.timeline import BASE, simulate
from app.projection.forecast import forecast
from app.projection.position import positions
from app.routers.render import brl


def snapshot(conn: sqlite3.Connection, *, today: date) -> dict:
    place = positions(conn)
    line = forecast(conn, today=today)
    plan = simulate(conn, BASE, today=today)
    return {
        "reference": today.isoformat(),
        "consolidated": place["consolidated_cents"],
        "cash": place["cash_cents"],
        "card": place["card_cents"],
        "committed": commitment_totals(conn, today=today)["committed_cents"],
        "monthly_result": plan["monthly_result_cents"],
        "reserve_target": reserve_target_cents(conn, today=today),
        "months_to_objective": plan["months_to_objective"],
        "worst_date": line["worst"]["date"],
        "worst_balance": line["worst"]["balance_cents"],
    }


def as_text(numbers: dict) -> str:
    # Every figure the model may say, spelled the way the screen spells it. It
    # copies from here or it says it does not know: the model interprets, the
    # code computes (invariante 23).
    when = (
        f"{numbers['months_to_objective']} meses"
        if numbers["months_to_objective"] is not None
        else "não chega, enquanto o resultado mensal não virar positivo"
    )
    return "\n".join(
        (
            f"Data de referência: {numbers['reference']}.",
            f"Posição consolidada: {brl(numbers['consolidated'])}.",
            f"Caixa: {brl(numbers['cash'])}. Cartão: {brl(numbers['card'])}.",
            f"Comprometido por mês: {brl(numbers['committed'])}.",
            f"Resultado mensal: {brl(numbers['monthly_result'])}.",
            f"Reserva alvo: {brl(numbers['reserve_target'])}.",
            f"Tempo até o objetivo: {when}.",
            f"Pior ponto dos próximos 45 dias: {brl(numbers['worst_balance'])}"
            f" em {numbers['worst_date']}.",
        )
    )
