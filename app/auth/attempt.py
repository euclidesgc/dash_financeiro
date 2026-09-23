import sqlite3
from dataclasses import dataclass

from app.auth.password import verify_absent_user, verify_password
from app.auth.rate_limit import blocked_seconds, record_failure, record_success

# Reason: one message for both causes, so the screen never tells an
# attacker which logins exist.
REJECTED_MESSAGE = "Login ou senha inválidos."
THROTTLED_MESSAGE = "Muitas tentativas seguidas. Tente novamente mais tarde."


@dataclass(frozen=True)
class LoginOutcome:
    accepted: bool
    epoch: int
    retry_after: int


def attempt_login(conn: sqlite3.Connection, ip: str, login: str, password: str) -> LoginOutcome:
    waiting = blocked_seconds(conn, ip)
    if waiting > 0:
        return LoginOutcome(False, 0, waiting)
    row = conn.execute(
        "SELECT password_hash, session_epoch FROM users WHERE login = ?", (login,)
    ).fetchone()
    # Reason: the absent login pays for a verification too, so the answer
    # time does not tell which logins exist.
    if row is None:
        accepted = verify_absent_user(password)
    else:
        accepted = verify_password(password, row["password_hash"])
    if not accepted:
        record_failure(conn, ip)
        return LoginOutcome(False, 0, 0)
    record_success(conn, ip)
    return LoginOutcome(True, int(row["session_epoch"]), 0)
