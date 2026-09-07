import sqlite3
from datetime import date

from app.debts.ladder import without_rate
from app.plan.whatif import facts

SETTLEMENT = "quitacao-cdc"
TRANSPORT = "transporte-sem-carro"

# What only the owner knows, in the order of how much the answer moves the
# projection. The order is not taste: a rate decides where the next real goes,
# and a payoff balance decides a thirty-nine thousand real question.
WANTED = (
    {
        "name": "taxa-cartao",
        "label": "a taxa mensal dos seus cartões",
        "moves": "a ordem da escada de dívida, e com ela onde o próximo real rende mais",
        "where": "/dividas",
    },
    {
        "name": SETTLEMENT,
        "label": "o saldo de quitação antecipada do CDC do carro",
        "moves": "a conta de vender o carro, que é a maior decisão em aberto",
        "where": "/simulador",
    },
    {
        "name": TRANSPORT,
        "label": "quanto custaria seu transporte por mês sem o carro",
        "moves": "o fluxo líquido que a venda do carro libera",
        "where": "/simulador",
    },
)


def pending(conn: sqlite3.Connection, *, today: date) -> list[dict]:
    known = {row["name"]: row for row in facts(conn, today=today)}
    marks = {row["name"]: dict(row) for row in conn.execute("SELECT * FROM advisor_questions")}
    open_questions = []
    for wanted in WANTED:
        fact = known.get(wanted["name"])
        if fact and not fact["stale"]:
            continue
        if wanted["name"] == "taxa-cartao" and not without_rate(conn):
            continue
        mark = marks.get(wanted["name"])
        if mark and mark["dismissed_at"] and not (fact and fact["stale"]):
            continue
        open_questions.append(dict(wanted, stale=bool(fact and fact["stale"])))
    return open_questions


def next_question(conn: sqlite3.Connection, *, today: date) -> dict | None:
    # One question, never a list: a panel that asks three things at once gets
    # none of them answered.
    found = pending(conn, today=today)
    return found[0] if found else None


class UnknownQuestionError(LookupError):
    pass


def postponed(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM advisor_questions WHERE dismissed_at IS NOT NULL"
    ).fetchone()[0]


def dismiss(conn: sqlite3.Connection, name: str) -> None:
    # Only a name from the catalogue: any string would grow the table without a
    # ceiling on an authenticated POST, and none of them would ever be shown.
    if name not in {wanted["name"] for wanted in WANTED}:
        raise UnknownQuestionError("Pergunta desconhecida.")
    conn.execute(
        "INSERT INTO advisor_questions (name, asked_at, dismissed_at) "
        "VALUES (?, datetime('now'), datetime('now')) "
        "ON CONFLICT(name) DO UPDATE SET dismissed_at = datetime('now')",
        (name,),
    )
    conn.commit()
