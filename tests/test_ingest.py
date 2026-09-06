import json
from pathlib import Path

import pytest

from app.db import connect
from app.ingest.loader import ingest
from app.ingest.source import load_accounts, load_transactions
from app.migrate import run_migrations

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def conn(tmp_path):
    path = str(tmp_path / "dash.sqlite")
    run_migrations(path)
    connection = connect(path)
    yield connection
    connection.close()


@pytest.fixture
def accounts():
    return load_accounts(str(FIXTURES / "accounts_fixture.json"))


def counts(conn):
    return (
        conn.execute("SELECT count(*) FROM transactions").fetchone()[0],
        conn.execute("SELECT count(*) FROM accounts").fetchone()[0],
        conn.execute("SELECT count(*) FROM sync_runs").fetchone()[0],
    )


def test_source_reads_both_the_envelope_and_the_bare_list(tmp_path):
    envelope = tmp_path / "accounts_envelope.json"
    envelope.write_text(json.dumps({"results": [{"id": "a"}]}), encoding="utf-8")
    bare = tmp_path / "accounts_bare.json"
    bare.write_text(json.dumps([{"id": "b"}]), encoding="utf-8")
    assert [a["id"] for a in load_accounts(str(tmp_path / "accounts_*.json"))] == ["b", "a"]


def test_rejects_the_offending_line_and_writes_nothing(conn, accounts):
    transactions = load_transactions(str(FIXTURES / "transacoes_invalidas.json"))
    result = ingest(conn, transactions=transactions, accounts=accounts, source="fixture")
    assert result.status == "failed"
    assert [(r.index, r.reason) for r in result.rejections] == [
        (1, "missing_pluggy_id"),
        (2, "fractional_cents"),
    ]
    assert counts(conn) == (0, 0, 1)


def test_divergence_rolls_back_and_the_failed_run_survives(conn, accounts):
    transactions = load_transactions(str(FIXTURES / "transacoes_id_duplicado.json"))
    result = ingest(conn, transactions=transactions, accounts=accounts, source="fixture")
    assert result.status == "failed"
    assert "accepted=3 written=2" in result.message
    assert counts(conn) == (0, 0, 1)
    run = conn.execute("SELECT status, message FROM sync_runs").fetchone()
    assert run["status"] == "failed"
    assert "accepted=3 written=2" in run["message"]


def test_second_run_over_the_same_source_does_not_duplicate(conn, accounts):
    transactions = load_transactions(str(FIXTURES / "transacoes_id_duplicado.json"))[:2]
    for _ in range(2):
        result = ingest(conn, transactions=transactions, accounts=accounts, source="fixture")
        assert result.status == "ok"
    assert counts(conn) == (2, 1, 2)


def test_updates_the_row_that_the_source_changed(conn, accounts):
    transactions = load_transactions(str(FIXTURES / "transacoes_id_duplicado.json"))[:1]
    ingest(conn, transactions=transactions, accounts=accounts, source="fixture")
    transactions[0]["descricao"] = "DESCRICAO CORRIGIDA"
    transactions[0]["valor"] = -11.0
    ingest(conn, transactions=transactions, accounts=accounts, source="fixture")
    row = conn.execute("SELECT description, amount_cents FROM transactions").fetchone()
    assert (row["description"], row["amount_cents"]) == ("DESCRICAO CORRIGIDA", -1100)


def test_card_balance_is_stored_as_debt(conn):
    card = {"id": "acc-card", "type": "CREDIT", "name": "Itau Black", "balance": 8666.7}
    result = ingest(conn, transactions=[], accounts=[card], source="fixture")
    assert result.status == "ok"
    assert conn.execute("SELECT sum(balance_cents) FROM accounts").fetchone()[0] == -866670


def test_amount_keeps_the_sign_the_consolidator_already_normalised(conn, accounts):
    payment = {
        "id": "c5120b3b",
        "data": "2025-08-01",
        "conta_id": "acc-fixture-1",
        "descricao": "Pagamento recebido",
        "valor": 3310.23,
        "tipo": "CREDIT",
        "eh_transferencia": True,
        "motivo_transferencia": "pagamento de fatura (sem par encontrado)",
        "eh_saque": False,
        "eh_estorno": False,
        "estornada_por": "",
    }
    ingest(conn, transactions=[payment], accounts=accounts, source="fixture")
    row = conn.execute(
        "SELECT amount_cents, is_transfer, transfer_reason FROM transactions"
    ).fetchone()
    assert row["amount_cents"] == 331023
    assert row["is_transfer"] == 1
    assert row["transfer_reason"] != ""


def test_refund_carries_the_identifier_of_the_debit_it_cancels(conn, accounts):
    refund = {
        "id": "d4714f41",
        "data": "2025-10-09",
        "conta_id": "acc-fixture-1",
        "descricao": "ESTORNO PRESTACAO HAB",
        "valor": 2462.56,
        "tipo": "CREDIT",
        "eh_transferencia": False,
        "motivo_transferencia": "",
        "eh_saque": False,
        "eh_estorno": True,
        "estornada_por": "8b073fe4",
    }
    debit = dict(refund, id="8b073fe4", valor=-2462.56, eh_estorno=False, estornada_por="")
    ingest(conn, transactions=[refund, debit], accounts=accounts, source="fixture")
    rows = {
        row["pluggy_id"]: row
        for row in conn.execute("SELECT pluggy_id, is_refund, refunded_by FROM transactions")
    }
    assert rows["d4714f41"]["is_refund"] == 1
    assert rows["d4714f41"]["refunded_by"] == "8b073fe4"
    assert rows["8b073fe4"]["is_refund"] == 0
    assert rows["8b073fe4"]["refunded_by"] is None
