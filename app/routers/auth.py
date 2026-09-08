from collections.abc import Mapping
from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.auth.password import verify_absent_user, verify_password
from app.auth.rate_limit import blocked_seconds, record_failure, record_success
from app.auth.session import COOKIE_NAME, MAX_AGE_SECONDS, issue_cookie
from app.auth.users import bump_session_epoch
from app.db import connect

from .render import TEMPLATES

# Reason: one message for both causes, so the screen never tells an
# attacker which logins exist.
REJECTED_MESSAGE = "Login ou senha inválidos."
THROTTLED_MESSAGE = "Muitas tentativas seguidas. Tente novamente mais tarde."

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
        waiting = blocked_seconds(conn, ip)
        if waiting > 0:
            return _form(
                request,
                error=THROTTLED_MESSAGE,
                login=login,
                status_code=429,
                headers={"Retry-After": str(waiting)},
            )
        row = conn.execute(
            "SELECT password_hash, session_epoch FROM users WHERE login = ?", (login,)
        ).fetchone()
        # Reason: the absent login pays for a verification too, so the
        # answer time does not tell which logins exist.
        if row is None:
            accepted = verify_absent_user(senha)
        else:
            accepted = verify_password(senha, row["password_hash"])
        if not accepted:
            record_failure(conn, ip)
            return _form(request, error=REJECTED_MESSAGE, login=login, status_code=401)
        epoch = int(row["session_epoch"])
        record_success(conn, ip)
    finally:
        conn.close()
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        COOKIE_NAME,
        issue_cookie(login, secret=request.app.state.session_secret, epoch=epoch),
        max_age=MAX_AGE_SECONDS,
        path="/",
        httponly=True,
        samesite="Lax",  # type: ignore[arg-type]  # wire casing "SameSite=Lax" is pinned by test_login.py; typeshed only accepts lowercase
    )
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
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="Lax",  # type: ignore[arg-type]  # wire casing "SameSite=Lax" is pinned by test_login.py; typeshed only accepts lowercase
    )
    return response
