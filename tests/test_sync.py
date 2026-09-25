import time
from datetime import date, timedelta, timezone
from pathlib import Path

import pytest

from app.config import PLUGGY_CREDENTIALS
from app.ingest.loader import ingest
from app.ingest.trigger import COMMAND, SCREEN
from app.sync import (
    MissingCredentialError,
    days_since,
    finished_on,
    last_runs,
    readable,
    synchronise,
)
from tests.conftest import ACCOUNT, transaction

REFERENCE = date(2026, 9, 5)
SYNC_DATA = Path(__file__).resolve().parent / "data"


def _point_the_load_step_at_the_fixture(monkeypatch):
    monkeypatch.setenv("DASH_TRANSACTIONS_PATH", str(SYNC_DATA / "sync_transactions.json"))
    monkeypatch.setenv("DASH_ACCOUNTS_GLOB", str(SYNC_DATA / "sync_accounts.json"))


def rows(conn):
    return conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]


def runs(conn):
    return [
        (row["transactions_count"], row["transactions_present"], row["status"])
        for row in conn.execute("SELECT * FROM sync_runs ORDER BY id")
    ]


def load_twice(conn, entries):
    for _ in range(2):
        ingest(conn, transactions=entries, accounts=[ACCOUNT], source="tests", trigger=COMMAND)
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

    assert (
        conn.execute("SELECT status FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()[0] == "ok"
    )


def test_a_run_that_inserts_new_rows_counts_only_the_new_ones(taxonomy_conn):
    ingest(
        taxonomy_conn,
        transactions=[transaction("t-1", "2026-08-10", -10.0)],
        accounts=[ACCOUNT],
        source="tests",
        trigger=COMMAND,
    )
    ingest(
        taxonomy_conn,
        transactions=[
            transaction("t-1", "2026-08-10", -10.0),
            transaction("t-2", "2026-08-11", -20.0),
        ],
        accounts=[ACCOUNT],
        source="tests",
        trigger=COMMAND,
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
        synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)

    assert PLUGGY_CREDENTIALS[0] in str(refusal.value)
    assert len(runs(taxonomy_conn)) == before


def test_the_last_success_and_the_last_attempt_are_read_apart(taxonomy_conn):
    ingest(
        taxonomy_conn,
        transactions=[transaction("t-1", "2026-08-10", -10.0)],
        accounts=[ACCOUNT],
        source="tests",
        trigger=COMMAND,
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
        trigger=COMMAND,
    )
    succeeded = last_runs(taxonomy_conn)["succeeded"]

    assert days_since(succeeded, REFERENCE) is not None
    assert days_since(None, REFERENCE) is None


def test_a_write_that_blows_up_still_leaves_a_failed_run(taxonomy_conn):
    before = rows(taxonomy_conn)
    result = ingest(
        taxonomy_conn,
        transactions=[transaction("t-orfa", "2026-08-10", -10.0, conta_id="nao-existe")],
        accounts=[ACCOUNT],
        source="tests",
        trigger=COMMAND,
    )

    assert result.status == "failed"
    assert rows(taxonomy_conn) == before
    assert runs(taxonomy_conn)[-1][2] == "failed"
    assert "erro de escrita" in _message(taxonomy_conn)


def test_a_foreign_key_restricao_is_named_and_not_just_the_exception_class(taxonomy_conn):
    ingest(
        taxonomy_conn,
        transactions=[transaction("t-orfa", "2026-08-10", -10.0, conta_id="nao-existe")],
        accounts=[ACCOUNT],
        source="tests",
        trigger=COMMAND,
    )

    message = _message(taxonomy_conn)
    assert "FOREIGN KEY constraint failed" in message
    assert message != "erro de escrita: IntegrityError"


def _message(conn):
    return conn.execute("SELECT message FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()[0]


def test_the_technical_message_is_said_in_portuguese():
    assert "não conseguiu ler" in readable("rejected=1")
    assert "não chegaram à tabela" in readable(
        "transactions accepted=1942 present=1900 accounts accepted=12 present=12"
    )
    assert "recusada (IntegrityError)" in readable("erro de escrita: IntegrityError")
    assert readable(None) == "sem detalhe registrado."


def test_a_run_stamped_in_utc_is_read_in_the_local_zone():
    stamped = {"finished_at": "2026-09-07T02:00:00+00:00"}
    minus_three = timezone(timedelta(hours=-3))

    assert finished_on(stamped).astimezone(minus_three).date() == date(2026, 9, 6)


def test_the_age_is_counted_over_the_local_date(monkeypatch, request):
    stamped = {"finished_at": "2026-09-07T02:00:00+00:00"}
    monkeypatch.setenv("TZ", "America/Sao_Paulo")
    time.tzset()
    # Reason: the env var is restored by monkeypatch, but the process zone is
    # not until tzset is called again — without this the zone leaks into
    # every test that runs after this one in the same worker.
    request.addfinalizer(time.tzset)

    assert days_since(stamped, date(2026, 9, 6)) == 0
    assert days_since(stamped, date(2026, 9, 8)) == 2


def test_a_source_that_cannot_be_read_records_a_failed_run(taxonomy_conn, monkeypatch):
    monkeypatch.setenv("DASH_TRANSACTIONS_PATH", "/tmp/nao-existe-006.json")
    before = len(runs(taxonomy_conn))

    outcome = synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)

    assert outcome.status == "failed"
    assert len(runs(taxonomy_conn)) == before + 1
    assert "não pôde ser lido" in readable(_message(taxonomy_conn))


def test_a_failure_after_the_load_demotes_the_run_instead_of_claiming_success(
    taxonomy_conn, monkeypatch
):
    import app.sync as sync

    def explode(conn, today):
        raise RuntimeError("a reclassificação quebrou")

    _point_the_load_step_at_the_fixture(monkeypatch)
    monkeypatch.setattr(sync, "_after", explode)
    outcome = synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)

    assert outcome.status == "failed"
    assert runs(taxonomy_conn)[-1][2] == "failed"
    assert "pós-carga falhou" in _message(taxonomy_conn)
    assert "não foram recalculados" in readable(_message(taxonomy_conn))


