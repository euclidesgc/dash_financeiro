from datetime import date

import pytest

from app.config import PLUGGY_CREDENTIALS
from app.ingest.loader import ingest
from app.sync import MissingCredentialError, days_since, last_runs, synchronise
from tests.conftest import ACCOUNT, transaction

REFERENCE = date(2026, 9, 5)


def rows(conn):
    return conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]


def runs(conn):
    return [
        (row["transactions_count"], row["transactions_present"], row["status"])
        for row in conn.execute("SELECT * FROM sync_runs ORDER BY id")
    ]


def load_twice(conn, entries):
    for _ in range(2):
        ingest(conn, transactions=entries, accounts=[ACCOUNT], source="tests")
    return conn


def test_the_second_load_of_the_same_file_inserts_nothing_and_duplicates_nothing(
    taxonomy_conn,
):
    entries = [transaction(f"t-{index}", "2026-08-10", -10.0) for index in range(3)]
    conn = load_twice(taxonomy_conn, entries)

    assert rows(conn) == 3
    assert runs(conn) == [(3, 3, "ok"), (0, 3, "ok")]


def test_inserting_nothing_is_success_and_not_failure(taxonomy_conn):
    entries = [transaction("t-1", "2026-08-10", -10.0)]
    conn = load_twice(taxonomy_conn, entries)

    assert conn.execute("SELECT status FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()[0] == "ok"


def test_a_run_that_inserts_new_rows_counts_only_the_new_ones(taxonomy_conn):
    ingest(
        taxonomy_conn,
        transactions=[transaction("t-1", "2026-08-10", -10.0)],
        accounts=[ACCOUNT],
        source="tests",
    )
    ingest(
        taxonomy_conn,
        transactions=[
            transaction("t-1", "2026-08-10", -10.0),
            transaction("t-2", "2026-08-11", -20.0),
        ],
        accounts=[ACCOUNT],
        source="tests",
    )

    assert runs(taxonomy_conn)[-1] == (1, 2, "ok")


def test_without_the_pluggy_credentials_the_sync_refuses_and_records_nothing(
    taxonomy_conn, monkeypatch
):
    monkeypatch.setenv("DASH_SYNC_SOURCE", "pluggy")
    for name in PLUGGY_CREDENTIALS:
        monkeypatch.delenv(name, raising=False)
    before = len(runs(taxonomy_conn))

    with pytest.raises(MissingCredentialError) as refusal:
        synchronise(taxonomy_conn, today=REFERENCE)

    assert PLUGGY_CREDENTIALS[0] in str(refusal.value)
    assert len(runs(taxonomy_conn)) == before


def test_the_last_success_and_the_last_attempt_are_read_apart(taxonomy_conn):
    ingest(
        taxonomy_conn,
        transactions=[transaction("t-1", "2026-08-10", -10.0)],
        accounts=[ACCOUNT],
        source="tests",
    )
    taxonomy_conn.execute(
        "INSERT INTO sync_runs (started_at, finished_at, source, status, message) "
        "VALUES ('2026-09-05T10:00:00', '2026-09-05T10:00:01', 'teste', 'failed', 'expirou')"
    )
    taxonomy_conn.commit()
    found = last_runs(taxonomy_conn)

    assert found["latest"]["status"] == "failed"
    assert found["succeeded"]["status"] == "ok"


def test_the_age_of_the_data_is_counted_from_the_last_success(taxonomy_conn):
    ingest(
        taxonomy_conn,
        transactions=[transaction("t-1", "2026-08-10", -10.0)],
        accounts=[ACCOUNT],
        source="tests",
    )
    succeeded = last_runs(taxonomy_conn)["succeeded"]

    assert days_since(succeeded, REFERENCE) is not None
    assert days_since(None, REFERENCE) is None
