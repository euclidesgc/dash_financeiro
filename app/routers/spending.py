import sqlite3
from datetime import date
from typing import Any

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from app.db import connect
from app.payees.names import labels as payee_labels
from app.queries.axes import AXES, PAYEE_AXIS, aggregate, transactions_of
from app.queries.crossings import crossing
from app.queries.period import InvalidPeriodError, check_period, default_period
from app.queries.series import monthly_series
from app.queries.spending import SPENDING, total_spending_cents
from app.taxonomy.classify import residue
from app.taxonomy.seed import load_seed

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
LABELS: dict[str, str] = load_seed().get("category_labels", {})

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
    axis, start, end = _selection(request)
    conn = connect()
    try:
        # The panel labels its crossings by category and the table labels the
        # chosen axis; on the payee axis the table's map is the resolved one, so
        # the table has the last word over the single `labels` the page renders.
        context = _panel_context(conn, start, end)
        context.update(_table_context(conn, axis, start, end, _key(request)))
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "gastos.html", context)


@router.get(TABLE)
def spending_table(request: Request) -> Response:
    axis, start, end = _selection(request)
    conn = connect()
    try:
        context = _table_context(conn, axis, start, end, _key(request))
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "fragments/gastos_tabela.html", context)


@router.get(PANEL)
def spending_panel(request: Request) -> Response:
    _, start, end = _selection(request)
    conn = connect()
    try:
        context = _panel_context(conn, start, end)
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "fragments/gastos_painel.html", context)


@router.get(DETAIL)
def spending_detail(request: Request) -> Response:
    axis, start, end = _selection(request)
    conn = connect()
    try:
        context = _detail_context(conn, axis, _key(request), start, end)
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(request, "fragments/gastos_detalhe.html", context)


def _selection(request: Request) -> tuple[str, str, str]:
    # The screen is reached by hand-typed URL as often as by its own form, so a
    # value it cannot read falls back to the default window instead of a 500.
    params = request.query_params
    axis = params.get("eixo", "")
    default_start, default_end = default_period(date.today())
    start = params.get("inicio") or default_start
    end = params.get("fim") or default_end
    try:
        check_period(start, end)
    except InvalidPeriodError:
        start, end = default_start, default_end
    return (axis if axis in AXES else AXES[0]), start, end


def _key(request: Request) -> str | None:
    return request.query_params.get("chave") or None


def _base(axis: str, start: str, end: str) -> dict[str, Any]:
    return {
        "axes": AXES,
        "axis": axis,
        "start": start,
        "end": end,
        "labels": LABELS,
        "screen": SCREEN,
        "table_url": TABLE,
        "panel_url": PANEL,
        "detail_url": DETAIL,
    }


def _table_context(
    conn: sqlite3.Connection, axis: str, start: str, end: str, key: str | None
) -> dict[str, Any]:
    rows = aggregate(conn, axis=axis, start=start, end=end)
    context = _base(axis, start, end)
    if axis == PAYEE_AXIS:
        # Only the label. row['key'] is the label and the drill-down parameter
        # at once, and replacing the rendered value would kill the opening of
        # the list in silence (RF-28).
        context["labels"] = {**context["labels"], **payee_labels(conn)}
    context.update(
        rows=rows,
        total_cents=sum(row["amount_cents"] for row in rows),
        entries=sum(row["entries"] for row in rows),
        detail=_detail_context(conn, axis, key, start, end),
    )
    return context


def _detail_context(
    conn: sqlite3.Connection, axis: str, key: str | None, start: str, end: str
) -> dict[str, Any]:
    context = _base(axis, start, end)
    if key is None:
        context.update(key=None, rows=[], total_cents=0)
        return context
    rows = transactions_of(conn, axis=axis, key=key, start=start, end=end)
    context.update(key=key, rows=rows, total_cents=sum(row["amount_cents"] for row in rows))
    return context


def _panel_context(conn: sqlite3.Connection, start: str, end: str) -> dict[str, Any]:
    fallback = conn.execute(_FALLBACK_TERM).fetchone()
    return {
        "crossings": [
            _crossing(conn, row, fallback, start, end)
            for row in conn.execute(_CROSSINGS).fetchall()
        ],
        "series": monthly_series(conn, end_month=end[:MONTH_LENGTH]),
        "residue": residue(conn, start=start, end=end),
        "period_total_cents": total_spending_cents(conn, start, end),
        "labels": LABELS,
        "start": start,
        "end": end,
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
