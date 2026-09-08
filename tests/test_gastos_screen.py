import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.queries.axes import AXES
from app.queries.period import default_period
from app.queries.series import MONTHS
from app.routers.reference import screen_date
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import load_seed, seed_taxonomy
from tests.conftest import ACCOUNT, load, transaction

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

SCREEN = "/gastos"
TABLE = f"{SCREEN}/tabela"
PANEL = f"{SCREEN}/painel"
DETAIL = f"{SCREEN}/detalhe"

FIGURE = re.compile(r"^−?R\$ [\d.]+,\d{2}$")
CIFRA = re.compile(r'class="[^"]*\bcifra\b[^"]*"[^>]*>([^<]*)<')
HIGHLIGHT = re.compile(r'class="([^"]*\bcifra\b[^"]*\bnegative\b[^"]*)"')
BODY_ROW = re.compile(r"<tbody>(.*?)</tbody>", re.S)
CONTROLS = re.compile(r'<form[^>]*id="controles"(.*?)</form>', re.S)
SUBMIT = re.compile(r"<button[^>]*type=\"submit\"[^>]*>(.*?)</button>", re.S)
ANCHORING = re.compile(r"\.screen\s*\{[^}]*overflow-anchor:\s*none", re.S)
SHRINKABLE = (
    re.compile(r"\.panels\s*\{[^}]*min-width:\s*0", re.S),
    re.compile(r"\.panel\s*\{[^}]*min-width:\s*0", re.S),
    re.compile(r"\.chart\s*\{[^}]*min-width:\s*0", re.S),
    re.compile(r"\.chart-canvas\s*\{[^}]*max-width:\s*100%", re.S),
)

CATEGORY = "categoria"
FLOOR_AMOUNT = -120000
CUT_AMOUNT = -80000
SMALL_CUT_AMOUNT = -30000
LOOSE_AMOUNT = -5000
TOTAL = FLOOR_AMOUNT + CUT_AMOUNT + SMALL_CUT_AMOUNT + LOOSE_AMOUNT
ENTRIES = 4
UNKNOWN_CATEGORY = "Categoria que nenhuma regra alcanca"


def _rows_of(html: str) -> list[str]:
    found = BODY_ROW.search(html)
    return [] if found is None else re.findall(r"<tr[^>]*>", found.group(1))


def _figures(html: str) -> list[str]:
    return [value.strip() for value in CIFRA.findall(html)]


@pytest.fixture()
def window():
    return default_period(screen_date(None).date)


@pytest.fixture()
def vocabulary():
    seed = load_seed()
    cut, floor = seed["crossings"][0], seed["crossings"][1]
    categories = [rule for rule in seed["rules"] if rule["match_kind"] == "category"]
    return {
        "cut": cut,
        "floor": floor,
        "term": seed["fallback_essentiality"],
        "floor_category": next(
            rule["match_value"]
            for rule in categories
            if rule["nature"] == floor["nature"] and rule["essentiality"] == floor["essentiality"]
        ),
        "candidates": [
            rule["match_value"]
            for rule in categories
            if rule["nature"] == cut["nature"]
            and rule["essentiality"] == seed["fallback_essentiality"]
        ][:2],
    }


@pytest.fixture()
def client(tmp_path, monkeypatch, window, vocabulary):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    start, end = window
    first, second = vocabulary["candidates"]
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    load(
        conn,
        [
            transaction(
                "t-floor", start, FLOOR_AMOUNT / 100, categoria=vocabulary["floor_category"]
            ),
            transaction("t-cut", start, CUT_AMOUNT / 100, categoria=first),
            transaction("t-cut-small", end, SMALL_CUT_AMOUNT / 100, categoria=second),
            transaction("t-loose", end, LOOSE_AMOUNT / 100, categoria=UNKNOWN_CATEGORY),
        ],
    )
    seed_taxonomy(conn)
    classify_all(conn)
    conn.commit()
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def test_the_screen_opens_on_the_running_month(client, window):
    start, end = window
    page = client.get(SCREEN)

    assert page.status_code == 200
    for axis in AXES:
        assert f'<option value="{axis}"' in page.text
    assert f'value="{start}"' in page.text
    assert f'value="{end}"' in page.text
    assert f"{ENTRIES} lançamentos" in page.text
    assert date.fromisoformat(start).day == 1


