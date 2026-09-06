import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect
from app.queries.spending import SPENDING
from app.taxonomy import classify
from app.taxonomy.rules import RuleError, create_rule, delete_rule, update_rule
from app.taxonomy.seed import load_seed, message

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/regras"
EDIT = "/editar"
REMOVE = "/remover"

CANDIDATES = 12
SAMPLES = 3

LABELS: dict[str, str] = load_seed().get("category_labels", {})

KINDS: tuple[tuple[str, str], ...] = (
    (classify.MATCH_CATEGORY, "Categoria"),
    (classify.MATCH_DESCRIPTION, "Descrição"),
)

EMPTY_MATCH_MESSAGE = "Casamento vazio: escreva o texto que a regra procura."
UNKNOWN_KIND_MESSAGE = "Tipo de casamento inválido: {value}"
DUPLICATE_MESSAGE = "Já existe uma regra com esse casamento: {value}"

_RULES = (
    "SELECT r.id AS id, r.match_kind AS match_kind, r.match_value AS match_value, "
    "r.group_id AS group_id, g.name AS group_name, r.nature AS nature, "
    "r.essentiality AS essentiality, count(t.id) AS entries, "
    f"coalesce(sum(CASE WHEN {SPENDING} THEN t.amount_cents END), 0) AS amount_cents "
    "FROM category_rules AS r JOIN category_groups AS g ON g.id = r.group_id "
    "LEFT JOIN transactions AS t ON t.rule_id = r.id "
    "GROUP BY r.id ORDER BY amount_cents, r.match_value"
)

_RULE = "SELECT id, match_kind, match_value, group_id, nature, essentiality FROM category_rules WHERE id = ?"

_RULE_OF = "SELECT id FROM category_rules WHERE match_kind = ? AND match_value = ?"

_REACH = "SELECT count(*) FROM transactions WHERE rule_id = ?"

_RESIDUE = (
    "SELECT count(*) AS entries, coalesce(sum(amount_cents), 0) AS amount_cents "
    f"FROM transactions WHERE rule_id IS NULL AND {SPENDING}"
)

# A rule is not bound to a period, so neither is what is missing one: the two
# readings of the same loose money — the category it carries and the payee it
# paid — are the two shapes a rule can take, and the money orders them.
_CANDIDATES = (
    "SELECT ? AS kind, category AS value, count(*) AS entries, "
    "sum(amount_cents) AS amount_cents FROM transactions "
    f"WHERE rule_id IS NULL AND {SPENDING} AND category IS NOT NULL AND category != '' "
    "GROUP BY category UNION ALL "
    "SELECT ? AS kind, payee AS value, count(*) AS entries, "
    "sum(amount_cents) AS amount_cents FROM transactions "
    f"WHERE rule_id IS NULL AND {SPENDING} AND payee IS NOT NULL AND payee != '' "
    "GROUP BY payee ORDER BY amount_cents LIMIT ?"
)

_GROUPS = "SELECT id, name FROM category_groups ORDER BY position, name"
_NATURES = "SELECT value FROM natures ORDER BY position"
_TERMS = "SELECT value FROM essentialities ORDER BY position"

_SAMPLES = (
    "SELECT payee AS value FROM transactions WHERE payee IS NOT NULL AND payee != '' "
    "GROUP BY payee ORDER BY count(*) DESC, payee LIMIT ?"
)


@router.get(SCREEN)
def rules_screen(request: Request) -> Response:
    conn = connect()
    try:
        return _answer(request, conn, _asked(conn, request))
    finally:
        conn.close()


@router.post(SCREEN)
def write_rule(
    request: Request,
    match_kind: Annotated[str, Form()] = "",
    match_value: Annotated[str, Form()] = "",
    group_id: Annotated[str, Form()] = "",
    nature: Annotated[str, Form()] = "",
    essentiality: Annotated[str, Form()] = "",
) -> Response:
    form = _submitted(None, match_kind, match_value, group_id, nature, essentiality)
    conn = connect()
    try:
        refused = _refused(form)
        if refused is None:
            try:
                done = create_rule(
                    conn,
                    match_kind=form["match_kind"],
                    match_value=form["match_value"],
                    group_id=int(form["group_id"]),
                    nature=form["nature"],
                    essentiality=form["essentiality"],
                )
            except RuleError as refusal:
                refused = str(refusal)
            except sqlite3.IntegrityError:
                refused = DUPLICATE_MESSAGE.format(value=form["match_value"])
        if refused is not None:
            return _answer(request, conn, form, notice=refused, status_code=400)
        written = conn.execute(_RULE_OF, (form["match_kind"], form["match_value"])).fetchone()
        return _answer(request, conn, _blank(), done=done, reach=_reach(conn, written["id"]))
    finally:
        conn.close()


