import shutil
import sqlite3
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.migrate import SQL_FOLDER
from app.migrations.runner import apply_migrations
from app.settings import store
from app.settings.catalog import CARD_RATE, MEDIAN, RESERVE, SETTLEMENT, TRANSPORT
from app.settings.typed import MAX_DIGITS, InvalidValueError, parse_money, parse_months, parse_rate

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

TODAY = date(2026, 9, 5)

BEFORE = "010"
SETTLEMENT_CENTS = 3500000
TRANSPORT_CENTS = 45000
CAPTURED = "2026-09-01T10:00:00"

NOT_A_NUMBER = ("inf", "nan", "1e308")


def _base(tmp_path, *, rows: list[tuple[str, int, str]]) -> sqlite3.Connection:
    # Reason: the migration is exercised over a base that already has data,
    # because ALTER TABLE ADD COLUMN NOT NULL passes on an empty table and
    # fails on a table with a row — the empty case would prove nothing about
    # the real base.
    folder = tmp_path / "sql"
    folder.mkdir()
    for path in sorted(SQL_FOLDER.glob("*.sql")):
        if path.stem.split("_", 1)[0] < BEFORE:
            shutil.copy(path, folder / path.name)
    conn = connect(str(tmp_path / "dash.sqlite"))
    apply_migrations(conn, folder)
    for name, value, updated_at in rows:
        conn.execute(
            "INSERT INTO plan_parameters (name, value_cents, updated_at) VALUES (?, ?, ?)",
            (name, value, updated_at),
        )
    conn.commit()
    return conn


def _facts(conn: sqlite3.Connection) -> dict[str, dict]:
    return {row["name"]: dict(row) for row in conn.execute("SELECT * FROM plan_facts")}


def test_the_migration_survives_a_base_that_already_has_a_fact(tmp_path):
    conn = _base(tmp_path, rows=[("quitacao", SETTLEMENT_CENTS, CAPTURED)])
    conn.execute(
        "INSERT INTO plan_facts (name, label, value_cents, unit, source, captured_at) "
        "VALUES ('taxa-observada', 'Taxa observada', 100, 'centavos', 'humano', '2026-08-01')"
    )
    conn.commit()

    assert apply_migrations(conn, SQL_FOLDER)[0] == "010_settings.sql"

    found = _facts(conn)
    assert found["taxa-observada"]["kind"] == "fato"
    assert found["taxa-observada"]["value"] == 100
    conn.close()


def test_the_old_name_is_converted_to_the_canonical_one(tmp_path):
    conn = _base(
        tmp_path,
        rows=[("quitacao", SETTLEMENT_CENTS, CAPTURED), ("transporte", TRANSPORT_CENTS, CAPTURED)],
    )
    apply_migrations(conn, SQL_FOLDER)

    found = _facts(conn)
    assert set(found) == {SETTLEMENT, TRANSPORT}
    assert found[SETTLEMENT]["value"] == SETTLEMENT_CENTS
    assert found[SETTLEMENT]["unit"] == "centavos"
    assert found[SETTLEMENT]["source"] == "plan_parameters"
    assert found[SETTLEMENT]["captured_at"] == CAPTURED
    conn.close()


def test_the_richer_row_wins_the_collision(tmp_path):
    conn = _base(tmp_path, rows=[("quitacao", SETTLEMENT_CENTS, CAPTURED)])
    conn.execute(
        "INSERT INTO plan_facts (name, label, value_cents, unit, source, captured_at, valid_until) "
        "VALUES (?, 'Saldo informado no simulador', 111, 'centavos', 'humano', "
        "'2026-08-01', '2026-12-31')",
        (SETTLEMENT,),
    )
    conn.commit()
    apply_migrations(conn, SQL_FOLDER)

    found = _facts(conn)
    assert found[SETTLEMENT]["value"] == 111
    assert found[SETTLEMENT]["valid_until"] == "2026-12-31"
    conn.close()


def test_the_old_table_is_gone(tmp_path):
    conn = _base(tmp_path, rows=[])
    apply_migrations(conn, SQL_FOLDER)

    names = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'plan_%'"
        )
    ]

    assert "plan_parameters" not in names
    assert "plan_facts" in names
    conn.close()


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    connection = connect()
    apply_migrations(connection, SQL_FOLDER)
    yield connection
    connection.close()


def test_a_name_outside_the_catalogue_is_refused_by_name(conn):
    with pytest.raises(InvalidValueError) as refusal:
        store.write(conn, "inexistente", "1.000,00")

    assert "inexistente" in str(refusal.value)
    assert _facts(conn) == {}


def test_the_rate_of_a_card_is_declared_but_never_a_row(conn):
    with pytest.raises(InvalidValueError) as refusal:
        store.write(conn, CARD_RATE, "3,52")

    assert "/dividas" in str(refusal.value)
    assert _facts(conn) == {}


def test_the_refusal_also_names_the_cards_section_now_on_the_same_screen(conn):
    with pytest.raises(InvalidValueError) as refusal:
        store.write(conn, CARD_RATE, "3,52")

    # Reason: the field now also lives in the Cartões section of
    # /configuracao, the very screen answering this refusal — the message may
    # not claim /dividas is the only place, and it borrows the catalogue's own
    # "help" text, which already names both.
    assert "Cartões desta tela" in str(refusal.value)


