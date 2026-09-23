from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.sync
import app.sync.exclusive
from app.auth.seed import seed_user
from app.config import PLUGGY_CREDENTIALS
from app.db import connect
from app.ingest.loader import ingest
from app.ingest.source import load_accounts, load_transactions
from app.main import create_app
from app.sync.fetch import UNREACHABLE, PluggyFetchError
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


def _runs_count(conn):
    return conn.execute("SELECT COUNT(*) FROM sync_runs").fetchone()[0]


def test_status_without_session_answers_401(client):
    response = client.get("/api/sync/status")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_run_without_session_answers_401(client):
    response = client.post("/api/sync/run")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_status_on_an_empty_base_has_no_last_run(client):
    _sign_in(client)

    response = client.get("/api/sync/status")

    assert response.status_code == 200
    assert response.json() == {"running": False, "last_run": None}


def test_status_after_an_ingest_shows_ok_and_finished_at(client):
    conn = connect()
    ingest(
        conn,
        transactions=load_transactions(str(DATA / "sync_transactions.json")),
        accounts=load_accounts(str(DATA / "sync_accounts.json")),
        source="tests",
    )
    conn.close()
    _sign_in(client)

    response = client.get("/api/sync/status")

    body = response.json()
    assert body["last_run"]["status"] == "ok"
    assert isinstance(body["last_run"]["finished_at"], str)
    assert body["last_run"]["reason"] is None


def test_run_with_the_file_source_answers_200_and_records_a_new_row(client):
    conn = connect()
    before = _runs_count(conn)
    conn.close()
    _sign_in(client)

    response = client.post("/api/sync/run")

    assert response.status_code == 200
    assert response.json()["last_run"]["status"] == "ok"
    conn = connect()
    assert _runs_count(conn) == before + 1
    conn.close()

    balances = client.get("/api/accounts/balances")
    names = [account["name"] for account in balances.json()["accounts"]]
    assert "Conta de sincronização" in names


def test_a_second_run_while_the_lock_is_held_answers_409_without_a_row(client):
    _sign_in(client)
    conn = connect()
    before = _runs_count(conn)
    conn.close()

    with app.sync.exclusive._LOCK:
        response = client.post("/api/sync/run")

    assert response.status_code == 409
    assert response.json() == {"detail": "Já existe uma atualização em andamento."}
    conn = connect()
    assert _runs_count(conn) == before
    conn.close()


def test_status_while_the_lock_is_held_says_running(client):
    _sign_in(client)

    with app.sync.exclusive._LOCK:
        response = client.get("/api/sync/status")

    assert response.json()["running"] is True


def test_run_without_credentials_and_pluggy_source_answers_503(client, monkeypatch):
    monkeypatch.setenv("DASH_SYNC_SOURCE", "pluggy")
    for name in PLUGGY_CREDENTIALS:
        monkeypatch.delenv(name, raising=False)
    _sign_in(client)

    response = client.post("/api/sync/run")

    assert response.status_code == 503
    assert "PLUGGY_CLIENT_ID" in response.json()["detail"]


def test_a_failed_row_comes_back_as_a_readable_reason(client):
    conn = connect()
    conn.execute(
        "INSERT INTO sync_runs (started_at, finished_at, source, status, message) "
        "VALUES ('2026-09-05T10:00:00', '2026-09-05T10:00:01', 'pluggy', 'failed', ?)",
        (UNREACHABLE,),
    )
    conn.commit()
    conn.close()
    _sign_in(client)

    response = client.get("/api/sync/status")

    body = response.json()
    assert body["last_run"]["status"] == "failed"
    assert (
        body["last_run"]["reason"]
        == "a Pluggy não respondeu; verifique a conexão com a internet e tente de novo."
    )


def test_a_pluggy_failure_during_run_is_200_with_status_failed(client, monkeypatch):
    monkeypatch.setenv("DASH_SYNC_SOURCE", "pluggy")
    monkeypatch.setenv("PLUGGY_CLIENT_ID", "id-falso")
    monkeypatch.setenv("PLUGGY_CLIENT_SECRET", "segredo-falso")

    def explode(config):
        raise PluggyFetchError(UNREACHABLE)

    monkeypatch.setattr(app.sync, "fetch_from_pluggy", explode)
    _sign_in(client)

    response = client.post("/api/sync/run")

    assert response.status_code == 200
    body = response.json()
    assert body["last_run"]["status"] == "failed"
    assert not body["last_run"]["reason"].startswith("pluggy: ")
