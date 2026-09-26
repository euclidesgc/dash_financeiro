import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

ProposalStatus = Literal["pending", "applied", "discarded", "undone"]
Source = Literal["auto", "manual"]


@dataclass(frozen=True)
class TransactionSnapshot:
    id: int
    date: str
    description: str | None
    amount_cents: int
    category: str | None
    source: Source


@dataclass(frozen=True)
class ProposalItemRow:
    transaction_id: int
    date: str
    description: str | None
    amount_cents: int
    previous_category: str | None
    previous_label: str | None
    previous_source: Source


@dataclass(frozen=True)
class ProposalRow:
    id: int
    conversation_id: int
    target_category: str
    target_label: str
    status: ProposalStatus
    created_at: str
    applied_at: str | None
    discarded_at: str | None
    undone_at: str | None
    undo_skipped: int | None
    items: list[ProposalItemRow]


@dataclass(frozen=True)
class UndoCandidate:
    transaction_id: int
    previous_category: str | None
    previous_source: Source
    current_category: str | None
    current_source: Source | None
    previous_exists: bool


_LABEL = "COALESCE(c.label, NULLIF({column}, ''))"
_PROPOSALS = (
    "SELECT p.id, p.conversation_id, p.target_category,"
    f" {_LABEL.format(column='p.target_category')} AS target_label, p.status, p.created_at,"
    " p.applied_at, p.discarded_at, p.undone_at, p.undo_skipped"
    " FROM advisor_proposals AS p LEFT JOIN categories AS c ON c.name = p.target_category"
)
_ITEMS = (
    "SELECT i.proposal_id, i.transaction_id, i.date, i.description, i.amount_cents,"
    f" i.previous_category, {_LABEL.format(column='i.previous_category')} AS previous_label,"
    " i.previous_source"
    " FROM advisor_proposal_items AS i LEFT JOIN categories AS c ON c.name = i.previous_category"
)


def _marks(count: int) -> str:
    return ", ".join("?" * count)


def transaction_snapshots(
    conn: sqlite3.Connection, transaction_ids: Sequence[int]
) -> list[TransactionSnapshot]:
    if not transaction_ids:
        return []
    rows = conn.execute(
        "SELECT id, date, description, amount_cents, category, category_source FROM transactions"
        f" WHERE id IN ({_marks(len(transaction_ids))}) ORDER BY date DESC, id DESC",
        list(transaction_ids),
    ).fetchall()
    return [
        TransactionSnapshot(
            id=row["id"],
            date=row["date"],
            description=row["description"],
            amount_cents=int(row["amount_cents"]),
            category=row["category"] or None,
            source="manual" if row["category_source"] == "manual" else "auto",
        )
        for row in rows
    ]


def insert_proposal(
    conn: sqlite3.Connection,
    conversation_id: int,
    target_category: str,
    snapshots: Sequence[TransactionSnapshot],
    now: str,
) -> int:
    cursor = conn.execute(
        "INSERT INTO advisor_proposals (conversation_id, target_category, created_at)"
        " VALUES (?, ?, ?)",
        (conversation_id, target_category, now),
    )
    proposal_id = int(cursor.lastrowid or 0)
    conn.executemany(
        "INSERT INTO advisor_proposal_items (proposal_id, transaction_id, date, description,"
        " amount_cents, previous_category, previous_source) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                proposal_id,
                item.id,
                item.date,
                item.description,
                item.amount_cents,
                item.category,
                item.source,
            )
            for item in snapshots
        ],
    )
    return proposal_id


def move_status(
    conn: sqlite3.Connection,
    proposal_id: int,
    *,
    from_status: ProposalStatus,
    to_status: ProposalStatus,
    stamp_column: Literal["applied_at", "discarded_at", "undone_at"],
    now: str,
) -> bool:
    cursor = conn.execute(
        f"UPDATE advisor_proposals SET status = ?, {stamp_column} = ? WHERE id = ? AND status = ?",
        (to_status, now, proposal_id, from_status),
    )
    return cursor.rowcount == 1