def test_the_five_axes_repartition_the_same_total(client):
    for axis in AXES:
        fragment = client.get(TABLE, params={"eixo": axis})

        assert fragment.status_code == 200
        assert 'id="tabela"' in fragment.text
        assert _figures(fragment.text)[0] == "−R$ 2.350,00"
        assert f"{ENTRIES} lançamentos" in fragment.text


def test_every_figure_carries_the_minus_glued_to_the_number(client):
    page = client.get(SCREEN, params={"eixo": CATEGORY})
    figures = _figures(page.text)

    assert figures
    assert [value for value in figures if not FIGURE.match(value)] == []


def test_the_semantic_colour_marks_only_the_totals_that_ask_for_a_decision(client):
    page = client.get(SCREEN, params={"eixo": CATEGORY})
    coloured = HIGHLIGHT.findall(page.text)

    assert sorted(set(coloured)) == [
        "crossing-total cifra negative",
        "headline cifra negative",
    ]
    assert len(_figures(page.text)) > len(coloured)


def test_a_category_already_in_portuguese_shows_its_name_once(client, window):
    start, _ = window
    key = next(name for name, label in load_seed()["category_labels"].items() if name == label)
    conn = connect()
    load(conn, [transaction("t-self", start, LOOSE_AMOUNT / 100, categoria=key)])
    classify_all(conn)
    conn.commit()
    conn.close()

    table = client.get(TABLE, params={"eixo": CATEGORY})
    row = next(part for part in table.text.split("<tr") if f">{key}<" in part)

    assert row.count(f">{key}<") == 1
    assert "cell-key" not in row


def test_an_open_row_sums_back_to_the_row_it_came_from(client, vocabulary):
    key = vocabulary["floor_category"]
    detail = client.get(DETAIL, params={"eixo": CATEGORY, "chave": key})

    assert detail.status_code == 200
    assert len(_rows_of(detail.text)) == 1
    assert _figures(detail.text)[0] == "−R$ 1.200,00"


def test_the_panel_carries_the_thirteen_points_without_the_chart(client):
    panel = client.get(PANEL)

    assert panel.status_code == 200
    assert 'id="painel"' in panel.text
    assert len(_rows_of(panel.text)) == MONTHS


def test_the_panel_names_both_crossings_with_a_figure_each(client, vocabulary):
    panel = client.get(PANEL)

    for crossing in (vocabulary["cut"], vocabulary["floor"]):
        assert crossing["label"] in panel.text
        after = panel.text[panel.text.index(crossing["label"]) :]
        assert re.search(r">(−?R\$ [\d.]+,\d{2})<", after) is not None


def test_the_cut_list_offers_candidates_while_no_rule_marks_the_term(client, vocabulary):
    panel = client.get(PANEL)
    block = panel.text[panel.text.index(vocabulary["cut"]["label"]) :]
    block = block[: block.index(vocabulary["floor"]["label"])]

    assert f"Nada foi marcado como {vocabulary['cut']['essentiality']} ainda" in block
    assert '<a href="/regras">' in block
    for candidate in vocabulary["candidates"]:
        assert candidate in block


def test_the_residue_counts_what_no_rule_reached(client):
    panel = client.get(PANEL)

    assert "Sem regra" in panel.text
    assert "1 lançamento." in panel.text
    assert "−R$ 50,00" in panel.text
    assert '<a href="/regras">' in panel.text


def test_a_period_without_spending_says_so_and_offers_the_way_back(client):
    page = client.get(SCREEN, params={"inicio": "2020-01-01", "fim": "2020-01-31"})
    table = page.text[page.text.index('id="tabela"') : page.text.index('id="painel"')]

    assert page.status_code == 200
    assert _rows_of(table) == []
    assert "Nenhum gasto" in table
    assert "período" in table
    assert f'href="{SCREEN}?eixo=' in table


