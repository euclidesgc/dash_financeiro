from datetime import date

import pytest
from fastapi.testclient import TestClient

import app.sync as sync
from app.auth.seed import seed_user
from app.db import connect
from app.ingest.trigger import COMMAND
from app.main import create_app
from app.queries.pluggy_connections import list_item_ids
from app.sync import readable, synchronise
from app.sync.connections import (
    ConnectionNotFoundError,
    DuplicateConnectionError,
    InvalidItemIdError,
    add_connection,
    import_file,
    remove_connection,
)

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
ITEM = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
OTHER = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
REFERENCE = date(2026, 9, 5)
FORMAT_MESSAGE = "Informe um identificador de conexão da Pluggy (formato 8-4-4-4-12)."


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


def test_the_list_starts_empty(client):
    _sign_in(client)

    response = client.get("/api/pluggy-connections")

    assert response.status_code == 200
    assert response.json() == {"connections": []}


def test_adding_trims_and_lowercases_and_the_list_shows_it(client):
    _sign_in(client)

    response = client.post("/api/pluggy-connections", json={"item_id": f"  {ITEM.upper()}  "})

    assert response.status_code == 201
    assert response.json()["item_id"] == ITEM
    listed = client.get("/api/pluggy-connections").json()["connections"]
    assert [row["item_id"] for row in listed] == [ITEM]
    assert listed[0]["created_at"] == response.json()["created_at"]


def test_a_repeated_connection_answers_409(client):
    _sign_in(client)
    client.post("/api/pluggy-connections", json={"item_id": ITEM})

    response = client.post("/api/pluggy-connections", json={"item_id": ITEM.upper()})

    assert response.status_code == 409
    assert response.json() == {"detail": "Essa conexão já está cadastrada."}


@pytest.mark.parametrize("raw", ["", "   ", "abc", f"{ITEM}0", ITEM.replace("-", "")])
def test_an_id_outside_the_pluggy_format_answers_422(client, raw):
    _sign_in(client)

    response = client.post("/api/pluggy-connections", json={"item_id": raw})

    assert response.status_code == 422
    assert response.json() == {"detail": FORMAT_MESSAGE}
    assert client.get("/api/pluggy-connections").json() == {"connections": []}


def test_removing_answers_204_and_a_second_removal_404(client):
    _sign_in(client)
    client.post("/api/pluggy-connections", json={"item_id": ITEM})

    first = client.delete(f"/api/pluggy-connections/{ITEM}")
    second = client.delete(f"/api/pluggy-connections/{ITEM}")

    assert first.status_code == 204
    assert second.status_code == 404
    assert second.json() == {"detail": "Conexão não encontrada."}
    assert client.get("/api/pluggy-connections").json() == {"connections": []}


def test_every_route_without_session_answers_401(client):
    assert client.get("/api/pluggy-connections").status_code == 401
    assert client.post("/api/pluggy-connections", json={"item_id": ITEM}).status_code == 401
    assert client.delete(f"/api/pluggy-connections/{ITEM}").status_code == 401


def test_the_domain_refuses_bad_ids_duplicates_and_unknown_removals(taxonomy_conn):
    add_connection(taxonomy_conn, ITEM)

    with pytest.raises(InvalidItemIdError):
        add_connection(taxonomy_conn, "abc")
    with pytest.raises(DuplicateConnectionError):
        add_connection(taxonomy_conn, ITEM)
    with pytest.raises(ConnectionNotFoundError):
        remove_connection(taxonomy_conn, OTHER)
    assert list_item_ids(taxonomy_conn) == [ITEM]


def test_import_file_keeps_valid_lines_once_and_is_idempotent(taxonomy_conn, tmp_path):
    source = tmp_path / "item_ids.txt"
    source.write_text(f"{ITEM}\n\n{OTHER.upper()}\n{ITEM}\nnao-e-id\n", encoding="utf-8")

    first = import_file(taxonomy_conn, source)
    second = import_file(taxonomy_conn, source)

    assert first == 2
    assert second == 0
    assert sorted(list_item_ids(taxonomy_conn)) == sorted([ITEM, OTHER])


def _pluggy_source(monkeypatch):
    monkeypatch.setenv("DASH_SYNC_SOURCE", "pluggy")
    monkeypatch.setenv("PLUGGY_CLIENT_ID", "id-falso")
    monkeypatch.setenv("PLUGGY_CLIENT_SECRET", "segredo-falso")


def test_without_connections_the_pluggy_sync_fails_pointing_at_the_screen(
    taxonomy_conn, monkeypatch
):
    _pluggy_source(monkeypatch)

    outcome = synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)

    assert outcome.status == "failed"
    assert readable(outcome.message) == "nenhuma conexão cadastrada; cadastre em Conexões."


def test_the_pluggy_sync_fetches_exactly_the_registered_connections(taxonomy_conn, monkeypatch):
    _pluggy_source(monkeypatch)
    add_connection(taxonomy_conn, ITEM)
    received: list[list[str]] = []

    def capture(config, item_ids):
        received.append(item_ids)
        raise sync.PluggyFetchError("pluggy: parada do teste.")

    monkeypatch.setattr(sync, "fetch_from_pluggy", capture)

    synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)

    assert received == [[ITEM]]
