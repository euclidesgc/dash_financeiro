from pathlib import Path

from fastapi import FastAPI

from app.auth.guard import install_guard
from app.config import resolve_session_secret
from app.migrate import run_migrations
from app.routers import auth, health, pages, spending
from app.routers.render import TEMPLATES, brl, day

STYLESHEETS_FOLDER = Path(__file__).resolve().parent / "static" / "css"


def _stylesheet(name: str) -> str:
    return (STYLESHEETS_FOLDER / name).read_text(encoding="utf-8")


def create_app() -> FastAPI:
    run_migrations()
    app = FastAPI()
    # The stylesheet travels inside the document instead of over a /static route:
    # every registered route demands a session, and the login page needs its own
    # styling before any session exists.
    TEMPLATES.env.globals["tokens_css"] = _stylesheet("tokens.css")
    TEMPLATES.env.globals["app_css"] = _stylesheet("app.css")
    TEMPLATES.env.filters["brl"] = brl
    TEMPLATES.env.filters["dia"] = day
    app.state.session_secret = resolve_session_secret()
    install_guard(app)
    app.include_router(auth.router)
    app.include_router(pages.router)
    app.include_router(spending.router)
    app.include_router(health.router)
    return app
