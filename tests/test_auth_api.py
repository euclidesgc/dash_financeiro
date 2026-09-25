import pytest
from fastapi.testclient import TestClient

from app.auth.attempt import REJECTED_MESSAGE, THROTTLED_MESSAGE
from app.auth.rate_limit import MAX_FAILURES, WINDOW_SECONDS
from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"


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


def _sign_in_api(client, password=PASSWORD):
    return client.post("/api/auth/login", json={"login": LOGIN, "password": password})


def test_login_answers_204_and_sets_the_same_cookie_as_the_html_form(client):
    response = _sign_in_api(client)

    assert response.status_code == 204
    assert response.text == ""
    cookie = response.headers["set-cookie"]
    for piece in ("dash_session=", "HttpOnly", "SameSite=Lax", "Path=/", "Max-Age=43200"):
        assert piece in cookie


def test_wrong_password_answers_401_with_the_generic_message(client):
    response = _sign_in_api(client, password="errada")

    assert response.status_code == 401
    assert response.json() == {"detail": REJECTED_MESSAGE}
    assert "set-cookie" not in response.headers


def test_unknown_login_gets_the_same_401_message(client):
    response = client.post("/api/auth/login", json={"login": "nao-existe", "password": "qualquer"})

    assert response.status_code == 401
    assert response.json() == {"detail": REJECTED_MESSAGE}


def test_the_sixth_failure_answers_429_with_retry_after(client):
    for _ in range(MAX_FAILURES):
        assert _sign_in_api(client, password="errada").status_code == 401

    blocked = _sign_in_api(client, password="errada")

    assert blocked.status_code == 429
    assert blocked.json() == {"detail": THROTTLED_MESSAGE}
    assert 1 <= int(blocked.headers["retry-after"]) <= WINDOW_SECONDS


def test_login_without_session_is_public(client):
    response = client.post("/api/auth/login", json={"login": "nao-existe", "password": "qualquer"})

    assert response.status_code == 401
    assert response.json() == {"detail": REJECTED_MESSAGE}


def test_login_with_missing_fields_answers_422(client):
    response = client.post("/api/auth/login", json={})

    assert response.status_code == 422


def test_me_without_session_answers_401(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_me_with_session_returns_the_login(client):
    _sign_in_api(client)

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json() == {"login": LOGIN}


def test_logout_expires_the_cookie_and_invalidates_the_previous_session(client):
    _sign_in_api(client)
    raw = client.cookies.get("dash_session")

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert "Max-Age=0" in response.headers["set-cookie"]

    client.cookies.clear()
    replayed = client.get("/api/auth/me", headers={"Cookie": f"dash_session={raw}"})

    assert replayed.status_code == 401


def test_the_html_login_still_works_with_the_extracted_logic(client):
    response = client.post("/login", data={"login": LOGIN, "senha": PASSWORD})

    assert response.status_code == 302
    assert response.headers["location"] == "/"
