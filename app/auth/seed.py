import sqlite3
import sys
from datetime import UTC, datetime

from app.auth.password import hash_password, verify_password
from app.config import load_config
from app.db import connect

CURRENT_HASH = "SELECT password_hash FROM users WHERE login = ?"
INSERT_USER = "INSERT INTO users (login, password_hash, created_at) VALUES (?, ?, ?)"
ROTATE_PASSWORD = (
    "UPDATE users SET password_hash = ?, session_epoch = session_epoch + 1 WHERE login = ?"
)


def seed_user(conn: sqlite3.Connection, login: str, password: str) -> None:
    row = conn.execute(CURRENT_HASH, (login,)).fetchone()
    if row is None:
        created_at = datetime.now(UTC).isoformat(timespec="seconds")
        conn.execute(INSERT_USER, (login, hash_password(password), created_at))
        conn.commit()
        return
    # Argon2id salts every hash, so the stored text always differs from a fresh
    # one: only the password itself says whether anything changed. Seeding the
    # same password again must not log the panel out.
    if verify_password(password, row[0]):
        return
    # A password changed on suspicion of a leak has to take the cookie that may
    # have leaked with it down as well.
    conn.execute(ROTATE_PASSWORD, (hash_password(password), login))
    conn.commit()


def main() -> int:
    config = load_config()
    missing = []
    if not config.login:
        missing.append("LOGIN")
    if not config.password:
        missing.append("PASSWORD")
    if missing:
        for name in missing:
            print(f"missing environment variable: {name}", file=sys.stderr, flush=True)
        return 1
    conn = connect()
    try:
        seed_user(conn, config.login, config.password)
    finally:
        conn.close()
    print(f"seeded user: {config.login}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
