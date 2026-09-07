import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.migrate import run_migrations

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"


@pytest.fixture()
def database(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    run_migrations()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()


# Every client is a fresh app over the same file, which is what a restart of
# the server leaves behind: the database, and nothing else.
def _restarted() -> TestClient:
    return TestClient(create_app(), follow_redirects=False)


def _sign_in(client: TestClient):
    return client.post("/login", data={"login": LOGIN, "senha": PASSWORD})


def test_the_cookie_from_before_the_logout_dies_with_the_process(database):
    with _restarted() as first:
        raw = _sign_in(first).cookies["dash_session"]
        assert first.get("/health").status_code == 200
        assert first.post("/logout").status_code == 302

    with _restarted() as second:
        replayed = second.get("/health", headers={"Cookie": f"dash_session={raw}"})

    assert replayed.status_code == 401
    assert replayed.text == '{"detail":"nao autenticado"}'


def test_the_cookie_issued_after_the_logout_is_accepted(database):
    with _restarted() as first:
        _sign_in(first)
        first.post("/logout")

    with _restarted() as second:
        assert _sign_in(second).status_code == 302

        assert second.get("/health").status_code == 200


def test_seeding_a_new_password_kills_the_open_cookie(database):
    with _restarted() as first:
        raw = _sign_in(first).cookies["dash_session"]
        assert first.get("/health").status_code == 200

    conn = connect()
    seed_user(conn, LOGIN, "senha-nova-7x4")
    conn.close()

    with _restarted() as second:
        replayed = second.get("/health", headers={"Cookie": f"dash_session={raw}"})

    assert replayed.status_code == 401
    assert replayed.text == '{"detail":"nao autenticado"}'


def test_seeding_the_same_password_keeps_the_open_cookie(database):
    with _restarted() as first:
        raw = _sign_in(first).cookies["dash_session"]

        conn = connect()
        seed_user(conn, LOGIN, PASSWORD)
        conn.close()

        replayed = first.get("/health", headers={"Cookie": f"dash_session={raw}"})

    assert replayed.status_code == 200
