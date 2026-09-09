import json
import shutil
import sqlite3
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.cards import store
from app.cards import typed as cards_typed
from app.cards.catalog import ACTION, BY_NAME, CLEAR_ACTION, CLOSING, DUE, FIELDS, LIMIT, RATE
from app.db import connect
from app.debts.ladder import ladder, rebuild, set_rate, without_rate
from app.financings import store as financings_store
from app.main import create_app
from app.migrate import SQL_FOLDER
from app.migrations.runner import apply_migrations
from app.settings import typed as settings_typed
from app.settings.typed import InvalidValueError

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

BEFORE = "013"


def _partial_folder(tmp_path, before: str):
    folder = tmp_path / "sql"
    folder.mkdir()
    for path in sorted(SQL_FOLDER.glob("*.sql")):
        if path.stem.split("_", 1)[0] < before:
            shutil.copy(path, folder / path.name)
    return folder


def _accounts(conn, *rows):
    conn.executemany(
        "INSERT INTO accounts (id, name, type, balance_cents) VALUES (?, ?, ?, ?)", rows
    )
    conn.commit()


def test_the_catalogue_exports_the_four_fields_in_order():
    assert [field["name"] for field in FIELDS] == [LIMIT, RATE, CLOSING, DUE]
    assert [field["column"] for field in FIELDS] == [
        "limit_cents",
        "monthly_rate_bp",
        "closing_day",
        "due_day",
    ]
    assert [field["label"] for field in FIELDS] == [
        "Limite",
        "Taxa mensal",
        "Dia do fechamento",
        "Dia do vencimento",
    ]
    for field in FIELDS:
        assert {"column", "label", "unit"} <= set(field)
    assert BY_NAME[LIMIT]["column"] == "limit_cents"


def test_the_typed_module_reuses_the_settings_grammar_without_redefining_it():
    assert cards_typed.parse_money is settings_typed.parse_money
    assert cards_typed.parse_rate is settings_typed.parse_rate
    assert cards_typed.parse_day("") is None
    assert cards_typed.parse_day("15") == 15
    with pytest.raises(InvalidValueError):
        cards_typed.parse_day("32")
    with pytest.raises(InvalidValueError):
        cards_typed.parse_day("3,5")


def test_the_store_module_exports_reconcile_read_and_write():
    assert callable(store.reconcile)
    assert callable(store.read)
    assert callable(store.write)


def test_the_cards_table_has_the_owner_fields_with_the_right_shape(tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    apply_migrations(conn, SQL_FOLDER)

    info = [dict(row) for row in conn.execute("PRAGMA table_info('cards')")]
    assert [row["name"] for row in info] == [
        "account_id",
        "limit_cents",
        "monthly_rate_bp",
        "closing_day",
        "due_day",
    ]
    assert info[0]["pk"] == 1
    assert all(row["notnull"] == 0 for row in info[1:])

    foreign_keys = [dict(row) for row in conn.execute("PRAGMA foreign_key_list('cards')")]
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["table"] == "accounts"
    conn.close()


def test_no_other_migration_file_creates_a_table_named_cards():
    creators = [
        path.name
        for path in SQL_FOLDER.glob("*.sql")
        if path.name != "013_cards.sql" and "CREATE TABLE cards" in path.read_text(encoding="utf-8")
    ]
    assert creators == []


def test_the_migration_moves_a_typed_rate_from_debts_to_cards(tmp_path):
    folder = _partial_folder(tmp_path, BEFORE)
    conn = connect(str(tmp_path / "dash.sqlite"))
    apply_migrations(conn, folder)
    _accounts(
        conn,
        ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462),
        ("acc-corrente", "Conta corrente", "BANK", -100000),
    )
    conn.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source, account_id) "
        "VALUES ('card', 'Cartão Azul', -1674462, 900, 'tests', 'acc-cartao-1')"
    )
    conn.commit()

    applied = apply_migrations(conn, SQL_FOLDER)

    # Reason: this equality freezes the whole migration list — it passes while
    # 013 is the last one and fails the next item that adds its own, for a
    # reason that is not its fault.
    assert "013_cards.sql" in applied
    assert [name for name in applied if name.split("_", 1)[0] < BEFORE] == []
    assert [
        tuple(row) for row in conn.execute("SELECT account_id, monthly_rate_bp FROM cards")
    ] == [("acc-cartao-1", 900)]
    assert (
        conn.execute("SELECT monthly_rate_bp FROM debts WHERE name = 'Cartão Azul'").fetchone()[0]
        is None
    )
    conn.close()