def missing_transactions(conn: sqlite3.Connection, proposal_id: int) -> int:
    (count,) = conn.execute(
        "SELECT count(*) FROM advisor_proposal_items AS i"
        " WHERE i.proposal_id = ? AND NOT EXISTS"
        " (SELECT 1 FROM transactions AS t WHERE t.id = i.transaction_id)",
        (proposal_id,),
    ).fetchone()
    return int(count)


def refresh_previous(conn: sqlite3.Connection, proposal_id: int) -> None:
    conn.execute(
        "UPDATE advisor_proposal_items SET"
        " previous_category = (SELECT NULLIF(t.category, '') FROM transactions AS t"
        " WHERE t.id = advisor_proposal_items.transaction_id),"
        " previous_source = (SELECT t.category_source FROM transactions AS t"
        " WHERE t.id = advisor_proposal_items.transaction_id)"
        " WHERE proposal_id = ?",
        (proposal_id,),
    )


def undo_candidates(conn: sqlite3.Connection, proposal_id: int) -> list[UndoCandidate]:
    rows = conn.execute(
        "SELECT i.transaction_id, i.previous_category, i.previous_source,"
        " NULLIF(t.category, '') AS current_category, t.category_source AS current_source,"
        " (i.previous_category IS NULL OR EXISTS"
        " (SELECT 1 FROM categories AS c WHERE c.name = i.previous_category)) AS previous_exists"
        " FROM advisor_proposal_items AS i"
        " LEFT JOIN transactions AS t ON t.id = i.transaction_id"
        " WHERE i.proposal_id = ? ORDER BY i.id",
        (proposal_id,),
    ).fetchall()
    return [
        UndoCandidate(
            transaction_id=row["transaction_id"],
            previous_category=row["previous_category"],
            previous_source="manual" if row["previous_source"] == "manual" else "auto",
            current_category=row["current_category"],
            current_source=row["current_source"],
            previous_exists=bool(row["previous_exists"]),
        )
        for row in rows
    ]


def set_undo_skipped(conn: sqlite3.Connection, proposal_id: int, skipped: int) -> None:
    conn.execute(
        "UPDATE advisor_proposals SET undo_skipped = ? WHERE id = ?", (skipped, proposal_id)
    )


def _item(row: sqlite3.Row) -> ProposalItemRow:
    return ProposalItemRow(
        transaction_id=row["transaction_id"],
        date=row["date"],
        description=row["description"],
        amount_cents=int(row["amount_cents"]),
        previous_category=row["previous_category"],
        previous_label=row["previous_label"],
        previous_source="manual" if row["previous_source"] == "manual" else "auto",
    )


def _proposals(conn: sqlite3.Connection, where: str, params: Sequence[int]) -> list[ProposalRow]:
    heads = conn.execute(f"{_PROPOSALS} WHERE {where} ORDER BY p.id", list(params)).fetchall()
    if not heads:
        return []
    ids = [row["id"] for row in heads]
    grouped: dict[int, list[ProposalItemRow]] = {proposal_id: [] for proposal_id in ids}
    for row in conn.execute(
        f"{_ITEMS} WHERE i.proposal_id IN ({_marks(len(ids))})"
        " ORDER BY i.proposal_id, i.date DESC, i.id",
        ids,
    ).fetchall():
        grouped[row["proposal_id"]].append(_item(row))
    return [
        ProposalRow(
            id=row["id"],
            conversation_id=row["conversation_id"],
            target_category=row["target_category"],
            target_label=row["target_label"],
            status=row["status"],
            created_at=row["created_at"],
            applied_at=row["applied_at"],
            discarded_at=row["discarded_at"],
            undone_at=row["undone_at"],
            undo_skipped=row["undo_skipped"],
            items=grouped[row["id"]],
        )
        for row in heads
    ]


def get_proposal(conn: sqlite3.Connection, proposal_id: int) -> ProposalRow | None:
    found = _proposals(conn, "p.id = ?", [proposal_id])
    return found[0] if found else None


def conversation_proposals(conn: sqlite3.Connection, conversation_id: int) -> list[ProposalRow]:
    return _proposals(conn, "p.conversation_id = ?", [conversation_id])
