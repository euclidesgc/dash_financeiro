import re

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.settings import store
from app.settings.catalog import CATALOG, MEDIAN, RESERVE, SETTLEMENT
from tests.conftest import transaction
from tests.test_plan import MONTHS, REFERENCE, prepare, rent, salary

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

SCREEN = "/configuracao"
OBJECTIVE = f"/objetivo?data={REFERENCE.isoformat()}"

CONFIG_ROW = re.compile(r'data-config="([^"]*)"')
TARGET = re.compile(r'data-alvo="([-0-9]*)"')

# Reason: the base carries six closed months, which is what makes a window of
# twelve a refusal and a window of three a real change. The last month carries
# a second fixed and essential expense: over uniform months the median window
# moves nothing, and a test over uniform months would pass with the window
# ignored.
MONTHS_IN_BASE = 6
HALF = 3
CROWDED = MONTHS[-1]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", REFERENCE.isoformat())
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    extra = transaction(
        "out-extra", f"{CROWDED}-20", -1000.0, descricao="Moradia", categoria="Housing"
    )
    prepare(conn, salary(5000.0) + rent(-1000.0) + [extra])
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def _saved(name: str) -> int | None:
    conn = connect()
    try:
        return store.value(conn, name)
    finally:
        conn.close()


def test_the_screen_lists_the_catalogue_in_two_blocks(client):
    page = client.get(SCREEN).text

    assert page.count('id="fatos"') == 1
    assert page.count('id="metas"') == 1
    assert sorted(set(CONFIG_ROW.findall(page))) == sorted(item["name"] for item in CATALOG)


def test_an_absent_value_says_what_the_panel_uses_meanwhile(client):
    page = client.get(SCREEN).text

    assert "Ausente" in page
    assert "o painel usa 6 meses" in page


def test_the_card_rate_edit_note_does_not_claim_dividas_is_the_only_place(client):
    page = client.get(SCREEN).text
    article = page.split('data-config="taxa-cartao"', 1)[1].split("</article>", 1)[0]

    # Reason: the old prose claimed the card rate was "uma taxa por dívida"
    # edited only at /dividas; the Cartões section on this very screen now
    # edits it too, so the "where" note points back at the help text instead
    # of repeating a claim that would go stale for any other non-value-line
    # entry as well.
    assert "uma taxa por dívida" not in article
    assert "o texto ao lado já explica onde" in article


def test_writing_moves_the_number_in_the_same_answer(client):
    written = client.post(SCREEN, data={"nome": SETTLEMENT, "valor": "35.000,00"})

    assert written.status_code == 200
    assert "Salvo." in written.text
    assert "R$ 35.000,00" in written.text
    assert _saved(SETTLEMENT) == 3500000


def test_the_goal_moves_the_reserve_target_and_the_sentence_that_names_it(client):
    before = client.get(OBJECTIVE).text
    client.post(SCREEN, data={"nome": RESERVE, "valor": str(HALF)})
    after = client.get(OBJECTIVE).text

    assert f"{MONTHS_IN_BASE} meses de reserva" in before
    assert f"{HALF} meses de reserva" in after
    assert f"{MONTHS_IN_BASE} meses de reserva" not in after
    assert int(TARGET.findall(after)[0]) * 2 == int(TARGET.findall(before)[0])


def test_a_window_the_base_cannot_fill_is_refused_and_says_how_many_months_it_has(client):
    refused = client.post(SCREEN, data={"nome": MEDIAN, "valor": "12"})

    assert refused.status_code == 400
    assert f"{MONTHS_IN_BASE} meses fechados" in refused.text
    assert _saved(MEDIAN) is None


def test_a_name_outside_the_catalogue_is_refused_without_writing(client):
    refused = client.post(SCREEN, data={"nome": "inexistente", "valor": "10"})

    assert refused.status_code == 400
    assert "inexistente" in refused.text


def test_a_value_the_reader_refuses_names_the_field_and_writes_nothing(client):
    refused = client.post(SCREEN, data={"nome": RESERVE, "valor": "abc"})

    assert refused.status_code == 400
    assert "Meses de reserva do objetivo" in refused.text
    assert 'id="recusa"' in refused.text
    assert _saved(RESERVE) is None


def test_an_accent_survives_the_form(client):
    refused = client.post(SCREEN, data={"nome": "correção-inexistente", "valor": "10"})

    assert refused.status_code == 400
    assert "correção-inexistente" in refused.text


def test_the_median_window_moves_the_survival_floor_and_the_reserve_with_it(client):
    before = int(TARGET.findall(client.get(OBJECTIVE).text)[0])
    client.post(SCREEN, data={"nome": MEDIAN, "valor": "1"})
    after = int(TARGET.findall(client.get(OBJECTIVE).text)[0])

    assert _saved(MEDIAN) == 1
    assert after != before
