import re
import sqlite3
from dataclasses import dataclass

from app.queries.reach import rule_reach
from app.settings.limits import RULE_EXPRESSION_MAX
from app.taxonomy import classify
from app.taxonomy.seed import message


class RuleError(ValueError):
    pass


MISSING_GROUP_MESSAGE = (
    "Grupo ausente: escolha um grupo existente ou digite um nome para criar um novo."
)


class MissingGroupError(RuleError):
    def __init__(self) -> None:
        super().__init__(MISSING_GROUP_MESSAGE)


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


class UnknownPayeeError(RuleError):
    def __init__(self, value: object) -> None:
        super().__init__(message("unknown_payee", value))
        self.value = value


class DuplicateGroupError(RuleError):
    def __init__(self, value: object) -> None:
        super().__init__(message("duplicate_group", value))
        self.value = value


@dataclass(frozen=True)
class Correction:
    rule_id: int
    created: bool
    group_id: int
    reclassified: int
    entries: int
    amount_cents: int


def expression_for(payee: str) -> str:
    return f"^{re.escape(payee)}$"


def correct_payee(
    conn: sqlite3.Connection,
    *,
    payee: str,
    group_id: int | None,
    new_group: str = "",
    nature: str,
    essentiality: str,
) -> Correction:
    if conn.execute("SELECT 1 FROM transactions WHERE payee = ?", (payee,)).fetchone() is None:
        raise UnknownPayeeError(payee)
    target_group = group_id
    if new_group:
        if (
            conn.execute("SELECT 1 FROM category_groups WHERE name = ?", (new_group,)).fetchone()
            is not None
        ):
            raise DuplicateGroupError(new_group)
        top = conn.execute("SELECT coalesce(max(position), 0) FROM category_groups").fetchone()[0]
        created_group = conn.execute(
            "INSERT INTO category_groups (name, position, is_fallback) VALUES (?, ?, 0)",
            (new_group, top + 1),
        )
        target_group = int(created_group.lastrowid or 0)
    expression = expression_for(payee)
    existing = conn.execute(
        "SELECT id FROM category_rules WHERE match_kind = ? AND match_value = ?",
        (classify.MATCH_DESCRIPTION, expression),
    ).fetchone()
    try:
        if existing is None:
            reclassified = create_rule(
                conn,
                match_kind=classify.MATCH_DESCRIPTION,
                match_value=expression,
                group_id=target_group,
                nature=nature,
                essentiality=essentiality,
            )
            created = True
        else:
            reclassified = update_rule(
                conn,
                existing["id"],
                group_id=target_group,
                nature=nature,
                essentiality=essentiality,
            )
            created = False
    except Exception:
        # Reason: the group above, when created, is an uncommitted write on
        # this same connection — without this rollback a refusal here would
        # leave it standing, invisible to every other connection but this
        # one — the one the screen redraws with.
        conn.rollback()
        raise
    rule_id = conn.execute(
        "SELECT id FROM category_rules WHERE match_kind = ? AND match_value = ?",
        (classify.MATCH_DESCRIPTION, expression),
    ).fetchone()["id"]
    reach = rule_reach(conn, rule_id)
    # Reason: create_rule/update_rule already ran _validate above, and a
    # None group_id never passes it — so reaching this point means
    # target_group is real.
    assert target_group is not None
    return Correction(
        rule_id=rule_id,
        created=created,
        group_id=target_group,
        reclassified=reclassified,
        entries=reach["entries"],
        amount_cents=reach["amount_cents"],
    )


def create_rule(
    conn: sqlite3.Connection,
    *,
    match_kind: str,
    match_value: str,
    group_id: int | None,
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
    final_match_kind = current["match_kind"] if match_kind is None else match_kind
    final_match_value = current["match_value"] if match_value is None else match_value
    final_group_id = current["group_id"] if group_id is None else group_id
    final_nature = current["nature"] if nature is None else nature
    final_essentiality = current["essentiality"] if essentiality is None else essentiality
    _validate(
        conn,
        match_kind=final_match_kind,
        match_value=final_match_value,
        group_id=final_group_id,
        nature=final_nature,
        essentiality=final_essentiality,
    )
    return _write(
        conn,
        "UPDATE category_rules SET match_kind = ?, match_value = ?, group_id = ?, "
        "nature = ?, essentiality = ? WHERE id = ?",
        (
            final_match_kind,
            final_match_value,
            final_group_id,
            final_nature,
            final_essentiality,
            rule_id,
        ),
    )


def delete_rule(conn: sqlite3.Connection, rule_id: int) -> int:
    if conn.execute("SELECT 1 FROM category_rules WHERE id = ?", (rule_id,)).fetchone() is None:
        raise UnknownRuleError(rule_id)
    return _write(conn, "DELETE FROM category_rules WHERE id = ?", (rule_id,))


def _write(conn: sqlite3.Connection, statement: str, params: tuple[object, ...]) -> int:
    # Reason: the write and the reclassification it triggers share one SQL
    # transaction — a half reclassified base keeps adding up and starts
    # lying (RF-14).
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
    group_id: int | None,
    nature: str,
    essentiality: str,
) -> None:
    if len(match_value) > RULE_EXPRESSION_MAX:
        raise InvalidExpressionError(match_value)
    if group_id is None:
        raise MissingGroupError()
    if conn.execute("SELECT 1 FROM category_groups WHERE id = ?", (group_id,)).fetchone() is None:
        raise InvalidTermError("invalid_group", group_id)
    if conn.execute("SELECT 1 FROM natures WHERE value = ?", (nature,)).fetchone() is None:
        raise InvalidTermError("invalid_nature", nature)
    if (
        conn.execute("SELECT 1 FROM essentialities WHERE value = ?", (essentiality,)).fetchone()
        is None
    ):
        raise InvalidTermError("invalid_essentiality", essentiality)
    if match_kind == classify.MATCH_DESCRIPTION:
        try:
            re.compile(match_value)
        except re.error:
            raise InvalidExpressionError(match_value) from None
