import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.commitments import engine
from app.commitments.mark import REFUSAL_MESSAGE
from app.db import connect
from app.main import create_app
from app.routers.commitments import DISMISS, RESUME, SCREEN
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

REFERENCE = date(2026, 9, 5)
ASKED = REFERENCE.isoformat()

FIGURE = re.compile(r"^−?R\$ [\d.]+,\d{2}$")
CIFRA = re.compile(r'class="[^"]*\bcifra\b[^"]*"[^>]*>([^<]*)<')
COMMITTED = re.compile(r'class="headline cifra(?: negative)?"[^>]*>([^<]+)<')
SAVED = re.compile(r'class="headline cifra(?: positive)?"[^>]*>([^<]+)<')

BIG = "Assinatura grande"
SMALL = "Assinatura pequena"
STOPPED = "Assinatura parada"
LONG_PURCHASE = "Loja parcelada"
SHORT_PURCHASE = "Outra loja"

BIG_KEY = "assinatura grande"
LONG_KEY = "loja parcelada"

BIG_AMOUNT = -300.0
SMALL_AMOUNT = -100.0
STOPPED_AMOUNT = -50.0
LONG_AMOUNT = -120.0
SHORT_AMOUNT = -60.0

LIVE_MONTHS = ("2026-06", "2026-07", "2026-08")
DEAD_MONTHS = ("2026-01", "2026-02", "2026-03")

LONG_TOTAL = 24
LONG_PAID = 2
SHORT_TOTAL = 3
SHORT_PAID = 1

SUBSCRIPTIONS = 3
INSTALLMENTS = 2
STALE_MARK = "Sem cobrança recente"
EMPTY_TITLE = "Nenhum compromisso detectado"
DISCLAIMER = '"Não uso mais" registra a decisão neste painel e não cancela nada no fornecedor.'
FORECAST = "a média observada das cobranças, não o valor contratado"
PREDICTION = "A data de cada vencimento é previsão a partir do histórico, não data contratual."
WINDOW_START = "05/09/2026"
WINDOW_END = "20/10/2026"
STALE_SERIES = 1
STOPPED_KEY = "assinatura parada"
EMPTY_CALENDAR = "Nenhum vencimento previsto até"
CLOSING_ASSUMED = "Sem dia de fechamento informado, a curva usa o mês do lançamento."
DUE_ASSUMED = "Sem dia de vencimento informado, a curva usa o mês do fechamento."
_ARTICLE = re.compile(
    r'<article class="released" data-cartao="([^"]+)" data-restante="(-?\d+)">(.*?)</article>',
    re.S,
)


def _section(html: str, name: str) -> str:
    start = html.index(f'id="{name}"')
    return html[start : html.index("</section>", start)]


def _article(html: str, marker: str) -> str:
    start = html.index(marker)
    return html[start : html.index("</article>", start)]


def _rows(html: str, name: str) -> list[str]:
    # Every tbody of the section, not the first: a screen that grows a second
    # table inside the same section would keep passing a check that only ever
    # looked at one of them.
    bodies = re.findall(r"<tbody>(.*?)</tbody>", _section(html, name), re.S)
    return [row for body in bodies for row in re.findall(r"<tr[^>]*>.*?</tr>", body, re.S)]


def _ordering(html: str, name: str, attribute: str) -> list[int]:
    return [
        abs(int(value)) for value in re.findall(f'{attribute}="(-?\\d+)"', _section(html, name))
    ]


def _totals(html: str) -> tuple[str, str]:
    return COMMITTED.search(html).group(1), SAVED.findall(html)[-1]


def _count(statement: str) -> int:
    conn = connect()
    try:
        return int(conn.execute(statement).fetchone()[0])
    finally:
        conn.close()


def _opened(app) -> TestClient:
    client = TestClient(app, follow_redirects=False)
    client.__enter__()
    client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
    return client


def _base(tmp_path, monkeypatch, name: str):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / name))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", ASKED)
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    return app, conn


@pytest.fixture()
def client(tmp_path, monkeypatch, seed):
    app, conn = _base(tmp_path, monkeypatch, "dash.sqlite")
    rows = [
        transaction(f"{key}-{month}", f"{month}-11", amount, descricao=name)
        for name, key, amount, months in (
            (BIG, "big", BIG_AMOUNT, LIVE_MONTHS),
            (SMALL, "small", SMALL_AMOUNT, LIVE_MONTHS),
            (STOPPED, "stopped", STOPPED_AMOUNT, DEAD_MONTHS),
        )
        for month in months
    ]
    rows.append(
        transaction(
            "long-1",
            "2026-08-11",
            LONG_AMOUNT,
            descricao=LONG_PURCHASE,
            parcela_atual=LONG_PAID,
            parcela_total=LONG_TOTAL,
        )
    )
    rows.append(
        transaction(
            "short-1",
            "2026-08-04",
            SHORT_AMOUNT,
            descricao=SHORT_PURCHASE,
            parcela_atual=SHORT_PAID,
            parcela_total=SHORT_TOTAL,
        )
    )
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify_all(conn)
    conn.commit()
    engine.recompute(conn, today=REFERENCE)
    conn.close()
    opened = _opened(app)
    yield opened
    opened.__exit__(None, None, None)


