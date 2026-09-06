import re
import sqlite3

from app.taxonomy import classify
from app.taxonomy.seed import message

_FIELDS = ("match_kind", "match_value", "group_id", "nature", "essentiality")


class RuleError(ValueError):
    pass


class InvalidTermError(RuleError):
    def __init__(self, key: str, value: object) -> None:
        super().__init__(message(key, value))
        self.value = value


class InvalidExpressionError(RuleError):
    def __init__(self, value: object) -> None:
        super().__init__(message("invalid_expression", value))
        self.value = value


class UnknownRuleError(RuleError):
    def __init__(self, value: object) -> None:
        super().__init__(message("unknown_rule", value))
        self.value = value


def create_rule(
    conn: sqlite3.Connection,
    *,
    match_kind: str,
    match_value: str,
    group_id: int,
    nature: str,
    essentiality: str,
) -> int:
    _validate(
        conn,
        match_kind=match_kind,
        match_value=match_value,
        group_id=group_id,
        nature=nature,
        essentiality=essentiality,
    )
    return _write(
        conn,
        "INSERT INTO category_rules (match_kind, match_value, group_id, nature, essentiality) "
        "VALUES (?, ?, ?, ?, ?)",
        (match_kind, match_value, group_id, nature, essentiality),
    )


def update_rule(
    conn: sqlite3.Connection,
    rule_id: int,
    *,
    match_kind: str | None = None,
    match_value: str | None = None,
    group_id: int | None = None,
    nature: str | None = None,
    essentiality: str | None = None,
) -> int:
    current = conn.execute(
        "SELECT match_kind, match_value, group_id, nature, essentiality "
        "FROM category_rules WHERE id = ?",
        (rule_id,),
    ).fetchone()
    if current is None:
        raise UnknownRuleError(rule_id)
    given = (match_kind, match_value, group_id, nature, essentiality)
    values = {
        field: current[field] if value is None else value
        for field, value in zip(_FIELDS, given)
    }
    _validate(conn, **values)
    return _write(
        conn,
        "UPDATE category_rules SET match_kind = ?, match_value = ?, group_id = ?, "
        "nature = ?, essentiality = ? WHERE id = ?",
        (*(values[field] for field in _FIELDS), rule_id),
    )


def delete_rule(conn: sqlite3.Connection, rule_id: int) -> int:
    if conn.execute("SELECT 1 FROM category_rules WHERE id = ?", (rule_id,)).fetchone() is None:
        raise UnknownRuleError(rule_id)
    return _write(conn, "DELETE FROM category_rules WHERE id = ?", (rule_id,))


def _write(conn: sqlite3.Connection, statement: str, params: tuple) -> int:
    # The write and the reclassification it triggers share one SQL transaction:
    # a half reclassified base keeps adding up and starts lying (RF-14).
    try:
        conn.execute(statement, params)
        reclassified = classify.classify_all(conn)
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return reclassified


def _validate(
    conn: sqlite3.Connection,
    *,
    match_kind: str,
    match_value: str,
    group_id: int,
    nature: str,
    essentiality: str,
) -> None:
    if conn.execute("SELECT 1 FROM category_groups WHERE id = ?", (group_id,)).fetchone() is None:
        raise InvalidTermError("invalid_group", group_id)
    if conn.execute("SELECT 1 FROM natures WHERE value = ?", (nature,)).fetchone() is None:
        raise InvalidTermError("invalid_nature", nature)
    if (
        conn.execute(
            "SELECT 1 FROM essentialities WHERE value = ?", (essentiality,)
        ).fetchone()
        is None
    ):
        raise InvalidTermError("invalid_essentiality", essentiality)
    if match_kind == classify.MATCH_DESCRIPTION:
        try:
            re.compile(match_value)
        except re.error:
            raise InvalidExpressionError(match_value) from None
