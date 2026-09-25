import pytest

from app.db import connect
from app.migrate import run_migrations
from app.taxonomy.classify import classify_all
from tests import e2e_seed


@pytest.fixture
def conn(tmp_path):
    path = str(tmp_path / "dash.sqlite")
    run_migrations(path)
    connection = connect(path)
    yield connection
    connection.close()


def _count(conn, where: str) -> int:
    return int(conn.execute(f"SELECT count(*) FROM transactions WHERE {where}").fetchone()[0])


def test_the_seed_leaves_every_transaction_classified(conn):
    result = e2e_seed.seed(conn)

    assert result.status == "ok", result.message
    assert _count(conn, "1") > 0
    assert _count(conn, "group_id IS NULL OR nature IS NULL OR essentiality IS NULL") == 0
    assert _count(conn, "rule_id IS NOT NULL") > 0


def test_classifying_again_after_the_seed_changes_nothing(conn):
    e2e_seed.seed(conn)

    assert classify_all(conn) == 0


def test_the_seed_records_no_sync_run_and_creates_the_e2e_user(conn):
    e2e_seed.seed(conn)

    assert conn.execute("SELECT count(*) FROM sync_runs").fetchone()[0] == 0
    user = conn.execute("SELECT login FROM users WHERE login = ?", (e2e_seed.LOGIN,)).fetchone()
    assert user is not None


def test_a_rejected_seed_load_classifies_nothing(conn, monkeypatch):
    monkeypatch.setattr(e2e_seed, "load_transactions", lambda path: [{"descricao": "SEM ID"}])

    result = e2e_seed.seed(conn)

    assert result.status != "ok"
    assert _count(conn, "group_id IS NOT NULL") == 0


def test_main_exits_with_one_when_the_seed_load_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setattr(e2e_seed, "load_transactions", lambda path: [{"descricao": "SEM ID"}])

    assert e2e_seed.main() == 1


def test_main_exits_with_zero_on_a_clean_seed(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))

    assert e2e_seed.main() == 0
