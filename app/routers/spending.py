import sqlite3
from typing import Any

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect
from app.payees.names import labels as payee_labels
from app.queries.ahead import Ahead, posted_ahead
from app.queries.axes import AXES, PAYEE_AXIS, aggregate, transactions_of
from app.queries.crossings import crossing
from app.queries.period import (
    InvalidPeriodError,
    check_period,
    covers_whole_months,
    default_period,
    month_end,
)
from app.queries.series import monthly_series
from app.queries.spending import SPENDING, total_spending_cents
from app.routers.reference import DATE_FIELD, Reference, screen_date
from app.taxonomy.classify import residue
from app.taxonomy.seed import category_labels

from .render import TEMPLATES

router = APIRouter()

SCREEN = "/gastos"
TABLE = f"{SCREEN}/tabela"
PANEL = f"{SCREEN}/painel"
DETAIL = f"{SCREEN}/detalhe"

CANDIDATES = 5
MONTH_LENGTH = 7

# The category key stays the raw name the source sends, because that is what
# matches it again on the next sync; the reading label is data next to it.
LABELS: dict[str, str] = category_labels()

_CROSSINGS = "SELECT slug, label, nature, essentiality FROM crossings ORDER BY position"
_FALLBACK_TERM = "SELECT value FROM essentialities WHERE is_fallback = 1"
_RULES_CARRYING = "SELECT count(*) FROM category_rules WHERE essentiality = ?"
_CANDIDATES = (
    "SELECT category AS key, sum(amount_cents) AS amount_cents, count(*) AS entries "
    f"FROM transactions WHERE {SPENDING} AND nature = ? AND essentiality = ? "
    "AND date >= ? AND date <= ? GROUP BY category ORDER BY amount_cents LIMIT ?"
)


@router.get(SCREEN)
def spending_screen(request: Request) -> Response:
    axis, start, end, reference = _selection(request)
    conn = connect()
    try:
        # The panel labels its crossings by category and the table labels the
        # chosen axis; on the payee axis the table's map is the resolved one, so
        # the table has the last word over the single `labels` the page renders.
        context = _panel_context(conn, start, end, reference)
        context.update(_table_context(conn, axis, start, end, _key(request), reference))
        context["notice"] = reference.notice
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "gastos.html", context)


@router.get(TABLE)
def spending_table(request: Request) -> Response:
    axis, start, end, reference = _selection(request)
    conn = connect()
    try:
        context = _table_context(conn, axis, start, end, _key(request), reference)
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
        context = _detail_context(conn, axis, _key(request), start, end, reference)
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "fragments/gastos_detalhe.html", context)


def _selection(request: Request) -> tuple[str, str, str, Reference]:
    # The screen is reached by hand-typed URL as often as by its own form, so a
    # value it cannot read falls back to the default window instead of a 500.
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


def _base(axis: str, start: str, end: str, reference: Reference) -> dict[str, Any]:
    return {
        "axes": AXES,
        "axis": axis,
        "start": start,
        "end": end,
        "reference": reference.date.isoformat(),
        "labels": LABELS,
        "screen": SCREEN,
        "table_url": TABLE,
        "panel_url": PANEL,
        "detail_url": DETAIL,
    }


def _ahead(conn: sqlite3.Connection, reference: Reference, end: str) -> Ahead:
    reference_iso = reference.date.isoformat()
    # A window whose end already reaches or passes the reference date already
    # carries whatever the current month posted ahead of it in its own total,
    # so naming it again here would say those entries are out of a total that
    # already holds them. A window that ends in an earlier month has nothing
    # to do with the reference's month at all, so naming it here would attach
    # a foreign month's number to a total that never touched it.
    if end[:MONTH_LENGTH] != reference_iso[:MONTH_LENGTH] or end > reference_iso:
        return Ahead(0, 0)
    return posted_ahead(conn, after=reference_iso, until=month_end(reference.date).isoformat())


def _table_context(
    conn: sqlite3.Connection, axis: str, start: str, end: str, key: str | None, reference: Reference
) -> dict[str, Any]:
    rows = aggregate(conn, axis=axis, start=start, end=end)
    context = _base(axis, start, end, reference)
    if axis == PAYEE_AXIS:
        # Only the label. row['key'] is the label and the drill-down parameter
        # at once, and replacing the rendered value would kill the opening of
        # the list in silence (RF-28).
        context["labels"] = {**context["labels"], **payee_labels(conn)}
    context.update(
        rows=rows,
        total_cents=sum(row["amount_cents"] for row in rows),
        entries=sum(row["entries"] for row in rows),
        detail=_detail_context(conn, axis, key, start, end, reference),
        ahead=_ahead(conn, reference, end),
    )
    return context


def _detail_context(
    conn: sqlite3.Connection, axis: str, key: str | None, start: str, end: str, reference: Reference
) -> dict[str, Any]:
    context = _base(axis, start, end, reference)
    if key is None:
        context.update(key=None, rows=[], total_cents=0)
        return context
    rows = transactions_of(conn, axis=axis, key=key, start=start, end=end)
    context.update(key=key, rows=rows, total_cents=sum(row["amount_cents"] for row in rows))
    return context


def _panel_context(
    conn: sqlite3.Connection, start: str, end: str, reference: Reference
) -> dict[str, Any]:
    fallback = conn.execute(_FALLBACK_TERM).fetchone()
    end_month = end[:MONTH_LENGTH]
    return {
        "crossings": [
            _crossing(conn, row, fallback, start, end)
            for row in conn.execute(_CROSSINGS).fetchall()
        ],
        "series": monthly_series(conn, end_month=end_month),
        # The series always closes on `end_month` in full calendar days, so a
        # window whose end still sits in the reference's own month draws its
        # last bar over days the period total never reaches (RF-06's own gap).
        "series_open": end_month == reference.date.isoformat()[:MONTH_LENGTH],
        "residue": residue(conn, start=start, end=end),
        "period_total_cents": total_spending_cents(conn, start, end),
        "whole_months": covers_whole_months(start, end),
        "labels": LABELS,
        "start": start,
        "end": end,
        "reference": reference.date.isoformat(),
        "panel_url": PANEL,
    }


def _crossing(
    conn: sqlite3.Connection,
    definition: sqlite3.Row,
    fallback: sqlite3.Row | None,
    start: str,
    end: str,
) -> dict[str, Any]:
    measured = crossing(conn, slug=definition["slug"], start=start, end=end)
    term = definition["essentiality"]
    # A crossing whose term no rule assigns is empty in every period, and an
    # empty block is the screen going mute on the question the item exists to
    # answer: it carries the candidates for that decision instead (RF-48).
    unassigned = conn.execute(_RULES_CARRYING, (term,)).fetchone()[0] == 0
    candidates = (
        _candidates(conn, definition["nature"], fallback["value"], start, end)
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
        "candidates": candidates,
        "candidates_term": fallback["value"] if fallback is not None else "",
        "candidates_total_cents": sum(row["amount_cents"] for row in candidates),
    }


def _candidates(
    conn: sqlite3.Connection, nature: str, term: str, start: str, end: str
) -> list[sqlite3.Row]:
    return conn.execute(_CANDIDATES, (nature, term, start, end, CANDIDATES)).fetchall()
