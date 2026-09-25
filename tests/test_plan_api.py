import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

INVALID_CEILING = "O teto precisa ser maior que zero."


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


def _put(client, cents):
    return client.put("/api/plan/ceiling", json={"monthly_ceiling_cents": cents})


def test_ceiling_without_session_answers_401(client):
    get_response = client.get("/api/plan/ceiling")
    put_response = _put(client, 500000)

    assert get_response.status_code == 401
    assert get_response.json() == {"detail": "nao autenticado"}
    assert put_response.status_code == 401
    assert put_response.json() == {"detail": "nao autenticado"}


def test_a_new_base_has_no_ceiling(client):
    _sign_in(client)

    response = client.get("/api/plan/ceiling")

    assert response.status_code == 200
    assert response.json() == {"monthly_ceiling_cents": None}


def test_put_stores_the_ceiling_and_get_reflects_it(client):
    _sign_in(client)

    written = _put(client, 500000)

    assert written.status_code == 200
    assert written.json() == {"monthly_ceiling_cents": 500000}
    assert client.get("/api/plan/ceiling").json() == {"monthly_ceiling_cents": 500000}


def test_put_null_clears_the_ceiling(client):
    _sign_in(client)
    _put(client, 500000)

    cleared = _put(client, None)

    assert cleared.status_code == 200
    assert cleared.json() == {"monthly_ceiling_cents": None}
    assert client.get("/api/plan/ceiling").json() == {"monthly_ceiling_cents": None}


def test_put_zero_or_negative_answers_422_and_keeps_the_previous_value(client):
    _sign_in(client)
    _put(client, 500000)

    zero = _put(client, 0)
    negative = _put(client, -1)

    assert zero.status_code == 422
    assert zero.json() == {"detail": INVALID_CEILING}
    assert negative.status_code == 422
    assert negative.json() == {"detail": INVALID_CEILING}
    assert client.get("/api/plan/ceiling").json() == {"monthly_ceiling_cents": 500000}


def test_put_without_the_field_or_with_a_fraction_is_refused_by_the_schema(client):
    _sign_in(client)

    missing = client.put("/api/plan/ceiling", json={})
    fraction = client.put("/api/plan/ceiling", json={"monthly_ceiling_cents": 12.5})

    assert missing.status_code == 422
    assert isinstance(missing.json()["detail"], list)
    assert fraction.status_code == 422
    assert isinstance(fraction.json()["detail"], list)


def test_the_openapi_lists_get_and_put_of_the_ceiling(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    ceiling_path = response.json()["paths"]["/api/plan/ceiling"]
    assert "get" in ceiling_path
    assert "put" in ceiling_path


def test_the_settings_screen_shows_the_ceiling_as_a_goal(client):
    _sign_in(client)
    _put(client, 500000)

    screen = client.get("/configuracao").text

    assert "Teto mensal de gasto" in screen
    assert "R$ 5.000,00" in screen
