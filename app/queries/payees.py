import sqlite3

__all__ = ("payee_cnpj", "payee_known")

_KNOWN = "SELECT 1 FROM transactions WHERE payee = ? LIMIT 1"
_CNPJ = (
    "SELECT MIN(merchant_cnpj) AS cnpj FROM transactions "
    "WHERE payee = ? AND merchant_cnpj IS NOT NULL"
)


def payee_known(conn: sqlite3.Connection, payee: str) -> bool:
    return conn.execute(_KNOWN, (payee,)).fetchone() is not None


def payee_cnpj(conn: sqlite3.Connection, payee: str) -> str | None:
    row = conn.execute(_CNPJ, (payee,)).fetchone()
    return None if row is None or row["cnpj"] is None else str(row["cnpj"])
