import sqlite3
from typing import Any

from app.queries.payees import DESCRIPTION as DESCRIPTION
from app.queries.payees import LEGAL as LEGAL
from app.queries.payees import LOOKUP as LOOKUP
from app.queries.payees import OWNER as OWNER
from app.queries.payees import PLUGGY as PLUGGY
from app.queries.payees import RESOLVED_PAYEES
from app.queries.spending import SPENDING
from app.settings.limits import PAYEE_ALIAS_MAX
from app.settings.typed import InvalidValueError

WRITABLE = (OWNER, LOOKUP)

# Reason: the origin travels with the value, and the screen reads this map
# instead of guessing from the text (RF-22).
ORIGINS = {
    OWNER: "apelido seu",
    PLUGGY: "nome fantasia da Pluggy",
    LOOKUP: "nome fantasia consultado",
    LEGAL: "razão social",
    DESCRIPTION: "descrição normalizada",
}

_SPENDING_BY_PAYEE = f"""
SELECT payee, SUM(amount_cents) AS total_cents
FROM transactions
WHERE payee IS NOT NULL AND {SPENDING}
GROUP BY payee
ORDER BY total_cents
"""

_WRITE = (
    "INSERT INTO payee_names (payee, source, name, updated_at) "
    "VALUES (?, ?, ?, datetime('now')) "
    "ON CONFLICT(payee, source) DO UPDATE SET name = excluded.name, "
    "updated_at = excluded.updated_at"
)


class UnknownSourceError(ValueError):
    pass


def display_name(conn: sqlite3.Connection) -> dict[str, dict[str, str]]:
    return {
        row["payee"]: {"name": row["name"] or row["payee"], "source": row["source"]}
        for row in conn.execute(RESOLVED_PAYEES)
    }


def labels(conn: sqlite3.Connection) -> dict[str, str]:
    # Reason: only the payees that reached a better name than the
    # normalised description. A reading screen already shows the
    # description it received, and overwriting it with the normalised key
    # would be a worse label, not a resolved one.
    return {
        payee: found["name"]
        for payee, found in display_name(conn).items()
        if found["source"] != DESCRIPTION
    }


def spending_by_payee(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    # Reason: all of history, and the project's single spending predicate —
    # a name is not a property of a period, and a payee outside the window
    # still needs one.
    return [dict(row) for row in conn.execute(_SPENDING_BY_PAYEE)]


def ranked(conn: sqlite3.Connection, limit: int) -> dict[str, Any]:
    every = spending_by_payee(conn)
    resolved = display_name(conn)
    total = sum(row["total_cents"] for row in every)
    top = every[:limit]
    covered = sum(row["total_cents"] for row in top)
    return {
        "payees": [
            dict(
                row,
                name=resolved.get(row["payee"], {}).get("name", row["payee"]),
                origin=resolved.get(row["payee"], {}).get("source", DESCRIPTION),
            )
            for row in top
        ],
        "total_payees": len(every),
        "total_cents": total,
        "covered_cents": covered,
        # Reason: integer per mille, so the screen can say 55,5% without a
        # float deciding what a percentage of this base is (invariant 22 in
        # spirit).
        "covered_permille": round(covered * 1000 / total) if total else 0,
    }


def name_it(conn: sqlite3.Connection, payee: str, name: str, source: str) -> None:
    if source not in WRITABLE:
        raise UnknownSourceError(f"Origem desconhecida: “{source}”.")
    # Reason: the ceiling is on the nickname the owner types (RF-02), not
    # on a trade name the CNPJ lookup brings back — that source is not a
    # field the owner types into.
    if source == OWNER and len(name) > PAYEE_ALIAS_MAX:
        raise InvalidValueError(f"Apelido muito longo: no máximo {PAYEE_ALIAS_MAX} caracteres.")
    conn.execute(_WRITE, (payee, source, name))
    conn.commit()


def forget(conn: sqlite3.Connection, payee: str, source: str) -> None:
    if source not in WRITABLE:
        raise UnknownSourceError(f"Origem desconhecida: “{source}”.")
    conn.execute("DELETE FROM payee_names WHERE payee = ? AND source = ?", (payee, source))
    conn.commit()
