from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.taxonomy.seed import UNCATEGORISED, pickable_categories, seed_taxonomy

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


def test_categories_without_session_answers_401(client):
    response = client.get("/api/categories")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_categories_lists_the_pickable_seed_in_label_order(client):
    _sign_in(client)

    response = client.get("/api/categories")

    assert response.status_code == 200
    expected = [{"key": c.key, "label": c.label} for c in pickable_categories()]
    assert response.json()["categories"] == expected
    assert expected[0]["label"] == pickable_categories()[0].label
    assert {"key": "Groceries", "label": "Supermercado"} in expected


def test_categories_never_contains_the_uncategorised_key(client):
    _sign_in(client)

    response = client.get("/api/categories")

    categories = response.json()["categories"]
    assert all(item["key"] != UNCATEGORISED for item in categories)
    assert all(item["label"] != "Sem categoria" for item in categories)


def test_the_openapi_lists_categories(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    assert "get" in response.json()["paths"]["/api/categories"]
