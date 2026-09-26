from datetime import date

import pytest

from app.advisor.proposals import (
    ProposalStateError,
    StaleProposalError,
    UnknownProposalError,
    apply,
    discard,
    undo,
)
from app.advisor.provider import ToolCall
from app.advisor.tools import (
    MAX_PROPOSAL,
    ToolContext,
    ToolInputError,
    propose_recategorization,
    run_tool,
)
from app.db import connect
from app.queries.advisor_chat import insert_conversation
from app.queries.advisor_proposals import get_proposal
from app.queries.expenses import list_expenses
from app.taxonomy.override import set_manual
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, transaction

NOW = "2026-09-26T12:00:00+00:00"
LATER = "2026-09-26T12:05:00+00:00"
ROWS = [
    transaction("p1", "2026-08-04", -100.00, descricao="Posto Sao Joao"),
    transaction("p2", "2026-08-31", -85.50, descricao="Posto dos Cavaleiros"),
    transaction("p3", "2026-07-10", -40.00, descricao="Posto antigo"),
    transaction("f1", "2026-08-12", -23.45, descricao="Drogaria Raia"),
]


@pytest.fixture
def conn(taxonomy_conn):
    seed_taxonomy(taxonomy_conn)
    load(taxonomy_conn, ROWS)
    taxonomy_conn.execute(
        "UPDATE transactions SET category = 'Gas stations', category_auto = 'Gas stations'"
        " WHERE pluggy_id IN ('p1', 'p2', 'p3')"
    )
    taxonomy_conn.execute(
        "UPDATE transactions SET category = 'Pharmacy', category_auto = 'Pharmacy'"
        " WHERE pluggy_id = 'f1'"
    )
    insert_conversation(taxonomy_conn, "Nova conversa", NOW)
    taxonomy_conn.commit()
    return taxonomy_conn


@pytest.fixture
def context():
    return ToolContext(conversation_id=1, now=NOW, today=date(2026, 9, 26))


def _id(conn, pluggy_id):
    row = conn.execute("SELECT id FROM transactions WHERE pluggy_id = ?", (pluggy_id,)).fetchone()
    return row["id"]


def _state(conn, pluggy_id):
    row = conn.execute(
        "SELECT category, category_source FROM transactions WHERE pluggy_id = ?", (pluggy_id,)
    ).fetchone()
    return row["category"], row["category_source"]


def _propose(conn, context, arguments):
    content = propose_recategorization(conn, arguments, context)
    conn.commit()
    return content["proposal_id"]


AUGUST = {"date_from": "2026-08-01", "date_to": "2026-08-31"}
AUGUST_FUEL = {"text": "posto", **AUGUST}


def test_proposal_by_filter_takes_the_same_ids_as_the_search_and_changes_nothing(conn, context):
    content = propose_recategorization(
        conn, {**AUGUST_FUEL, "target_category": "supermercado"}, context
    )

    searched = list_expenses(conn, page=1, page_size=50, search="posto", **AUGUST)
    assert [item["id"] for item in content["items"]] == [item["id"] for item in searched.items]
    assert content["count"] == 2
    assert content["total"] == "−R$ 185,50"
    assert content["target_category"] == "Supermercado"
    assert content["status"] == "pending"
    assert [item["from_category"] for item in content["items"]] == ["Posto de combustível"] * 2
    assert _state(conn, "p1") == ("Gas stations", "auto")
    assert "Nada foi alterado" in content["next_step"]


def test_proposal_by_ids_leaves_out_what_is_already_in_the_target(conn, context):
    ids = [_id(conn, "p1"), _id(conn, "f1")]

    content = propose_recategorization(
        conn, {"transaction_ids": ids, "target_category": "Farmácia"}, context
    )

    assert [item["id"] for item in content["items"]] == [_id(conn, "p1")]
    assert content["already_in_target"] == 1


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"text": "posto", "target_category": "Categoria inventada"}, "Supermercado"),
        ({"target_category": "Supermercado"}, "Diga quais lançamentos"),
        ({"transaction_ids": [999999], "target_category": "Supermercado"}, "999999"),
        ({"transaction_ids": [], "target_category": "Supermercado"}, "lista de ids"),
        ({"transaction_ids": ["abc"], "target_category": "Supermercado"}, "inteiros"),
        ({"text": "nada disso", "target_category": "Supermercado"}, "Nenhum lançamento"),
        ({"text": "drogaria", "target_category": "Farmácia"}, "já estão em Farmácia"),
        ({"text": "posto"}, "target_category"),
        (
            {
                "transaction_ids": list(range(1, MAX_PROPOSAL + 2)),
                "target_category": "Supermercado",
            },
            f"mais de {MAX_PROPOSAL}",
        ),
    ],
)
def test_invalid_proposals_are_refused_with_the_next_step(conn, context, arguments, message):
    with pytest.raises(ToolInputError, match=message):
        propose_recategorization(conn, arguments, context)
    assert conn.execute("SELECT count(*) FROM advisor_proposals").fetchone()[0] == 0


def test_run_tool_returns_the_refusal_to_the_model(conn, context):
    call = ToolCall(
        id="c1", name="propose_recategorization", input={"text": "posto", "target_category": "Xyz"}
    )

    result = run_tool(conn, call, context)

    assert result.is_error and "não existe" in result.content["error"]


