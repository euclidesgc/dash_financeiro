from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.ingest.loader import ingest
from app.ingest.source import load_accounts
from app.main import create_app
from app.payees.names import name_it
from app.taxonomy.classify import _fill_payees
from app.taxonomy.seed import seed_taxonomy

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
DATA = Path(__file__).parent / "data"

CREDIT_ACCOUNT = {
    "id": "sync-acc-2",
    "type": "CREDIT",
    "subtype": "CREDIT_CARD",
    "name": "Cartão de sincronização",
    "marketingName": "Banco de teste",
    "balance": 0.0,
    "currencyCode": "BRL",
    "updatedAt": "2026-09-05T12:00:00.000Z",
}


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


def _load(rows: list[dict[str, Any]], accounts: list[dict[str, Any]] | None = None) -> None:
    conn = connect()
    ingest(
        conn,
        transactions=rows,
        accounts=[*load_accounts(str(DATA / "sync_accounts.json")), *(accounts or [])],
        source="teste",
    )
    conn.close()


def _descriptions(client: TestClient, query: str) -> list[str]:
    response = client.get(f"/api/transactions/expenses?{query}")
    return [item["description"] for item in response.json()["items"]]


def _payee_of(conn, id: str) -> str:
    row = conn.execute("SELECT payee FROM transactions WHERE pluggy_id = ?", (id,)).fetchone()
    return row["payee"]


def _month_signal(client: TestClient, query: str = "") -> dict[str, Any]:
    return client.get(f"/api/transactions/expenses/month-signal?{query}").json()


def _put_ceiling(client: TestClient, cents: int | None):
    return client.put("/api/plan/ceiling", json={"monthly_ceiling_cents": cents})


MONTH = "from=2026-08-01&to=2026-08-31"


def test_expenses_without_session_answers_401(client):
    response = client.get("/api/transactions/expenses")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_an_empty_base_answers_an_empty_first_page(client):
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "page": 1,
        "page_size": 20,
        "total": 0,
        "total_cents": 0,
    }


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

    body = response.json()
    item = body["items"][0]
    assert set(item.keys()) == {
        "id",
        "date",
        "description",
        "payee_name",
        "account_name",
        "account_institution",
        "account_type",
        "category",
        "category_key",
        "category_source",
        "amount_cents",
        "account_id",
    }
    assert item["amount_cents"] == -5000
    assert item["account_id"] == "sync-acc-1"
    assert "total_cents" in body
    assert isinstance(body["total_cents"], int)


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


def test_total_cents_sums_every_spending_without_a_filter(client):
    _load(
        [
            _transaction("a", "2026-09-01", -50.0),
            _transaction("b", "2026-09-02", -84.9),
            _transaction("c", "2026-09-03", -150.0),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    body = response.json()
    assert body["total"] == 3
    assert body["total_cents"] == -28490


def test_from_and_to_keep_only_the_month(client):
    _load(
        [
            _transaction("before", "2026-08-31", -10.0),
            _transaction("start", "2026-09-01", -10.0),
            _transaction("middle", "2026-09-15", -10.0),
            _transaction("end", "2026-09-30", -10.0),
            _transaction("after", "2026-10-01", -10.0),
        ]
    )
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses", params={"from": "2026-09-01", "to": "2026-09-30"}
    )

    body = response.json()
    assert [item["date"] for item in body["items"]] == ["2026-09-30", "2026-09-15", "2026-09-01"]
    assert body["total"] == 3
    assert body["total_cents"] == -3000


def test_total_and_total_cents_cover_the_whole_filter_not_the_page(client):
    _load(
        [
            _transaction("before", "2026-08-31", -10.0),
            _transaction("start", "2026-09-01", -10.0),
            _transaction("middle", "2026-09-15", -10.0),
            _transaction("end", "2026-09-30", -10.0),
            _transaction("after", "2026-10-01", -10.0),
        ]
    )
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses",
        params={"from": "2026-09-01", "to": "2026-09-30", "page_size": 1},
    )

    body = response.json()
    assert len(body["items"]) == 1
    assert body["total"] == 3
    assert body["total_cents"] == -3000


def test_only_from_is_an_open_ended_interval(client):
    _load(
        [
            _transaction("before", "2026-08-31", -10.0),
            _transaction("start", "2026-09-01", -10.0),
            _transaction("middle", "2026-09-15", -10.0),
            _transaction("end", "2026-09-30", -10.0),
            _transaction("after", "2026-10-01", -10.0),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"from": "2026-09-15"})

    assert [item["date"] for item in response.json()["items"]] == [
        "2026-10-01",
        "2026-09-30",
        "2026-09-15",
    ]


def test_only_to_is_an_open_ended_interval(client):
    _load(
        [
            _transaction("before", "2026-08-31", -10.0),
            _transaction("start", "2026-09-01", -10.0),
            _transaction("middle", "2026-09-15", -10.0),
            _transaction("end", "2026-09-30", -10.0),
            _transaction("after", "2026-10-01", -10.0),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"to": "2026-09-01"})

    assert [item["date"] for item in response.json()["items"]] == ["2026-09-01", "2026-08-31"]


def test_a_transfer_inside_the_period_stays_out_of_total_cents(client):
    _load(
        [
            _transaction("spend-1", "2026-09-02", -50.0),
            _transaction("transfer-1", "2026-09-02", -500.0, eh_transferencia=True),
        ]
    )
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses", params={"from": "2026-09-01", "to": "2026-09-30"}
    )

    body = response.json()
    assert body["total"] == 1
    assert body["total_cents"] == -5000


def test_sorting_respects_the_period(client):
    _load(
        [
            _transaction("outside", "2026-08-01", -300.0),
            _transaction("small", "2026-09-01", -50.0),
            _transaction("medium", "2026-09-02", -120.0),
        ]
    )
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses",
        params={"from": "2026-09-01", "to": "2026-09-30", "sort": "amount", "order": "desc"},
    )

    amounts = [item["amount_cents"] for item in response.json()["items"]]
    assert amounts == [-12000, -5000]


