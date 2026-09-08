import sqlite3
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.advisor.gaps import pending
from app.auth.seed import seed_user
from app.cards.catalog import CLOSING, DUE, LIMIT, RATE
from app.db import connect
from app.debts.ladder import ladder, rebuild, set_rate, without_rate
from app.financings import store as financings_store
from app.main import create_app
from app.settings.catalog import CARD_RATE

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

SCREEN = "/configuracao"
ACTION = f"{SCREEN}/cartao"
DEBTS_SCREEN = "/dividas"
DEBTS_RATE = f"{DEBTS_SCREEN}/taxa"

BLUE_CARD = ("acc-cartao-1", "Cartão Azul", "CREDIT", -1674462)
PURPLE_CARD = ("acc-cartao-2", "Cartão Roxo", "CREDIT", -32100)
CHECKING = ("acc-corrente", "Conta corrente", "BANK", -100000)

TODAY = date(2026, 9, 5)


def _accounts(conn: sqlite3.Connection, *rows: tuple) -> None:
    conn.executemany(
        "INSERT INTO accounts (id, name, type, balance_cents) VALUES (?, ?, ?, ?)", rows
    )
    conn.commit()


def _section(html: str, marker: str) -> str:
    return html.split(marker, 1)[1].split("</section>", 1)[0]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", TODAY.isoformat())
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def test_the_screen_lists_credit_accounts_and_not_the_bank_one(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD, PURPLE_CARD, CHECKING)
    rebuild(conn)
    conn.close()

    page = client.get(SCREEN).text

    assert page.count('id="cartoes"') == 1
    assert 'data-cartao="acc-cartao-1"' in page
    assert 'data-cartao="acc-cartao-2"' in page
    assert 'data-cartao="acc-corrente"' not in page
    cartoes = _section(page, 'id="cartoes"')
    for field in (LIMIT, RATE, CLOSING, DUE):
        assert cartoes.count(f'data-campo="{field}"') == 2
    assert cartoes.count('data-valor=""') == 8
    assert page.count('id="fatos"') == 1
    assert page.count('id="metas"') == 1
    assert page.count('id="beneficiarios"') == 1


def test_the_empty_section_invites_instead_of_disappearing(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, CHECKING)
    conn.close()

    page = client.get(SCREEN).text

    assert page.count('id="cartoes"') == 1
    cartoes = _section(page, 'id="cartoes"')
    assert 'class="empty"' in cartoes
    assert "Nenhum cartão na base." in cartoes


def test_writing_the_four_fields_lands_in_the_table_and_the_next_render(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD)
    rebuild(conn)
    conn.close()

    pairs = ((LIMIT, "12.000,00"), (RATE, "12,5"), (CLOSING, "3"), (DUE, "10"))
    responses = [
        client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": campo, "valor": valor})
        for campo, valor in pairs
    ]

    for response in responses:
        assert response.status_code == 200
        assert "Salvo." in response.text

    conn = connect(str(tmp_path / "dash.sqlite"))
    row = conn.execute(
        "SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards "
        "WHERE account_id = 'acc-cartao-1'"
    ).fetchone()
    conn.close()
    assert tuple(row) == (1200000, 1250, 3, 10)

    last = responses[-1].text
    assert 'data-campo="limite" data-valor="1200000"' in last
    assert 'data-campo="taxa" data-valor="1250"' in last
    assert 'data-campo="fechamento" data-valor="3"' in last
    assert 'data-campo="vencimento" data-valor="10"' in last
    assert "R$ 12.000,00" in last
    assert "12,50%" in last


def test_the_section_declares_that_a_blank_field_clears_the_value(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD)
    rebuild(conn)
    conn.close()

    page = client.get(SCREEN).text
    cartoes = _section(page, 'id="cartoes"')

    assert "apaga o valor" in cartoes


def test_clearing_a_written_field_answers_cleared_instead_of_saved(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD)
    rebuild(conn)
    conn.close()

    written = client.post(
        ACTION, data={"cartao": "acc-cartao-1", "campo": LIMIT, "valor": "12.000,00"}
    )
    assert written.status_code == 200
    assert "Salvo." in written.text

    cleared = client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": LIMIT, "valor": ""})
    assert cleared.status_code == 200
    assert "Apagado." in cleared.text
    assert "Salvo." not in cleared.text

    conn = connect(str(tmp_path / "dash.sqlite"))
    value = conn.execute(
        "SELECT limit_cents FROM cards WHERE account_id = 'acc-cartao-1'"
    ).fetchone()[0]
    conn.close()
    assert value is None


