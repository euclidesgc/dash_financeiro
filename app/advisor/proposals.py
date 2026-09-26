import sqlite3
from collections.abc import Sequence

from app.queries.advisor_proposals import (
    ProposalRow,
    ProposalStatus,
    TransactionSnapshot,
    get_proposal,
    insert_proposal,
    missing_transactions,
    move_status,
    refresh_previous,
    set_undo_skipped,
    undo_candidates,
)
from app.taxonomy.override import CategoryChange, UnknownCategoryError, recategorize

WRONG_STATE: dict[ProposalStatus, str] = {
    "pending": "A proposta ainda não foi aplicada.",
    "applied": "A proposta já foi aplicada.",
    "discarded": "A proposta foi descartada e não pode mais ser aplicada.",
    "undone": "A proposta já foi desfeita.",
}
MISSING = (
    "Algum lançamento desta proposta não existe mais (a atualização da Pluggy o removeu). "
    "Nada foi alterado; peça uma proposta nova ao consultor."
)
TARGET_GONE = (
    "A categoria de destino não existe mais. Nada foi alterado; peça uma proposta nova ao "
    "consultor."
)


class UnknownProposalError(LookupError):
    pass


class ProposalStateError(ValueError):
    pass


class StaleProposalError(ValueError):
    pass


def propose(
    conn: sqlite3.Connection,
    conversation_id: int,
    target_category: str,
    snapshots: Sequence[TransactionSnapshot],
    now: str,
) -> ProposalRow:
    # Reason: no commit — the proposal is part of the question's turn, which
    # app/advisor/chat.py:send commits at once; a provider failure later in
    # the loop leaves no orphan proposal behind.
    proposal_id = insert_proposal(conn, conversation_id, target_category, snapshots, now)
    return _found(conn, proposal_id)


def _found(conn: sqlite3.Connection, proposal_id: int) -> ProposalRow:
    proposal = get_proposal(conn, proposal_id)
    if proposal is None:
        raise UnknownProposalError(proposal_id)
    return proposal


def _settled(conn: sqlite3.Connection, proposal_id: int, wanted: ProposalStatus) -> ProposalRow:
    # Reason: the status move matched nothing — either the proposal does not
    # exist, or a previous click already moved it. Reaching the wanted status
    # again is the double click and answers with the proposal as it is.
    conn.rollback()
    proposal = _found(conn, proposal_id)
    if proposal.status != wanted:
        raise ProposalStateError(WRONG_STATE[proposal.status])
    return proposal


def apply(conn: sqlite3.Connection, proposal_id: int, now: str) -> ProposalRow:
    try:
        # Reason: the status move is the first write, so it takes SQLite's
        # write lock; a second click waits on it and then finds 'applied'.
        if not move_status(
            conn,
            proposal_id,
            from_status="pending",
            to_status="applied",
            stamp_column="applied_at",
            now=now,
        ):
            return _settled(conn, proposal_id, "applied")
        if missing_transactions(conn, proposal_id):
            raise StaleProposalError(MISSING)
        refresh_previous(conn, proposal_id)
        proposal = _found(conn, proposal_id)
        try:
            recategorize(
                conn,
                [
                    CategoryChange(item.transaction_id, proposal.target_category, "manual")
                    for item in proposal.items
                ],
            )
        except UnknownCategoryError as error:
            raise StaleProposalError(TARGET_GONE) from error
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return _found(conn, proposal_id)


def discard(conn: sqlite3.Connection, proposal_id: int, now: str) -> ProposalRow:
    if not move_status(
        conn,
        proposal_id,
        from_status="pending",
        to_status="discarded",
        stamp_column="discarded_at",
        now=now,
    ):
        return _settled(conn, proposal_id, "discarded")
    conn.commit()
    return _found(conn, proposal_id)


def undo(conn: sqlite3.Connection, proposal_id: int, now: str) -> ProposalRow:
    try:
        if not move_status(
            conn,
            proposal_id,
            from_status="applied",
            to_status="undone",
            stamp_column="undone_at",
            now=now,
        ):
            return _settled(conn, proposal_id, "undone")
        target = _found(conn, proposal_id).target_category
        changes: list[CategoryChange] = []
        skipped = 0
        for candidate in undo_candidates(conn, proposal_id):
            # Reason: an item the owner changed again after applying keeps
            # that later choice; so does one whose previous manual category
            # was deleted meanwhile, since restoring it would leave an
            # orphan key.
            still_ours = (
                candidate.current_category == target and candidate.current_source == "manual"
            )
            restorable = candidate.previous_source == "auto" or candidate.previous_exists
            if still_ours and restorable:
                changes.append(
                    CategoryChange(
                        candidate.transaction_id,
                        candidate.previous_category,
                        candidate.previous_source,
                    )
                )
            else:
                skipped += 1
        recategorize(conn, changes)
        set_undo_skipped(conn, proposal_id, skipped)
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return _found(conn, proposal_id)