def test_every_credit_account_gets_a_card_and_keeps_it_through_a_reload(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))
    rebuild(taxonomy_conn)
    store.write(taxonomy_conn, "acc-cartao-1", LIMIT, "12.000,00")
    store.write(taxonomy_conn, "acc-cartao-1", RATE, "12,5")
    store.write(taxonomy_conn, "acc-cartao-1", CLOSING, "3")
    store.write(taxonomy_conn, "acc-cartao-1", DUE, "10")

    _accounts(taxonomy_conn, ("acc-cartao-2", "Cartão Roxo", "CREDIT", -32100))
    rebuild(taxonomy_conn)

    ids = [
        row[0] for row in taxonomy_conn.execute("SELECT account_id FROM cards ORDER BY account_id")
    ]
    assert ids == ["acc-cartao-1", "acc-cartao-2"]
    row = taxonomy_conn.execute(
        "SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards "
        "WHERE account_id = 'acc-cartao-1'"
    ).fetchone()
    assert tuple(row) == (1200000, 1250, 3, 10)


def test_the_ladder_reads_the_cards_rate_and_only_erase_clears_it_back_to_without_rate(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    _accounts(
        taxonomy_conn,
        ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462),
        ("acc-corrente", "Conta corrente", "BANK", -100000),
    )
    rebuild(taxonomy_conn)
    checking_id = taxonomy_conn.execute("SELECT id FROM debts WHERE kind = 'overdraft'").fetchone()[
        0
    ]
    set_rate(taxonomy_conn, checking_id, "3,52")

    store.write(taxonomy_conn, "acc-cartao-1", RATE, "12,5")
    steps = ladder(taxonomy_conn)

    assert [step["name"] for step in steps] == ["Cartão Azul", "Conta corrente"]
    assert [step["monthly_rate_bp"] for step in steps] == [1250, 352]
    assert without_rate(taxonomy_conn) == []

    # Reason: set_rate reuses the cards writer, and a blank rate through it
    # must obey the same rule as every other card field — RF-01, not a hidden
    # clear.
    set_rate(taxonomy_conn, checking_id, "3,52")
    store.write(taxonomy_conn, "acc-cartao-1", RATE, "")
    steps = ladder(taxonomy_conn)

    assert [step["name"] for step in steps] == ["Cartão Azul", "Conta corrente"]
    assert [step["monthly_rate_bp"] for step in steps] == [1250, 352]
    assert without_rate(taxonomy_conn) == []

    store.erase(taxonomy_conn, "acc-cartao-1", RATE)
    steps = ladder(taxonomy_conn)
    missing = without_rate(taxonomy_conn)

    assert [step["name"] for step in steps] == ["Conta corrente"]
    assert [step["name"] for step in missing] == ["Cartão Azul"]


def test_set_rate_on_a_card_step_writes_to_cards_not_debts(taxonomy_conn, tmp_path, monkeypatch):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))
    rebuild(taxonomy_conn)
    identifier = taxonomy_conn.execute("SELECT id FROM debts WHERE kind = 'card'").fetchone()[0]

    set_rate(taxonomy_conn, identifier, "12,5")

    assert (
        taxonomy_conn.execute(
            "SELECT monthly_rate_bp FROM cards WHERE account_id = 'acc-cartao-1'"
        ).fetchone()[0]
        == 1250
    )
    assert (
        taxonomy_conn.execute(
            "SELECT monthly_rate_bp FROM debts WHERE id = ?", (identifier,)
        ).fetchone()[0]
        is None
    )


