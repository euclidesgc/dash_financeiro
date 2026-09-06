import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
TOKENS_STYLESHEET = ROOT / "app" / "static" / "css" / "tokens.css"

STYLE_BLOCK = re.compile(r"<style>(.*?)</style>", re.DOTALL)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    with TestClient(create_app(), follow_redirects=False) as opened:
        yield opened


def test_the_login_page_carries_the_tokens_it_was_built_from(client):
    page = client.get("/login")
    blocks = STYLE_BLOCK.findall(page.text)
    declared = re.search(r"--color-bg:\s*[^;]+;", TOKENS_STYLESHEET.read_text(encoding="utf-8"))

    assert declared is not None
    assert any(declared.group(0) in block for block in blocks)


def test_the_page_needs_no_network_to_dress_itself(client):
    page = client.get("/login")

    assert "<link" not in page.text
    assert "http://" not in page.text
    assert "https://" not in page.text


def test_the_stylesheet_has_no_route_of_its_own(client):
    served = client.get("/static/css/tokens.css")

    assert served.status_code != 200
    assert "--color-bg" not in served.text


def test_the_form_names_its_fields_for_a_person_and_for_a_browser(client):
    page = client.get("/login")

    for bound in ('<label class="field-label" for="campo-login">', 'id="campo-login"'):
        assert bound in page.text
    for bound in ('<label class="field-label" for="campo-senha">', 'id="campo-senha"'):
        assert bound in page.text
    assert 'autocomplete="username"' in page.text
    assert 'autocomplete="current-password"' in page.text
    assert "aria-describedby" not in page.text


def test_the_rejection_reaches_the_field_that_caused_it(client):
    rejected = client.post("/login", data={"login": "teste", "senha": "errada"})

    password_field = re.search(r"<input[^>]*id=\"campo-senha\"[^>]*>", rejected.text)

    assert rejected.text.count('id="erro-credencial"') == 1
    assert rejected.text.count('aria-describedby="erro-credencial"') == 2
    assert password_field is not None
    assert "value=" not in password_field.group(0)
    assert "errada" not in rejected.text
