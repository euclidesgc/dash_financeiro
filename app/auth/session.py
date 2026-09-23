from itsdangerous import BadSignature, TimestampSigner
from starlette.responses import Response

COOKIE_NAME = "dash_session"
MAX_AGE_SECONDS = 43200
SEPARATOR = "|"


class _FixedClockSigner(TimestampSigner):
    def __init__(self, secret: str, now: float) -> None:
        super().__init__(secret)
        self._now = now

    def get_timestamp(self) -> int:
        return int(self._now)


def _signer(secret: str, now: float | None) -> TimestampSigner:
    if now is None:
        return TimestampSigner(secret)
    return _FixedClockSigner(secret, now)


def issue_cookie(login: str, *, secret: str, now: float | None = None, epoch: int = 0) -> str:
    payload = f"{login}{SEPARATOR}{epoch}".encode()
    return _signer(secret, now).sign(payload).decode()


def read_cookie(
    raw: str, *, secret: str, now: float | None = None, epoch: int | None = None
) -> str | None:
    try:
        payload = _signer(secret, now).unsign(raw.encode(), max_age=MAX_AGE_SECONDS)
    except BadSignature:
        return None
    # Reason: a cookie minted before the epoch existed carries no separator,
    # and no logout can reach it — it is refused instead of trusted.
    login, separator, carried = bytes(payload).decode().rpartition(SEPARATOR)
    if not separator or not carried.isdigit():
        return None
    if epoch is not None and int(carried) != epoch:
        return None
    return login


def attach_session(response: Response, login: str, *, secret: str, epoch: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        issue_cookie(login, secret=secret, epoch=epoch),
        max_age=MAX_AGE_SECONDS,
        path="/",
        httponly=True,
        samesite="Lax",  # type: ignore[arg-type]  # wire casing "SameSite=Lax" is pinned by test_login.py; typeshed only accepts lowercase
    )


def detach_session(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="Lax",  # type: ignore[arg-type]  # wire casing "SameSite=Lax" is pinned by test_login.py; typeshed only accepts lowercase
    )
