from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from app.auth.session import COOKIE_NAME, read_cookie
from app.auth.users import session_epoch
from app.db import connect

# Reason: the login form is the only door that can be reached without a
# session — guarding it too would turn the redirect of RF-26 into a loop.
PUBLIC_PATHS = frozenset({"/login"})
JSON_PATHS = frozenset({"/health"})


def _answers_json(path: str) -> bool:
    return path in JSON_PATHS or path.startswith("/api/")


def _stored_epoch(login: str) -> int | None:
    # Reason: a SQLite connection cannot cross threads, so the request opens
    # and closes its own instead of sharing one held by the app.
    conn = connect()
    try:
        return session_epoch(conn, login)
    finally:
        conn.close()


def _session_login(request: Request) -> str | None:
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    secret = request.app.state.session_secret
    signed = read_cookie(raw, secret=secret)
    if signed is None:
        return None
    epoch = _stored_epoch(signed)
    if epoch is None:
        return None
    return read_cookie(raw, secret=secret, epoch=epoch)


async def require_session(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    path = request.url.path
    if path in PUBLIC_PATHS:
        return await call_next(request)
    login = _session_login(request)
    if login is None:
        if _answers_json(path):
            return JSONResponse({"detail": "nao autenticado"}, status_code=401)
        return RedirectResponse("/login", status_code=302)
    request.state.login = login
    return await call_next(request)


def install_guard(app: FastAPI) -> None:
    app.middleware("http")(require_session)
