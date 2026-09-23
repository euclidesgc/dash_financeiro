import pytest

from app.db import connect
from app.migrate import SQL_FOLDER
from app.migrations.runner import apply_migrations
from app.plan.ceiling import InvalidCeilingError, month_signal, read_ceiling, set_ceiling


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    connection = connect()
    apply_migrations(connection, SQL_FOLDER)
    yield connection
    connection.close()


def test_set_ceiling_refuses_zero_and_negative_and_keeps_the_previous_value(conn):
    set_ceiling(conn, 500000)

    with pytest.raises(InvalidCeilingError) as zero:
        set_ceiling(conn, 0)
    assert zero.value.cents == 0

    with pytest.raises(InvalidCeilingError) as negative:
        set_ceiling(conn, -1)
    assert negative.value.cents == -1

    assert read_ceiling(conn) == 500000


def test_set_ceiling_writes_and_read_ceiling_reads(conn):
    assert read_ceiling(conn) is None

    set_ceiling(conn, 500000)

    assert read_ceiling(conn) == 500000


def test_set_ceiling_with_none_clears_it(conn):
    set_ceiling(conn, 500000)

    set_ceiling(conn, None)

    assert read_ceiling(conn) is None


def test_month_signal_over_the_ceiling():
    result = month_signal(spent_cents=10500, ceiling_cents=10000, whole_month=True)

    assert result.scope == "month"
    assert result.signal == "over"
    assert result.remaining_cents == -500


def test_month_signal_within_the_ceiling():
    result = month_signal(spent_cents=10500, ceiling_cents=20000, whole_month=True)

    assert result.signal == "within"
    assert result.remaining_cents == 9500


def test_month_signal_warning_near_the_ceiling():
    result = month_signal(spent_cents=10500, ceiling_cents=12000, whole_month=True)

    assert result.signal == "warning"
    assert result.remaining_cents == 1500


def test_month_signal_exactly_at_the_ceiling_is_warning_with_zero_left():
    result = month_signal(spent_cents=10500, ceiling_cents=10500, whole_month=True)

    assert result.signal == "warning"
    assert result.remaining_cents == 0


def test_month_signal_without_a_ceiling_has_no_signal_and_no_remaining():
    result = month_signal(spent_cents=10500, ceiling_cents=None, whole_month=True)

    assert result.scope == "month"
    assert result.ceiling_cents is None
    assert result.signal is None
    assert result.remaining_cents is None


def test_month_signal_outside_a_whole_month_keeps_the_ceiling_but_no_signal():
    result = month_signal(spent_cents=10500, ceiling_cents=10000, whole_month=False)

    assert result.scope == "none"
    assert result.signal is None
    assert result.remaining_cents is None
    assert result.ceiling_cents == 10000
    assert result.spent_cents == 10500
