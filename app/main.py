from pathlib import Path

from fastapi import FastAPI

from app.auth.guard import install_guard
from app.config import resolve_session_secret
from app.migrate import run_migrations
from app.routers import (
    accounts,
    advisor,
    auth,
    auth_api,
    cards,
    commitments,
    debts,
    financings,
    health,
    offers,
    plan,
    rules,
    settings,
    spending,
    summary,
    sync,
    transactions,
    whatif,
)
from app.routers.navigation import marked
from app.routers.render import (
    TEMPLATES,
    brl,
    day,
    month,
    number,
    rate,
    unit_typed,
    unit_value,
)
from app.settings import limits
from app.spa import mount_spa

STYLESHEETS_FOLDER = Path(__file__).resolve().parent / "static" / "css"


def _stylesheet(name: str) -> str:
    return (STYLESHEETS_FOLDER / name).read_text(encoding="utf-8")


def create_app() -> FastAPI:
    run_migrations()
    app = FastAPI()
    # Reason: the stylesheet travels inside the document instead of over a
    # /static route — every registered route demands a session, and the login
    # page needs its own styling before any session exists.
    TEMPLATES.env.globals["tokens_css"] = _stylesheet("tokens.css")
    TEMPLATES.env.globals["app_css"] = _stylesheet("app.css")
    TEMPLATES.env.globals["screens"] = marked
    # Reason: RF-03 asks for the same number on both sides — the template
    # reads the ceiling from here instead of repeating it.
    TEMPLATES.env.globals["limits"] = limits
    TEMPLATES.env.filters["brl"] = brl
    TEMPLATES.env.filters["dia"] = day
    TEMPLATES.env.filters["mes"] = month
    TEMPLATES.env.filters["taxa"] = rate
    TEMPLATES.env.filters["numero"] = number
    TEMPLATES.env.filters["unidade"] = unit_value
    TEMPLATES.env.filters["digitado"] = unit_typed
    app.state.session_secret = resolve_session_secret()
    install_guard(app)
    app.include_router(auth.router)
    app.include_router(auth_api.router)
    app.include_router(accounts.router)
    app.include_router(sync.router)
    app.include_router(transactions.router)
    app.include_router(cards.router)
    app.include_router(summary.router)
    app.include_router(spending.router)
    app.include_router(rules.router)
    app.include_router(commitments.router)
    app.include_router(debts.router)
    app.include_router(plan.router)
    app.include_router(whatif.router)
    app.include_router(settings.router)
    app.include_router(financings.router)
    app.include_router(offers.router)
    app.include_router(advisor.router)
    app.include_router(health.router)
    mount_spa(app, Path("dist"))
    return app
