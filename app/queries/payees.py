import sqlite3

__all__ = (
    "DESCRIPTION",
    "LEGAL",
    "LOOKUP",
    "OWNER",
    "PLUGGY",
    "RESOLVED_PAYEES",
    "payee_cnpj",
    "payee_known",
)

OWNER = "dono"
PLUGGY = "pluggy"
LOOKUP = "cnpj"
LEGAL = "razao-social"
DESCRIPTION = "descricao"

_KNOWN = "SELECT 1 FROM transactions WHERE payee = ? LIMIT 1"
_CNPJ = (
    "SELECT MIN(merchant_cnpj) AS cnpj FROM transactions "
    "WHERE payee = ? AND merchant_cnpj IS NOT NULL"
)

# Reason: the one place the display name's precedence lives — the payees
# screen and the expenses list (name and search) both read RESOLVED_PAYEES.
# Ordered by the quality of the name, not by the source: merchant.name
# answers "Apple", "Shopee", "outback", while receiver.name answers
# "IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A." — both come from the
# Pluggy, and one is an answer while the other is a legal record.
_PRECEDENCE = (
    ("own.name", OWNER),
    ("p.merchant_name", PLUGGY),
    ("lk.name", LOOKUP),
    ("p.legal_name", LEGAL),
    ("p.receiver_name", LEGAL),
)

_NAME = "COALESCE(" + ", ".join(f"NULLIF({column}, '')" for column, _ in _PRECEDENCE) + ")"
_SOURCE = (
    "CASE "
    + " ".join(
        f"WHEN NULLIF({column}, '') IS NOT NULL THEN '{origin}'" for column, origin in _PRECEDENCE
    )
    + f" ELSE '{DESCRIPTION}' END"
)

# Reason: MIN() over the group is deterministic — without it the answer
# would depend on the order SQLite happens to scan in. One row per payee,
# so joining it never multiplies transactions.
RESOLVED_PAYEES = f"""
SELECT p.payee AS payee, {_NAME} AS name, {_SOURCE} AS source
FROM (
    SELECT payee,
           MIN(merchant_name) AS merchant_name,
           MIN(merchant_legal_name) AS legal_name,
           MIN(receiver_name) AS receiver_name
    FROM transactions
    WHERE payee IS NOT NULL
    GROUP BY payee
) AS p
LEFT JOIN payee_names AS own ON own.payee = p.payee AND own.source = '{OWNER}'
LEFT JOIN payee_names AS lk ON lk.payee = p.payee AND lk.source = '{LOOKUP}'
"""


def payee_known(conn: sqlite3.Connection, payee: str) -> bool:
    return conn.execute(_KNOWN, (payee,)).fetchone() is not None


def payee_cnpj(conn: sqlite3.Connection, payee: str) -> str | None:
    row = conn.execute(_CNPJ, (payee,)).fetchone()
    return None if row is None or row["cnpj"] is None else str(row["cnpj"])
