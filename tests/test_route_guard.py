import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routers.auth import REJECTED_MESSAGE

PUBLIC = {("GET", "/login"), ("POST", "/login")}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    with TestClient(create_app(), follow_redirects=False) as opened:
        yield opened


# FastAPI keeps an included router as a single wrapper entry in app.routes, so
# the sweep has to walk into it to reach the routes it carries.
def _registered(app, routes=None, prefix=""):
    for route in app.routes if routes is None else routes:
        nested = getattr(route, "original_router", None)
        if nested is not None:
            context = getattr(route, "include_context", None)
            yield from _registered(app, nested.routes, prefix + getattr(context, "prefix", ""))
            continue
        path = getattr(route, "path", None)
        if path is None:
            continue
        for method in sorted(getattr(route, "methods", {"GET"})):
            yield method, prefix + path


def test_every_registered_route_requires_session(client):
    guarded = []
    for method, path in _registered(client.app):
        if (method, path) in PUBLIC:
            continue
        response = client.request(method, path)
        assert response.status_code in {302, 401}, f"{method} {path} sem guarda"
        guarded.append((method, path))

    assert ("GET", "/health") in guarded
    assert ("GET", "/") in guarded
    assert ("POST", "/logout") in guarded


def test_the_login_form_is_the_open_door(client):
    form = client.get("/login")

    assert form.status_code == 200
    for attribute in ('method="post"', 'action="/login"', 'name="login"', 'name="senha"'):
        assert attribute in form.text

    # The rejection message proves the handler answered: had the guard caught
    # this route, the answer would be a redirect instead.
    rejected = client.post("/login", data={"login": "teste", "senha": "errada"})

    assert rejected.status_code == 401
    assert REJECTED_MESSAGE in rejected.text
