import re

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.commitments import engine
from app.db import connect
from app.main import create_app
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction
from app.routers.summary import _moving
from tests.test_comprometido_screen import LOGIN, PASSWORD, REFERENCE

ASKED = REFERENCE.isoformat()
BALANCE = -100000
EMPTY_TITLE = "Nenhum lançamento na base."
SALARY = 5000.0
SUBSCRIPTION = -300.0
DAY = re.compile(r'data-dia="([^"]+)"')


def _screen(client):
    return client.get(f"/?data={ASKED}")


def _section(html: str, name: str) -> str:
    start = html.index(f'id="{name}"')
    return html[start : html.index("</section>", start)]


def _app(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    return app, conn


def _opened(app) -> TestClient:
    client = TestClient(app, follow_redirects=False)
    client.__enter__()
    client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
    return client


@pytest.fixture()
def empty(tmp_path, monkeypatch):
    app, conn = _app(tmp_path, monkeypatch)
    conn.close()
    opened = _opened(app)
    yield opened
    opened.__exit__(None, None, None)


@pytest.fixture()
def client(tmp_path, monkeypatch, seed):
    app, conn = _app(tmp_path, monkeypatch)
    rows = [
        transaction(f"in-{month}", f"{month}-14", SALARY, descricao="Salario")
        for month in ("2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08")
    ]
    rows += [
        transaction(f"out-{month}", f"{month}-20", SUBSCRIPTION, descricao="Assinatura X")
        for month in ("2026-06", "2026-07", "2026-08", "2026-09")
    ]
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify_all(conn)
    conn.execute("UPDATE accounts SET balance_cents = ?", (BALANCE,))
    conn.commit()
    engine.recompute(conn, today=REFERENCE)
    conn.close()
    opened = _opened(app)
    yield opened
    opened.__exit__(None, None, None)


def test_the_screen_shows_the_three_positions(client):
    html = _screen(client).text

    assert "Posição consolidada" in html
    assert "Caixa" in html
    assert "Cartão" in html
    assert "−R$ 1.000,00" in html


def test_the_projection_chains_day_by_day(client):
    block = _section(_screen(client).text, "projecao")
    days = re.findall(
        r'data-dia="([^"]+)" data-saldo="(-?\d+)"\s+data-entra="(-?\d+)" '
        r'data-sai="(-?\d+)"\s+data-variavel="(-?\d+)"',
        block,
    )

    assert days
    assert [when for when, *_ in days] == sorted({when for when, *_ in days})
    for earlier, later in zip(days, days[1:]):
        parts = sum(int(value) for value in later[2:])
        assert int(later[1]) == int(earlier[1]) + parts


def test_the_screen_leads_to_the_rest_of_the_panel(client):
    html = _screen(client).text

    assert 'href="/gastos"' in html
    assert 'href="/comprometido"' in html
    assert 'href="/regras"' in html


def test_an_empty_base_says_what_to_do_instead_of_showing_a_blank(empty):
    answer = _screen(empty)

    assert answer.status_code == 200
    assert EMPTY_TITLE in answer.text
    assert 'href="/regras"' in answer.text
    assert 'id="projecao"' not in answer.text


def test_the_screen_needs_a_session(tmp_path, monkeypatch):
    app, conn = _app(tmp_path, monkeypatch)
    conn.close()
    with TestClient(app, follow_redirects=False) as anonymous:
        answer = anonymous.get(f"/?data={ASKED}")

    assert answer.status_code == 302
    assert answer.headers["location"] == "/login"


def _line(when, balance, income=0, due=0, variable=-100):
    return {
        "date": when,
        "balance_cents": balance,
        "income_cents": income,
        "due_cents": due,
        "variable_cents": variable,
    }


def test_the_list_reaches_the_end_of_the_window_when_the_tail_is_quiet():
    days = [
        _line("2026-09-05", -1000, variable=0),
        _line("2026-09-06", -1200, due=-100),
        _line("2026-09-07", -1300),
        _line("2026-09-08", -1400),
    ]
    shown = _moving(days)

    assert shown[-1]["date"] == "2026-09-08"
    assert shown[-1]["balance_cents"] == -1400
    assert shown[-1]["variable_cents"] == -200


def test_the_list_does_not_repeat_the_last_day_when_it_already_moves():
    days = [
        _line("2026-09-05", -1000, variable=0),
        _line("2026-09-06", -1200, due=-100),
    ]
    shown = _moving(days)

    assert [entry["date"] for entry in shown] == ["2026-09-06"]


def test_a_window_with_no_movement_at_all_shows_no_list():
    assert _moving([_line("2026-09-05", -1000, variable=0), _line("2026-09-06", -1000, variable=0)]) == []


def test_the_list_of_the_real_screen_ends_at_the_window_end(client):
    days = DAY.findall(_section(_screen(client).text, "projecao"))

    assert days[-1] == "2026-10-20"


def test_a_window_moved_only_by_undated_spending_still_shows_a_line():
    days = [
        _line("2026-09-05", -1000, variable=0),
        _line("2026-09-06", -1100),
        _line("2026-09-07", -1200),
    ]
    shown = _moving(days)

    assert [entry["date"] for entry in shown] == ["2026-09-07"]
    assert shown[0]["variable_cents"] == -200
    assert shown[0]["balance_cents"] == -1200


def test_the_screen_does_not_print_none_when_no_income_was_ever_observed(client):
    html = client.get("/?data=2020-01-01").text

    assert "None" not in _section(html, "projecao")
    assert "não há entrada observada no histórico" in html


def test_a_date_with_no_complete_month_behind_it_says_so(client):
    html = client.get("/?data=2020-01-01").text

    block = _section(html, "projecao")

    assert "Não há mês completo anterior a esta data na base" in html
    assert "de <span" not in _section(html, "mes")
    assert all(int(value) <= 0 for value in re.findall(r'data-variavel="(-?\d+)"', block))
    assert 'class="calendar-name">gasto sem data' not in block


def test_a_date_it_cannot_read_is_said_out_loud(client):
    html = client.get("/?data=banana").text

    assert 'id="recusa"' in html
    assert "A tela responde pela data de hoje." in html


def test_a_reference_that_is_not_today_says_the_position_is_still_current(client):
    html = client.get("/?data=2020-01-01").text

    assert "A posição é sempre a atual" in html
    assert "Ponto de partida" in _section(html, "projecao")
