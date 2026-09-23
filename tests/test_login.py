import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from app.auth import password as password_module
from app.auth.attempt import REJECTED_MESSAGE
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


def _sign_in(client, password=PASSWORD):
    return client.post("/login", data={"login": LOGIN, "senha": password})


def test_the_right_credential_opens_a_session(client):
    response = _sign_in(client)

    assert response.status_code == 302
    assert response.headers["location"] == "/"
    cookie = response.headers["set-cookie"]
    for piece in ("dash_session=", "HttpOnly", "SameSite=Lax", "Path=/", "Max-Age=43200"):
        assert piece in cookie


def test_health_answers_only_with_a_session(client):
    without = client.get("/health")

    assert without.status_code == 401
    assert without.headers["content-type"].startswith("application/json")
    assert without.text == '{"detail":"nao autenticado"}'

    _sign_in(client)
    with_session = client.get("/health")

    assert with_session.status_code == 200
    assert with_session.text == '{"status":"ok"}'


def test_the_wrong_password_never_reaches_the_html(client):
    response = _sign_in(client, password="errada")

    assert response.status_code == 401
    assert response.text.count(REJECTED_MESSAGE) == 1
    assert "errada" not in response.text
    assert "set-cookie" not in response.headers


def test_an_unknown_login_gets_the_same_message(client):
    response = client.post("/login", data={"login": "nao-existe", "senha": "qualquer"})

    assert response.status_code == 401
    assert response.text.count(REJECTED_MESSAGE) == 1
    assert "qualquer" not in response.text


def test_the_sixth_failure_is_throttled(client):
    for _ in range(MAX_FAILURES):
        assert _sign_in(client, password="errada").status_code == 401

    blocked = _sign_in(client, password="errada")

    assert blocked.status_code == 429
    assert 1 <= int(blocked.headers["retry-after"]) <= WINDOW_SECONDS


def test_the_block_holds_against_the_right_password(client):
    for _ in range(MAX_FAILURES):
        _sign_in(client, password="errada")

    blocked = _sign_in(client)

    assert blocked.status_code == 429
    assert "dash_session=" not in blocked.headers.get("set-cookie", "")

    conn = connect()
    stored, origins = conn.execute(
        "SELECT count(*), count(distinct ip) FROM login_attempts WHERE success = 0"
    ).fetchone()
    conn.close()

    assert (stored, origins) == (MAX_FAILURES, 1)


def test_logout_expires_the_cookie_and_the_session(client):
    raw = _sign_in(client).cookies["dash_session"]

    response = client.post("/logout")

    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert "Max-Age=0" in response.headers["set-cookie"]

    client.cookies.clear()
    replayed = client.get("/", headers={"Cookie": f"dash_session={raw}"})

    assert replayed.status_code == 302
    assert replayed.headers["location"] == "/login"


def test_the_unknown_login_pays_for_a_verification_too(client, monkeypatch):
    verified = []
    original = PasswordHasher.verify

    def counted(self, stored, plain):
        verified.append(stored)
        return original(self, stored, plain)

    monkeypatch.setattr(PasswordHasher, "verify", counted)

    client.post("/login", data={"login": "nao-existe", "senha": "qualquer"})
    _sign_in(client, password="errada")

    assert len(verified) == 2
    assert verified[0] == password_module.ABSENT_USER_HASH
    assert verified[1] != password_module.ABSENT_USER_HASH
    assert password_module.ABSENT_USER_HASH.startswith("$argon2id$")


def test_the_session_that_opened_leaves_a_trail(client):
    _sign_in(client, password="errada")
    _sign_in(client)

    conn = connect()
    stored = conn.execute("SELECT ip, success FROM login_attempts ORDER BY id").fetchall()
    conn.close()

    assert [row["success"] for row in stored] == [0, 1]
    assert {row["ip"] for row in stored} == {"testclient"}


def test_a_success_inside_the_window_does_not_soften_the_block(client):
    _sign_in(client)
    for _ in range(MAX_FAILURES):
        assert _sign_in(client, password="errada").status_code == 401

    assert _sign_in(client, password="errada").status_code == 429
