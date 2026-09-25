import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect
from app.queries.rules import (
    held_by_rule,
    payee_samples,
    residue,
    rule,
    rule_candidates,
    rule_id_of,
    rule_listing,
)
from app.queries.vocabulary import groups, natures, terms
from app.taxonomy import classify
from app.taxonomy.rules import RuleError, create_rule, delete_rule, update_rule
from app.taxonomy.seed import message, seed_labels

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/regras"
EDIT = "/editar"
REMOVE = "/remover"

CANDIDATES = 12
SAMPLES = 3

LABELS: dict[str, str] = seed_labels()

KINDS: tuple[tuple[str, str], ...] = (
    (classify.MATCH_CATEGORY, "Categoria"),
    (classify.MATCH_DESCRIPTION, "Descrição"),
)

EMPTY_MATCH_MESSAGE = "Casamento vazio: escreva o texto que a regra procura."
UNKNOWN_KIND_MESSAGE = "Tipo de casamento inválido: {value}"
DUPLICATE_MESSAGE = "Já existe uma regra com esse casamento: {value}"


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
        written = rule_id_of(conn, match_kind=form["match_kind"], match_value=form["match_value"])
        reach = None if written is None else held_by_rule(conn, written)
        return _answer(request, conn, _blank(), done=done, reach=reach)
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
        return _answer(request, conn, _blank(), done=done, reach=held_by_rule(conn, rule_id))
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
    return {
        "rules": rule_listing(conn),
        "residue": residue(conn),
        "candidates": rule_candidates(
            conn,
            category_kind=classify.MATCH_CATEGORY,
            payee_kind=classify.MATCH_DESCRIPTION,
            limit=CANDIDATES,
        ),
        "groups": groups(conn),
        "natures": natures(conn),
        "terms": terms(conn),
        "samples": payee_samples(conn, SAMPLES),
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
    # Reason: an empty expression compiles and matches every description —
    # the write would succeed and drag the whole base under a single rule.
    if not form["match_value"]:
        return EMPTY_MATCH_MESSAGE
    if _number(form["group_id"]) is None:
        return message("invalid_group", form["group_id"])
    return None


def _asked(conn: sqlite3.Connection, request: Request) -> dict[str, str]:
    params = request.query_params
    asked = params.get("editar", "")
    if asked:
        found = rule(conn, asked)
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
        "match_kind": form_text(match_kind),
        "match_value": form_text(match_value).strip(),
        "group_id": str(group_id),
        "nature": form_text(nature),
        "essentiality": form_text(essentiality),
    }


def form_text(raw: str) -> str:
    # Reason: Starlette reads an urlencoded field as latin-1 before
    # percent-decoding it, so a body carrying raw UTF-8 bytes arrives
    # mojibake and every accented term of the vocabulary is refused. Reading
    # those bytes back as UTF-8 is exact when it succeeds and leaves the
    # value untouched when it does not.
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
