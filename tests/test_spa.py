import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.guard import install_guard
from app.spa import SPA_MISSING, mount_spa


@pytest.fixture()
def spa_client(tmp_path, monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>spa shell</html>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("window.appLoaded = true", encoding="utf-8")

    app = FastAPI()
    app.state.session_secret = "chave-de-teste"
    install_guard(app)
    mount_spa(app, dist)
    with TestClient(app, follow_redirects=False) as opened:
        yield opened


def test_app_root_returns_index_without_session(spa_client):
    response = spa_client.get("/app/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text == "<html>spa shell</html>"


def test_app_deep_path_returns_index_without_session(spa_client):
    response = spa_client.get("/app/qualquer/coisa")

    assert response.status_code == 200
    assert response.text == "<html>spa shell</html>"


def test_app_assets_are_served_statically(spa_client):
    response = spa_client.get("/app/assets/app.js")

    assert response.status_code == 200
    assert response.text == "window.appLoaded = true"


def test_without_dist_answers_503(tmp_path, monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = FastAPI()
    app.state.session_secret = "chave-de-teste"
    install_guard(app)
    mount_spa(app, tmp_path / "does-not-exist")

    with TestClient(app, follow_redirects=False) as client:
        response = client.get("/app/")

    assert response.status_code == 503
    assert response.json() == {"detail": SPA_MISSING}


def test_apple_is_not_public(spa_client):
    response = spa_client.get("/apple")

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_api_under_app_prefix_still_requires_session(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    from app.main import create_app

    app = create_app()
    with TestClient(app, follow_redirects=False) as client:
        response = client.get("/api/accounts/balances")

    assert response.status_code == 401
