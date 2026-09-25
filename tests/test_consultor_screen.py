import re

import httpx
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.routers.advisor import SCREEN

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
REFERENCE = "2026-09-05"
CONFIG_OFFER = "/configuracao/proposta"


def _app(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", REFERENCE)
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()
    return app


def _section(html: str, marker: str) -> str:
    start = html.index(marker)
    end = html.index("</section>", start)
    return html[start:end]


def _step(**overrides):
    row = {
        "kind": "overdraft",
        "name": "Conta corrente",
        "balance_cents": -500000,
        "monthly_rate_bp": 2000,
        "source": "accounts",
    }
    row.update(overrides)
    conn = connect()
    conn.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source) "
        "VALUES (:kind, :name, :balance_cents, :monthly_rate_bp, :source)",
        row,
    )
    conn.commit()
    conn.close()


def _offer_response(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_the_screen_answers_without_a_date_and_shows_no_refusal(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        page = client.get(SCREEN)

    assert page.status_code == 200
    assert 'id="recusa"' not in page.text
    assert f'<input type="hidden" name="data" value="{REFERENCE}">' in page.text


def test_an_unreadable_date_is_refused_and_the_screen_still_answers_by_the_reference(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        page = client.get(SCREEN, params={"data": "banana"})

    assert page.status_code == 200
    assert 'id="recusa"' in page.text
    assert "data inválida: data (banana)" in page.text
    assert f'<input type="hidden" name="data" value="{REFERENCE}">' in page.text


def test_without_any_key_the_screen_points_to_the_configuration_screen(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = _app(tmp_path, monkeypatch)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        page = client.get(SCREEN)

    assert page.status_code == 200
    assert '<a href="/configuracao#ia">Configuração</a>' in page.text
    assert ">/configuracao</a>" not in page.text
    assert "GEMINI_API_KEY" not in page.text


def test_the_comparison_section_shows_the_three_costs_and_names_who_is_left_out(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    _step()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        client.post(
            CONFIG_OFFER,
            data={
                "nome": "Banco Teste",
                "taxa": "10",
                "prazo": "2",
                "liberado": "1.000,00",
                "contratacao": "50,00",
            },
        )
        client.post(
            CONFIG_OFFER,
            data={"nome": "Banco Sem Taxa", "taxa": "", "prazo": "24", "liberado": "1.000,00"},
        )
        page = client.get(SCREEN)

    assert page.status_code == 200
    section = _section(page.text, 'id="comparativo"')
    assert "R$ 309,10" in section
    assert "R$ 202,38" in section
    assert "R$ 106,72" in section
    assert "diferença" in section
    assert "Conta corrente" in section
    assert "1 proposta ficou de fora" in section
    assert "Banco Sem Taxa" in section


def test_without_a_key_the_comparison_still_shows_every_figure(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = _app(tmp_path, monkeypatch)
    _step()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        client.post(
            CONFIG_OFFER,
            data={
                "nome": "Banco Teste",
                "taxa": "10",
                "prazo": "2",
                "liberado": "1.000,00",
                "contratacao": "50,00",
            },
        )
        page = client.get(SCREEN)

    assert page.status_code == 200
    section = _section(page.text, 'id="comparativo"')
    assert "R$ 309,10" in section
    assert "R$ 202,38" in section
    assert "R$ 106,72" in section
    assert "a leitura não roda" in page.text
    assert "/configuracao" in page.text


def test_a_reading_that_only_cites_context_figures_is_shown(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-teste")
    app = _app(tmp_path, monkeypatch)
    _step()
    captured: dict = {}
    reading_text = "O caminho da proposta custa R$ 202,38 e continuar como está custa R$ 309,10."

    def fake_post(url, *, headers, json, timeout):
        captured["body"] = json

        class Answer:
            def raise_for_status(self):
                return None

            def json(self):
                return _offer_response(reading_text)

        return Answer()

    monkeypatch.setattr(httpx, "post", fake_post)

    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        client.post(
            CONFIG_OFFER,
            data={
                "nome": "Banco Teste",
                "taxa": "10",
                "prazo": "2",
                "liberado": "1.000,00",
                "contratacao": "50,00",
            },
        )
        page = client.post(SCREEN, data={"pergunta": "qual sai mais barato?"})

    assert page.status_code == 200
    assert 'id="leitura"' in page.text
    assert reading_text in page.text

    text_sent = captured["body"]["contents"][0]["parts"][0]["text"]
    for figure in re.findall(r"R\$ [\d.]+,\d{2}", reading_text):
        assert figure in text_sent


def test_a_reading_citing_a_figure_outside_the_context_is_discarded_not_flagged(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-teste")
    app = _app(tmp_path, monkeypatch)
    _step()

    def fake_post(*args, **kwargs):
        class Answer:
            def raise_for_status(self):
                return None

            def json(self):
                return _offer_response("Essa proposta te economiza R$ 987.654,32 no total.")

        return Answer()

    monkeypatch.setattr(httpx, "post", fake_post)

    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        client.post(
            CONFIG_OFFER,
            data={
                "nome": "Banco Teste",
                "taxa": "10",
                "prazo": "2",
                "liberado": "1.000,00",
                "contratacao": "50,00",
            },
        )
        page = client.post(SCREEN, data={"pergunta": "qual sai mais barato?"})

    assert page.status_code == 200
    assert 'id="leitura"' not in page.text
    assert "987.654,32" not in page.text
    assert 'id="nao-conferido"' in page.text
    assert "não está no contexto" in page.text
    assert "números da tela são os mesmos" in page.text
