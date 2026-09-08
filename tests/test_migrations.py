import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from app.db import connect
from app.migrate import SQL_FOLDER
from app.migrations.runner import OutOfOrderMigrationError, apply_migrations

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = [
    "accounts",
    "advisor_config",
    "advisor_questions",
    "cards",
    "categories",
    "category_groups",
    "category_rules",
    "commitment_dismissals",
    "commitments",
    "crossings",
    "debts",
    "essentialities",
    "financings",
    "login_attempts",
    "natures",
    "offers",
    "payee_names",
    "plan_facts",
    "plan_snapshots",
    "scenarios",
    "schema_migrations",
    "sync_runs",
    "transactions",
    "users",
]

EXPECTED_MIGRATIONS = [
    "001_schema.sql",
    "002_session_epoch.sql",
    "003_taxonomy.sql",
    "004_commitments.sql",
    "005_debts.sql",
    "006_sync_semantics.sql",
    "007_plan.sql",
    "008_facts.sql",
    "009_advisor.sql",
    "010_settings.sql",
    "011_payee_names.sql",
    "012_taxonomy_tree.sql",
    "013_cards.sql",
    "014_financings.sql",
    "015_advisor_config.sql",
    "018_offers.sql",
]

TABLE_NAMES = (
    "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
)


@pytest.fixture()
def conn(tmp_path):
    connection = connect(str(tmp_path / "dash.sqlite"))
    yield connection
    connection.close()


def test_first_run_creates_every_declared_table(conn):
    assert apply_migrations(conn, SQL_FOLDER) == EXPECTED_MIGRATIONS
    assert [row[0] for row in conn.execute(TABLE_NAMES)] == EXPECTED_TABLES


def test_second_run_applies_nothing(conn):
    apply_migrations(conn, SQL_FOLDER)

    assert apply_migrations(conn, SQL_FOLDER) == []

    row = conn.execute(
        "select count(*), min(version), max(version) from schema_migrations"
    ).fetchone()
    assert tuple(row) == (
        len(EXPECTED_MIGRATIONS),
        "001",
        EXPECTED_MIGRATIONS[-1].split("_")[0],
    )


def test_the_session_epoch_starts_at_zero(conn):
    apply_migrations(conn, SQL_FOLDER)

    row = conn.execute(
        "select type, \"notnull\", dflt_value from pragma_table_info('users') "
        "where name = 'session_epoch'"
    ).fetchone()

    assert tuple(row) == ("INTEGER", 1, "0")


def test_money_columns_are_integer(conn):
    apply_migrations(conn, SQL_FOLDER)

    row = conn.execute(
        "select (select type from pragma_table_info('transactions') where name='amount_cents'), "
        "(select type from pragma_table_info('accounts') where name='balance_cents')"
    ).fetchone()

    assert tuple(row) == ("INTEGER", "INTEGER")


def test_pluggy_id_is_unique(conn):
    apply_migrations(conn, SQL_FOLDER)
    conn.execute("insert into accounts (id, balance_cents) values ('acc-1', 0)")
    conn.execute(
        "insert into transactions (pluggy_id, account_id, date, amount_cents) "
        "values ('abc-1', 'acc-1', '2026-09-05', -100)"
    )

    with pytest.raises(
        sqlite3.IntegrityError, match="UNIQUE constraint failed: transactions.pluggy_id"
    ):
        conn.execute(
            "insert into transactions (pluggy_id, account_id, date, amount_cents) "
            "values ('abc-1', 'acc-1', '2026-09-05', -200)"
        )


def test_unknown_account_is_refused(conn):
    apply_migrations(conn, SQL_FOLDER)

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
        conn.execute(
            "insert into transactions (pluggy_id, account_id, date, amount_cents) "
            "values ('abc-2', 'nao-existe', '2026-09-05', -100)"
        )


def _write_sql(folder, name, script):
    (folder / name).write_text(script, encoding="utf-8")


def test_a_migration_fora_de_ordem_names_both_versions_in_the_refusal(tmp_path, conn):
    folder = tmp_path / "sql"
    folder.mkdir()
    _write_sql(folder, "018_first.sql", "CREATE TABLE marker_018 (id INTEGER PRIMARY KEY);")
    apply_migrations(conn, folder)

    _write_sql(folder, "016_late.sql", "CREATE TABLE marker_016 (id INTEGER PRIMARY KEY);")

    with pytest.raises(OutOfOrderMigrationError) as excinfo:
        apply_migrations(conn, folder)

    assert "016" in str(excinfo.value)
    assert "018" in str(excinfo.value)


def test_the_refusal_da_ordem_leaves_schema_migrations_unchanged(tmp_path, conn):
    folder = tmp_path / "sql"
    folder.mkdir()
    _write_sql(folder, "018_first.sql", "CREATE TABLE marker_018 (id INTEGER PRIMARY KEY);")
    apply_migrations(conn, folder)

    _write_sql(folder, "016_late.sql", "CREATE TABLE marker_016 (id INTEGER PRIMARY KEY);")

    before = conn.execute("select version from schema_migrations order by version").fetchall()

    with pytest.raises(OutOfOrderMigrationError):
        apply_migrations(conn, folder)

    after = conn.execute("select version from schema_migrations order by version").fetchall()
    assert after == before

    tables = [
        row[0]
        for row in conn.execute(
            "select name from sqlite_master where type='table' and name like 'marker_%'"
        )
    ]
    assert tables == ["marker_018"]


def test_a_fresh_base_applies_the_sixteen_real_migrations(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "app.migrate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "DASH_DB_PATH": str(tmp_path / "dash.sqlite"),
            "DASH_ENV_FILE": "/dev/null",
        },
    )

    assert result.returncode == 0
    assert "migrations applied: 16" in result.stdout
