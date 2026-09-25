import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect, storable_int
from app.payees.names import labels as payee_labels
from app.queries.ahead import Ahead, posted_ahead
from app.queries.axes import AXES, ESSENTIALITY_AXIS, PAYEE_AXIS, aggregate, transactions_of
from app.queries.categories import category_labels
from app.queries.crossings import candidates, crossing, crossing_definitions
from app.queries.period import (
    InvalidPeriodError,
    check_period,
    covers_whole_months,
    default_period,
    month_end,
)
from app.queries.reach import category_reach, correction_target, holders, payee_reach
from app.queries.rules import residue, rules_carrying
from app.queries.series import monthly_series
from app.queries.spending import total_spending_cents
from app.queries.vocabulary import fallback_term, group_name, groups, natures, terms
from app.routers.reference import DATE_FIELD, Reference, screen_date
from app.routers.rules import form_text
from app.taxonomy.rules import Correction, RuleError, correct_payee

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/gastos"
TABLE = f"{SCREEN}/tabela"
PANEL = f"{SCREEN}/painel"
DETAIL = f"{SCREEN}/detalhe"
CORRECTION = f"{SCREEN}/correcao"

CANDIDATES = 5
MONTH_LENGTH = 7

CORRECTION_DONE_MESSAGE = "{entries} lançamento{plural} recolocado{plural} em {group}."
CORRECTION_HELD_MESSAGE = (
    "0 dos {previsto} lançamentos previstos foram movidos: a regra {match_value} "
    "ainda segura {payee}."
)
CORRECTION_MISSING_TARGET_MESSAGE = "Nenhum lançamento selecionado para corrigir."


@router.get(SCREEN)
def spending_screen(request: Request) -> Response:
    axis, start, end, reference = _selection(request)
    conn = connect()
    try:
        # Reason: the panel labels its crossings by category and the table
        # labels the chosen axis; on the payee axis the table's map is the
        # resolved one, so the table has the last word over the single
        # `labels` the page renders.
        context = _panel_context(conn, start, end, reference)
        context.update(
            _table_context(conn, axis, start, end, _key(request), reference, _corrigir(request))
        )
        context["notice"] = reference.notice
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "gastos.html", context)


@router.get(TABLE)
def spending_table(request: Request) -> Response:
    axis, start, end, reference = _selection(request)
    conn = connect()
    try:
        context = _table_context(
            conn, axis, start, end, _key(request), reference, _corrigir(request)
        )
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "fragments/gastos_tabela.html", context)


@router.get(PANEL)
def spending_panel(request: Request) -> Response:
    _, start, end, reference = _selection(request)
    conn = connect()
    try:
        context = _panel_context(conn, start, end, reference)
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "fragments/gastos_painel.html", context)


@router.get(DETAIL)
def spending_detail(request: Request) -> Response:
    axis, start, end, reference = _selection(request)
    conn = connect()
    try:
        context = _detail_context(
            conn, axis, _key(request), start, end, reference, _corrigir(request)
        )
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "fragments/gastos_detalhe.html", context)


@router.post(CORRECTION)
def spending_correction(
    request: Request,
    grupo: Annotated[str, Form()] = "",
    grupo_novo: Annotated[str, Form()] = "",
    natureza: Annotated[str, Form()] = "",
    # Workaround: bound by alias, not by name. The parameter reads whatever
    # the form field named after ESSENTIALITY_AXIS carries, without
    # spelling that field's name here as a literal.
    term: Annotated[str, Form(alias=ESSENTIALITY_AXIS)] = "",
) -> Response:
    axis, start, end, reference = _selection(request)
    key = _key(request)
    corrigir = _corrigir(request)
    conn = connect()
    try:
        target = _target(conn, corrigir)
        payee = (target["payee"] or "") if target is not None else ""
        new_group = form_text(grupo_novo).strip()
        notice: str | None = None
        result: Correction | None = None
        if corrigir is None:
            # Reason: without a target there is no payee to look up, so
            # calling correct_payee here would blame an "unknown payee" for a
            # request that never named one.
            notice = CORRECTION_MISSING_TARGET_MESSAGE
        else:
            try:
                result = correct_payee(
                    conn,
                    payee=payee,
                    group_id=storable_int(grupo),
                    new_group=new_group,
                    nature=form_text(natureza),
                    essentiality=form_text(term),
                )
            except RuleError as refusal:
                notice = str(refusal)
        context = _panel_context(conn, start, end, reference)
        context.update(
            _table_context(
                conn,
                axis,
                start,
                end,
                key,
                reference,
                corrigir,
                correction_notice=notice,
                correction_result=result,
            )
        )
        context["notice"] = reference.notice
        status_code = 400 if notice is not None else 200
        return TEMPLATES.TemplateResponse(request, "gastos.html", context, status_code=status_code)
    finally:
        conn.close()


