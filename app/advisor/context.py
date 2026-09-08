import sqlite3
from datetime import date
from typing import Any

from app.commitments.live import totals as commitment_totals
from app.plan.objective import reserve_target_cents
from app.plan.timeline import BASE, simulate
from app.projection.forecast import forecast
from app.projection.position import positions
from app.routers.render import brl


def snapshot(conn: sqlite3.Connection, *, today: date) -> dict[str, Any]:
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


def lines(numbers: dict[str, Any]) -> list[dict[str, Any]]:
    # The screen renders these and the model receives these — one list, so the
    # claim "you find on screen every number it may cite" stays true. Showing a
    # subset would make the screen that exists to prove the model invents nothing
    # the very thing that produces the suspicion.
    when = (
        f"{numbers['months_to_objective']} meses"
        if numbers["months_to_objective"] is not None
        else "não chega, enquanto o resultado mensal não virar positivo"
    )
    return [
        {"label": "Data de referência", "value": numbers["reference"]},
        {"label": "Posição consolidada", "value": brl(numbers["consolidated"])},
        {"label": "Caixa", "value": brl(numbers["cash"])},
        {"label": "Cartão", "value": brl(numbers["card"])},
        {"label": "Comprometido por mês", "value": brl(numbers["committed"])},
        {"label": "Resultado mensal", "value": brl(numbers["monthly_result"])},
        {"label": "Reserva alvo", "value": brl(numbers["reserve_target"])},
        {"label": "Tempo até o objetivo", "value": when},
        {
            "label": f"Pior ponto dos próximos 45 dias, em {numbers['worst_date']}",
            "value": brl(numbers["worst_balance"]),
        },
    ]


def as_text(numbers: dict[str, Any]) -> str:
    # Every figure the model may say, spelled the way the screen spells it. It
    # copies from here or it says it does not know: the model interprets, the
    # code computes (invariante 23).
    return "\n".join(f"{line['label']}: {line['value']}." for line in lines(numbers))