def test_the_demotion_names_its_own_row_and_not_the_largest_id(taxonomy_conn, monkeypatch):
    import app.sync as sync

    def explode_after_someone_else_writes(conn, today):
        conn.execute(
            "INSERT INTO sync_runs (started_at, finished_at, source, status, message) "
            "VALUES ('2026-09-05T00:00:00', '2026-09-05T00:00:01', 'outro', 'ok', 'alheia')"
        )
        conn.commit()
        raise RuntimeError("quebrou depois")

    _point_the_load_step_at_the_fixture(monkeypatch)
    monkeypatch.setattr(sync, "_after", explode_after_someone_else_writes)
    synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)
    found = [
        (row["source"], row["status"])
        for row in taxonomy_conn.execute("SELECT * FROM sync_runs ORDER BY id")
    ]

    assert found[-1] == ("outro", "ok")
    assert found[-2][1] == "failed"


def test_the_message_does_not_promise_the_previous_state():
    said = readable("pós-carga falhou: RuntimeError")

    assert "Parte das telas pode estar desatualizada" in said
    assert "mostram o estado anterior" not in said


def test_with_the_pluggy_source_a_fetch_failure_records_a_failed_run(taxonomy_conn, monkeypatch):
    import app.sync as sync

    monkeypatch.setenv("DASH_SYNC_SOURCE", "pluggy")
    monkeypatch.setenv("PLUGGY_CLIENT_ID", "id-falso")
    monkeypatch.setenv("PLUGGY_CLIENT_SECRET", "segredo-falso")

    def explode(config, item_ids):
        raise sync.PluggyFetchError(
            "pluggy: a Pluggy não respondeu; verifique a conexão com a internet e tente de novo."
        )

    monkeypatch.setattr(sync, "fetch_from_pluggy", explode)
    before = len(runs(taxonomy_conn))

    outcome = synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)

    assert outcome.status == "failed"
    assert len(runs(taxonomy_conn)) == before + 1
    row = taxonomy_conn.execute("SELECT source FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()
    assert row["source"] == "pluggy"
    assert readable(_message(taxonomy_conn)).startswith("a Pluggy não respondeu")


def test_the_pluggy_prefix_is_removed_by_readable():
    assert readable("pluggy: x") == "x"


def test_synchronise_ends_with_the_payee_filled_on_every_row_with_a_description(
    taxonomy_conn, monkeypatch
):
    _point_the_load_step_at_the_fixture(monkeypatch)

    synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)

    assert rows(taxonomy_conn) > 0
    missing = taxonomy_conn.execute(
        "SELECT count(*) FROM transactions "
        "WHERE description IS NOT NULL AND (payee IS NULL OR payee = '')"
    ).fetchone()[0]
    assert missing == 0


def _trigger(conn):
    return conn.execute("SELECT triggered_by FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()[0]


def test_a_sync_that_loads_records_who_asked_for_it(taxonomy_conn, monkeypatch):
    _point_the_load_step_at_the_fixture(monkeypatch)

    synchronise(taxonomy_conn, trigger=SCREEN, today=REFERENCE)

    assert rows(taxonomy_conn) > 0
    assert _trigger(taxonomy_conn) == "screen"


def test_an_unreadable_source_records_who_asked_for_the_failed_run(taxonomy_conn, monkeypatch):
    monkeypatch.setenv("DASH_TRANSACTIONS_PATH", "/tmp/nao-existe-018.json")

    synchronise(taxonomy_conn, trigger=SCREEN, today=REFERENCE)

    assert _trigger(taxonomy_conn) == "screen"


def test_a_pluggy_failure_records_who_asked_for_the_failed_run(taxonomy_conn, monkeypatch):
    import app.sync as sync

    monkeypatch.setenv("DASH_SYNC_SOURCE", "pluggy")
    monkeypatch.setenv("PLUGGY_CLIENT_ID", "id-falso")
    monkeypatch.setenv("PLUGGY_CLIENT_SECRET", "segredo-falso")

    def explode(config, item_ids):
        raise sync.PluggyFetchError("pluggy: fora do ar")

    monkeypatch.setattr(sync, "fetch_from_pluggy", explode)

    synchronise(taxonomy_conn, trigger=COMMAND, today=REFERENCE)

    assert _trigger(taxonomy_conn) == "command"


def test_the_daily_command_says_it_was_a_command(monkeypatch):
    import app.sync as sync

    asked = {}

    def record(conn, *, trigger, today=None):
        asked["trigger"] = trigger
        return sync.SyncOutcome(status="ok", message="", transactions=0, accounts=0)

    class Closable:
        def close(self):
            return None

    monkeypatch.setattr(sync, "synchronise", record)
    monkeypatch.setattr(sync, "connect", lambda: Closable())

    assert sync.main() == 0
    assert asked["trigger"] == "command"
