import pytest

from app.auth.password import verify_password
from app.auth.seed import seed_user
from app.auth.users import session_epoch
from app.db import connect
from app.migrate import SQL_FOLDER
from app.migrations.runner import apply_migrations

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
NEW_PASSWORD = "senha-nova-7x4"

STORED_HASH = "SELECT password_hash FROM users WHERE login = ?"


@pytest.fixture()
def conn(tmp_path):
    connection = connect(str(tmp_path / "dash.sqlite"))
    apply_migrations(connection, SQL_FOLDER)
    yield connection
    connection.close()


def _stored(conn) -> str:
    return conn.execute(STORED_HASH, (LOGIN,)).fetchone()[0]


def test_the_first_seed_starts_the_epoch_at_zero(conn):
    seed_user(conn, LOGIN, PASSWORD)

    assert session_epoch(conn, LOGIN) == 0
    assert verify_password(PASSWORD, _stored(conn))


def test_seeding_the_same_password_changes_nothing(conn):
    seed_user(conn, LOGIN, PASSWORD)
    before = _stored(conn)

    seed_user(conn, LOGIN, PASSWORD)
    seed_user(conn, LOGIN, PASSWORD)

    assert session_epoch(conn, LOGIN) == 0
    assert _stored(conn) == before


def test_a_new_password_bumps_the_epoch(conn):
    seed_user(conn, LOGIN, PASSWORD)

    seed_user(conn, LOGIN, NEW_PASSWORD)

    assert session_epoch(conn, LOGIN) == 1
    assert verify_password(NEW_PASSWORD, _stored(conn))
    assert not verify_password(PASSWORD, _stored(conn))


def test_each_password_change_bumps_the_epoch_again(conn):
    seed_user(conn, LOGIN, PASSWORD)
    seed_user(conn, LOGIN, NEW_PASSWORD)

    seed_user(conn, LOGIN, "terceira-senha-1a2")

    assert session_epoch(conn, LOGIN) == 2


def test_the_seed_does_not_touch_another_login(conn):
    seed_user(conn, LOGIN, PASSWORD)
    seed_user(conn, "outro", PASSWORD)

    seed_user(conn, "outro", NEW_PASSWORD)

    assert (session_epoch(conn, LOGIN), session_epoch(conn, "outro")) == (0, 1)
