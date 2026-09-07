import sqlite3
from datetime import date

from app.debts.ladder import without_rate
from app.plan.whatif import facts
from app.settings.catalog import CARD_RATE, FACT, of_kind


def wanted() -> tuple[dict, ...]:
    # Read from the catalogue at every call, never copied: a second list here is
    # the same defect this item closed in the base, where one fact had one name
    # on the screen that wrote it and another on the screen that asked for it.
    # A goal never appears: it has a default, so its absence is not a gap.
    return tuple(
        {
            "name": item["name"],
            "label": item["question"],
            "moves": item["moves"],
            "where": item["screen"],
        }
        for item in of_kind(FACT)
    )


def pending(conn: sqlite3.Connection, *, today: date) -> list[dict]:
    known = {row["name"]: row for row in facts(conn, today=today)}
    marks = {row["name"]: dict(row) for row in conn.execute("SELECT * FROM advisor_questions")}
    open_questions = []
    for question in wanted():
        fact = known.get(question["name"])
        if fact and not fact["stale"]:
            continue
        if question["name"] == CARD_RATE and not without_rate(conn):
            continue
        mark = marks.get(question["name"])
        if mark and mark["dismissed_at"] and not (fact and fact["stale"]):
            continue
        open_questions.append(dict(question, stale=bool(fact and fact["stale"])))
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
    if name not in {question["name"] for question in wanted()}:
        raise UnknownQuestionError("Pergunta desconhecida.")
    conn.execute(
        "INSERT INTO advisor_questions (name, asked_at, dismissed_at) "
        "VALUES (?, datetime('now'), datetime('now')) "
        "ON CONFLICT(name) DO UPDATE SET dismissed_at = datetime('now')",
        (name,),
    )
    conn.commit()
