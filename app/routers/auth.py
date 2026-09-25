from collections.abc import Mapping
from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.auth.attempt import REJECTED_MESSAGE, THROTTLED_MESSAGE, attempt_login
from app.auth.session import attach_session, detach_session
from app.auth.users import bump_session_epoch
from app.db import connect

from .render import TEMPLATES

router = APIRouter()


def _form(
    request: Request,
    *,
    error: str | None,
    login: str = "",
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
) -> Response:
    return TEMPLATES.TemplateResponse(
        request,
        "login.html",
        {"error": error, "login": login},
        status_code=status_code,
        headers=headers,
    )


@router.get("/login")
def login_form(request: Request) -> Response:
    return _form(request, error=None)


@router.post("/login")
def submit_login(
    request: Request,
    login: Annotated[str, Form()] = "",
    senha: Annotated[str, Form()] = "",
) -> Response:
    ip = request.client.host if request.client else "unknown"
    conn = connect()
    try:
        outcome = attempt_login(conn, ip, login, senha)
    finally:
        conn.close()
    if outcome.retry_after > 0:
        return _form(
            request,
            error=THROTTLED_MESSAGE,
            login=login,
            status_code=429,
            headers={"Retry-After": str(outcome.retry_after)},
        )
    if not outcome.accepted:
        return _form(request, error=REJECTED_MESSAGE, login=login, status_code=401)
    response = RedirectResponse("/", status_code=302)
    attach_session(response, login, secret=request.app.state.session_secret, epoch=outcome.epoch)
    return response


@router.post("/logout")
def logout(request: Request) -> Response:
    login = getattr(request.state, "login", None)
    if login:
        conn = connect()
        try:
            bump_session_epoch(conn, login)
        finally:
            conn.close()
    response = RedirectResponse("/login", status_code=302)
    detach_session(response)
    return response
