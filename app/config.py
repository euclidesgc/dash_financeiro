import os
from collections.abc import Mapping
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_DB_PATH = "data/dash.sqlite"
DEFAULT_ENV_FILE = ".env"
DEFAULT_TRANSACTIONS_PATH = "data/processed/transacoes.json"
DEFAULT_ACCOUNTS_GLOB = "data/raw/accounts_*.json"


@dataclass(frozen=True)
class Config:
    login: str | None
    password: str | None
    gemini_api_key: str | None
    db_path: str
    session_secret: str | None
    transactions_path: str
    accounts_glob: str


def _first(env: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        value = env.get(name)
        if value:
            return value
    return None


def load_config(env: Mapping[str, str] | None = None) -> Config:
    if env is None:
        load_dotenv(os.environ.get("DASH_ENV_FILE", DEFAULT_ENV_FILE), override=False)
        env = os.environ
    return Config(
        login=_first(env, "LOGIN"),
        password=_first(env, "PASSWORD", "PASSORD"),
        gemini_api_key=_first(env, "GEMINI_API_KEY", "GEMIMI_API_KEY"),
        db_path=_first(env, "DASH_DB_PATH") or DEFAULT_DB_PATH,
        session_secret=_first(env, "SESSION_SECRET"),
        transactions_path=_first(env, "DASH_TRANSACTIONS_PATH") or DEFAULT_TRANSACTIONS_PATH,
        accounts_glob=_first(env, "DASH_ACCOUNTS_GLOB") or DEFAULT_ACCOUNTS_GLOB,
    )
