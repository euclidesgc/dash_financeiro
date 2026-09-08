import sqlite3
from datetime import date

from app.commitments.live import totals as commitment_totals
from app.offers.cost import comparison
from app.plan.objective import reserve_target_cents
from app.plan.timeline import BASE, simulate
from app.projection.forecast import forecast
from app.projection.position import positions
from app.routers.render import brl
from app.routers.render import rate as as_rate


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
        "comparison": comparison(conn),
    }


def lines(numbers: dict) -> list[dict]:
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
        *[entry for row in numbers["comparison"]["rows"] for entry in _offer_lines(row)],
    ]


def _offer_lines(row: dict) -> list[dict]:
    # Decisão: a taxa e o prazo da proposta viajam dentro do rótulo, e não só no
    # valor, porque a tela de /consultor mostra os dois na comparação — uma
    # cifra visível na tela e ausente do contexto é uma cifra que a conferência
    # de app.advisor.cited recusaria se o modelo a copiasse de lá. O rótulo
    # nomeia a taxa como "desta proposta" para não sugerir que é a taxa de
    # continuar como está, que é outro número.
    term = row["term_months"]
    when = f"{term} mês" if term == 1 else f"{term} meses"
    tag = f"{row['name']} (proposta a {as_rate(row['monthly_rate_bp'])} ao mês, {when})"
    entries = [
        {"label": f"{tag} — custo desta proposta até zerar", "value": brl(row["offer_cents"])}
    ]
    if row["stay_cents"] is not None:
        entries.append(
            {
                "label": f"{tag} — custo de continuar como está, no mesmo prazo e valor",
                "value": brl(row["stay_cents"]),
            }
        )
        entries.append(
            {
                "label": f"{tag} — diferença entre continuar e trocar",
                "value": brl(row["difference_cents"]),
            }
        )
    return entries


def as_text(numbers: dict) -> str:
    # Every figure the model may say, spelled the way the screen spells it. It
    # copies from here or it says it does not know: the model interprets, the
    # code computes (invariante 23).
    return "\n".join(f"{line['label']}: {line['value']}." for line in lines(numbers))
