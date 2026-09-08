from pathlib import Path

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


ROUTERS_DIR = Path(__file__).resolve().parent.parent / "app" / "routers"

CLOCK_CALL = "date.today()"


def _sources(root: Path) -> dict[str, str]:
    found = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts:
            continue
        found[relative.as_posix()] = path.read_text(encoding="utf-8")
    return found


def _tree(root: Path, files: dict[str, str]) -> Path:
    for relative, text in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return root


def _accused(sources: dict[str, str]) -> list[str]:
    return sorted(name for name, text in sources.items() if CLOCK_CALL in text)


def test_no_router_resolves_the_screen_date_by_itself():
    accused = _accused(_sources(ROUTERS_DIR))

    assert accused == [], f"resolve a data pelo relógio: {', '.join(accused)}"


def test_the_sweep_reaches_every_module_of_the_routers_folder():
    top_level = {entry.name for entry in ROUTERS_DIR.iterdir() if entry.suffix == ".py"}
    sources = _sources(ROUTERS_DIR)

    assert top_level <= sources.keys()
    assert all(name.endswith(".py") for name in sources)
    assert all("__pycache__" not in name for name in sources)
    assert _accused(sources) == []


def test_the_sweep_accuses_a_router_inside_a_subpackage(tmp_path):
    clock = "from datetime import date\ndate.today()\n"
    _tree(tmp_path, {"cards/screen.py": clock, "cards/detail/screen.py": clock})

    accused = _accused(_sources(tmp_path))

    assert accused == ["cards/detail/screen.py", "cards/screen.py"]


def test_the_sweep_accepts_a_subpackage_router_that_reads_the_reference(tmp_path):
    reader = (
        "from app.routers.reference import screen_date\n"
        "\n"
        "\n"
        "def screen(pedido):\n"
        "    return screen_date(pedido).date\n"
    )
    _tree(tmp_path, {"cards/screen.py": reader})

    sources = _sources(tmp_path)

    assert "cards/screen.py" in sources
    assert _accused(sources) == []


def test_two_routers_of_the_same_name_are_two_measurements(tmp_path):
    reader = "from app.routers.reference import screen_date\n"
    clock = "from datetime import date\ndate.today()\n"
    _tree(tmp_path, {"cards/screen.py": reader, "goals/screen.py": clock})

    sources = _sources(tmp_path)

    assert sources.keys() == {"cards/screen.py", "goals/screen.py"}
    assert _accused(sources) == ["goals/screen.py"]


def test_a_cached_copy_is_not_a_router(tmp_path):
    reader = "from app.routers.reference import screen_date\n"
    clock = "from datetime import date\ndate.today()\n"
    _tree(tmp_path, {"screen.py": reader, "__pycache__/screen.py": clock})

    sources = _sources(tmp_path)

    assert sources.keys() == {"screen.py"}
    assert _accused(sources) == []
