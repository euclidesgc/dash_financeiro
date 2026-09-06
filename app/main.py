from fastapi import FastAPI

from app.auth.guard import install_guard
from app.config import resolve_session_secret
from app.migrate import run_migrations
from app.routers import auth, health, pages


def create_app() -> FastAPI:
    run_migrations()
    app = FastAPI()
    app.state.session_secret = resolve_session_secret()
    install_guard(app)
    app.include_router(auth.router)
    app.include_router(pages.router)
    app.include_router(health.router)
    return app
