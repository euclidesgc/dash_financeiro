from fastapi import APIRouter
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.auth.attempt import REJECTED_MESSAGE, THROTTLED_MESSAGE, attempt_login
from app.auth.session import attach_session, detach_session
from app.auth.users import bump_session_epoch
from app.db import connect

router = APIRouter(prefix="/api/auth")


class LoginRequest(BaseModel):
    login: str
    password: str


class MeResponse(BaseModel):
    login: str


@router.post("/login", status_code=204)
def api_login(request: Request, body: LoginRequest) -> Response:
    ip = request.client.host if request.client else "unknown"
    conn = connect()
    try:
        outcome = attempt_login(conn, ip, body.login, body.password)
    finally:
        conn.close()
    if outcome.retry_after > 0:
        return JSONResponse(
            {"detail": THROTTLED_MESSAGE},
            status_code=429,
            headers={"Retry-After": str(outcome.retry_after)},
        )
    if not outcome.accepted:
        return JSONResponse({"detail": REJECTED_MESSAGE}, status_code=401)
    response = Response(status_code=204)
    attach_session(
        response, body.login, secret=request.app.state.session_secret, epoch=outcome.epoch
    )
    return response


@router.post("/logout", status_code=204)
def api_logout(request: Request) -> Response:
    login = getattr(request.state, "login", None)
    if login:
        conn = connect()
        try:
            bump_session_epoch(conn, login)
        finally:
            conn.close()
    response = Response(status_code=204)
    detach_session(response)
    return response


@router.get("/me")
def api_me(request: Request) -> MeResponse:
    return MeResponse(login=request.state.login)
