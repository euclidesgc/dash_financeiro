import pytest

from app.advisor import config

ENV_KEY = "chave-do-ambiente-MB9Z"
SCREEN_KEY = "chave-da-tela-0123456789ABCDEF"


def test_the_environment_wins_when_nothing_is_stored(taxonomy_conn, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", ENV_KEY)

    setup = config.current(taxonomy_conn)

    assert setup.api_key == ENV_KEY
    assert setup.model == config.DEFAULT_MODEL
    assert setup.origin == config.FROM_ENV


def test_the_screen_wins_over_the_environment(taxonomy_conn, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", ENV_KEY)
    config.save(taxonomy_conn, api_key=SCREEN_KEY, model="gemini-2.5-pro")

    setup = config.current(taxonomy_conn)

    assert setup.api_key == SCREEN_KEY
    assert setup.model == "gemini-2.5-pro"
    assert setup.origin == config.FROM_SCREEN


def test_nothing_stored_and_nothing_in_the_environment_is_absent(taxonomy_conn, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    setup = config.current(taxonomy_conn)

    assert setup.api_key is None
    assert setup.model == config.DEFAULT_MODEL
    assert setup.origin == config.ABSENT


def test_view_shows_only_the_last_four_characters(taxonomy_conn):
    config.save(taxonomy_conn, api_key=SCREEN_KEY, model="gemini-2.5-pro")

    seen = config.view(taxonomy_conn)

    assert seen["tail"] == "CDEF"
    assert seen["stored"] is True
    assert seen["model"] == "gemini-2.5-pro"
    assert seen["models"] == config.MODELS
    assert SCREEN_KEY not in str(seen)


def test_a_key_of_eight_characters_or_fewer_shows_nothing(taxonomy_conn):
    config.save(taxonomy_conn, api_key="12345678", model="gemini-2.5-pro")

    seen = config.view(taxonomy_conn)

    assert seen["tail"] is None


def test_an_unknown_model_is_refused_and_writes_nothing(taxonomy_conn, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", ENV_KEY)

    with pytest.raises(config.UnknownModelError, match="gemini-2.5-flash"):
        config.save(taxonomy_conn, api_key=SCREEN_KEY, model="gemini-9-turbo")

    setup = config.current(taxonomy_conn)
    assert setup.origin == config.FROM_ENV
    assert setup.model == config.DEFAULT_MODEL


def test_an_empty_key_does_not_erase_the_stored_one(taxonomy_conn):
    config.save(taxonomy_conn, api_key=SCREEN_KEY, model="gemini-2.5-flash")

    config.save(taxonomy_conn, api_key="", model="gemini-2.5-pro")

    setup = config.current(taxonomy_conn)
    assert setup.api_key == SCREEN_KEY
    assert setup.model == "gemini-2.5-pro"


def test_forget_returns_control_to_the_environment_without_touching_the_model(
    taxonomy_conn, monkeypatch
):
    monkeypatch.setenv("GEMINI_API_KEY", ENV_KEY)
    config.save(taxonomy_conn, api_key=SCREEN_KEY, model="gemini-2.5-pro")

    config.forget(taxonomy_conn)

    setup = config.current(taxonomy_conn)
    assert setup.api_key == ENV_KEY
    assert setup.origin == config.FROM_ENV
    assert setup.model == "gemini-2.5-pro"


def test_a_key_with_control_characters_is_refused_and_writes_nothing(taxonomy_conn, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    injected = "chave-INJETADA-7777\r\nX-Injetado: sim"

    with pytest.raises(config.InvalidApiKeyError) as refusal:
        config.save(taxonomy_conn, api_key=injected, model="gemini-2.5-pro")

    assert "INJETADA" not in str(refusal.value)
    assert "7777" not in str(refusal.value)
    setup = config.current(taxonomy_conn)
    assert setup.api_key is None
    assert setup.model == config.DEFAULT_MODEL


def test_a_key_with_non_ascii_characters_is_refused_and_writes_nothing(taxonomy_conn, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    accented = "chave-com-acentuação-áéí"

    with pytest.raises(config.InvalidApiKeyError) as refusal:
        config.save(taxonomy_conn, api_key=accented, model="gemini-2.5-pro")

    assert "acentuação" not in str(refusal.value)
    assert "áéí" not in str(refusal.value)
    setup = config.current(taxonomy_conn)
    assert setup.api_key is None
    assert setup.model == config.DEFAULT_MODEL
