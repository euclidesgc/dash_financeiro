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


def _descriptions(client: TestClient, query: str) -> list[str]:
    response = client.get(f"/api/transactions/expenses?{query}")
    return [item["description"] for item in response.json()["items"]]


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


def test_the_default_order_is_date_desc_then_id_desc(client):
    _load(
        [
            _transaction("a", "2026-08-01", -10.0),
            _transaction("b", "2026-08-03", -20.0),
            _transaction("c", "2026-08-03", -30.0),
        ]
    )
    _sign_in(client)

    default = client.get("/api/transactions/expenses")
    explicit = client.get("/api/transactions/expenses", params={"sort": "date", "order": "desc"})

    default_dates = [item["date"] for item in default.json()["items"]]
    explicit_dates = [item["date"] for item in explicit.json()["items"]]
    assert default_dates == ["2026-08-03", "2026-08-03", "2026-08-01"]
    assert explicit_dates == default_dates
    assert default.json()["items"] == explicit.json()["items"]


def test_sort_date_asc_puts_the_oldest_first(client):
    _load(
        [
            _transaction("a", "2026-08-01", -10.0),
            _transaction("b", "2026-08-03", -20.0),
            _transaction("c", "2026-08-03", -30.0),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"sort": "date", "order": "asc"})

    items = response.json()["items"]
    assert [item["date"] for item in items] == ["2026-08-01", "2026-08-03", "2026-08-03"]
    assert items[1]["id"] > items[2]["id"]


def test_sort_amount_desc_puts_the_biggest_spending_first(client):
    _load(
        [
            _transaction("small", "2026-09-01", -50.0),
            _transaction("biggest", "2026-09-02", -300.0),
            _transaction("medium", "2026-09-03", -120.0),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"sort": "amount", "order": "desc"})

    amounts = [item["amount_cents"] for item in response.json()["items"]]
    assert amounts == [-30000, -12000, -5000]


def test_sort_amount_asc_puts_the_smallest_spending_first(client):
    _load(
        [
            _transaction("small", "2026-09-01", -50.0),
            _transaction("biggest", "2026-09-02", -300.0),
            _transaction("medium", "2026-09-03", -120.0),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"sort": "amount", "order": "asc"})

    amounts = [item["amount_cents"] for item in response.json()["items"]]
    assert amounts == [-5000, -12000, -30000]


def test_sort_category_asc_follows_the_label_with_uncategorised_last(client):
    _load(
        [
            _transaction("groceries", "2026-09-01", -10.0, categoria="Groceries"),
            _transaction("housing", "2026-09-02", -20.0, categoria="Housing"),
            _transaction("uncategorised", "2026-09-03", -30.0, categoria=""),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"sort": "category", "order": "asc"})

    categories = [item["category"] for item in response.json()["items"]]
    assert categories == ["Casa", "Supermercado", None]


def test_sort_category_desc_reverses_the_labels_and_keeps_uncategorised_last(client):
    _load(
        [
            _transaction("groceries", "2026-09-01", -10.0, categoria="Groceries"),
            _transaction("housing", "2026-09-02", -20.0, categoria="Housing"),
            _transaction("uncategorised", "2026-09-03", -30.0, categoria=""),
        ]
    )
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses", params={"sort": "category", "order": "desc"}
    )

    categories = [item["category"] for item in response.json()["items"]]
    assert categories == ["Supermercado", "Casa", None]


def test_accented_labels_sort_by_their_base_letter(client):
    _load(
        [
            _transaction("water", "2026-09-01", -10.0, categoria="Water"),
            _transaction("housing", "2026-09-02", -20.0, categoria="Housing"),
        ]
    )
    _sign_in(client)

    asc = client.get("/api/transactions/expenses", params={"sort": "category", "order": "asc"})
    desc = client.get("/api/transactions/expenses", params={"sort": "category", "order": "desc"})

    assert [item["category"] for item in asc.json()["items"]] == ["Água", "Casa"]
    assert [item["category"] for item in desc.json()["items"]] == ["Casa", "Água"]


def test_a_category_outside_the_seed_comes_after_the_labelled_ones(client):
    _load(
        [
            _transaction("groceries", "2026-09-01", -10.0, categoria="Groceries"),
            _transaction("unlabelled", "2026-09-02", -20.0, categoria="Zzz-desconhecida"),
            _transaction("uncategorised", "2026-09-03", -30.0, categoria=""),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"sort": "category", "order": "asc"})

    categories = [item["category"] for item in response.json()["items"]]
    assert categories == ["Supermercado", "Zzz-desconhecida", None]


def test_equal_amounts_break_ties_by_id_desc(client):
    _load(
        [
            _transaction("first", "2026-09-01", -50.0),
            _transaction("second", "2026-09-02", -50.0),
        ]
    )
    _sign_in(client)

    asc = client.get("/api/transactions/expenses", params={"sort": "amount", "order": "asc"})
    desc = client.get("/api/transactions/expenses", params={"sort": "amount", "order": "desc"})

    asc_ids = [item["id"] for item in asc.json()["items"]]
    desc_ids = [item["id"] for item in desc.json()["items"]]
    assert asc_ids[0] > asc_ids[1]
    assert desc_ids[0] > desc_ids[1]


def test_sorting_applies_before_pagination(client):
    _load([_transaction(f"e{i}", f"2026-08-{i:02d}", -(i * 10.0)) for i in range(1, 26)])
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses",
        params={"sort": "amount", "order": "desc", "page": 2},
    )

    body = response.json()
    amounts = [item["amount_cents"] for item in body["items"]]
    assert amounts == [-5000, -4000, -3000, -2000, -1000]
    assert body["total"] == 25


def test_unknown_sort_and_order_answer_422(client):
    _sign_in(client)

    assert client.get("/api/transactions/expenses", params={"sort": "payee"}).status_code == 422
    assert client.get("/api/transactions/expenses", params={"order": "up"}).status_code == 422


def test_the_openapi_lists_the_sort_and_order_enums(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    parameters = response.json()["paths"]["/api/transactions/expenses"]["get"]["parameters"]
    by_name = {parameter["name"]: parameter for parameter in parameters}
    assert by_name["sort"]["schema"]["enum"] == ["date", "amount", "category"]
    assert by_name["sort"]["schema"]["default"] == "date"
    assert by_name["order"]["schema"]["enum"] == ["asc", "desc"]
    assert by_name["order"]["schema"]["default"] == "desc"
