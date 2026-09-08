import sqlite3
from dataclasses import dataclass
from typing import Any

from app.config import load_config

MODELS = ("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite")
DEFAULT_MODEL = MODELS[0]
API_KEY, MODEL = "api_key", "model"
FROM_SCREEN, FROM_ENV, ABSENT = "tela", "ambiente", "ausente"
# Four of eight is half the secret, and "no máximo quatro" needs a floor.
TAIL, MIN_TO_SHOW = 4, 8
UNKNOWN_MODEL = "Modelo desconhecido. Escolha um da lista: {models}."

_SELECT = "SELECT value FROM advisor_config WHERE name = ?"
_UPSERT = (
    "INSERT INTO advisor_config (name, value, updated_at) VALUES (?, ?, datetime('now')) "
    "ON CONFLICT(name) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at"
)
_DELETE = "DELETE FROM advisor_config WHERE name = ?"


class UnknownModelError(ValueError):
    pass


@dataclass(frozen=True)
class Setup:
    api_key: str | None
    model: str
    origin: str


def _stored(conn: sqlite3.Connection, name: str) -> str | None:
    row = conn.execute(_SELECT, (name,)).fetchone()
    return row["value"] if row else None


def current(conn: sqlite3.Connection) -> Setup:
    model = _stored(conn, MODEL) or DEFAULT_MODEL
    screen_key = _stored(conn, API_KEY)
    if screen_key:
        return Setup(api_key=screen_key, model=model, origin=FROM_SCREEN)
    env_key = load_config().gemini_api_key
    if env_key:
        return Setup(api_key=env_key, model=model, origin=FROM_ENV)
    return Setup(api_key=None, model=model, origin=ABSENT)


def view(conn: sqlite3.Connection) -> dict[str, Any]:
    # Separate from current() on purpose: the screen receives a dict that never
    # held the key, instead of receiving the key and promising not to print it.
    setup = current(conn)
    long_enough = setup.api_key is not None and len(setup.api_key) > MIN_TO_SHOW
    return {
        "stored": setup.origin == FROM_SCREEN,
        "origin": setup.origin,
        "tail": setup.api_key[-TAIL:] if long_enough else None,
        "model": setup.model,
        "models": MODELS,
    }


def save(conn: sqlite3.Connection, *, api_key: str, model: str) -> None:
    if model not in MODELS:
        raise UnknownModelError(UNKNOWN_MODEL.format(models=", ".join(MODELS)))
    conn.execute(_UPSERT, (MODEL, model))
    cleaned = api_key.strip()
    if cleaned:
        conn.execute(_UPSERT, (API_KEY, cleaned))
    conn.commit()


def forget(conn: sqlite3.Connection) -> None:
    conn.execute(_DELETE, (API_KEY,))
    conn.commit()
