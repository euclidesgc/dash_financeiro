import json

import pytest

from app.db import connect
from app.migrate import run_migrations
from app.queries.pluggy_connections import list_item_ids
from app.sync.connections import add_connection
from ingestao import pluggy_consolidate, pluggy_extract
from ingestao.pluggy_consolidate import NoRawAccountsError, consolidate
from ingestao.pluggy_extract import (
    MissingCredentialsError,
    itens_salvos,
    read_credentials,
    registrar_item,
)

SECRET = "segredo-do-arquivo"
FIRST = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
SECOND = "0b8e5f3a-1c2d-4e5f-8a9b-0c1d2e3f4a5b"


@pytest.fixture()
def clean_environment(monkeypatch):
    # Reason: load_dotenv writes straight into os.environ; setting before
    # deleting makes monkeypatch restore whatever the file put there.
    for name in ("PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET", "DASH_ENV_FILE"):
        monkeypatch.setenv(name, "placeholder")
        monkeypatch.delenv(name)
    return monkeypatch


def test_the_credentials_come_from_the_file_named_by_dash_env_file(tmp_path, clean_environment):
    env_file = tmp_path / "outro.env"
    env_file.write_text(
        f"PLUGGY_CLIENT_ID=id-do-arquivo\nPLUGGY_CLIENT_SECRET={SECRET}\n", encoding="utf-8"
    )
    clean_environment.setenv("DASH_ENV_FILE", str(env_file))
    clean_environment.chdir(tmp_path)

    assert read_credentials() == ("id-do-arquivo", SECRET)


def test_a_variable_already_in_the_environment_wins_over_the_file(tmp_path, clean_environment):
    env_file = tmp_path / "outro.env"
    env_file.write_text(
        f"PLUGGY_CLIENT_ID=id-do-arquivo\nPLUGGY_CLIENT_SECRET={SECRET}\n", encoding="utf-8"
    )
    clean_environment.setenv("DASH_ENV_FILE", str(env_file))
    clean_environment.setenv("PLUGGY_CLIENT_ID", "id-do-processo")

    assert read_credentials() == ("id-do-processo", SECRET)


def test_a_missing_secret_names_the_variable_and_never_shows_a_value():
    with pytest.raises(MissingCredentialsError) as failure:
        read_credentials({"PLUGGY_CLIENT_ID": "id-presente"})

    assert "PLUGGY_CLIENT_SECRET" in str(failure.value)
    assert "id-presente" not in str(failure.value)


def test_the_command_turns_missing_credentials_into_an_exit(tmp_path, clean_environment):
    clean_environment.setenv("DASH_ENV_FILE", str(tmp_path / "inexistente.env"))
    clean_environment.setattr("sys.argv", ["pluggy_extract.py", "status", "--item", "x"])

    with pytest.raises(SystemExit, match="PLUGGY_CLIENT_ID"):
        pluggy_extract.main()


def test_consolidating_without_raw_accounts_raises_and_prints_nothing(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(NoRawAccountsError):
        consolidate()

    assert capsys.readouterr().out == ""
    assert not (tmp_path / "data" / "processed").exists()


def test_consolidating_returns_the_counts_and_prints_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "accounts_x.json").write_text(
        json.dumps({"results": [{"id": "acc-1", "name": "Conta", "type": "BANK"}]}),
        encoding="utf-8",
    )
    (raw / "v2_transactions_acc-1_p1.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "id": "tx-1",
                        "accountId": "acc-1",
                        "date": "2026-09-20T00:00:00.000Z",
                        "amount": -10.0,
                        "description": "Padaria",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    summary = consolidate()

    assert summary["transacoes"] == 1
    assert capsys.readouterr().out == ""
    assert (tmp_path / "data" / "processed" / "transacoes.json").exists()


@pytest.mark.parametrize(
    ("instant", "expected"),
    [
        ("2026-04-01T02:59:00.000Z", "2026-03-31"),
        ("2026-09-01T01:25:35.091Z", "2026-08-31"),
        ("2026-11-06T03:00:00.000Z", "2026-11-06"),
        ("2026-08-04T03:43:04.000Z", "2026-08-04"),
    ],
)
def test_the_consolidated_date_is_the_day_in_sao_paulo_not_in_utc(
    tmp_path, monkeypatch, instant, expected
):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "accounts_x.json").write_text(
        json.dumps({"results": [{"id": "acc-1", "name": "Conta", "type": "BANK"}]}),
        encoding="utf-8",
    )
    (raw / "v2_transactions_acc-1_p1.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "id": "tx-1",
                        "accountId": "acc-1",
                        "date": instant,
                        "amount": 2928.46,
                        "description": "Salário REMUNERACAO/SALARIO",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    consolidate()

    rows = json.loads(
        (tmp_path / "data" / "processed" / "transacoes.json").read_text(encoding="utf-8")
    )
    assert [row["data"] for row in rows] == [expected]


def test_the_consolidation_command_still_exits_without_raw_accounts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="accounts_"):
        pluggy_consolidate.main()


def test_the_saved_items_are_the_registered_connections_in_registration_order(taxonomy_conn):
    add_connection(taxonomy_conn, FIRST)
    add_connection(taxonomy_conn, SECOND)

    assert itens_salvos(taxonomy_conn) == [FIRST, SECOND]


def test_registering_an_item_adds_it_once_and_tolerates_a_repeat(taxonomy_conn):
    registrar_item(taxonomy_conn, FIRST)
    registrar_item(taxonomy_conn, FIRST)

    assert list_item_ids(taxonomy_conn) == [FIRST]


@pytest.fixture()
def database(tmp_path, monkeypatch):
    path = tmp_path / "dash.sqlite"
    monkeypatch.setenv("DASH_DB_PATH", str(path))
    return path


@pytest.fixture()
def queried(monkeypatch):
    items: list[str] = []
    monkeypatch.setattr(pluggy_extract, "autenticar", lambda: "chave-falsa")
    monkeypatch.setattr(
        pluggy_extract, "status_de_um", lambda api_key, item_id: items.append(item_id)
    )
    return items


def _status(monkeypatch, *arguments: str) -> None:
    monkeypatch.setattr("sys.argv", ["pluggy_extract.py", "status", *arguments])
    pluggy_extract.main()


def test_status_without_item_queries_every_registered_connection(database, queried, monkeypatch):
    run_migrations(str(database))
    conn = connect(str(database))
    try:
        add_connection(conn, FIRST)
        add_connection(conn, SECOND)
    finally:
        conn.close()

    _status(monkeypatch)

    assert queried == [FIRST, SECOND]


def test_status_without_item_and_without_connections_points_at_the_screen(
    database, queried, monkeypatch
):
    with pytest.raises(SystemExit) as stop:
        _status(monkeypatch)

    assert str(stop.value) == "Nenhuma conexão cadastrada. Cadastre em Conexões ou passe --item."
    assert queried == []


def test_status_with_item_queries_only_it_and_leaves_the_database_alone(
    database, queried, monkeypatch
):
    _status(monkeypatch, "--item", SECOND)

    assert queried == [SECOND]
    assert not database.exists()
