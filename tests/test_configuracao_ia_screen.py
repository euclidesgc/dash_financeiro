import logging
import re

import httpx
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.routers.settings import IA, IA_FORGET, SCREEN

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
REFERENCE = "2026-09-05"
ENV_KEY = "chave-do-ambiente-MB9Z"
SCREEN_KEY = "chave-da-tela-0123456789ABCDEF"

ANSWER_OK = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}


def _app(tmp_path, monkeypatch, *, gemini_key=None):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", REFERENCE)
    if gemini_key is None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GEMINI_API_KEY", gemini_key)
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()
    return app


class _Response:
    def __init__(self, body, status_code=200):
        self._body = body
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(str(self.status_code), request=None, response=self)

    def json(self):
        return self._body


def _double(monkeypatch, calls, *, status_code=200):
    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return _Response(ANSWER_OK, status_code=status_code)

    monkeypatch.setattr(httpx, "post", fake_post)


def _login(client):
    client.post("/login", data={"login": LOGIN, "senha": PASSWORD})


def test_the_section_lists_after_beneficiaries_with_nothing_stored(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with TestClient(app, follow_redirects=False) as client:
        _login(client)
        page = client.get(SCREEN)

    assert page.status_code == 200
    text = page.text
    assert text.count('id="ia"') == 1
    assert text.index('id="beneficiarios"') < text.index('id="ia"')
    assert '<option value="gemini-2.5-flash"' in text
    assert '<option value="gemini-2.5-pro"' in text
    assert '<option value="gemini-2.5-flash-lite"' in text
    assert f'action="{IA}"' in text
    assert "Nenhuma chave guardada" in text
    match = re.search(r'<input[^>]*name="chave"[^>]*>', text)
    assert match is not None
    assert "value=" not in match.group(0)


def test_saving_the_key_answers_with_the_whole_screen_and_reaches_the_provider_by_header(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch, gemini_key=ENV_KEY)
    calls = []
    _double(monkeypatch, calls)
    with TestClient(app, follow_redirects=False) as client:
        _login(client)
        saved = client.post(IA, data={"chave": SCREEN_KEY, "modelo": "gemini-2.5-pro"})
        client.post("/consultor", data={"pergunta": "e daí?"})

    assert saved.status_code == 200
    assert "Salvo." in saved.text
    assert 'id="ia"' in saved.text
    assert len(calls) == 1
    assert "gemini-2.5-pro" in str(calls[0]["url"])
    assert calls[0]["headers"]["x-goog-api-key"] == SCREEN_KEY


def test_an_empty_field_keeps_the_stored_key_and_still_changes_the_model(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    calls = []
    _double(monkeypatch, calls)
    with TestClient(app, follow_redirects=False) as client:
        _login(client)
        client.post(IA, data={"chave": SCREEN_KEY, "modelo": "gemini-2.5-flash"})
        second = client.post(IA, data={"chave": "", "modelo": "gemini-2.5-pro"})
        client.post("/consultor", data={"pergunta": "e daí?"})

    assert second.status_code == 200
    assert "Salvo." in second.text
    assert "Há uma chave guardada nesta tela" in second.text
    assert "CDEF" in second.text
    assert calls[-1]["headers"]["x-goog-api-key"] == SCREEN_KEY
    assert "gemini-2.5-pro" in str(calls[-1]["url"])


def test_forgetting_the_key_hands_control_back_to_the_environment(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, gemini_key=ENV_KEY)
    calls = []
    _double(monkeypatch, calls)
    with TestClient(app, follow_redirects=False) as client:
        _login(client)
        client.post(IA, data={"chave": SCREEN_KEY, "modelo": "gemini-2.5-flash"})
        forgotten = client.post(IA_FORGET)
        client.post("/consultor", data={"pergunta": "e daí?"})

    assert forgotten.status_code == 200
    assert "Chave apagada." in forgotten.text
    assert "Sem chave gravada aqui, o painel usa a do ambiente" in forgotten.text
    assert "MB9Z" in forgotten.text
    assert "Há uma chave guardada nesta tela" not in forgotten.text
    assert calls[-1]["headers"]["x-goog-api-key"] == ENV_KEY


def test_an_unknown_model_is_refused_with_the_whole_screen_and_writes_no_key(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, gemini_key=ENV_KEY)
    with TestClient(app, follow_redirects=False) as client:
        _login(client)
        refused = client.post(IA, data={"chave": SCREEN_KEY, "modelo": "gemini-9-turbo"})

    assert refused.status_code == 400
    assert 'id="ia"' in refused.text
    assert 'id="beneficiarios"' in refused.text
    assert 'id="recusa"' in refused.text
    assert "Modelo desconhecido. Escolha um da lista:" in refused.text
    for name in ("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"):
        assert name in refused.text
    assert "Sem chave gravada aqui, o painel usa a do ambiente" in refused.text


def test_the_key_never_leaks_even_when_the_provider_refuses_it(
    tmp_path, monkeypatch, caplog, capsys
):
    caplog.set_level(logging.DEBUG)
    app = _app(tmp_path, monkeypatch, gemini_key=ENV_KEY)
    calls = []
    _double(monkeypatch, calls, status_code=401)
    with TestClient(app, follow_redirects=False) as client:
        _login(client)
        client.post(IA, data={"chave": SCREEN_KEY, "modelo": "gemini-2.5-flash"})

        screen = client.get(SCREEN)
        advisor = client.get("/consultor")
        refused_model = client.post(IA, data={"chave": SCREEN_KEY, "modelo": "nao-existe"})
        asked = client.post("/consultor", data={"pergunta": "e daí?"})

    out, err = capsys.readouterr()
    for haystack in (
        screen.text,
        advisor.text,
        refused_model.text,
        asked.text,
        caplog.text,
        out,
        err,
    ):
        assert SCREEN_KEY not in haystack
        assert ENV_KEY not in haystack
    assert 'id="indisponivel"' in asked.text
    assert "a chave foi recusada pelo provedor" in asked.text
    assert "CDEF" in screen.text
    assert "BCDEF" not in screen.text


def test_the_key_travels_in_the_header_and_never_in_the_url(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    calls = []
    _double(monkeypatch, calls)
    with TestClient(app, follow_redirects=False) as client:
        _login(client)
        client.post(IA, data={"chave": SCREEN_KEY, "modelo": "gemini-2.5-flash"})
        client.post("/consultor", data={"pergunta": "e daí?"})

    call = calls[-1]
    assert call["headers"]["x-goog-api-key"] == SCREEN_KEY
    assert SCREEN_KEY not in str(call["url"])
    assert call.get("params") is None or SCREEN_KEY not in str(call.get("params"))
    assert "key=" not in str(call["url"])