def test_invalid_dates_answer_422(client):
    _sign_in(client)

    assert (
        client.get("/api/transactions/expenses", params={"from": "2026-13-01"}).status_code == 422
    )
    assert (
        client.get("/api/transactions/expenses", params={"from": "01/09/2026"}).status_code == 422
    )
    assert (
        client.get("/api/transactions/expenses", params={"from": "2026-02-31"}).status_code == 422
    )
    assert client.get("/api/transactions/expenses", params={"to": "hoje"}).status_code == 422


def test_an_inverted_interval_answers_422(client):
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses", params={"from": "2026-09-10", "to": "2026-09-01"}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "A data final precisa ser igual ou posterior à inicial."


def test_the_openapi_lists_from_and_to_as_dates(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    parameters = response.json()["paths"]["/api/transactions/expenses"]["get"]["parameters"]
    by_name = {parameter["name"]: parameter for parameter in parameters}
    for name in ("from", "to"):
        schema = by_name[name]["schema"]
        date_options = [
            option
            for option in schema["anyOf"]
            if option.get("type") == "string" and option.get("format") == "date"
        ]
        assert date_options, f"{name} deveria aceitar uma data ISO"


def _load_account_filter_fixture(extra: list[dict[str, Any]] | None = None) -> None:
    _load(
        [
            _transaction("bank-1", "2026-09-01", -50.0),
            _transaction("bank-2", "2026-09-10", -120.0),
            _transaction("card-1", "2026-09-02", -30.0, conta_id="sync-acc-2"),
            _transaction("card-2", "2026-08-20", -80.0, conta_id="sync-acc-2"),
            *(extra or []),
        ],
        accounts=[CREDIT_ACCOUNT],
    )


def test_without_account_id_the_spending_of_every_account_comes_back(client):
    _load_account_filter_fixture()
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    body = response.json()
    assert body["total"] == 4
    assert [item["description"] for item in body["items"]] == [
        "GASTO bank-2",
        "GASTO card-1",
        "GASTO bank-1",
        "GASTO card-2",
    ]


def test_account_id_keeps_only_that_account(client):
    _load_account_filter_fixture()
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"account_id": "sync-acc-2"})

    body = response.json()
    assert [item["description"] for item in body["items"]] == ["GASTO card-1", "GASTO card-2"]
    assert body["total"] == 2
    assert body["total_cents"] == -11000
    assert all(item["account_id"] == "sync-acc-2" for item in body["items"])


def test_total_and_total_cents_cover_the_whole_account_filter_not_the_page(client):
    _load_account_filter_fixture()
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses", params={"account_id": "sync-acc-2", "page_size": 1}
    )

    body = response.json()
    assert len(body["items"]) == 1
    assert body["total"] == 2
    assert body["total_cents"] == -11000


def test_account_id_and_period_combine_with_and(client):
    _load_account_filter_fixture()
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses",
        params={"account_id": "sync-acc-2", "from": "2026-09-01", "to": "2026-09-30"},
    )

    body = response.json()
    assert [item["description"] for item in body["items"]] == ["GASTO card-1"]
    assert body["total"] == 1
    assert body["total_cents"] == -3000


def test_sorting_respects_the_account(client):
    _load_account_filter_fixture()
    _sign_in(client)

    response = client.get(
        "/api/transactions/expenses",
        params={"account_id": "sync-acc-1", "sort": "amount", "order": "asc"},
    )

    amounts = [item["amount_cents"] for item in response.json()["items"]]
    assert amounts == [-5000, -12000]


def test_a_transfer_of_the_filtered_account_stays_out_of_total_cents(client):
    _load_account_filter_fixture(
        extra=[
            _transaction(
                "transfer-1",
                "2026-09-05",
                -500.0,
                conta_id="sync-acc-2",
                eh_transferencia=True,
            )
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"account_id": "sync-acc-2"})

    body = response.json()
    assert body["total"] == 2
    assert body["total_cents"] == -11000


def test_an_unknown_account_id_answers_an_empty_page(client):
    _load_account_filter_fixture()
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"account_id": "nao-existe"})

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["total_cents"] == 0


def test_an_empty_account_id_answers_422(client):
    _load_account_filter_fixture()
    _sign_in(client)

    response = client.get("/api/transactions/expenses", params={"account_id": ""})

    assert response.status_code == 422


def test_each_item_carries_the_ingested_account_id(client):
    _load_account_filter_fixture()
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    items = {item["description"]: item for item in response.json()["items"]}
    assert items["GASTO bank-1"]["account_id"] == "sync-acc-1"
    assert items["GASTO card-1"]["account_id"] == "sync-acc-2"