def test_a_value_the_screen_cannot_read_falls_back_to_the_default_window(client, window):
    start, end = window
    page = client.get(SCREEN, params={"eixo": "inexistente", "inicio": "ontem", "fim": end})

    assert page.status_code == 200
    assert f'<option value="{AXES[0]}" selected>' in page.text
    assert f'value="{start}"' in page.text


def test_the_screen_is_closed_to_a_visitor_without_a_session(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    with TestClient(create_app(), follow_redirects=False) as anonymous:
        for path in (SCREEN, TABLE, PANEL, DETAIL):
            response = anonymous.get(path)

            assert response.status_code == 302
            assert response.headers["location"] == "/login"


def test_the_login_screen_still_needs_no_network(client):
    page = client.get("/login")

    assert "<script" not in page.text
    assert "https://" not in page.text


def test_the_axis_travels_by_the_same_form_the_period_travels_by(client):
    page = client.get(SCREEN)
    controls = CONTROLS.search(page.text)

    assert controls is not None
    assert 'method="get"' in controls.group(1)
    assert f'action="{SCREEN}"' in controls.group(1)
    assert 'name="eixo"' in controls.group(1)
    submit = SUBMIT.search(controls.group(1))
    assert submit is not None
    assert "eixo" in submit.group(1).lower()


def test_the_whole_screen_answers_the_axis_the_form_sends(client, window):
    start, end = window
    page = client.get(SCREEN, params={"eixo": CATEGORY, "inicio": start, "fim": end})
    table = page.text[page.text.index('id="tabela"') : page.text.index('id="painel"')]

    assert page.status_code == 200
    assert f'<option value="{CATEGORY}" selected>' in page.text
    assert _rows_of(table) != []


def test_the_screen_never_re_anchors_the_scroll_after_a_swap(client):
    page = client.get(SCREEN)

    assert ANCHORING.search(page.text) is not None


def test_nothing_between_the_body_and_the_chart_refuses_to_shrink(client):
    # The chart canvas keeps the width it was drawn at, and a grid item floors
    # at the intrinsic width of its content: without these four declarations the
    # panel never narrows and the body inherits a horizontal scroll that only
    # appears when the window is resized, never when the page loads narrow.
    page = client.get(SCREEN)

    for rule in SHRINKABLE:
        assert rule.search(page.text) is not None


def test_the_account_of_the_row_reaches_the_open_list(client, vocabulary):
    detail = client.get(DETAIL, params={"eixo": CATEGORY, "chave": vocabulary["floor_category"]})

    assert ACCOUNT["name"] in detail.text
    assert "Data" in detail.text
    assert "Descrição" in detail.text
    assert "Conta" in detail.text


def test_the_default_window_follows_the_reference_not_the_clock(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", "2026-05-15")
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        page = client.get(SCREEN)

    assert page.status_code == 200
    assert "de 01/05/2026 a 15/05/2026" in page.text
    assert "de 01/11/2025 a 30/04/2026" not in page.text


REFERENCE_TODAY = "2026-09-05"
FLOOR_ENTRIES = (
    ("t-aug-20", "2026-08-20", -111.00),
    ("t-sep-01", "2026-09-01", -200.00),
    ("t-sep-05", "2026-09-05", -30.00),
    ("t-sep-06", "2026-09-06", -40.00),
    ("t-sep-30", "2026-09-30", -62.00),
    ("t-oct-02", "2026-10-02", -77.00),
)


def _paragraph(html: str, marker: str) -> str:
    start = html.index(marker)
    return html[start : html.index("</p>", start) + len("</p>")]


@pytest.fixture()
def open_client(tmp_path, monkeypatch, vocabulary):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", REFERENCE_TODAY)
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    load(
        conn,
        [
            transaction(pid, when, amount, categoria=vocabulary["floor_category"])
            for pid, when, amount in FLOOR_ENTRIES
        ],
    )
    seed_taxonomy(conn)
    classify_all(conn)
    conn.commit()
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def test_the_screen_opens_from_the_first_of_the_month_to_the_reference_date(open_client):
    page = open_client.get(SCREEN)

    assert page.status_code == 200
    assert 'value="2026-09-01"' in page.text
    assert 'value="2026-09-05"' in page.text
    assert "2 lançamentos de 01/09/2026 a 05/09/2026" in page.text
    assert "−R$ 230,00" in page.text
    assert 'id="recusa"' not in page.text


def test_an_accepted_date_moves_the_whole_window(open_client):
    page = open_client.get(SCREEN, params={"data": "2026-08-20"})

    assert page.status_code == 200
    assert 'value="2026-08-01"' in page.text
    assert 'value="2026-08-20"' in page.text
    assert "1 lançamento de 01/08/2026 a 20/08/2026" in page.text
    assert "−R$ 111,00" in page.text
    assert '<input type="hidden" name="data" value="2026-08-20">' in page.text
    assert 'id="recusa"' not in page.text


def test_a_refused_date_falls_back_and_says_so(open_client):
    page = open_client.get(SCREEN, params={"data": "banana"})

    assert page.status_code == 200
    assert 'id="recusa"' in page.text
    assert "data inválida: data (banana)" in page.text
    assert 'value="2026-09-01"' in page.text
    assert 'value="2026-09-05"' in page.text


def test_explicit_dates_win_over_the_default_and_an_unreadable_one_falls_back(open_client):
    explicit = open_client.get(SCREEN, params={"inicio": "2026-08-01", "fim": "2026-08-31"})
    unreadable = open_client.get(SCREEN, params={"inicio": "ontem", "fim": "2026-08-31"})

    assert explicit.status_code == 200
    assert "1 lançamento de 01/08/2026 a 31/08/2026" in explicit.text
    assert "−R$ 111,00" in explicit.text
    assert unreadable.status_code == 200
    assert 'value="2026-09-01"' in unreadable.text
    assert 'value="2026-09-05"' in unreadable.text


def test_what_is_already_posted_ahead_of_the_reference_is_named_apart(open_client):
    page = open_client.get(SCREEN)
    block = _paragraph(page.text, 'id="posterior"')

    assert page.status_code == 200
    assert "2 lançamento" in block
    assert "−R$ 102,00" in block
    assert "05/09/2026" in block
    assert "77,00" not in block
    assert "2 lançamentos de 01/09/2026 a 05/09/2026" in page.text
    assert "−R$ 230,00" in page.text


def test_a_window_that_already_reaches_the_ahead_entries_sums_them_instead(open_client):
    page = open_client.get(SCREEN, params={"inicio": "2026-09-01", "fim": "2026-09-30"})

    assert page.status_code == 200
    assert 'id="posterior"' not in page.text
    assert "4 lançamentos de 01/09/2026 a 30/09/2026" in page.text
    assert "−R$ 332,00" in page.text


def test_a_window_touching_two_months_prints_the_period_total_not_an_average(open_client):
    page = open_client.get(SCREEN, params={"inicio": "2026-08-20", "fim": "2026-09-05"})
    block = page.text[page.text.index('id="cruzamentos"') : page.text.index('id="residuo"')]

    assert page.status_code == 200
    assert "No período" in block
    assert "−R$ 341,00" in block
    assert "Média mensal" not in block
    assert "−R$ 170,50" not in block


def test_a_window_of_whole_months_keeps_naming_it_a_monthly_average(open_client):
    page = open_client.get(SCREEN, params={"inicio": "2026-03-01", "fim": "2026-08-31"})
    block = page.text[page.text.index('id="cruzamentos"') : page.text.index('id="residuo"')]

    assert page.status_code == 200
    assert "Média mensal" in block
    assert "−R$ 18,50" in block