def test_a_card_step_without_an_account_keeps_reading_its_rate_from_debts(taxonomy_conn):
    taxonomy_conn.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source) "
        "VALUES ('card', 'Cartao solto', -500000, 900, 'tests')"
    )
    taxonomy_conn.commit()

    steps = ladder(taxonomy_conn)

    assert [(step["name"], step["monthly_rate_bp"]) for step in steps] == [("Cartao solto", 900)]


def test_an_account_that_stops_being_a_card_does_not_inherit_the_dead_cards_rate(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    _accounts(taxonomy_conn, ("acc-x", "Conta X", "CREDIT", -125000))
    rebuild(taxonomy_conn)
    store.write(taxonomy_conn, "acc-x", RATE, "12,5")

    taxonomy_conn.execute("UPDATE accounts SET type = 'BANK' WHERE id = 'acc-x'")
    taxonomy_conn.commit()
    rebuild(taxonomy_conn)

    every_step = {
        step["account_id"]: step for step in ladder(taxonomy_conn) + without_rate(taxonomy_conn)
    }
    assert every_step["acc-x"]["kind"] == "overdraft"
    assert every_step["acc-x"]["monthly_rate_bp"] is None

    overdraft_id = [step for step in without_rate(taxonomy_conn) if step["account_id"] == "acc-x"][
        0
    ]["id"]
    set_rate(taxonomy_conn, overdraft_id, "3,52")

    updated = [step for step in ladder(taxonomy_conn) if step["account_id"] == "acc-x"][0]
    assert updated["monthly_rate_bp"] == 352


def test_the_vehicle_and_checking_steps_are_unaffected_when_there_is_no_card(
    taxonomy_conn, tmp_path, monkeypatch
):
    folder = tmp_path / "manual"
    folder.mkdir()
    (folder / financings_store.VEHICLE_FILE).write_text(
        json.dumps(
            {
                "prazo_meses": 60,
                "juros_efetivo_mensal_pct": 1.63,
                "valor_parcela": 1235.33,
                "primeiro_vencimento": "2025-06-11",
            }
        )
    )
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(folder))
    _accounts(taxonomy_conn, ("acc-corrente", "Conta corrente", "BANK", -100000))
    rebuild(taxonomy_conn, today=date(2026, 9, 5))
    checking_id = taxonomy_conn.execute("SELECT id FROM debts WHERE kind = 'overdraft'").fetchone()[
        0
    ]
    set_rate(taxonomy_conn, checking_id, "3,52")

    rebuild(taxonomy_conn, today=date(2026, 9, 5))

    steps = {step["kind"]: step for step in ladder(taxonomy_conn)}
    assert steps["overdraft"]["monthly_rate_bp"] == 352
    assert steps["vehicle"]["monthly_rate_bp"] == 163
    assert steps["vehicle"]["term_months"] == 45
    assert steps["vehicle"]["balance_cents"] == -3917636


def test_read_lists_credit_accounts_with_the_four_fields_in_catalogue_order(taxonomy_conn):
    taxonomy_conn.execute(
        "INSERT INTO accounts (id, name, type, institution, balance_cents) VALUES "
        "('acc-cartao-1', 'Cartão Azul', 'CREDIT', 'Banco X', -1674462), "
        "('acc-corrente', 'Conta corrente', 'BANK', 'Banco X', -100000)"
    )
    taxonomy_conn.commit()
    store.reconcile(taxonomy_conn)
    taxonomy_conn.commit()

    cards = store.read(taxonomy_conn)

    assert [card["account_id"] for card in cards] == ["acc-cartao-1"]
    assert [field["name"] for field in cards[0]["fields"]] == [LIMIT, RATE, CLOSING, DUE]
    assert all(field["value"] is None for field in cards[0]["fields"])


