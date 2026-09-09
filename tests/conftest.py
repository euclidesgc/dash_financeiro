import os
import sqlite3
from copy import deepcopy

import httpx
import pytest

from app.db import connect
from app.ingest.loader import ingest
from app.migrate import run_migrations
from app.taxonomy.seed import load_seed


@pytest.fixture(autouse=True, scope="session")
def ignore_the_owner_env_file():
    # Reason: load_config falls back to the repository .env, so without this
    # the suite reads the owner's real credentials, and a test that unsets a
    # variable to exercise its absence gets the value handed back by the file.
    os.environ["DASH_ENV_FILE"] = os.devnull


ACCOUNT = {
    "id": "acc-1",
    "type": "BANK",
    "subtype": "CHECKING_ACCOUNT",
    "name": "Conta de teste",
    "balance": 100.0,
}


def transaction(pluggy_id: str, date: str, valor: float, **overrides) -> dict:
    row = {
        "id": pluggy_id,
        "data": date,
        "conta_id": ACCOUNT["id"],
        "descricao": pluggy_id,
        "valor": valor,
        "tipo": "DEBIT",
        "categoria": "",
        "eh_transferencia": False,
        "motivo_transferencia": "",
        "eh_saque": False,
        "eh_estorno": False,
        "estornada_por": "",
        "nome_fantasia": "",
        "razao_social": "",
        "cnpj": "",
        "recebedor": "",
    }
    row.update(overrides)
    return row


def load(conn: sqlite3.Connection, rows: list[dict]) -> sqlite3.Connection:
    result = ingest(conn, transactions=rows, accounts=[ACCOUNT], source="tests")
    assert result.status == "ok", result.message
    return conn


def narrowed(seed: dict, rules: list[dict]) -> dict:
    narrow = deepcopy(seed)
    narrow["rules"] = rules
    return narrow


def rule(match_kind: str, match_value: str, group: str, nature: str, essentiality: str) -> dict:
    return {
        "match_kind": match_kind,
        "match_value": match_value,
        "group": group,
        "nature": nature,
        "essentiality": essentiality,
    }


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    # Reason: two modules of app/ leave for the internet, and each test that
    # exercises one used to install its own monkeypatch. A test that forgets
    # goes to the real network, and then the suite passes or fails by what a
    # third party answered. Only the module-level helpers are replaced: the
    # TestClient drives httpx through a client instance of its own, which is
    # not egress.
    def refused(*args, **kwargs):
        raise AssertionError("o teste tentou sair para a rede")

    monkeypatch.setattr(httpx, "get", refused)
    monkeypatch.setattr(httpx, "post", refused)


@pytest.fixture
def seed():
    return load_seed()


@pytest.fixture
def taxonomy_conn(tmp_path):
    path = str(tmp_path / "dash.sqlite")
    run_migrations(path)
    conn = connect(path)
    yield conn
    conn.close()