def test_the_openapi_lists_account_id_as_an_optional_string(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    parameters = response.json()["paths"]["/api/transactions/expenses"]["get"]["parameters"]
    by_name = {parameter["name"]: parameter for parameter in parameters}
    parameter = by_name["account_id"]
    assert parameter["in"] == "query"
    assert not parameter.get("required", False)
    string_options = [
        option
        for option in parameter["schema"]["anyOf"]
        if option.get("type") == "string" and option.get("minLength") == 1
    ]
    assert string_options


def _load_search_fixture(extra: list[dict[str, Any]] | None = None) -> None:
    _load(
        [
            _transaction("acougue", "2026-09-01", -60.0, descricao="AÇOUGUE SÃO JORGE"),
            _transaction("mercado", "2026-09-02", -84.9, descricao="Pagamento mercado"),
            _transaction(
                "bairro",
                "2026-09-03",
                -30.0,
                descricao="COMPRA 123",
                nome_fantasia="Mercado do Bairro",
            ),
            _transaction("x1", "2026-09-04", -10.0),
            _transaction("x2", "2026-08-20", -20.0, conta_id="sync-acc-2"),
            *(extra or []),
        ],
        accounts=[CREDIT_ACCOUNT],
    )


def test_q_matches_the_description_ignoring_accents(client):
    _load_search_fixture()
    _sign_in(client)

    response = client.get("/api/transactions/expenses?q=acougue")

    body = response.json()
    assert [item["description"] for item in body["items"]] == ["AÇOUGUE SÃO JORGE"]
    assert body["total"] == 1
    assert body["total_cents"] == -6000


def test_q_matches_the_description_ignoring_case(client):
    _load_search_fixture()
    _sign_in(client)

    assert _descriptions(client, "q=MERCADO") == ["Pagamento mercado"]


def test_q_matches_the_payee_name_from_the_merchant_name(client):
    _load_search_fixture()
    conn = connect()
    _fill_payees(conn)
    conn.commit()
    conn.close()
    _sign_in(client)

    assert _descriptions(client, "q=bairro") == ["COMPRA 123"]


def test_the_owner_nickname_wins_over_the_merchant_name_in_the_search(client):
    _load_search_fixture()
    conn = connect()
    _fill_payees(conn)
    conn.commit()
    name_it(conn, _payee_of(conn, "bairro"), "Padaria da Esquina", "dono")
    conn.close()
    _sign_in(client)

    assert _descriptions(client, "q=padaria") == ["COMPRA 123"]
    response = client.get("/api/transactions/expenses?q=bairro")
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_without_a_payee_key_the_merchant_name_is_not_searched(client):
    _load_search_fixture()
    _sign_in(client)

    response = client.get("/api/transactions/expenses?q=bairro")

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_a_percent_sign_in_q_is_literal(client):
    _load(
        [
            _transaction("p1", "2026-09-01", -10.0, descricao="GASTO 100%"),
            _transaction("p2", "2026-09-02", -10.0, descricao="GASTO 1000"),
        ]
    )
    _sign_in(client)

    assert _descriptions(client, "q=100%25") == ["GASTO 100%"]


def test_an_underscore_in_q_is_literal(client):
    _load(
        [
            _transaction("u1", "2026-09-01", -10.0, descricao="GASTO_1"),
            _transaction("u2", "2026-09-02", -10.0, descricao="GASTOX1"),
        ]
    )
    _sign_in(client)

    assert _descriptions(client, "q=to_1") == ["GASTO_1"]


def test_a_backslash_in_q_is_literal(client):
    _load(
        [
            _transaction("b1", "2026-09-01", -10.0, descricao="A\\B"),
            _transaction("b2", "2026-09-02", -10.0, descricao="AB"),
        ]
    )
    _sign_in(client)

    assert _descriptions(client, "q=a%5Cb") == ["A\\B"]


def test_q_shorter_than_two_characters_is_ignored(client):
    _load_search_fixture()
    _sign_in(client)

    baseline = client.get("/api/transactions/expenses").json()

    for query in ("q=a", "q=%20a%20", "q=%20%20"):
        response = client.get(f"/api/transactions/expenses?{query}")
        assert response.json()["total"] == baseline["total"]
        assert [item["description"] for item in response.json()["items"]] == [
            item["description"] for item in baseline["items"]
        ]


def test_q_is_stripped_before_matching(client):
    _load_search_fixture()
    _sign_in(client)

    assert _descriptions(client, "q=%20acougue%20") == ["AÇOUGUE SÃO JORGE"]


def test_q_combines_with_account_and_period_by_and(client):
    _load_search_fixture(
        extra=[
            _transaction(
                "x3", "2026-08-25", -15.0, descricao="AÇOUGUE DO CARTÃO", conta_id="sync-acc-2"
            )
        ]
    )
    _sign_in(client)

    assert _descriptions(client, "q=acougue&account_id=sync-acc-2") == ["AÇOUGUE DO CARTÃO"]
    assert _descriptions(client, "q=acougue&from=2026-09-01&to=2026-09-30") == ["AÇOUGUE SÃO JORGE"]
    assert _descriptions(client, "q=acougue&account_id=sync-acc-2&from=2026-09-01") == []


def test_total_and_total_cents_cover_the_whole_search_not_the_page(client):
    _load(
        [
            _transaction("m1", "2026-09-01", -10.0, descricao="MERCADO 1"),
            _transaction("m2", "2026-09-02", -20.0, descricao="MERCADO 2"),
            _transaction("m3", "2026-09-03", -30.0, descricao="MERCADO 3"),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses?q=mercado&page_size=1")

    body = response.json()
    assert len(body["items"]) == 1
    assert body["total"] == 3
    assert body["total_cents"] == -6000


def test_a_transfer_whose_description_matches_stays_out(client):
    _load_search_fixture(
        extra=[
            _transaction("t1", "2026-09-05", -500.0, descricao="TED ACOUGUE", eh_transferencia=True)
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses?q=acougue")

    body = response.json()
    assert body["total"] == 1
    assert body["total_cents"] == -6000


def test_a_null_description_does_not_break_the_search(client):
    _load(
        [
            _transaction("n1", "2026-09-01", -10.0, descricao=None),
            _transaction("n2", "2026-09-02", -10.0, descricao="GASTO n2"),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses?q=gasto")

    assert response.status_code == 200
    assert _descriptions(client, "q=gasto") == ["GASTO n2"]


def test_sorting_respects_the_search(client):
    _load_search_fixture()
    conn = connect()
    _fill_payees(conn)
    conn.commit()
    conn.close()
    _sign_in(client)

    without_q = client.get("/api/transactions/expenses?sort=amount&order=asc").json()
    with_short_q = client.get("/api/transactions/expenses?q=a&sort=amount&order=asc").json()
    assert with_short_q["items"] == without_q["items"]

    response = client.get("/api/transactions/expenses?q=mercado&sort=amount&order=asc")
    amounts = [item["amount_cents"] for item in response.json()["items"]]
    assert amounts == [-3000, -8490]


def test_the_openapi_lists_q_as_an_optional_string(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    parameters = response.json()["paths"]["/api/transactions/expenses"]["get"]["parameters"]
    by_name = {parameter["name"]: parameter for parameter in parameters}
    parameter = by_name["q"]
    assert parameter["in"] == "query"
    assert not parameter.get("required", False)
    string_options = [
        option
        for option in parameter["schema"]["anyOf"]
        if option.get("type") == "string" and "minLength" not in option
    ]
    assert string_options


_BY_CATEGORY_ROWS = [
    _transaction("hou", "2026-09-01", -150.0, categoria="Housing"),
    _transaction("gro1", "2026-09-02", -60.0, categoria="Groceries"),
    _transaction("gro2", "2026-09-15", -84.9, categoria="Groceries"),
    _transaction("card", "2026-08-20", -45.0, categoria="Shopping", conta_id="sync-acc-2"),
    _transaction("unc", "2026-09-05", -50.0, categoria=""),
]


def _by_category(client: TestClient, query: str = "") -> dict[str, Any]:
    response = client.get(f"/api/transactions/expenses/by-category?{query}")
    return response.json()


def _group_tuples(body: dict[str, Any]) -> list[tuple[str | None, str, int, int]]:
    return [
        (group["category"], group["label"], group["count"], group["total_cents"])
        for group in body["groups"]
    ]


def _put_limit(client: TestClient, key: str, cents: int | None) -> Any:
    return client.put(f"/api/categories/{key}/limit", json={"monthly_limit_cents": cents})


def _group_of(body: dict[str, Any], category: str | None) -> dict[str, Any]:
    return next(group for group in body["groups"] if group["category"] == category)


_SIGNAL_ROWS = [
    _transaction("s-over", "2026-08-10", -60.0, categoria="Groceries"),
    _transaction("s-warn", "2026-08-11", -40.0, categoria="Shopping"),
    _transaction("s-in", "2026-08-12", -30.0, categoria="Housing"),
    _transaction("s-none", "2026-08-13", -20.0, categoria="Healthcare"),
    _transaction("s-unc", "2026-08-14", -10.0, categoria=""),
]


def _load_signal_fixture(client: TestClient) -> None:
    _sign_in(client)
    _load(_SIGNAL_ROWS)
    _put_limit(client, "Groceries", 5000)
    _put_limit(client, "Shopping", 5000)
    _put_limit(client, "Housing", 5000)


def test_by_category_without_session_answers_401(client):
    response = client.get("/api/transactions/expenses/by-category")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_an_empty_base_answers_no_groups(client):
    _sign_in(client)

    response = client.get("/api/transactions/expenses/by-category")

    assert response.status_code == 200
    assert response.json() == {
        "groups": [],
        "total_cents": 0,
        "over_limit_count": 0,
        "signal_scope": "none",
    }


def test_the_by_category_response_has_the_contract_fields(client):
    _load(_BY_CATEGORY_ROWS, accounts=[CREDIT_ACCOUNT])
    _sign_in(client)

    body = _by_category(client)

    assert set(body) == {"groups", "total_cents", "over_limit_count", "signal_scope"}
    for group in body["groups"]:
        assert set(group) == {
            "category",
            "label",
            "count",
            "total_cents",
            "limit_cents",
            "signal",
        }


def test_groups_come_biggest_first_with_the_seed_label_and_the_count(client):
    _load(_BY_CATEGORY_ROWS, accounts=[CREDIT_ACCOUNT])
    _sign_in(client)

    body = _by_category(client)

    assert _group_tuples(body) == [
        ("Housing", "Casa", 1, -15000),
        ("Groceries", "Supermercado", 2, -14490),
        (None, "Sem categoria", 1, -5000),
        ("Shopping", "Compras", 1, -4500),
    ]
    assert body["total_cents"] == -38990


def test_empty_and_missing_categories_fall_into_a_single_uncategorised_group_ordered_by_total(
    client,
):
    _load(
        [
            _transaction("e1", "2026-09-01", -10.0, categoria=""),
            _transaction("e2", "2026-09-02", -20.0, categoria=None),
            _transaction("s1", "2026-09-03", -40.0, categoria="Shopping"),
            _transaction("h1", "2026-09-04", -25.0, categoria="Housing"),
        ]
    )
    _sign_in(client)

    body = _by_category(client)

    assert _group_tuples(body) == [
        ("Shopping", "Compras", 1, -4000),
        (None, "Sem categoria", 2, -3000),
        ("Housing", "Casa", 1, -2500),
    ]


def test_a_category_outside_the_seed_uses_its_own_key_as_label(client):
    _load([_transaction("d1", "2026-09-01", -10.0, categoria="Desconhecida")])
    _sign_in(client)

    body = _by_category(client)

    assert _group_tuples(body) == [("Desconhecida", "Desconhecida", 1, -1000)]


def test_equal_totals_put_the_uncategorised_group_last_and_then_sort_by_key(client):
    _load(
        [
            _transaction("h1", "2026-09-01", -10.0, categoria="Housing"),
            _transaction("e1", "2026-09-02", -10.0, categoria=""),
            _transaction("g1", "2026-09-03", -10.0, categoria="Groceries"),
        ]
    )
    _sign_in(client)

    body = _by_category(client)

    assert [group["category"] for group in body["groups"]] == ["Groceries", "Housing", None]


def test_transfers_and_refunds_stay_out_of_the_groups(client):
    _load(
        [
            *_BY_CATEGORY_ROWS,
            _transaction("t1", "2026-09-05", -500.0, categoria="Housing", eh_transferencia=True),
            _transaction("r1", "2026-09-06", -70.0, categoria="Housing", eh_estorno=True),
        ],
        accounts=[CREDIT_ACCOUNT],
    )
    _sign_in(client)

    body = _by_category(client)

    housing = next(group for group in body["groups"] if group["category"] == "Housing")
    assert housing["count"] == 1
    assert housing["total_cents"] == -15000
    assert body["total_cents"] == -38990


def test_from_and_to_limit_the_groups(client):
    _load(_BY_CATEGORY_ROWS, accounts=[CREDIT_ACCOUNT])
    _sign_in(client)

    within_month = _by_category(client, "from=2026-09-01&to=2026-09-30")
    assert [group["category"] for group in within_month["groups"]] == [
        "Housing",
        "Groceries",
        None,
    ]
    assert within_month["total_cents"] == -34490

    before_month = _by_category(client, "to=2026-08-31")
    assert _group_tuples(before_month) == [("Shopping", "Compras", 1, -4500)]


def test_account_id_limits_the_groups(client):
    _load(_BY_CATEGORY_ROWS, accounts=[CREDIT_ACCOUNT])
    _sign_in(client)

    by_account = _by_category(client, "account_id=sync-acc-2")
    assert [group["category"] for group in by_account["groups"]] == ["Shopping"]

    unknown_account = _by_category(client, "account_id=desconhecida")
    assert unknown_account["groups"] == []
    assert unknown_account["total_cents"] == 0


def test_q_limits_the_groups_and_a_short_q_is_ignored(client):
    _load(
        [
            *_BY_CATEGORY_ROWS,
        ],
        accounts=[CREDIT_ACCOUNT],
    )
    conn = connect()
    conn.execute(
        "UPDATE transactions SET description = ? WHERE pluggy_id = ?",
        ("Aluguel central", "hou"),
    )
    conn.execute(
        "UPDATE transactions SET description = ? WHERE pluggy_id = ?",
        ("Acougue do bairro", "gro1"),
    )
    conn.commit()
    conn.close()
    _sign_in(client)

    central = _by_category(client, "q=central")
    assert _group_tuples(central) == [("Housing", "Casa", 1, -15000)]

    acougue = _by_category(client, "q=acougue")
    assert _group_tuples(acougue) == [("Groceries", "Supermercado", 1, -6000)]

    baseline = _by_category(client)
    short_q = _by_category(client, "q=a")
    assert _group_tuples(short_q) == _group_tuples(baseline)


def test_an_inverted_interval_answers_422_on_by_category(client):
    _sign_in(client)

    response = client.get("/api/transactions/expenses/by-category?from=2026-09-30&to=2026-09-01")

    assert response.status_code == 422
    assert response.json()["detail"] == "A data final precisa ser igual ou posterior à inicial."


def test_an_empty_account_id_answers_422_on_by_category(client):
    _sign_in(client)

    response = client.get("/api/transactions/expenses/by-category?account_id=")

    assert response.status_code == 422


def test_the_group_totals_add_up_to_the_list_total_for_the_same_filter(client):
    _load(_BY_CATEGORY_ROWS, accounts=[CREDIT_ACCOUNT])
    _sign_in(client)

    for query in (
        "",
        "from=2026-09-01&to=2026-09-30",
        "account_id=sync-acc-2",
        "q=mercado",
        "from=2026-09-02&account_id=sync-acc-1&q=ma",
    ):
        body = _by_category(client, query)
        list_body = client.get(f"/api/transactions/expenses?{query}").json()

        assert sum(group["total_cents"] for group in body["groups"]) == body["total_cents"]
        assert body["total_cents"] == list_body["total_cents"]
        assert sum(group["count"] for group in body["groups"]) == list_body["total"]


def test_the_openapi_lists_by_category_with_four_optional_parameters(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    parameters = response.json()["paths"]["/api/transactions/expenses/by-category"]["get"][
        "parameters"
    ]
    assert {parameter["name"] for parameter in parameters} == {"from", "to", "account_id", "q"}
    for parameter in parameters:
        assert parameter["in"] == "query"
        assert not parameter.get("required", False)


def _patch(client: TestClient, id: int, body: dict[str, Any]) -> Any:
    return client.patch(f"/api/transactions/{id}/category", json=body)


def _first_id(client: TestClient) -> int:
    return client.get("/api/transactions/expenses").json()["items"][0]["id"]


def test_each_expense_carries_category_key_and_category_source(client):
    _load(
        [
            _transaction("known", "2026-09-01", -10.0, categoria="Groceries"),
            _transaction("unset", "2026-09-02", -20.0, categoria=""),
        ]
    )
    _sign_in(client)

    response = client.get("/api/transactions/expenses")

    items = {item["description"]: item for item in response.json()["items"]}
    known = items["GASTO known"]
    unset = items["GASTO unset"]
    assert known["category_key"] == "Groceries"
    assert known["category_source"] == "auto"
    assert unset["category_key"] is None
    assert unset["category_source"] == "auto"
    assert "category_key" in set(known)
    assert "category_source" in set(known)


def test_patch_category_without_session_answers_401(client):
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")])

    response = _patch(client, 1, {"mode": "manual", "category": "Healthcare"})

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_patch_manual_category_answers_the_updated_expense_and_the_list_and_the_groups_follow(
    client,
):
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")])
    _sign_in(client)
    id = _first_id(client)

    response = _patch(client, id, {"mode": "manual", "category": "Healthcare"})

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "Plano de saúde"
    assert body["category_key"] == "Healthcare"
    assert body["category_source"] == "manual"

    item = client.get("/api/transactions/expenses").json()["items"][0]
    assert item["category"] == "Plano de saúde"
    assert item["category_key"] == "Healthcare"
    assert item["category_source"] == "manual"

    groups = client.get("/api/transactions/expenses/by-category").json()["groups"]
    assert [(g["category"], g["label"], g["count"], g["total_cents"]) for g in groups] == [
        ("Healthcare", "Plano de saúde", 1, -6000)
    ]


def test_patch_manual_null_clears_the_category(client):
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")])
    _sign_in(client)
    id = _first_id(client)

    response = _patch(client, id, {"mode": "manual", "category": None})

    assert response.status_code == 200
    body = response.json()
    assert body["category"] is None
    assert body["category_key"] is None
    assert body["category_source"] == "manual"

    groups = client.get("/api/transactions/expenses/by-category").json()["groups"]
    assert [(g["category"], g["label"], g["count"], g["total_cents"]) for g in groups] == [
        (None, "Sem categoria", 1, -6000)
    ]


def test_patch_auto_returns_to_the_source_category(client):
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")])
    _sign_in(client)
    id = _first_id(client)
    _patch(client, id, {"mode": "manual", "category": "Healthcare"})

    response = _patch(client, id, {"mode": "auto"})

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "Supermercado"
    assert body["category_key"] == "Groceries"
    assert body["category_source"] == "auto"


def test_patch_refuses_an_unknown_category_with_422(client):
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")])
    _sign_in(client)
    id = _first_id(client)

    response = _patch(client, id, {"mode": "manual", "category": "Inexistente"})

    assert response.status_code == 422
    assert response.json() == {"detail": "Categoria desconhecida."}
    item = client.get("/api/transactions/expenses").json()["items"][0]
    assert item["category"] == "Supermercado"
    assert item["category_source"] == "auto"


def test_patch_refuses_the_uncategorised_key_with_422(client):
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")])
    _sign_in(client)
    id = _first_id(client)

    response = _patch(client, id, {"mode": "manual", "category": "Não classificado"})

    assert response.status_code == 422
    assert response.json() == {"detail": "Categoria desconhecida."}


def test_patch_an_unknown_expense_answers_404(client):
    _sign_in(client)

    response = _patch(client, 999999, {"mode": "manual", "category": "Healthcare"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Gasto não encontrado."}


def test_patch_with_an_invalid_mode_answers_422(client):
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")])
    _sign_in(client)
    id = _first_id(client)

    response = _patch(client, id, {"mode": "outro"})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_a_manual_category_survives_reingesting_the_same_source(client):
    base = [_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")]
    _load(base)
    _sign_in(client)
    id = _first_id(client)
    _patch(client, id, {"mode": "manual", "category": "Healthcare"})

    _load(base)

    item = client.get("/api/transactions/expenses").json()["items"][0]
    assert item["category"] == "Plano de saúde"
    assert item["category_source"] == "manual"

    _patch(client, id, {"mode": "auto"})
    _load(base)

    item = client.get("/api/transactions/expenses").json()["items"][0]
    assert item["category"] == "Supermercado"
    assert item["category_source"] == "auto"


def test_a_manual_category_still_follows_the_source_after_going_back_to_auto(client):
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries", descricao="ACOUGUE")])
    _sign_in(client)
    id = _first_id(client)
    _patch(client, id, {"mode": "manual", "category": "Healthcare"})
    _patch(client, id, {"mode": "auto"})

    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Housing", descricao="ACOUGUE")])

    item = client.get("/api/transactions/expenses").json()["items"][0]
    assert item["category"] == "Casa"
    assert item["category_source"] == "auto"


def test_the_openapi_lists_patch_category(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    assert "patch" in response.json()["paths"]["/api/transactions/{transaction_id}/category"]


def test_renaming_a_category_reflects_in_the_list_and_in_by_category(client):
    _sign_in(client)
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries")])

    response = client.patch("/api/categories/Groceries", json={"label": "Mercado"})

    assert response.status_code == 200
    expenses = client.get("/api/transactions/expenses").json()["items"]
    assert expenses[0]["category"] == "Mercado"
    assert expenses[0]["category_key"] == "Groceries"
    assert _group_tuples(_by_category(client)) == [("Groceries", "Mercado", 1, -6000)]


SIMILAR_ROWS = [
    _transaction("o", "2026-09-01", -45.0, descricao="FARMACIA CENTRAL", categoria="Healthcare"),
    _transaction("s1", "2026-08-15", -30.0, descricao="FARMACIA CENTRAL"),
    _transaction("s2", "2026-07-08", -20.0, descricao="Farmácia Central"),
    _transaction("x", "2026-09-02", -10.0, descricao="MERCADO"),
]


def _ids(client: TestClient) -> dict[str, int]:
    items = client.get("/api/transactions/expenses").json()["items"]
    return {item["description"]: item["id"] for item in items}


def _items(client: TestClient) -> list[dict[str, Any]]:
    return client.get("/api/transactions/expenses").json()["items"]


def _id_of(pluggy_id: str) -> int:
    conn = connect()
    row = conn.execute("SELECT id FROM transactions WHERE pluggy_id = ?", (pluggy_id,)).fetchone()
    conn.close()
    return int(row["id"])


def test_similar_without_session_answers_401(client):
    response = client.get("/api/transactions/1/similar")

    assert response.status_code == 401


def test_similar_of_an_unknown_expense_answers_404(client):
    _sign_in(client)

    response = client.get("/api/transactions/999999/similar")

    assert response.status_code == 404
    assert response.json() == {"detail": "Gasto não encontrado."}


def test_similar_counts_by_description_on_an_unclassified_base(client):
    _load(SIMILAR_ROWS)
    _sign_in(client)
    o_id = _id_of("o")
    conn = connect()
    payee = _payee_of(conn, "o")
    conn.close()

    response = client.get(f"/api/transactions/{o_id}/similar")

    assert not payee
    assert response.json() == {"count": 2}


def test_similar_counts_by_payee_after_a_patch(client):
    _load(SIMILAR_ROWS)
    _sign_in(client)
    o_id = _id_of("o")
    _patch(client, o_id, {"mode": "manual", "category": "Groceries"})
    conn = connect()
    payee = _payee_of(conn, "o")
    conn.close()

    response = client.get(f"/api/transactions/{o_id}/similar")

    assert payee
    assert response.json() == {"count": 2}


def test_apply_to_similar_without_session_answers_401(client):
    response = client.post(
        "/api/transactions/1/category/apply-to-similar", json={"category": "Groceries"}
    )

    assert response.status_code == 401


def test_apply_to_similar_of_an_unknown_expense_answers_404(client):
    _sign_in(client)

    response = client.post(
        "/api/transactions/999999/category/apply-to-similar", json={"category": "Groceries"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Gasto não encontrado."}


def test_apply_to_similar_refuses_an_unknown_category_with_422(client):
    _load(SIMILAR_ROWS)
    _sign_in(client)
    o_id = _id_of("o")

    for category in ("Inexistente", "Não classificado"):
        response = client.post(
            f"/api/transactions/{o_id}/category/apply-to-similar", json={"category": category}
        )
        assert response.status_code == 422
        assert response.json() == {"detail": "Categoria desconhecida."}

    assert all(item["category_source"] != "manual" for item in _items(client))


def test_apply_to_similar_without_category_answers_422_from_pydantic(client):
    _load(SIMILAR_ROWS)
    _sign_in(client)
    o_id = _id_of("o")

    response = client.post(f"/api/transactions/{o_id}/category/apply-to-similar", json={})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_apply_to_similar_marks_the_similar_rows_manual_and_leaves_the_origin(client):
    _load(SIMILAR_ROWS)
    _sign_in(client)
    o_id = _id_of("o")
    _patch(client, o_id, {"mode": "manual", "category": "Groceries"})

    response = client.post(
        f"/api/transactions/{o_id}/category/apply-to-similar", json={"category": "Groceries"}
    )

    assert response.status_code == 200
    assert response.json() == {"updated": 2}
    items = {item["description"]: item for item in _items(client)}
    for key in ("FARMACIA CENTRAL", "Farmácia Central"):
        if items[key]["id"] == o_id:
            continue
        assert items[key]["category_key"] == "Groceries"
        assert items[key]["category"] == "Supermercado" or items[key]["category"] is not None
        assert items[key]["category_source"] == "manual"
    assert items["MERCADO"]["category_source"] == "auto"
    origin = (
        items["FARMACIA CENTRAL"]
        if items["FARMACIA CENTRAL"]["id"] == o_id
        else items["Farmácia Central"]
    )
    assert origin["category_key"] == "Groceries"
    assert origin["category_source"] == "manual"


def test_apply_to_similar_with_null_clears_the_category_of_the_similar_rows(client):
    _load(SIMILAR_ROWS)
    _sign_in(client)
    o_id = _id_of("o")

    response = client.post(
        f"/api/transactions/{o_id}/category/apply-to-similar", json={"category": None}
    )

    assert response.status_code == 200
    assert response.json() == {"updated": 2}
    items = {item["id"]: item for item in _items(client)}
    for item in items.values():
        if item["id"] == o_id:
            continue
        if item["description"] in ("FARMACIA CENTRAL", "Farmácia Central"):
            assert item["category"] is None
            assert item["category_key"] is None
            assert item["category_source"] == "manual"


def test_applied_categories_survive_reingesting_the_same_source(client):
    _load(SIMILAR_ROWS)
    _sign_in(client)
    o_id = _id_of("o")
    client.post(
        f"/api/transactions/{o_id}/category/apply-to-similar", json={"category": "Groceries"}
    )

    _load(SIMILAR_ROWS)

    items = {item["description"]: item for item in _items(client)}
    for key in ("FARMACIA CENTRAL", "Farmácia Central"):
        item = items[key]
        if item["id"] == o_id:
            continue
        assert item["category_key"] == "Groceries"
        assert item["category_source"] == "manual"


def test_a_whole_month_carries_limit_signal_count_and_scope(client):
    _load_signal_fixture(client)

    body = _by_category(client, "from=2026-08-01&to=2026-08-31")

    groceries = _group_of(body, "Groceries")
    assert groceries["limit_cents"] == 5000
    assert groceries["signal"] == "over"

    shopping = _group_of(body, "Shopping")
    assert shopping["signal"] == "warning"

    housing = _group_of(body, "Housing")
    assert housing["signal"] == "within"

    healthcare = _group_of(body, "Healthcare")
    assert healthcare["limit_cents"] is None
    assert healthcare["signal"] is None

    uncategorised = _group_of(body, None)
    assert uncategorised["limit_cents"] is None
    assert uncategorised["signal"] is None

    assert body["over_limit_count"] == 1
    assert body["signal_scope"] == "month"


def test_a_partial_interval_keeps_the_limit_but_no_signal(client):
    _load_signal_fixture(client)

    body = _by_category(client, "from=2026-08-01&to=2026-08-30")

    assert all(group["signal"] is None for group in body["groups"])
    assert body["over_limit_count"] == 0
    assert body["signal_scope"] == "none"
    assert _group_of(body, "Groceries")["limit_cents"] == 5000


def test_only_from_and_no_dates_give_no_signal(client):
    _load_signal_fixture(client)

    with_from = _by_category(client, "from=2026-08-01")
    without_dates = _by_category(client, "")

    for body in (with_from, without_dates):
        assert all(group["signal"] is None for group in body["groups"])
        assert body["over_limit_count"] == 0
        assert body["signal_scope"] == "none"
        assert _group_of(body, "Groceries")["limit_cents"] == 5000


def test_setting_a_limit_changes_the_signal_of_the_next_by_category(client):
    _sign_in(client)
    _load(_SIGNAL_ROWS)

    body = _by_category(client, "from=2026-08-01&to=2026-08-31")
    assert _group_of(body, "Groceries")["signal"] is None

    _put_limit(client, "Groceries", 5000)
    body = _by_category(client, "from=2026-08-01&to=2026-08-31")
    assert _group_of(body, "Groceries")["signal"] == "over"

    _put_limit(client, "Groceries", 7500)
    body = _by_category(client, "from=2026-08-01&to=2026-08-31")
    assert _group_of(body, "Groceries")["signal"] == "warning"

    _put_limit(client, "Groceries", None)
    body = _by_category(client, "from=2026-08-01&to=2026-08-31")
    groceries = _group_of(body, "Groceries")
    assert groceries["signal"] is None
    assert groceries["limit_cents"] is None


def test_the_signal_fields_keep_the_order_and_totals_of_the_groups(client):
    _load_signal_fixture(client)

    body = _by_category(client, "from=2026-08-01&to=2026-08-31")

    assert _group_tuples(body) == [
        ("Groceries", "Supermercado", 1, -6000),
        ("Shopping", "Compras", 1, -4000),
        ("Housing", "Casa", 1, -3000),
        ("Healthcare", "Plano de saúde", 1, -2000),
        (None, "Sem categoria", 1, -1000),
    ]
    assert body["total_cents"] == -16000


def test_the_openapi_lists_the_signal_fields_of_by_category(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    schemas = response.json()["components"]["schemas"]
    assert "limit_cents" in schemas["CategoryGroup"]["properties"]
    assert "signal" in schemas["CategoryGroup"]["properties"]
    assert "over_limit_count" in schemas["CategoryTotalsResponse"]["properties"]
    assert "signal_scope" in schemas["CategoryTotalsResponse"]["properties"]


def test_the_openapi_lists_similar_and_apply_to_similar(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    paths = response.json()["paths"]
    assert "get" in paths["/api/transactions/{transaction_id}/similar"]
    assert "post" in paths["/api/transactions/{transaction_id}/category/apply-to-similar"]


def _load_month_signal_fixture(client):
    _load(
        [
            _transaction("m-1", "2026-08-20", -60.0, categoria="Groceries"),
            _transaction("m-2", "2026-08-15", -45.0, categoria="Healthcare"),
        ]
    )
    _sign_in(client)


def test_month_signal_without_session_answers_401(client):
    response = client.get(f"/api/transactions/expenses/month-signal?{MONTH}")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_a_whole_month_over_the_ceiling(client):
    _load_month_signal_fixture(client)
    _put_ceiling(client, 10000)

    body = _month_signal(client, MONTH)

    assert body == {
        "scope": "month",
        "spent_cents": 10500,
        "ceiling_cents": 10000,
        "signal": "over",
        "remaining_cents": -500,
    }


def test_a_whole_month_within_the_ceiling(client):
    _load_month_signal_fixture(client)
    _put_ceiling(client, 20000)

    body = _month_signal(client, MONTH)

    assert body["signal"] == "within"
    assert body["remaining_cents"] == 9500


def test_a_whole_month_near_the_ceiling_is_warning(client):
    _load_month_signal_fixture(client)
    _put_ceiling(client, 12000)

    body = _month_signal(client, MONTH)

    assert body["signal"] == "warning"
    assert body["remaining_cents"] == 1500


def test_a_whole_month_without_a_ceiling_has_no_signal(client):
    _load_month_signal_fixture(client)

    body = _month_signal(client, MONTH)

    assert body["spent_cents"] == 10500
    assert body["ceiling_cents"] is None
    assert body["signal"] is None
    assert body["remaining_cents"] is None
    assert body["scope"] == "month"


def test_a_partial_interval_only_from_and_no_dates_give_scope_none(client):
    _load_month_signal_fixture(client)
    _put_ceiling(client, 10000)

    partial = _month_signal(client, "from=2026-08-01&to=2026-08-30")
    only_from = _month_signal(client, "from=2026-08-01")
    no_dates = _month_signal(client)

    for body in (partial, only_from, no_dates):
        assert body["scope"] == "none"
        assert body["signal"] is None
        assert body["remaining_cents"] is None
        assert body["ceiling_cents"] == 10000


def test_month_signal_refuses_inverted_dates(client):
    _load_month_signal_fixture(client)

    response = client.get("/api/transactions/expenses/month-signal?from=2026-08-31&to=2026-08-01")

    assert response.status_code == 422


def test_transfers_and_refunds_stay_out_of_the_month_signal(client):
    _load(
        [
            _transaction("m-1", "2026-08-20", -60.0, categoria="Groceries"),
            _transaction("m-2", "2026-08-15", -45.0, categoria="Healthcare"),
            _transaction("t-1", "2026-08-05", -500.0, eh_transferencia=True),
            _transaction("r-1", "2026-08-06", 30.0, eh_estorno=True),
        ]
    )
    _sign_in(client)

    body = _month_signal(client, MONTH)

    assert body["spent_cents"] == 10500


def test_spent_cents_equals_the_absolute_total_of_the_expenses_page(client):
    _load_month_signal_fixture(client)

    signal_body = _month_signal(client, MONTH)
    expenses_body = client.get(f"/api/transactions/expenses?{MONTH}").json()

    assert signal_body["spent_cents"] == abs(expenses_body["total_cents"])


def test_the_openapi_lists_month_signal_with_from_and_to_only(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    body = response.json()
    parameters = body["paths"]["/api/transactions/expenses/month-signal"]["get"]["parameters"]
    assert {param["name"] for param in parameters} == {"from", "to"}
    properties = body["components"]["schemas"]["MonthSignalResponse"]["properties"]
    assert set(properties) >= {"scope", "spent_cents", "ceiling_cents", "signal", "remaining_cents"}