@pytest.fixture()
def empty_client(tmp_path, monkeypatch):
    app, conn = _base(tmp_path, monkeypatch, "vazia.sqlite")
    conn.close()
    opened = _opened(app)
    yield opened
    opened.__exit__(None, None, None)


_CARDS_ACCOUNTS = (
    "INSERT INTO accounts (id, name, type, balance_cents) VALUES "
    "('acc-azul', 'Cartão Azul', 'CREDIT', -100000), "
    "('acc-roxo', 'Cartão Roxo', 'CREDIT', -50000), "
    "('acc-verde', 'Cartão Verde', 'CREDIT', 0)"
)
_CARDS_AZUL = "INSERT INTO cards (account_id, closing_day, due_day) VALUES ('acc-azul', 5, 15)"
_CARDS_VERDE = "INSERT INTO cards (account_id, closing_day) VALUES ('acc-verde', 10)"
_CARDS_COMMITMENTS = (
    "INSERT INTO commitments (kind, series_key, description, account, amount_cents, "
    "last_seen_date, installment_total, installments_left, ends_month) VALUES "
    "('installment', 'loja azul', 'Loja Azul', 'Cartão Azul', -12000, '2026-08-11', 24, 3, '2026-11'), "
    "('installment', 'posto azul', 'Posto Azul', 'Cartão Azul', -5000, '2026-09-02', 6, 2, '2026-11'), "
    "('installment', 'loja roxa', 'Loja Roxa', 'Cartão Roxo', -20000, '2026-08-20', 10, 1, '2026-09')"
)


@pytest.fixture()
def cards_client(tmp_path, monkeypatch):
    app, conn = _base(tmp_path, monkeypatch, "cartoes.sqlite")
    conn.executescript(f"{_CARDS_ACCOUNTS}; {_CARDS_AZUL}; {_CARDS_VERDE}; {_CARDS_COMMITMENTS};")
    conn.commit()
    conn.close()
    opened = _opened(app)
    yield opened
    opened.__exit__(None, None, None)


@pytest.fixture()
def engine_cards_client(tmp_path, monkeypatch, seed):
    app, conn = _base(tmp_path, monkeypatch, "motor-cartoes.sqlite")
    conn.executescript(
        "INSERT INTO accounts (id, name, type, balance_cents) VALUES "
        "('acc-cartao', 'Cartão Azul', 'CREDIT', -100000);"
        "INSERT INTO cards (account_id, closing_day, due_day) VALUES ('acc-cartao', 5, 15);"
    )
    rows = [
        transaction(
            "loja-azul-1",
            "2026-08-11",
            -120.00,
            conta_id="acc-cartao",
            descricao="Loja Azul",
            parcela_atual=2,
            parcela_total=24,
        ),
        transaction(
            "carne-loja-1",
            "2026-08-20",
            -50.00,
            descricao="Carne Loja",
            parcela_atual=1,
            parcela_total=6,
        ),
    ]
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify_all(conn)
    conn.commit()
    engine.recompute(conn, today=REFERENCE)
    conn.close()
    opened = _opened(app)
    yield opened
    opened.__exit__(None, None, None)


def _screen(client):
    return client.get(SCREEN, params={"data": ASKED})


def _dismiss(client, series_key: str, path: str = DISMISS):
    return client.post(path, data={"serie": series_key, "data": ASKED})


def test_the_screen_answers_with_a_session_and_carries_its_three_blocks(client):
    page = _screen(client)

    assert page.status_code == 200
    for block in ('id="assinaturas"', 'id="parcelamentos"', 'id="caixa-liberado"'):
        assert block in page.text
    assert len(_rows(page.text, "assinaturas")) == SUBSCRIPTIONS
    assert len(_rows(page.text, "parcelamentos")) == INSTALLMENTS


def test_every_figure_of_the_screen_is_written_as_a_figure(client):
    page = _screen(client)
    figures = [value.strip() for value in CIFRA.findall(page.text)]

    assert figures
    assert [value for value in figures if not FIGURE.match(value)] == []


def test_the_screen_says_the_value_is_observed_and_the_mark_cancels_nothing(client):
    page = _screen(client)

    assert FORECAST in page.text
    assert DISCLAIMER in page.text