@router.post(f"{SCREEN}/{{rule_id}}{EDIT}")
def edit_rule(
    request: Request,
    rule_id: int,
    match_kind: Annotated[str, Form()] = "",
    match_value: Annotated[str, Form()] = "",
    group_id: Annotated[str, Form()] = "",
    nature: Annotated[str, Form()] = "",
    essentiality: Annotated[str, Form()] = "",
) -> Response:
    form = _submitted(rule_id, match_kind, match_value, group_id, nature, essentiality)
    conn = connect()
    try:
        refused = _refused(form)
        if refused is None:
            try:
                done = update_rule(
                    conn,
                    rule_id,
                    match_kind=form["match_kind"],
                    match_value=form["match_value"],
                    group_id=int(form["group_id"]),
                    nature=form["nature"],
                    essentiality=form["essentiality"],
                )
            except RuleError as refusal:
                refused = str(refusal)
            except sqlite3.IntegrityError:
                refused = DUPLICATE_MESSAGE.format(value=form["match_value"])
        if refused is not None:
            return _answer(request, conn, form, notice=refused, status_code=400)
        return _answer(request, conn, _blank(), done=done, reach=_reach(conn, rule_id))
    finally:
        conn.close()


@router.post(f"{SCREEN}/{{rule_id}}{REMOVE}")
def remove_rule(request: Request, rule_id: int) -> Response:
    conn = connect()
    try:
        try:
            done = delete_rule(conn, rule_id)
        except RuleError as refusal:
            return _answer(request, conn, _blank(), notice=str(refusal), status_code=400)
        return _answer(request, conn, _blank(), done=done)
    finally:
        conn.close()


def _answer(
    request: Request,
    conn: sqlite3.Connection,
    form: dict[str, str],
    *,
    notice: str | None = None,
    done: int | None = None,
    reach: int | None = None,
    status_code: int = 200,
) -> Response:
    context = _context(conn, form)
    context.update(notice=notice, done=done, reach=reach)
    return TEMPLATES.TemplateResponse(request, "regras.html", context, status_code=status_code)


def _context(conn: sqlite3.Connection, form: dict[str, str]) -> dict[str, Any]:
    kinds = (classify.MATCH_CATEGORY, classify.MATCH_DESCRIPTION, CANDIDATES)
    return {
        "rules": conn.execute(_RULES).fetchall(),
        "residue": conn.execute(_RESIDUE).fetchone(),
        "candidates": conn.execute(_CANDIDATES, kinds).fetchall(),
        "groups": conn.execute(_GROUPS).fetchall(),
        "natures": [row["value"] for row in conn.execute(_NATURES)],
        "terms": [row["value"] for row in conn.execute(_TERMS)],
        "samples": [row["value"] for row in conn.execute(_SAMPLES, (SAMPLES,))],
        "kinds": KINDS,
        "kind_names": dict(KINDS),
        "form": form,
        "labels": LABELS,
        "screen": SCREEN,
        "edit_suffix": EDIT,
        "remove_suffix": REMOVE,
    }


def _refused(form: dict[str, str]) -> str | None:
    if form["match_kind"] not in dict(KINDS):
        return UNKNOWN_KIND_MESSAGE.format(value=form["match_kind"])
    # An empty expression compiles and matches every description: the write
    # would succeed and drag the whole base under a single rule.
    if not form["match_value"]:
        return EMPTY_MATCH_MESSAGE
    if _number(form["group_id"]) is None:
        return message("invalid_group", form["group_id"])
    return None


def _asked(conn: sqlite3.Connection, request: Request) -> dict[str, str]:
    params = request.query_params
    asked = params.get("editar", "")
    if asked:
        found = conn.execute(_RULE, (asked,)).fetchone()
        if found is not None:
            return _submitted(
                found["id"],
                found["match_kind"],
                found["match_value"],
                found["group_id"],
                found["nature"],
                found["essentiality"],
            )
    form = _blank()
    kind = params.get("tipo", "")
    if kind in dict(KINDS):
        form["match_kind"] = kind
    form["match_value"] = params.get("valor", "")
    return form


def _submitted(
    rule_id: object,
    match_kind: str,
    match_value: str,
    group_id: object,
    nature: str,
    essentiality: str,
) -> dict[str, str]:
    return {
        "rule_id": "" if rule_id is None else str(rule_id),
        "match_kind": _text(match_kind),
        "match_value": _text(match_value).strip(),
        "group_id": str(group_id),
        "nature": _text(nature),
        "essentiality": _text(essentiality),
    }


def _text(raw: str) -> str:
    # Starlette reads an urlencoded field as latin-1 before percent-decoding it,
    # so a body carrying raw UTF-8 bytes arrives mojibake and every accented
    # term of the vocabulary is refused. Reading those bytes back as UTF-8 is
    # exact when it succeeds and leaves the value untouched when it does not.
    try:
        return raw.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return raw


def _blank() -> dict[str, str]:
    return _submitted(None, classify.MATCH_CATEGORY, "", "", "", "")


def _number(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None


def _reach(conn: sqlite3.Connection, rule_id: int) -> int:
    return int(conn.execute(_REACH, (rule_id,)).fetchone()[0])
