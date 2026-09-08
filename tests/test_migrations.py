import sqlite3

import pytest

from app.db import connect
from app.migrate import SQL_FOLDER
from app.migrations.runner import apply_migrations

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
    "013_cards.sql",
    "014_financings.sql",
    "015_advisor_config.sql",
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