def test_write_refuses_an_unknown_field_name(taxonomy_conn):
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))

    with pytest.raises(InvalidValueError) as refusal:
        store.write(taxonomy_conn, "acc-cartao-1", "bandeira", "roxo")

    assert "bandeira" in str(refusal.value)


def test_write_refuses_an_account_that_does_not_exist(taxonomy_conn):
    with pytest.raises(InvalidValueError) as refusal:
        store.write(taxonomy_conn, "acc-inexistente", LIMIT, "12.000,00")

    assert "acc-inexistente" in str(refusal.value)


def test_write_refuses_an_account_that_is_not_a_credit_card(taxonomy_conn):
    _accounts(taxonomy_conn, ("acc-corrente", "Conta corrente", "BANK", -100000))

    with pytest.raises(InvalidValueError) as not_found:
        store.write(taxonomy_conn, "acc-inexistente", LIMIT, "12.000,00")
    with pytest.raises(InvalidValueError) as wrong_type:
        store.write(taxonomy_conn, "acc-corrente", LIMIT, "12.000,00")

    # Reason: same refusal for "no such account" and "account exists but is
    # not a credit card" — the owner never learns that acc-corrente exists at
    # all.
    assert str(wrong_type.value) == str(not_found.value).replace("acc-inexistente", "acc-corrente")
    assert (
        taxonomy_conn.execute(
            "SELECT COUNT(*) FROM cards WHERE account_id = 'acc-corrente'"
        ).fetchone()[0]
        == 0
    )


def test_read_never_shows_a_row_forged_for_a_non_credit_account(taxonomy_conn):
    _accounts(taxonomy_conn, ("acc-corrente", "Conta corrente", "BANK", -100000))
    # Reason: stands in for the pre-fix bug — a row that reached `cards` for an
    # account that is not of type CREDIT, by whatever path. The join in `read`
    # is the last line of defence, independent of what let the row in.
    taxonomy_conn.execute(
        "INSERT INTO cards (account_id, limit_cents) VALUES ('acc-corrente', 500000)"
    )
    taxonomy_conn.commit()

    cards = store.read(taxonomy_conn)

    assert [card["account_id"] for card in cards] == []


def test_the_four_fields_are_written_and_bad_grammar_is_refused_without_writing(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))
    rebuild(taxonomy_conn)

    store.write(taxonomy_conn, "acc-cartao-1", LIMIT, "12.000,00")
    store.write(taxonomy_conn, "acc-cartao-1", RATE, "12,5")
    store.write(taxonomy_conn, "acc-cartao-1", CLOSING, "3")
    store.write(taxonomy_conn, "acc-cartao-1", DUE, "10")

    row = taxonomy_conn.execute(
        "SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards"
    ).fetchone()
    assert tuple(row) == (1200000, 1250, 3, 10)

    bad = (
        (LIMIT, "5000.00", "Escreva na forma 1.234,56"),
        (RATE, "200", "Use de 0 a 100% ao mês"),
        (CLOSING, "32", "Use um dia do mês, de 1 a 31"),
        (DUE, "3,5", "Use um dia do mês, de 1 a 31"),
    )
    for field, typed, message in bad:
        with pytest.raises(InvalidValueError) as refusal:
            store.write(taxonomy_conn, "acc-cartao-1", field, typed)
        assert typed in str(refusal.value)
        assert message in str(refusal.value)

    row = taxonomy_conn.execute(
        "SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards"
    ).fetchone()
    assert tuple(row) == (1200000, 1250, 3, 10)


def test_the_primary_key_refuses_a_null_account_id(taxonomy_conn):
    with pytest.raises(sqlite3.IntegrityError):
        taxonomy_conn.execute("INSERT INTO cards (account_id, limit_cents) VALUES (NULL, 100)")