def test_the_subscriptions_come_from_the_largest_average_to_the_smallest(client):
    page = _screen(client)
    ordering = _ordering(page.text, "assinaturas", "data-media")

    assert ordering == sorted(ordering, reverse=True)
    assert BIG in _rows(page.text, "assinaturas")[0]


def test_a_subscription_that_stopped_being_charged_is_marked_and_not_hidden(client):
    page = _screen(client)
    rows = _rows(page.text, "assinaturas")

    assert len([row for row in rows if STALE_MARK in row]) == 1
    assert [row for row in rows if STOPPED in row][0].count(STALE_MARK) == 1


def test_the_instalments_come_ordered_by_what_is_left_to_pay(client):
    page = _screen(client)
    ordering = _ordering(page.text, "parcelamentos", "data-restante")
    row = [line for line in _rows(page.text, "parcelamentos") if LONG_PURCHASE in line][0]

    assert ordering == sorted(ordering, reverse=True)
    assert f">{LONG_TOTAL - LONG_PAID}<" in row
    assert "06/2028" in row


def test_the_released_cash_names_the_month_each_series_frees(client):
    block = _section(_screen(client).text, "caixa-liberado")

    assert "10/2026" in block
    assert "R$ 60,00" in block
    assert "R$ 180,00" in block


def test_the_mark_moves_the_money_in_the_answer_of_the_same_request(client):
    before = _totals(_screen(client).text)
    marked = _dismiss(client, BIG_KEY)

    assert marked.status_code == 200
    assert before == ("−R$ 580,00", "R$ 0,00")
    assert _totals(marked.text) == ("−R$ 280,00", "R$ 300,00")
    assert len(_rows(marked.text, "dispensadas")) == 1
    assert DISCLAIMER in _section(marked.text, "dispensadas")


def test_unmarking_gives_the_subscription_back_to_the_total(client):
    _dismiss(client, BIG_KEY)
    resumed = _dismiss(client, BIG_KEY, RESUME)

    assert resumed.status_code == 200
    assert _totals(resumed.text) == ("−R$ 580,00", "R$ 0,00")
    assert 'id="dispensadas"' not in resumed.text
    assert len(_rows(resumed.text, "assinaturas")) == SUBSCRIPTIONS


def test_an_instalment_refuses_the_mark_and_the_total_stays_to_the_cent(client):
    before = _totals(_screen(client).text)
    refused = _dismiss(client, LONG_KEY)

    assert refused.status_code == 400
    assert REFUSAL_MESSAGE in refused.text
    assert _totals(refused.text) == before
    assert _count("SELECT count(*) FROM commitment_dismissals") == 0


def test_the_calendar_names_its_window_and_calls_the_date_a_forecast(client):
    block = _section(_screen(client).text, "calendario")

    assert WINDOW_START in block
    assert WINDOW_END in block
    assert PREDICTION in block


def test_every_day_of_the_calendar_totals_the_entries_it_lists(client):
    block = _section(_screen(client).text, "calendario")
    days = re.findall(r'data-dia="([^"]+)" data-total="(-?\d+)">(.*?)</ul>', block, re.S)

    assert days
    assert [when for when, _, _ in days] == sorted({when for when, _, _ in days})
    for when, total, inner in days:
        cents = re.findall(r'data-centavos="(-?\d+)"', inner)
        assert int(total) == sum(int(value) for value in cents)
        assert WINDOW_START.split("/")[::-1] <= when.split("-")


def test_the_calendar_counts_the_series_it_left_out_and_lists_none_of_them(client):
    block = _section(_screen(client).text, "calendario")

    assert f"{STALE_SERIES} sem cobrança recente" in block
    assert STOPPED_KEY not in re.findall(r'data-serie="([^"]+)"', block)


def test_an_empty_calendar_says_what_happened_and_where_to_go_next(empty_client):
    block = _section(empty_client.get(SCREEN, params={"data": ASKED}).text, "calendario")

    assert 'data-dia="' not in block
    assert EMPTY_CALENDAR in block
    assert '<a href="/gastos">' in block


def test_a_date_the_screen_cannot_read_falls_back_instead_of_breaking(client):
    answered = client.get(SCREEN, params={"data": "trinta de fevereiro"})

    assert answered.status_code == 200


def test_an_empty_base_shows_what_happened_and_where_to_go_next(empty_client):
    page = empty_client.get(SCREEN, params={"data": ASKED})

    assert page.status_code == 200
    assert _rows(page.text, "assinaturas") == []
    assert _rows(page.text, "parcelamentos") == []
    assert EMPTY_TITLE in page.text
    assert '<a href="/gastos">' in page.text[page.text.index(EMPTY_TITLE) :]


