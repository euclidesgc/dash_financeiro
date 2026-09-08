from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.routers.advisor import SCREEN

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
REFERENCE = "2026-09-05"


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
    assert "/configuracao" in page.text
    assert "GEMINI_API_KEY" not in page.text