def test_apply_moves_every_item_as_a_manual_choice_and_reclassifies(conn, context):
    proposal_id = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})

    applied = apply(conn, proposal_id, LATER)

    assert applied.status == "applied" and applied.applied_at == LATER
    assert _state(conn, "p1") == ("Groceries", "manual")
    assert _state(conn, "p2") == ("Groceries", "manual")
    assert _state(conn, "p3") == ("Gas stations", "auto")
    groups = conn.execute(
        "SELECT DISTINCT t.group_id = c.group_id FROM transactions AS t"
        " JOIN categories AS c ON c.name = t.category WHERE t.pluggy_id IN ('p1', 'p2')"
    ).fetchall()
    assert [row[0] for row in groups] == [1]


def test_applied_choice_survives_the_next_bank_update(conn, context):
    proposal_id = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})
    apply(conn, proposal_id, LATER)

    load(conn, ROWS)

    assert _state(conn, "p1") == ("Groceries", "manual")


def test_applying_twice_answers_the_same_proposal_without_writing_again(conn, context):
    proposal_id = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})
    apply(conn, proposal_id, LATER)
    set_manual(conn, _id(conn, "p1"), "Pharmacy")

    again = apply(conn, proposal_id, "2026-09-26T13:00:00+00:00")

    assert again.status == "applied" and again.applied_at == LATER
    assert _state(conn, "p1") == ("Pharmacy", "manual")


def test_a_second_connection_clicking_apply_finds_it_applied(conn, context, tmp_path):
    proposal_id = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})
    other = connect(str(tmp_path / "dash.sqlite"))
    try:
        first = apply(conn, proposal_id, LATER)
        second = apply(other, proposal_id, "2026-09-26T13:00:00+00:00")
    finally:
        other.close()

    assert first.applied_at == second.applied_at == LATER


def test_apply_with_a_vanished_target_or_transaction_writes_nothing(conn, context):
    proposal_id = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})
    conn.execute(
        "UPDATE advisor_proposals SET target_category = 'Gone' WHERE id = ?", (proposal_id,)
    )
    conn.commit()

    with pytest.raises(StaleProposalError, match="categoria de destino"):
        apply(conn, proposal_id, LATER)

    assert get_proposal(conn, proposal_id).status == "pending"
    assert _state(conn, "p1") == ("Gas stations", "auto")

    other_id = _propose(conn, context, {"text": "drogaria", "target_category": "Supermercado"})
    conn.execute("DELETE FROM transactions WHERE pluggy_id = 'f1'")
    conn.commit()
    with pytest.raises(StaleProposalError, match="não existe mais"):
        apply(conn, other_id, LATER)
    assert get_proposal(conn, other_id).status == "pending"


def test_undo_restores_previous_category_and_source(conn, context):
    set_manual(conn, _id(conn, "p2"), "Pharmacy")
    proposal_id = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})
    apply(conn, proposal_id, LATER)

    undone = undo(conn, proposal_id, "2026-09-26T13:00:00+00:00")

    assert undone.status == "undone" and undone.undo_skipped == 0
    assert _state(conn, "p1") == ("Gas stations", "auto")
    assert _state(conn, "p2") == ("Pharmacy", "manual")


def test_undo_keeps_an_item_changed_after_applying_and_counts_it(conn, context):
    proposal_id = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})
    apply(conn, proposal_id, LATER)
    set_manual(conn, _id(conn, "p1"), "Pharmacy")

    undone = undo(conn, proposal_id, "2026-09-26T13:00:00+00:00")

    assert undone.undo_skipped == 1
    assert _state(conn, "p1") == ("Pharmacy", "manual")
    assert _state(conn, "p2") == ("Gas stations", "auto")


def test_undo_twice_is_idempotent(conn, context):
    proposal_id = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})
    apply(conn, proposal_id, LATER)
    first = undo(conn, proposal_id, "2026-09-26T13:00:00+00:00")

    second = undo(conn, proposal_id, "2026-09-26T14:00:00+00:00")

    assert second.undone_at == first.undone_at


def test_transitions_a_status_does_not_allow_are_refused(conn, context):
    pending = _propose(conn, context, {**AUGUST_FUEL, "target_category": "Supermercado"})
    with pytest.raises(ProposalStateError, match="ainda não foi aplicada"):
        undo(conn, pending, LATER)

    discarded = discard(conn, pending, LATER)
    assert discarded.status == "discarded" and discarded.discarded_at == LATER
    assert discard(conn, pending, "2026-09-26T13:00:00+00:00").discarded_at == LATER
    with pytest.raises(ProposalStateError, match="descartada"):
        apply(conn, pending, LATER)
    assert _state(conn, "p1") == ("Gas stations", "auto")

    applied = _propose(conn, context, {"text": "drogaria", "target_category": "Supermercado"})
    apply(conn, applied, LATER)
    with pytest.raises(ProposalStateError, match="já foi aplicada"):
        discard(conn, applied, LATER)
    with pytest.raises(UnknownProposalError):
        apply(conn, 999, LATER)
