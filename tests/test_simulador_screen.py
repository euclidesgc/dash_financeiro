from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.routers.whatif import FACT, SCREEN

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
REFERENCE = "2026-09-05"

NOT_DUE_FACT = "quitacao-cdc"
NOT_DUE_VALIDITY = "2026-09-06"
DUE_FACT = "transporte-sem-carro"
DUE_VALIDITY = "2026-09-04"


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


def _row(html: str, fact: str) -> str:
    start = html.index(f'data-fato="{fact}"')
    return html[start : html.index("</tr>", start)]


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


def test_the_stale_mark_follows_the_reference_not_the_clock(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        client.post(
            FACT, data={"nome": NOT_DUE_FACT, "valor": "1.000,00", "validade": NOT_DUE_VALIDITY}
        )
        client.post(FACT, data={"nome": DUE_FACT, "valor": "500,00", "validade": DUE_VALIDITY})
        page = client.get(SCREEN)

    assert "vencido" not in _row(page.text, NOT_DUE_FACT)
    assert "vencido" in _row(page.text, DUE_FACT)
