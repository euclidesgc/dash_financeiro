import sqlite3
from copy import deepcopy

import pytest

from app.db import connect
from app.ingest.loader import ingest
from app.migrate import run_migrations
from app.taxonomy.seed import load_seed

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
