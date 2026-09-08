import sqlite3
from typing import Any

from app.queries.spending import SPENDING

OWNER = "dono"
LOOKUP = "cnpj"
WRITABLE = (OWNER, LOOKUP)

PLUGGY = "pluggy"
LEGAL = "razao-social"
DESCRIPTION = "descricao"

# The origin travels with the value, and the screen reads this map instead of
# guessing from the text (RF-22).
ORIGINS = {
    OWNER: "apelido seu",
    PLUGGY: "nome fantasia da Pluggy",
    LOOKUP: "nome fantasia consultado",
    LEGAL: "razão social",
    DESCRIPTION: "descrição normalizada",
}

# MIN() over the group is deterministic and today changes nothing: not one of
# the payees in this base carries two different values at any level. Without it
# the answer would depend on the order SQLite happens to scan in.
_FROM_PLUGGY = """
SELECT payee,
       MIN(merchant_name) AS merchant_name,
       MIN(merchant_legal_name) AS legal_name,
       MIN(receiver_name) AS receiver_name
FROM transactions
WHERE payee IS NOT NULL
GROUP BY payee
"""

_SPENDING_BY_PAYEE = f"""
SELECT payee, SUM(amount_cents) AS total_cents
FROM transactions
WHERE payee IS NOT NULL AND {SPENDING}
GROUP BY payee
ORDER BY total_cents
"""

_NAMES = "SELECT payee, source, name FROM payee_names"

_WRITE = (
    "INSERT INTO payee_names (payee, source, name, updated_at) "
    "VALUES (?, ?, ?, datetime('now')) "
    "ON CONFLICT(payee, source) DO UPDATE SET name = excluded.name, "
    "updated_at = excluded.updated_at"
)


class UnknownSourceError(ValueError):
    pass


def _chosen(payee: str, row: dict[str, Any], given: dict[str, str]) -> tuple[str, str]:
    # Ordered by the quality of the name, not by the source: merchant.name
    # answers "Apple", "Shopee", "outback", while receiver.name answers
    # "IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A." — both come from the
    # Pluggy, and one is an answer while the other is a legal record.
    for name, origin in (
        (given.get(OWNER), OWNER),
        (row.get("merchant_name"), PLUGGY),
        (given.get(LOOKUP), LOOKUP),
        (row.get("legal_name") or row.get("receiver_name"), LEGAL),
    ):
        if name:
            return name, origin
    return payee, DESCRIPTION


def display_name(conn: sqlite3.Connection) -> dict[str, dict[str, str]]:
    given: dict[str, dict[str, str]] = {}
    for row in conn.execute(_NAMES):
        given.setdefault(row["payee"], {})[row["source"]] = row["name"]
    answer: dict[str, dict[str, str]] = {}
    for row in conn.execute(_FROM_PLUGGY):
        payee = row["payee"]
        name, origin = _chosen(payee, dict(row), given.get(payee, {}))
        answer[payee] = {"name": name, "source": origin}
    return answer


def labels(conn: sqlite3.Connection) -> dict[str, str]:
    # Only the payees that reached a better name than the normalised
    # description. A reading screen already shows the description it received,
    # and overwriting it with the normalised key would be a worse label, not a
    # resolved one.
    return {
        payee: found["name"]
        for payee, found in display_name(conn).items()
        if found["source"] != DESCRIPTION
    }


def spending_by_payee(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    # All of history, and the project's single spending predicate: a name is not
    # a property of a period, and a payee outside the window still needs one.
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
        # Integer per mille, so the screen can say 55,5% without a float
        # deciding what a percentage of this base is (invariante 22 in spirit).
        "covered_permille": round(covered * 1000 / total) if total else 0,
    }


def name_it(conn: sqlite3.Connection, payee: str, name: str, source: str) -> None:
    if source not in WRITABLE:
        raise UnknownSourceError(f"Origem desconhecida: “{source}”.")
    conn.execute(_WRITE, (payee, source, name))
    conn.commit()


def forget(conn: sqlite3.Connection, payee: str, source: str) -> None:
    if source not in WRITABLE:
        raise UnknownSourceError(f"Origem desconhecida: “{source}”.")
    conn.execute("DELETE FROM payee_names WHERE payee = ? AND source = ?", (payee, source))
    conn.commit()