def test_the_check_constraint_refuses_a_day_out_of_range_by_sql(taxonomy_conn):
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))

    with pytest.raises(sqlite3.IntegrityError):
        taxonomy_conn.execute(
            "INSERT INTO cards (account_id, closing_day) VALUES ('acc-cartao-1', 32)"
        )


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    app = create_app()
    connection = connect()
    seed_user(connection, LOGIN, PASSWORD)
    _accounts(connection, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))
    rebuild(connection)
    connection.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def test_the_rate_written_through_dividas_lands_in_cards_and_the_simulation_sees_it(
    client, tmp_path
):
    conn = connect(str(tmp_path / "dash.sqlite"))
    identifier = conn.execute("SELECT id FROM debts WHERE kind = 'card'").fetchone()[0]
    conn.close()

    written = client.post("/dividas/taxa", data={"degrau": str(identifier), "taxa": "12,5"})
    assert written.status_code == 200

    conn = connect(str(tmp_path / "dash.sqlite"))
    assert (
        conn.execute(
            "SELECT monthly_rate_bp FROM cards WHERE account_id = 'acc-cartao-1'"
        ).fetchone()[0]
        == 1250
    )
    assert (
        conn.execute("SELECT monthly_rate_bp FROM debts WHERE id = ?", (identifier,)).fetchone()[0]
        is None
    )
    conn.close()

    screen = client.get("/dividas").text
    escada = screen.split('id="escada"', 1)[1].split("</section>", 1)[0]
    assert 'data-taxa="1250"' in escada
    missing_section = (
        screen.split('id="sem-taxa"', 1)[1].split("</section>", 1)[0]
        if 'id="sem-taxa"' in screen
        else ""
    )
    assert f'data-degrau="{identifier}"' not in missing_section

    simulated = client.post(
        "/dividas/simular", data={"degrau": str(identifier), "aporte": "1.000,00"}
    )
    assert simulated.status_code == 200
    assert "Informe a taxa primeiro." not in simulated.text


def test_write_returns_a_value_and_a_changed_flag_for_a_grammatically_valid_input(taxonomy_conn):
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))

    value, changed = store.write(taxonomy_conn, "acc-cartao-1", LIMIT, "12.000,00")

    assert (value, changed) == (1200000, True)


def test_write_with_a_blank_typed_value_reports_unchanged_and_touches_nothing_vazio(
    taxonomy_conn,
):
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))
    store.write(taxonomy_conn, "acc-cartao-1", LIMIT, "12.000,00")

    value, changed = store.write(taxonomy_conn, "acc-cartao-1", LIMIT, "")

    assert (value, changed) == (None, False)
    assert (
        taxonomy_conn.execute(
            "SELECT limit_cents FROM cards WHERE account_id = 'acc-cartao-1'"
        ).fetchone()[0]
        == 1200000
    )


def test_write_with_only_whitespace_is_treated_the_same_as_blank_vazio(taxonomy_conn):
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))
    store.write(taxonomy_conn, "acc-cartao-1", DUE, "10")

    value, changed = store.write(taxonomy_conn, "acc-cartao-1", DUE, "   ")

    assert (value, changed) == (None, False)
    assert (
        taxonomy_conn.execute(
            "SELECT due_day FROM cards WHERE account_id = 'acc-cartao-1'"
        ).fetchone()[0]
        == 10
    )


def test_a_blank_write_still_refuses_an_unknown_account_before_reporting_unchanged_vazio(
    taxonomy_conn,
):
    with pytest.raises(InvalidValueError) as refusal:
        store.write(taxonomy_conn, "acc-inexistente", LIMIT, "")

    assert "acc-inexistente" in str(refusal.value)


def test_erase_clears_only_the_named_field_and_reports_it_apagar(taxonomy_conn):
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))
    store.write(taxonomy_conn, "acc-cartao-1", LIMIT, "12.000,00")
    store.write(taxonomy_conn, "acc-cartao-1", RATE, "12,5")
    store.write(taxonomy_conn, "acc-cartao-1", CLOSING, "3")
    store.write(taxonomy_conn, "acc-cartao-1", DUE, "10")

    item = store.erase(taxonomy_conn, "acc-cartao-1", RATE)

    assert item["name"] == RATE
    row = taxonomy_conn.execute(
        "SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards"
    ).fetchone()
    assert tuple(row) == (1200000, None, 3, 10)


