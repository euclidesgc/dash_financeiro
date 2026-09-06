from datetime import datetime, timedelta, timezone

import pytest

from app.auth.rate_limit import (
    MAX_FAILURES,
    WINDOW_SECONDS,
    blocked_seconds,
    record_failure,
    record_success,
)
from app.db import connect
from app.migrate import SQL_FOLDER
from app.migrations.runner import apply_migrations

IP = "127.0.0.1"


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "dash.sqlite")
    connection = connect(path)
    apply_migrations(connection, SQL_FOLDER)
    connection.close()
    return path


def _fail(conn, times, *, now=None):
    for offset in range(times):
        moment = None if now is None else now - timedelta(seconds=offset)
        record_failure(conn, IP, now=moment)


def test_below_the_limit_nothing_is_blocked(db_path):
    conn = connect(db_path)
    _fail(conn, MAX_FAILURES - 1)

    assert blocked_seconds(conn, IP) == 0
    conn.close()


def test_the_sixth_attempt_is_blocked(db_path):
    conn = connect(db_path)
    _fail(conn, MAX_FAILURES)

    waiting = blocked_seconds(conn, IP)

    assert 1 <= waiting <= WINDOW_SECONDS
    conn.close()


def test_another_ip_is_not_blocked(db_path):
    conn = connect(db_path)
    _fail(conn, MAX_FAILURES)

    assert blocked_seconds(conn, "10.0.0.9") == 0
    conn.close()


def test_failures_outside_the_window_do_not_block(db_path):
    conn = connect(db_path)
    now = datetime.now(timezone.utc)
    _fail(conn, MAX_FAILURES, now=now - timedelta(seconds=WINDOW_SECONDS + 60))

    assert blocked_seconds(conn, IP, now=now) == 0
    conn.close()


def test_the_window_survives_a_new_connection(db_path):
    first = connect(db_path)
    _fail(first, MAX_FAILURES)
    first.close()

    second = connect(db_path)

    assert blocked_seconds(second, IP) > 0
    second.close()


def test_every_recorded_failure_is_stored(db_path):
    conn = connect(db_path)
    _fail(conn, MAX_FAILURES)

    stored = conn.execute(
        "SELECT count(*) FROM login_attempts WHERE ip = ? AND success = 0", (IP,)
    ).fetchone()[0]

    assert stored == MAX_FAILURES
    conn.close()


def test_a_success_is_stored_with_its_flag(db_path):
    conn = connect(db_path)
    record_success(conn, IP)

    stored = conn.execute(
        "SELECT ip, success FROM login_attempts WHERE success = 1"
    ).fetchall()

    assert [(row["ip"], row["success"]) for row in stored] == [(IP, 1)]
    conn.close()


def test_successes_do_not_count_toward_the_block(db_path):
    conn = connect(db_path)
    for _ in range(MAX_FAILURES * 2):
        record_success(conn, IP)
    _fail(conn, MAX_FAILURES - 1)

    assert blocked_seconds(conn, IP) == 0

    record_failure(conn, IP)

    assert blocked_seconds(conn, IP) > 0
    conn.close()


def test_a_success_after_the_failures_does_not_lift_the_block(db_path):
    conn = connect(db_path)
    _fail(conn, MAX_FAILURES)
    record_success(conn, IP)

    assert blocked_seconds(conn, IP) > 0
    conn.close()
