import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_DB_PATH = "data/dash.sqlite"
DEFAULT_ENV_FILE = ".env"
DEFAULT_KEY_PATH = "data/session.key"
DEFAULT_TRANSACTIONS_PATH = "data/processed/transacoes.json"
DEFAULT_ACCOUNTS_GLOB = "data/raw/accounts_*.json"
SESSION_SECRET_BYTES = 32

# The panel reads the already consolidated file by default: it is the path that
# works without network, and the one every test exercises.
DEFAULT_SYNC_SOURCE = "arquivo"
PLUGGY_CREDENTIALS = ("PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET")


@dataclass(frozen=True)
class Config:
    login: str | None
    password: str | None
    gemini_api_key: str | None
    db_path: str
    session_secret: str | None
    key_path: str
    transactions_path: str
    accounts_glob: str
    sync_source: str
    pluggy: dict[str, str | None]


def _first(env: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        value = env.get(name)
        if value:
            return value
    return None


def _environment(env: Mapping[str, str] | None) -> Mapping[str, str]:
    if env is not None:
        return env
    load_dotenv(os.environ.get("DASH_ENV_FILE", DEFAULT_ENV_FILE), override=False)
    return os.environ


def reference_date(env: Mapping[str, str] | None = None) -> date:
    # Read by the commands that decide what is still alive. Without it the same
    # command over an unchanged base answers differently tomorrow, and no run can
    # be replayed or compared against the frozen reference numbers.
    value = _first(_environment(env), "DASH_TODAY")
    return date.fromisoformat(value) if value else date.today()


def load_config(env: Mapping[str, str] | None = None) -> Config:
    env = _environment(env)
    return Config(
        login=_first(env, "LOGIN"),
        password=_first(env, "PASSWORD", "PASSORD"),
        gemini_api_key=_first(env, "GEMINI_API_KEY", "GEMIMI_API_KEY"),
        db_path=_first(env, "DASH_DB_PATH") or DEFAULT_DB_PATH,
        session_secret=_first(env, "SESSION_SECRET"),
        key_path=_first(env, "DASH_KEY_PATH") or DEFAULT_KEY_PATH,
        transactions_path=_first(env, "DASH_TRANSACTIONS_PATH") or DEFAULT_TRANSACTIONS_PATH,
        accounts_glob=_first(env, "DASH_ACCOUNTS_GLOB") or DEFAULT_ACCOUNTS_GLOB,
        sync_source=_first(env, "DASH_SYNC_SOURCE") or DEFAULT_SYNC_SOURCE,
        pluggy={name: _first(env, name) for name in PLUGGY_CREDENTIALS},
    )


def resolve_session_secret(config: Config | None = None) -> str:
    settings = config or load_config()
    if settings.session_secret:
        return settings.session_secret
    path = Path(settings.key_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        stored = path.read_text(encoding="utf-8").strip()
        # An empty key file signs every cookie with an empty secret, which anyone
        # can forge: two processes racing, an interrupted write or a restored
        # backup all reach here, and none of them may boot the app.
        if not stored:
            raise RuntimeError(f"empty session key file: {path}") from None
        return stored
    secret = secrets.token_hex(SESSION_SECRET_BYTES)
    with os.fdopen(handle, "w", encoding="utf-8") as file:
        file.write(secret)
    # The creation mode passes through the umask, so the mode is stated again.
    os.chmod(path, 0o600)
    return secret
