import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from app.db import connect
from app.migrate import SQL_FOLDER
from app.migrations.runner import (
    OutOfOrderMigrationError,
    SkippedMigrationError,
    apply_migrations,
    reconcile_skipped,
)

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


def test_a_version_narrower_than_three_digits_is_refused_at_the_door(tmp_path, conn):
    # A ordem e o guarda comparam texto, e "9" ordena depois de "015": uma
    # migração sem o zero à esquerda inverteria as duas coisas ao mesmo tempo.
    folder = tmp_path / "sql"
    folder.mkdir()
    _write_sql(folder, "9_sem_zero.sql", "CREATE TABLE marker_9 (id INTEGER PRIMARY KEY);")

    with pytest.raises(OutOfOrderMigrationError) as excinfo:
        apply_migrations(conn, folder)

    assert "9_sem_zero.sql" in str(excinfo.value)
    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 0


def test_the_three_digit_form_the_project_uses_still_applies(tmp_path, conn):
    folder = tmp_path / "sql"
    folder.mkdir()
    _write_sql(folder, "019_next.sql", "CREATE TABLE marker_019 (id INTEGER PRIMARY KEY);")

    assert apply_migrations(conn, folder) == ["019_next.sql"]


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


def _base_que_pulou(conn, folder):
    # Fiel ao que aconteceu na base do dono: ela migrou quando a 012 ainda não
    # existia na pasta, e a 012 apareceu depois, entre versões já aplicadas.
    _write_sql(folder, "010_a.sql", "CREATE TABLE marker_010 (id INTEGER PRIMARY KEY);")
    _write_sql(folder, "015_c.sql", "CREATE TABLE marker_015 (id INTEGER PRIMARY KEY);")
    apply_migrations(conn, folder)
    _write_sql(folder, "012_pulada.sql", "CREATE TABLE marker_012 (id INTEGER PRIMARY KEY);")


def test_a_base_that_skipped_a_version_is_told_to_reconcile_not_to_renumber(tmp_path, conn):
    folder = tmp_path / "sql"
    folder.mkdir()
    _base_que_pulou(conn, folder)

    with pytest.raises(SkippedMigrationError) as excinfo:
        apply_migrations(conn, folder)

    mensagem = str(excinfo.value)
    assert "pulou" in mensagem
    assert "--reconciliar 012" in mensagem
    assert "renumere" not in mensagem


def test_a_new_low_numbered_migration_on_a_base_with_no_gap_is_told_to_renumber(tmp_path, conn):
    # Sem versão aplicada ABAIXO da que chega, não há vão: esta base é nova
    # numa árvore que já tem números altos, e o conselho certo é renumerar.
    folder = tmp_path / "sql"
    folder.mkdir()
    _write_sql(folder, "015_c.sql", "CREATE TABLE marker_015 (id INTEGER PRIMARY KEY);")
    apply_migrations(conn, folder)
    _write_sql(folder, "012_nova.sql", "CREATE TABLE marker_012 (id INTEGER PRIMARY KEY);")

    with pytest.raises(OutOfOrderMigrationError) as excinfo:
        apply_migrations(conn, folder)

    assert "renumere" in str(excinfo.value)
    assert "pulou" not in str(excinfo.value)


def test_reconciling_applies_the_skipped_version_and_unblocks_the_rest(tmp_path, conn):
    folder = tmp_path / "sql"
    folder.mkdir()
    _base_que_pulou(conn, folder)

    resultado = reconcile_skipped(conn, folder, "012")

    assert "fechou" in resultado
    _write_sql(folder, "019_depois.sql", "CREATE TABLE marker_019 (id INTEGER PRIMARY KEY);")
    assert apply_migrations(conn, folder) == ["019_depois.sql"]


def test_reconciling_a_version_that_does_not_fit_writes_nothing(tmp_path, conn):
    folder = tmp_path / "sql"
    folder.mkdir()
    _base_que_pulou(conn, folder)
    # A 012 passa a colidir com uma tabela que a 010 já criou: não cabe.
    _write_sql(folder, "012_pulada.sql", "CREATE TABLE marker_010 (id INTEGER PRIMARY KEY);")

    resultado = reconcile_skipped(conn, folder, "012")

    assert "não se aplica" in resultado
    registradas = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    assert "012" not in registradas
