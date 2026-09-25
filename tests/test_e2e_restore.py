import shutil

import pytest

from app.db import connect
from app.migrate import run_migrations
from tests import e2e_restore, e2e_seed


@pytest.fixture
def paths(tmp_path):
    live = str(tmp_path / "dash.sqlite")
    snapshot = str(tmp_path / "seed.sqlite")
    run_migrations(live)
    conn = connect(live)
    e2e_seed.seed(conn)
    conn.close()
    shutil.copyfile(live, snapshot)
    return snapshot, live


def _sync_runs(conn) -> int:
    return int(conn.execute("SELECT count(*) FROM sync_runs").fetchone()[0])


def test_restore_brings_back_the_seed_under_an_open_connection(paths):
    snapshot, live = paths
    conn = connect(live)
    conn.execute(
        "INSERT INTO sync_runs (started_at, finished_at, source, status, message) "
        "VALUES ('2026-09-25', '2026-09-25', 'arquivo', 'ok', '')"
    )
    conn.commit()
    assert _sync_runs(conn) == 1

    e2e_restore.restore(snapshot, live)

    assert _sync_runs(conn) == 0
    conn.close()


def test_main_restores_with_the_two_paths(paths):
    snapshot, live = paths
    conn = connect(live)
    conn.execute("DELETE FROM users")
    conn.commit()

    assert e2e_restore.main([snapshot, live]) == 0

    assert conn.execute("SELECT count(*) FROM users").fetchone()[0] == 1
    conn.close()


def test_main_refuses_the_wrong_number_of_arguments(capsys):
    assert e2e_restore.main([]) == 1
    assert "usage" in capsys.readouterr().err