def test_bad_grammar_is_refused_with_the_screen_standing_and_writes_nothing(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD)
    rebuild(conn)
    conn.close()

    limit_refused = client.post(
        ACTION, data={"cartao": "acc-cartao-1", "campo": LIMIT, "valor": "5000.00"}
    )
    day_refused = client.post(
        ACTION, data={"cartao": "acc-cartao-1", "campo": CLOSING, "valor": "32"}
    )

    for response in (limit_refused, day_refused):
        assert response.status_code == 400
        assert 'id="recusa"' in response.text
        assert 'id="metas"' in response.text
        assert 'id="beneficiarios"' in response.text
    assert "5000.00" in limit_refused.text
    assert "Escreva na forma 1.234,56" in limit_refused.text
    assert "32" in day_refused.text
    assert "Use um dia do mês, de 1 a 31" in day_refused.text

    conn = connect(str(tmp_path / "dash.sqlite"))
    row = conn.execute(
        "SELECT limit_cents, closing_day FROM cards WHERE account_id = 'acc-cartao-1'"
    ).fetchone()
    conn.close()
    assert tuple(row) == (None, None)


def test_an_unknown_account_or_field_is_refused_naming_what_was_asked(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD)
    rebuild(conn)
    conn.close()

    unknown_account = client.post(
        ACTION, data={"cartao": "acc-inexistente", "campo": LIMIT, "valor": "12.000,00"}
    )
    unknown_field = client.post(
        ACTION, data={"cartao": "acc-cartao-1", "campo": "bandeira", "valor": "roxo"}
    )

    assert unknown_account.status_code == 400
    assert 'id="recusa"' in unknown_account.text
    assert "acc-inexistente" in unknown_account.text
    assert unknown_field.status_code == 400
    assert 'id="recusa"' in unknown_field.text
    assert "bandeira" in unknown_field.text

    conn = connect(str(tmp_path / "dash.sqlite"))
    count = conn.execute("SELECT COUNT(*) FROM cards WHERE limit_cents IS NOT NULL").fetchone()[0]
    conn.close()
    assert count == 0


def test_the_rate_travels_between_configuracao_and_dividas_in_both_directions(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD)
    rebuild(conn)
    identifier = conn.execute("SELECT id FROM debts WHERE kind = 'card'").fetchone()[0]
    conn.close()

    written = client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": RATE, "valor": "12,5"})
    assert written.status_code == 200

    debts_page = client.get(DEBTS_SCREEN).text
    escada = _section(debts_page, 'id="escada"')
    assert 'data-taxa="1250"' in escada

    back = client.post(DEBTS_RATE, data={"degrau": str(identifier), "taxa": "9"})
    assert back.status_code == 200

    config_page = client.get(SCREEN).text
    assert 'data-campo="taxa" data-valor="900"' in config_page


def test_the_write_from_configuracao_is_seen_by_the_ladder_the_phase_1_changed(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD, CHECKING)
    rebuild(conn)
    checking_id = conn.execute("SELECT id FROM debts WHERE kind = 'overdraft'").fetchone()[0]
    set_rate(conn, checking_id, "3,52")
    before_missing = without_rate(conn)
    before_ladder = ladder(conn)
    conn.close()

    assert [step["kind"] for step in before_missing] == ["card"]
    assert [step["kind"] for step in before_ladder] == ["overdraft"]

    written = client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": RATE, "valor": "12,5"})
    assert written.status_code == 200

    conn = connect(str(tmp_path / "dash.sqlite"))
    after_missing = without_rate(conn)
    after_ladder = ladder(conn)
    conn.close()

    assert after_missing == []
    assert [step["kind"] for step in after_ladder] == ["card", "overdraft"]


def test_the_advisor_question_about_the_card_rate_disappears_once_answered(client, tmp_path):
    conn = connect(str(tmp_path / "dash.sqlite"))
    _accounts(conn, BLUE_CARD)
    rebuild(conn)
    before = pending(conn, today=TODAY)
    conn.close()

    assert CARD_RATE in [question["name"] for question in before]

    written = client.post(ACTION, data={"cartao": "acc-cartao-1", "campo": RATE, "valor": "12,5"})
    assert written.status_code == 200

    conn = connect(str(tmp_path / "dash.sqlite"))
    after = pending(conn, today=TODAY)
    conn.close()

    assert CARD_RATE not in [question["name"] for question in after]