def _selection(request: Request) -> tuple[str, str, str, Reference]:
    # Reason: the screen is reached by hand-typed URL as often as by its own
    # form, so a value it cannot read falls back to the default window
    # instead of a 500.
    params = request.query_params
    axis = params.get("eixo", "")
    reference = screen_date(params.get(DATE_FIELD))
    default_start, default_end = default_period(reference.date)
    start = params.get("inicio") or default_start
    end = params.get("fim") or default_end
    try:
        check_period(start, end)
    except InvalidPeriodError:
        start, end = default_start, default_end
    return (axis if axis in AXES else AXES[0]), start, end, reference


def _key(request: Request) -> str | None:
    return request.query_params.get("chave") or None


def _corrigir(request: Request) -> str | None:
    return request.query_params.get("corrigir") or None


def _base(
    conn: sqlite3.Connection, axis: str, start: str, end: str, reference: Reference
) -> dict[str, Any]:
    return {
        "axes": AXES,
        "axis": axis,
        "start": start,
        "end": end,
        "reference": reference.date.isoformat(),
        "labels": category_labels(conn),
        "screen": SCREEN,
        "table_url": TABLE,
        "panel_url": PANEL,
        "detail_url": DETAIL,
    }


def _ahead(conn: sqlite3.Connection, reference: Reference, end: str) -> Ahead:
    reference_iso = reference.date.isoformat()
    # Reason: a window whose end already reaches or passes the reference date
    # already carries whatever the current month posted ahead of it in its own
    # total, so naming it again here would say those entries are out of a
    # total that already holds them. A window that ends in an earlier month
    # has nothing to do with the reference's month at all, so naming it here
    # would attach a foreign month's number to a total that never touched it.
    if end[:MONTH_LENGTH] != reference_iso[:MONTH_LENGTH] or end > reference_iso:
        return Ahead(0, 0)
    return posted_ahead(conn, after=reference_iso, until=month_end(reference.date).isoformat())


def _table_context(
    conn: sqlite3.Connection,
    axis: str,
    start: str,
    end: str,
    key: str | None,
    reference: Reference,
    corrigir: str | None,
    *,
    correction_notice: str | None = None,
    correction_result: Correction | None = None,
) -> dict[str, Any]:
    rows = aggregate(conn, axis=axis, start=start, end=end)
    context = _base(conn, axis, start, end, reference)
    if axis == PAYEE_AXIS:
        # Reason: only the label. row['key'] is the label and the drill-down
        # parameter at once, and replacing the rendered value would kill the
        # opening of the list in silence (RF-28).
        context["labels"] = {**context["labels"], **payee_labels(conn)}
    context.update(
        rows=rows,
        total_cents=sum(row["amount_cents"] for row in rows),
        entries=sum(row["entries"] for row in rows),
        detail=_detail_context(
            conn,
            axis,
            key,
            start,
            end,
            reference,
            corrigir,
            correction_notice=correction_notice,
            correction_result=correction_result,
        ),
        ahead=_ahead(conn, reference, end),
    )
    return context


def _detail_context(
    conn: sqlite3.Connection,
    axis: str,
    key: str | None,
    start: str,
    end: str,
    reference: Reference,
    corrigir: str | None,
    *,
    correction_notice: str | None = None,
    correction_result: Correction | None = None,
) -> dict[str, Any]:
    context = _base(conn, axis, start, end, reference)
    context["correction"] = _correction_context(
        conn, corrigir, notice=correction_notice, result=correction_result
    )
    if key is None:
        context.update(key=None, rows=[], total_cents=0)
        return context
    rows = transactions_of(conn, axis=axis, key=key, start=start, end=end)
    context.update(key=key, rows=rows, total_cents=sum(row["amount_cents"] for row in rows))
    return context


