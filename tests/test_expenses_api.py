from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.ingest.loader import ingest
from app.ingest.source import load_accounts
from app.main import create_app
from app.taxonomy.classify import _fill_payees
from app.taxonomy.seed import seed_taxonomy

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
DATA = Path(__file__).parent / "data"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TRANSACTIONS_PATH", str(DATA / "sync_transactions.json"))
    monkeypatch.setenv("DASH_ACCOUNTS_GLOB", str(DATA / "sync_accounts.json"))
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    seed_taxonomy(conn)
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        yield opened


def _sign_in(client):
    client.post("/api/auth/login", json={"login": LOGIN, "password": PASSWORD})


def _transaction(id: str, date: str, amount: float, **overrides: Any) -> dict[str, Any]:
    row = {
        "id": id,
        "data": date,
        "conta_id": "sync-acc-1",
        "descricao": f"GASTO {id}",
        "valor": amount,
        "tipo": "DEBIT",
        "categoria_pluggy": "",
        "categoria": "",
        "parcela_atual": None,
        "parcela_total": None,
        "eh_transferencia": False,
        "motivo_transferencia": "",
        "eh_saque": False,
        "eh_estorno": False,
        "estornada_por": "",
        "nome_fantasia": "",
        "razao_social": "",
        "cnpj": "",
        "recebedor": "",
    }
    row.update(overrides)
    return row


def _load(rows: list[dict[str, Any]]) -> None:
    conn = connect()
    ingest(
        conn,
        transactions=rows,
        accounts=load_accounts(str(DATA / "sync_accounts.json")),
        source="teste",
    )
    conn.close()


def test_expenses_without_session_answers_401(client):
    response = client.get("/api/transactions/expenses")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_an_empty_base_answers_an_empty_first_page(client):
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    assert response.status_code == 200
    assert response.json() == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_only_spending_rows_come_back(client):
    _load(
        [
            _transaction("spend-1", "2026-09-01", -50.0),
            _transaction("transfer-1", "2026-09-02", -500.0, eh_transferencia=True),
            _transaction("refund-1", "2026-09-03", 30.0, eh_estorno=True),
            _transaction("refunded-1", "2026-09-03", -30.0, estornada_por="refund-1"),
            _transaction("income-1", "2026-09-04", 6000.0),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["description"] == "GASTO spend-1"


def test_rows_come_newest_first_and_ties_break_by_id_desc(client):
    _load(
        [
            _transaction("a", "2026-08-01", -10.0),
            _transaction("b", "2026-08-03", -20.0),
            _transaction("c", "2026-08-03", -30.0),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    items = response.json()["items"]
    assert [item["date"] for item in items] == ["2026-08-03", "2026-08-03", "2026-08-01"]
    assert items[0]["id"] > items[1]["id"]


def test_pages_hold_twenty_rows_and_the_last_page_the_rest(client):
    _load([_transaction(f"e{i}", f"2026-08-{i + 1:02d}", -10.0) for i in range(25)])
    _sign_in(client)

    first = client.get("/api/transactions/expenses", params={"page": 1})
    second = client.get("/api/transactions/expenses", params={"page": 2})

    assert len(first.json()["items"]) == 20
    assert first.json()["total"] == 25
    assert len(second.json()["items"]) == 5
    assert second.json()["total"] == 25
    assert second.json()["page_size"] == 20


def test_a_page_past_the_end_is_empty_with_the_right_total(client):
    _load([_transaction(f"e{i}", f"2026-08-{i + 1:02d}", -10.0) for i in range(25)])
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"page": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 25
    assert body["page"] == 3


def test_page_size_is_honoured(client):
    _load([_transaction(f"e{i}", f"2026-08-{i + 1:02d}", -10.0) for i in range(25)])
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"page_size": 10})

    body = response.json()
    assert len(body["items"]) == 10
    assert body["page_size"] == 10


def test_page_zero_and_page_size_over_100_answer_422(client):
    _sign_in(client)

    assert client.get("/api/transactions/expenses", params={"page": 0}).status_code == 422
    assert client.get("/api/transactions/expenses", params={"page_size": 101}).status_code == 422
    assert client.get("/api/transactions/expenses", params={"page_size": 0}).status_code == 422


def test_the_merchant_name_becomes_the_payee_name(client):
    _load(
        [
            _transaction("with-merchant", "2026-09-01", -10.0, nome_fantasia="Mercado do Bairro"),
            _transaction("without-merchant", "2026-09-02", -20.0),
        ]
    )
    conn = connect()
    _fill_payees(conn)
    conn.commit()
    conn.close()
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    items = {item["description"]: item for item in response.json()["items"]}
    assert items["GASTO with-merchant"]["payee_name"] == "Mercado do Bairro"
    assert items["GASTO without-merchant"]["payee_name"] is None


def test_the_category_comes_back_as_the_seed_label(client):
    _load(
        [
            _transaction("known", "2026-09-01", -10.0, categoria="Shopping"),
            _transaction("empty", "2026-09-02", -20.0, categoria=""),
            _transaction("unknown", "2026-09-03", -30.0, categoria="Desconhecida"),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    items = {item["description"]: item for item in response.json()["items"]}
    assert items["GASTO known"]["category"] == "Compras"
    assert items["GASTO empty"]["category"] is None
    assert items["GASTO unknown"]["category"] == "Desconhecida"


def test_the_account_name_and_institution_come_from_the_account(client):
    _load([_transaction("spend-1", "2026-09-01", -50.0)])
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    item = response.json()["items"][0]
    assert item["account_name"] == "Conta de sincronização"
    assert item["account_institution"] == "Banco de teste"
    assert item["account_type"] == "BANK"


def test_the_response_has_the_contract_fields(client):
    _load([_transaction("spend-1", "2026-09-01", -50.0)])
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    item = response.json()["items"][0]
    assert set(item.keys()) == {
        "id",
        "date",
        "description",
        "payee_name",
        "account_name",
        "account_institution",
        "account_type",
        "category",
        "amount_cents",
    }
    assert item["amount_cents"] == -5000
