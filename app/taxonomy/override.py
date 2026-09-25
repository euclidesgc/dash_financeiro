import sqlite3
from typing import Literal

from app.queries.similar import SIMILAR_IDS
from app.queries.spending import INFLOW, OUTFLOW
from app.taxonomy import classify
from app.taxonomy.seed import pickable_categories

Reason = Literal["own_transfer", "refund", "other"]
REASONS: frozenset[str] = frozenset({"own_transfer", "refund", "other"})


class UnknownTransactionError(LookupError):
    def __init__(self, transaction_id: object) -> None:
        super().__init__(f"transação desconhecida: {transaction_id}")
        self.transaction_id = transaction_id


class NotCountableError(ValueError):
    def __init__(self, transaction_id: object) -> None:
        super().__init__(f"lançamento não conta como gasto nem como entrada: {transaction_id}")
        self.transaction_id = transaction_id


class UnknownCategoryError(ValueError):
    def __init__(self, category: object) -> None:
        super().__init__(f"categoria desconhecida: {category}")
        self.category = category


def _check_category(conn: sqlite3.Connection, category: str | None) -> None:
    if category is not None and category not in {c.key for c in pickable_categories(conn)}:
        raise UnknownCategoryError(category)


def set_manual(conn: sqlite3.Connection, transaction_id: int, category: str | None) -> None:
    _check_category(conn, category)
    _require(conn, transaction_id)
    _write(
        conn,
        "UPDATE transactions SET category = ?, category_source = 'manual' WHERE id = ?",
        (category, transaction_id),
    )


def restore_auto(conn: sqlite3.Connection, transaction_id: int) -> None:
    _require(conn, transaction_id)
    _write(
        conn,
        "UPDATE transactions SET category = category_auto, category_source = 'auto' WHERE id = ?",
        (transaction_id,),
    )


def apply_to_similar(conn: sqlite3.Connection, transaction_id: int, category: str | None) -> int:
    _check_category(conn, category)
    _require(conn, transaction_id)
    return _write(
        conn,
        "UPDATE transactions SET category = ?, category_source = 'manual' "
        f"WHERE id IN ({SIMILAR_IDS})",
        (category, transaction_id),
    )


def set_not_expense(conn: sqlite3.Connection, transaction_id: int, reason: Reason) -> None:
    _require(conn, transaction_id)
    row = conn.execute(
        f"SELECT 1 FROM transactions WHERE id = ? AND ({OUTFLOW} OR {INFLOW})", (transaction_id,)
    ).fetchone()
    if row is None:
        raise NotCountableError(transaction_id)
    _write(
        conn,
        "UPDATE transactions SET not_expense_reason = ? WHERE id = ?",
        (reason, transaction_id),
    )


def clear_not_expense(conn: sqlite3.Connection, transaction_id: int) -> None:
    _require(conn, transaction_id)
    _write(
        conn,
        "UPDATE transactions SET not_expense_reason = NULL WHERE id = ?",
        (transaction_id,),
    )


def _require(conn: sqlite3.Connection, transaction_id: int) -> None:
    row = conn.execute("SELECT 1 FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
    if row is None:
        raise UnknownTransactionError(transaction_id)


def _write(conn: sqlite3.Connection, statement: str, params: tuple[object, ...]) -> int:
    # Reason: the write and the reclassification it triggers share one SQL
    # transaction (the same shape as app/taxonomy/rules.py:_write).
    try:
        cursor = conn.execute(statement, params)
        updated = cursor.rowcount
        classify.classify_all(conn)
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return updated
