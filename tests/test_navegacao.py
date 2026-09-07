import re

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.routers import (
    advisor,
    commitments,
    debts,
    navigation,
    plan,
    rules,
    settings,
    spending,
    summary,
    whatif,
)

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

CURRENT = re.compile(r'aria-current="page"[^>]*>([^<]+)</a>')
LINK = re.compile(r'class="rail-link[^"]*"\s+href="([^"]+)"')


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


@pytest.mark.parametrize("screen", navigation.SCREENS, ids=lambda item: item["href"])
def test_every_screen_carries_the_whole_rail(client, screen):
    page = client.get(screen["href"])
    assert page.status_code == 200, page.status_code
    assert LINK.findall(page.text) == [item["href"] for item in navigation.SCREENS]
    assert "</button>" in page.text and ">Sair<" in page.text


@pytest.mark.parametrize("screen", navigation.SCREENS, ids=lambda item: item["href"])
def test_the_open_screen_is_the_one_marked(client, screen):
    page = client.get(screen["href"])
    assert CURRENT.findall(page.text) == [screen["label"]]


def test_the_login_has_no_rail(client):
    page = client.get("/login")
    assert page.status_code == 200
    # The stylesheet travels inside the document, so the class name is in every
    # page: what says the rail is absent is the element, not the word.
    assert 'aria-label="Telas do painel"' not in page.text
    assert not LINK.findall(page.text)


def test_a_screen_keeps_the_mark_inside_its_own_paths():
    assert navigation.current("/regras/7/editar", "/regras")
    assert not navigation.current("/regras", "/")
    assert not navigation.current("/gastos", "/configuracao")


def test_no_screen_route_is_missing_from_the_rail():
    # A screen that exists and is not on the rail is a screen nobody reaches:
    # the source of truth is the router that declares it, not this list.
    declared = {
        module.SCREEN
        for module in (advisor, commitments, debts, plan, rules, settings, spending, summary, whatif)
    }
    assert declared == {item["href"] for item in navigation.SCREENS}