def test_each_unit_is_read_by_its_own_grammar(conn):
    store.write(conn, SETTLEMENT, "35.000,00")
    store.write(conn, RESERVE, "3")

    found = _facts(conn)
    assert (found[SETTLEMENT]["value"], found[SETTLEMENT]["unit"]) == (3500000, "centavos")
    assert (found[RESERVE]["value"], found[RESERVE]["unit"]) == (3, "meses")
    assert (found[SETTLEMENT]["kind"], found[RESERVE]["kind"]) == ("fato", "meta")


def test_an_absent_value_is_none_and_never_zero(conn):
    assert store.value(conn, SETTLEMENT) is None

    absent = {item["name"]: item for item in store.read(conn, today=TODAY)}[SETTLEMENT]

    assert absent["value"] is None


def test_the_default_of_the_catalogue_is_what_the_panel_uses_meanwhile(conn):
    reading = {item["name"]: item for item in store.read(conn, today=TODAY)}

    assert reading[RESERVE]["default"] == reading[MEDIAN]["default"]
    assert reading[RESERVE]["value"] is None
    assert reading[SETTLEMENT]["default"] is None


def test_a_stale_value_is_marked(conn):
    store.write(conn, SETTLEMENT, "35.000,00", valid_until="2026-08-01")
    fresh = store.write(conn, TRANSPORT, "450,00", valid_until="2026-12-31")

    reading = {item["name"]: item for item in store.read(conn, today=TODAY)}

    assert reading[SETTLEMENT]["stale"] is True
    assert reading[TRANSPORT]["stale"] is False
    assert fresh == 45000


def test_a_write_without_a_validity_keeps_the_one_already_there(conn):
    store.write(conn, SETTLEMENT, "35.000,00", valid_until="2026-12-31")
    store.write(conn, SETTLEMENT, "36.000,00")

    found = _facts(conn)[SETTLEMENT]

    assert (found["value"], found["valid_until"]) == (3600000, "2026-12-31")


def test_the_money_grammar_refuses_what_is_not_written_in_the_brazilian_form():
    for typed in ("5000.00", *NOT_A_NUMBER):
        with pytest.raises(InvalidValueError):
            parse_money(typed, "Saldo")

    assert parse_money("2.500,00") == 250000


def test_the_rate_grammar_takes_the_dot_and_refuses_what_is_out_of_range():
    assert parse_rate("3,52") == parse_rate("3.52%") == 352
    assert parse_rate("") is None

    for typed in ("200", *NOT_A_NUMBER):
        with pytest.raises(InvalidValueError):
            parse_rate(typed)


def test_the_month_grammar_takes_whole_months_only():
    assert parse_months("3") == 3
    assert parse_months("") is None

    for typed in ("3,5", "-1", "0", *NOT_A_NUMBER):
        with pytest.raises(InvalidValueError):
            parse_months(typed)


def test_the_month_grammar_caps_digits_but_still_takes_a_mortgage_term():
    assert parse_months("420") == 420
    assert parse_months("9" * MAX_DIGITS) == int("9" * MAX_DIGITS)

    with pytest.raises(InvalidValueError):
        parse_months("9" * (MAX_DIGITS + 1))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    connection = connect()
    seed_user(connection, LOGIN, PASSWORD)
    # Reason: the payoff field lives inside the car decision, and that block
    # only exists when there is a vehicle debt — without the step the screen
    # renders without the field and the test would prove nothing.
    connection.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, term_months, "
        "payment_cents, source) VALUES ('vehicle', 'CDC do veículo', -3917636, 163, 45, "
        "-123533, 'tests')"
    )
    connection.commit()
    connection.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def test_the_payoff_balance_typed_in_one_screen_is_read_by_the_other(client):
    written = client.post("/dividas/parametro", data={"nome": SETTLEMENT, "valor": "35.000,00"})

    assert written.status_code == 200
    assert "35.000,00" in client.get("/simulador").text
    assert "35.000,00" in client.get("/dividas").text


def test_the_advisor_stops_asking_what_the_owner_answered(client):
    before = client.get("/consultor").text
    client.post("/dividas/parametro", data={"nome": SETTLEMENT, "valor": "35.000,00"})
    after = client.get("/consultor").text

    question = "o saldo de quitação antecipada do CDC do carro"
    assert question in before
    assert question not in after


def test_a_value_the_reader_refuses_answers_400_and_writes_nothing(client):
    refused = client.post("/dividas/parametro", data={"nome": SETTLEMENT, "valor": "5000.00"})

    assert refused.status_code == 400
    assert "5000.00" in refused.text
    conn = connect()
    try:
        assert store.value(conn, SETTLEMENT) is None
    finally:
        conn.close()


def test_a_fact_in_months_is_never_shown_as_money(client):
    client.post("/simulador/fato", data={"nome": RESERVE, "valor": "6", "data": "2026-09-05"})

    screen = client.get("/simulador").text

    assert "6 meses" in screen
    assert "R$ 0,06" not in screen


def test_the_goals_route_refuses_a_reserve_months_that_overflows_sqlite_not_a_500(client):
    refused = client.post("/configuracao", data={"nome": RESERVE, "valor": "9" * 20})

    assert refused.status_code == 400
    assert "algarismos" in refused.text
    conn = connect()
    try:
        assert store.value(conn, RESERVE) is None
    finally:
        conn.close()