def test_calendar_window_pair_without_query_string_and_with_an_unreadable_date(client):
    unasked = client.get(SCREEN)
    unreadable = client.get(SCREEN, params={"data": "banana"})

    assert unasked.status_code == 200
    assert unreadable.status_code == 200
    for answer in (unasked, unreadable):
        block = _section(answer.text, "calendario")
        assert f">{WINDOW_START}<" in block
        assert f">{WINDOW_END}<" in block
    assert 'id="recusa"' not in unasked.text
    assert 'id="recusa"' in unreadable.text


def test_a_date_that_breaks_calendar_arithmetic_is_refused_without_a_500(client):
    answer = client.get(SCREEN, params={"data": "0001-01-01"})

    assert answer.status_code == 200
    assert 'id="recusa"' in answer.text
    assert f">{WINDOW_START}<" in _section(answer.text, "calendario")


def test_the_invoice_curve_names_the_month_the_invoice_is_paid_and_when_it_frees_cash(cards_client):
    page = _screen(cards_client)
    block = _section(page.text, "fatura")

    assert page.status_code == 200
    assert 'data-cartao="Cartão Azul"' in block
    assert 'data-restante="-46000"' in block
    assert 'data-mes="2026-09" data-total="0"' in block
    assert 'data-mes="2026-10" data-total="-17000"' in block
    assert 'data-mes="2026-11" data-total="-17000"' in block
    assert 'data-mes="2026-12" data-total="-12000"' in block
    assert 'data-serie="loja azul" data-termina="2026-12" data-devolve="12000"' in block
    assert 'data-serie="posto azul" data-termina="2026-11" data-devolve="5000"' in block
    assert "12/2026" in block
    assert "−R$ 170,00" in block


def test_the_screen_declares_the_premise_when_a_cards_day_is_missing(cards_client):
    block = _section(_screen(cards_client).text, "fatura")
    roxo = _article(block, 'data-cartao="Cartão Roxo"')
    verde = _article(block, 'data-cartao="Cartão Verde"')
    azul = _article(block, 'data-cartao="Cartão Azul"')

    assert 'data-premissa="1"' in roxo
    assert CLOSING_ASSUMED in roxo
    assert DUE_ASSUMED in roxo

    assert 'data-fechamento="10"' in verde
    assert 'data-premissa="1"' in verde
    assert DUE_ASSUMED in verde
    assert CLOSING_ASSUMED not in verde

    assert 'data-fechamento="5"' in azul
    assert 'data-vencimento="15"' in azul
    assert CLOSING_ASSUMED not in azul
    assert DUE_ASSUMED not in azul


def test_every_cards_months_sum_to_its_own_remaining_balance(cards_client):
    block = _section(_screen(cards_client).text, "fatura")
    cards = {name: (int(remaining), body) for name, remaining, body in _ARTICLE.findall(block)}

    assert set(cards) == {"Cartão Azul", "Cartão Roxo", "Cartão Verde"}
    for remaining, body in cards.values():
        totals = [int(value) for value in re.findall(r'data-total="(-?\d+)"', body)]
        assert sum(totals) == remaining
    assert cards["Cartão Azul"][0] == -46000
    assert cards["Cartão Roxo"][0] == -20000
    assert cards["Cartão Verde"][0] == 0
    total_cartoes = int(re.search(r'data-total-cartoes="(-?\d+)"', block).group(1))
    assert total_cartoes == -66000


def test_a_card_without_a_live_instalment_shows_the_empty_state_and_no_months(cards_client):
    block = _section(_screen(cards_client).text, "fatura")
    verde = _article(block, 'data-cartao="Cartão Verde"')
    azul = _article(block, 'data-cartao="Cartão Azul"')

    assert "Nenhum parcelamento em aberto neste cartão." in verde
    assert "data-mes=" not in verde
    assert azul.count("data-mes=") == 4


def test_the_page_opens_and_closes_the_same_number_of_sections_it_writes(cards_client):
    page = _screen(cards_client)

    opened = page.text.count("<section")
    closed = page.text.count("</section>")

    assert opened == closed
    assert opened > 0


def test_the_curve_and_the_instalment_table_agree_on_the_engines_own_base(engine_cards_client):
    page = _screen(engine_cards_client)

    assert page.status_code == 200
    restantes = sorted(
        int(value)
        for value in re.findall(
            r'data-restante="(-?\d+)"', "".join(_rows(page.text, "parcelamentos"))
        )
    )
    assert restantes == [-264000, -25000]
    assert sum(restantes) == -289000

    fatura = _section(page.text, "fatura")
    cards = _ARTICLE.findall(fatura)
    assert len(cards) == 1
    _, remaining, body = cards[0]
    assert remaining == "-264000"
    totals = [int(value) for value in re.findall(r'data-total="(-?\d+)"', body)]
    assert sum(totals) == -264000
    assert "loja azul" in fatura
    assert "carne loja" not in fatura
    assert 'data-fora="1"' in fatura
    assert "fora de cartão" in fatura
