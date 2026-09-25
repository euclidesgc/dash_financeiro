import json

import pytest

from ingestao import pluggy_consolidate, pluggy_extract
from ingestao.pluggy_consolidate import NoRawAccountsError, consolidate
from ingestao.pluggy_extract import MissingCredentialsError, read_credentials

SECRET = "segredo-do-arquivo"


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


def test_the_consolidation_command_still_exits_without_raw_accounts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="accounts_"):
        pluggy_consolidate.main()
