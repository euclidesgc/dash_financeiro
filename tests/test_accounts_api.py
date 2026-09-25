from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.ingest.loader import ingest
from app.ingest.source import load_accounts
from app.ingest.trigger import COMMAND
from app.main import create_app

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        yield opened


def _sign_in(client):
    client.post("/api/auth/login", json={"login": LOGIN, "password": PASSWORD})


def test_balances_without_session_answers_401(client):
    response = client.get("/api/accounts/balances")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_balances_returns_the_fixture_account_with_integer_cents(client):
    accounts = load_accounts(str(FIXTURES / "accounts_fixture.json"))
    conn = connect()
    ingest(conn, transactions=[], accounts=accounts, source="tests", trigger=COMMAND)
    conn.close()
    _sign_in(client)

    response = client.get("/api/accounts/balances")

    assert response.status_code == 200
    assert response.json() == {
        "accounts": [
            {
                "id": "acc-fixture-1",
                "name": "Conta de teste",
                "institution": "Banco de teste",
                "type": "BANK",
                "subtype": "CHECKING_ACCOUNT",
                "balance_cents": 1234,
                "updated_at": "2026-09-05T21:36:27.516Z",
            }
        ]
    }


def test_balances_are_ordered_by_type_then_name(client):
    accounts = [
        {
            "id": "acc-zeta",
            "type": "CREDIT",
            "subtype": "CREDIT_CARD",
            "name": "Zeta",
            "marketingName": "Emissor Zeta",
            "balance": 50.0,
            "currencyCode": "BRL",
            "updatedAt": "2026-09-05T21:36:27.516Z",
        },
        {
            "id": "acc-beta",
            "type": "BANK",
            "subtype": "CHECKING_ACCOUNT",
            "name": "Beta",
            "marketingName": "Banco Beta",
            "balance": 10.0,
            "currencyCode": "BRL",
            "updatedAt": "2026-09-05T21:36:27.516Z",
        },
        {
            "id": "acc-alfa",
            "type": "BANK",
            "subtype": "CHECKING_ACCOUNT",
            "name": "Alfa",
            "marketingName": "Banco Alfa",
            "balance": 5.0,
            "currencyCode": "BRL",
            "updatedAt": "2026-09-05T21:36:27.516Z",
        },
    ]
    conn = connect()
    ingest(conn, transactions=[], accounts=accounts, source="tests", trigger=COMMAND)
    conn.close()
    _sign_in(client)

    response = client.get("/api/accounts/balances")

    body = response.json()
    assert [account["name"] for account in body["accounts"]] == ["Alfa", "Beta", "Zeta"]
    zeta = next(account for account in body["accounts"] if account["name"] == "Zeta")
    assert zeta["balance_cents"] == -5000


def test_balances_on_an_empty_base_returns_an_empty_list(client):
    _sign_in(client)

    response = client.get("/api/accounts/balances")

    assert response.status_code == 200
    assert response.json() == {"accounts": []}


def test_balances_with_null_updated_at_returns_null(client):
    accounts = [
        {
            "id": "acc-no-date",
            "type": "BANK",
            "subtype": "CHECKING_ACCOUNT",
            "name": "Sem data",
            "marketingName": "Banco sem data",
            "balance": 1.0,
            "currencyCode": "BRL",
        },
    ]
    conn = connect()
    ingest(conn, transactions=[], accounts=accounts, source="tests", trigger=COMMAND)
    conn.close()
    _sign_in(client)

    response = client.get("/api/accounts/balances")

    body = response.json()
    assert body["accounts"][0]["updated_at"] is None
