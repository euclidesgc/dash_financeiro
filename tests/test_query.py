import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.migrate import run_migrations

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "dash.sqlite"
    run_migrations(str(path))
    return path


def query(db_path, statement):
    return subprocess.run(
        [sys.executable, "-m", "app.query", statement],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "DASH_DB_PATH": str(db_path), "DASH_ENV_FILE": "/dev/null"},
    )


def test_select_prints_one_line_per_row(db_path):
    result = query(db_path, "select count(*), min(version) from schema_migrations")

    assert result.returncode == 0
    assert result.stdout == "1 001\n"


def test_pragma_is_allowed(db_path):
    result = query(db_path, "pragma table_info('users')")

    assert result.returncode == 0
    assert "password_hash" in result.stdout


def test_write_statement_is_refused(db_path):
    result = query(db_path, "delete from users")

    assert result.returncode != 0
    assert result.stdout == ""
    assert query(db_path, "select count(*) from users").stdout == "0\n"


def test_missing_argument_is_refused(db_path):
    result = subprocess.run(
        [sys.executable, "-m", "app.query"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "DASH_DB_PATH": str(db_path), "DASH_ENV_FILE": "/dev/null"},
    )

    assert result.returncode != 0