def test_erase_refuses_an_unknown_field_or_account_apagar(taxonomy_conn):
    _accounts(taxonomy_conn, ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462))

    with pytest.raises(InvalidValueError):
        store.erase(taxonomy_conn, "acc-cartao-1", "bandeira")
    with pytest.raises(InvalidValueError):
        store.erase(taxonomy_conn, "acc-inexistente", LIMIT)


_TYPED = {
    LIMIT: ("12.000,00", 1200000, "15.000,00", 1500000),
    RATE: ("12,5", 1250, "9,9", 990),
    CLOSING: ("3", 3, "20", 20),
    DUE: ("10", 10, "25", 25),
}


@pytest.mark.parametrize("field", [LIMIT, RATE, CLOSING, DUE])
def test_a_blank_post_leaves_the_field_unchanged_and_a_new_value_still_overwrites_it_vazio(
    client, tmp_path, field
):
    first_typed, first_value, second_typed, second_value = _TYPED[field]
    column = BY_NAME[field]["column"]

    saved = client.post(
        ACTION, data={"cartao": "acc-cartao-1", "campo": field, "valor": first_typed}
    )
    assert saved.status_code == 200

    blank = client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": field, "valor": ""})
    assert blank.status_code == 200
    conn = connect(str(tmp_path / "dash.sqlite"))
    try:
        assert (
            conn.execute(
                f"SELECT {column} FROM cards WHERE account_id = 'acc-cartao-1'"
            ).fetchone()[0]
            == first_value
        )
    finally:
        conn.close()

    written = client.post(
        ACTION, data={"cartao": "acc-cartao-1", "campo": field, "valor": second_typed}
    )
    assert written.status_code == 200
    conn = connect(str(tmp_path / "dash.sqlite"))
    try:
        assert (
            conn.execute(
                f"SELECT {column} FROM cards WHERE account_id = 'acc-cartao-1'"
            ).fetchone()[0]
            == second_value
        )
    finally:
        conn.close()


def test_the_explicit_gesture_apagar_clears_only_the_field_it_names(client, tmp_path):
    for field, typed in _TYPED.items():
        client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": field, "valor": typed[0]})

    erased = client.post(CLEAR_ACTION, data={"cartao": "acc-cartao-1", "campo": CLOSING})

    assert erased.status_code == 200
    conn = connect(str(tmp_path / "dash.sqlite"))
    try:
        row = conn.execute(
            "SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards "
            "WHERE account_id = 'acc-cartao-1'"
        ).fetchone()
    finally:
        conn.close()
    assert tuple(row) == (1200000, 1250, None, 10)


def test_the_response_names_the_field_that_changed_instead_of_a_bare_salvo(client, tmp_path):
    client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": CLOSING, "valor": "3"})
    client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": DUE, "valor": "10"})

    changed = client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": CLOSING, "valor": "20"})

    assert changed.status_code == 200
    assert "Dia do fechamento" in changed.text
    assert BY_NAME[CLOSING]["label"] + " — valor salvo: 20." in changed.text
    assert ">Salvo.<" not in changed.text


def test_the_response_says_nothing_changed_when_the_field_arrives_blank(client, tmp_path):
    client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": CLOSING, "valor": "3"})

    untouched = client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": CLOSING, "valor": ""})

    assert untouched.status_code == 200
    assert "Dia do fechamento — em branco, valor mantido." in untouched.text


def test_the_response_names_the_field_the_erase_gesture_cleared(client, tmp_path):
    client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": LIMIT, "valor": "12.000,00"})

    erased = client.post(CLEAR_ACTION, data={"cartao": "acc-cartao-1", "campo": LIMIT})

    assert erased.status_code == 200
    assert "Limite — valor apagado." in erased.text
