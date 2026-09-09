import sqlite3
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.config import load_config

MODELS = ("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite")
DEFAULT_MODEL = MODELS[0]
API_KEY, MODEL = "api_key", "model"
FROM_SCREEN, FROM_ENV, ABSENT = "tela", "ambiente", "ausente"
# Reason: four of eight is half the secret, and the plan's own "no máximo
# quatro" (at most four) needs a floor.
TAIL, MIN_TO_SHOW = 4, 8
UNKNOWN_MODEL = "Modelo desconhecido. Escolha um da lista: {models}."
INVALID_API_KEY = (
    "Chave recusada: ela tem um caractere que o cabeçalho HTTP não aceita "
    "(quebra de linha ou caractere fora do alfabeto simples). Copie a chave de novo, "
    "direto do provedor."
)

_SELECT = "SELECT value FROM advisor_config WHERE name = ?"
_UPSERT = (
    "INSERT INTO advisor_config (name, value, updated_at) VALUES (?, ?, datetime('now')) "
    "ON CONFLICT(name) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at"
)
_DELETE = "DELETE FROM advisor_config WHERE name = ?"


class UnknownModelError(ValueError):
    pass


class InvalidApiKeyError(ValueError):
    pass


@dataclass(frozen=True)
class Setup:
    api_key: str | None
    model: str
    origin: str


def _stored(conn: sqlite3.Connection, name: str) -> str | None:
    row = conn.execute(_SELECT, (name,)).fetchone()
    return row["value"] if row else None


def _unfit_for_a_header(value: str) -> bool:
    # Reason: httpx encodes a str header value as ascii before writing it on
    # the wire (httpx._models._normalize_header_value) — a control character
    # is legal ascii yet corrupts the request line seen by h11, and a
    # character above that range makes the encoding itself raise. Both must
    # be refused before the value is ever written, not discovered on the
    # outbound call.
    if any(unicodedata.category(char) == "Cc" for char in value):
        return True
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return True
    return False


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
    # Reason: separate from current() on purpose — the screen receives a
    # dict that never held the key, instead of receiving the key and
    # promising not to print it.
    setup = current(conn)
    return {
        "stored": setup.origin == FROM_SCREEN,
        "origin": setup.origin,
        "tail": setup.api_key[-TAIL:]
        if setup.api_key is not None and len(setup.api_key) > MIN_TO_SHOW
        else None,
        "model": setup.model,
        "models": MODELS,
    }


def save(conn: sqlite3.Connection, *, api_key: str, model: str) -> None:
    if model not in MODELS:
        raise UnknownModelError(UNKNOWN_MODEL.format(models=", ".join(MODELS)))
    cleaned = api_key.strip()
    if cleaned and _unfit_for_a_header(cleaned):
        raise InvalidApiKeyError(INVALID_API_KEY)
    conn.execute(_UPSERT, (MODEL, model))
    if cleaned:
        conn.execute(_UPSERT, (API_KEY, cleaned))
    conn.commit()


def forget(conn: sqlite3.Connection) -> None:
    conn.execute(_DELETE, (API_KEY,))
    conn.commit()