def _target(conn: sqlite3.Connection, corrigir: str | None) -> sqlite3.Row | None:
    if not corrigir:
        return None
    target_id = storable_int(corrigir)
    if target_id is None:
        return None
    return correction_target(conn, target_id)


def _correction_context(
    conn: sqlite3.Connection,
    corrigir: str | None,
    *,
    notice: str | None,
    result: Correction | None,
) -> dict[str, Any] | None:
    if corrigir is None:
        # Reason: a refusal built above (missing target) still needs a place
        # to land; returning None here would carry the built notice into the
        # template and then drop it, which is the bug this guards against.
        return {"found": False, "notice": notice} if notice is not None else None
    target = _target(conn, corrigir)
    if target is None:
        return {"found": False, "notice": notice}
    payee = target["payee"] or ""
    category = target["category"] or ""
    return {
        "found": True,
        "id": target["id"],
        "payee": payee,
        "payee_reach": payee_reach(conn, payee),
        "category_reach": category_reach(conn, category),
        "groups": groups(conn),
        "natures": natures(conn),
        "terms": terms(conn),
        "current_group_id": target["group_id"],
        "current_nature": target["nature"] or "",
        "current_essentiality": target["essentiality"] or "",
        "notice": notice,
        "result": _result_context(conn, payee, result) if result is not None else None,
    }


def _result_context(conn: sqlite3.Connection, payee: str, result: Correction) -> dict[str, Any]:
    preview = payee_reach(conn, payee)
    if result.entries == 0 and preview["entries"] > 0:
        holder = holders(conn, payee=payee, rule_id=result.rule_id)[0]
        return {
            "held": True,
            "message": CORRECTION_HELD_MESSAGE.format(
                previsto=preview["entries"], match_value=holder["match_value"], payee=payee
            ),
        }
    plural = "" if result.entries == 1 else "s"
    return {
        "held": False,
        "message": CORRECTION_DONE_MESSAGE.format(
            entries=result.entries, plural=plural, group=group_name(conn, result.group_id)
        ),
    }


def _panel_context(
    conn: sqlite3.Connection, start: str, end: str, reference: Reference
) -> dict[str, Any]:
    fallback = fallback_term(conn)
    end_month = end[:MONTH_LENGTH]
    return {
        "crossings": [
            _crossing(conn, row, fallback, start, end) for row in crossing_definitions(conn)
        ],
        "series": monthly_series(conn, end_month=end_month),
        # Reason: the series always closes on `end_month` in full calendar
        # days, so a window whose end still sits in the reference's own
        # month draws its last bar over days the period total never reaches
        # (RF-06's own gap).
        "series_open": end_month == reference.date.isoformat()[:MONTH_LENGTH],
        "residue": residue(conn, start=start, end=end),
        "period_total_cents": total_spending_cents(conn, start, end),
        "whole_months": covers_whole_months(start, end),
        "labels": category_labels(conn),
        "start": start,
        "end": end,
        "reference": reference.date.isoformat(),
        "panel_url": PANEL,
    }


def _crossing(
    conn: sqlite3.Connection,
    definition: sqlite3.Row,
    fallback: str | None,
    start: str,
    end: str,
) -> dict[str, Any]:
    measured = crossing(conn, slug=definition["slug"], start=start, end=end)
    term = definition["essentiality"]
    # Reason: a crossing whose term no rule assigns is empty in every
    # period, and an empty block is the screen going mute on the question
    # the item exists to answer — it carries the candidates for that
    # decision instead (RF-48).
    unassigned = rules_carrying(conn, term) == 0
    offered = (
        candidates(
            conn,
            nature=definition["nature"],
            term=fallback,
            start=start,
            end=end,
            limit=CANDIDATES,
        )
        if unassigned and fallback is not None
        else []
    )
    return {
        "label": measured.label,
        "rows": measured.rows,
        "total_cents": measured.total_cents,
        "monthly_average_cents": measured.monthly_average_cents,
        "term": term,
        "nature": definition["nature"],
        "unassigned": unassigned,
        "candidates": offered,
        "candidates_term": fallback or "",
        "candidates_total_cents": sum(row["amount_cents"] for row in offered),
    }
