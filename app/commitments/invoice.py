import sqlite3
from datetime import date
from typing import Any

from app.commitments import INSTALLMENT
from app.commitments.live import installments, live_floor
from app.commitments.schedule import end_month
from app.queries.invoices import card_series

_SeriesEntry = tuple[str, dict[str, Any]]


def invoice_month(when: str, closing_day: int | None) -> str:
    if closing_day is None or int(when[8:10]) <= closing_day:
        return when[:7]
    return end_month(when[:7], 1)


def payment_month(when: str, closing_day: int | None, due_day: int | None) -> str:
    anchor = invoice_month(when, closing_day)
    # Reason: (D-006) closing_day decides which invoice a parcel belongs
    # to; due_day decides the month that invoice leaves the account. The
    # offset is constant per card, so it moves the whole curve and changes
    # no sum.
    if closing_day is None or due_day is None:
        return end_month(anchor, 0)
    return end_month(anchor, 1 if due_day < closing_day else 0)


def invoice_curve(conn: sqlite3.Connection, *, today: date | None = None) -> dict[str, Any]:
    reference = today or date.today()
    ref_month = f"{reference.year:04d}-{reference.month:02d}"
    floor = live_floor(today)
    rows = card_series(conn, kind=INSTALLMENT, floor=floor)
    cards = [_card(name, group, ref_month) for name, group in _grouped(rows).items()]
    matched = sum(len(card["series"]) for card in cards)
    return {
        "cards": cards,
        "off_card": len(installments(conn, today=today)) - matched,
        "remaining_cents": sum(card["remaining_cents"] for card in cards),
    }


def _grouped(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["card_name"], []).append(row)
    return grouped


def _card(name: str, rows: list[dict[str, Any]], ref_month: str) -> dict[str, Any]:
    closing_day, due_day = rows[0]["closing_day"], rows[0]["due_day"]
    entries = [_series(row, closing_day, due_day) for row in rows if row["series_key"] is not None]
    series = [entry for _, entry in entries]
    return {
        "name": name,
        "closing_day": closing_day,
        "due_day": due_day,
        "assumed": closing_day is None or due_day is None,
        "months": _months(ref_month, entries),
        "series": series,
        "remaining_cents": sum(entry["remaining_cents"] for entry in series),
        "last_invoice": max((entry["last_invoice"] for entry in series), default=None),
    }


def _series(row: dict[str, Any], closing_day: int | None, due_day: int | None) -> _SeriesEntry:
    anchor = payment_month(row["last_seen_date"], closing_day, due_day)
    last_invoice = end_month(anchor, row["installments_left"])
    amount_cents = row["amount_cents"]
    return anchor, {
        "series_key": row["series_key"],
        "description": row["description"],
        "amount_cents": amount_cents,
        "installments_left": row["installments_left"],
        "remaining_cents": amount_cents * row["installments_left"],
        "last_invoice": last_invoice,
        "frees_cents": -amount_cents,
    }


def _months(ref_month: str, entries: list[_SeriesEntry]) -> list[dict[str, Any]]:
    if not entries:
        return []
    last = max(entry["last_invoice"] for _, entry in entries)
    return [
        {
            "month": label,
            "total_cents": sum(
                entry["amount_cents"]
                for anchor, entry in entries
                if anchor < label <= entry["last_invoice"]
            ),
        }
        for label in _label_range(ref_month, last)
    ]


def _label_range(start: str, end: str) -> list[str]:
    labels = [start]
    while labels[-1] < end:
        labels.append(end_month(labels[-1], 1))
    return labels
