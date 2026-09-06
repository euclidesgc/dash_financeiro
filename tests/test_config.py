import re
from datetime import date

import pytest

from app.config import (
    DEFAULT_DB_PATH,
    load_config,
    reference_date,
    resolve_session_secret,
)


def test_typo_spellings_are_accepted():
    config = load_config({"LOGIN": "teste", "PASSORD": "abc123", "GEMIMI_API_KEY": "k-1"})

    assert (config.login, config.password, config.gemini_api_key) == ("teste", "abc123", "k-1")


def test_correct_spellings_win_over_typos():
    config = load_config(
        {
            "LOGIN": "teste",
            "PASSORD": "abc123",
            "PASSWORD": "xyz789",
            "GEMIMI_API_KEY": "k-1",
            "GEMINI_API_KEY": "k-2",
        }
    )

    assert (config.password, config.gemini_api_key) == ("xyz789", "k-2")


def test_missing_credentials_are_none():
    config = load_config({})

    assert (config.login, config.password, config.gemini_api_key, config.session_secret) == (
        None,
        None,
        None,
        None,
    )


def test_db_path_defaults_to_the_project_database():
    assert DEFAULT_DB_PATH == "data/dash.sqlite"
    assert load_config({}).db_path == DEFAULT_DB_PATH
    assert load_config({"DASH_DB_PATH": "/tmp/other.sqlite"}).db_path == "/tmp/other.sqlite"


def test_process_environment_beats_the_env_file(monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("LOGIN", "teste")
    monkeypatch.setenv("PASSORD", "abc123")
    monkeypatch.setenv("GEMIMI_API_KEY", "k-1")
    monkeypatch.delenv("PASSWORD", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    config = load_config()

    assert (config.login, config.password, config.gemini_api_key) == ("teste", "abc123", "k-1")


def test_a_generated_key_file_is_read_back(tmp_path):
    config = load_config({"DASH_KEY_PATH": str(tmp_path / "session.key")})

    first = resolve_session_secret(config)

    assert first
    assert resolve_session_secret(config) == first


def test_an_empty_key_file_stops_the_boot(tmp_path):
    key = tmp_path / "session.key"
    key.write_text("", encoding="utf-8")
    config = load_config({"DASH_KEY_PATH": str(key)})

    with pytest.raises(RuntimeError, match=re.escape(str(key))):
        resolve_session_secret(config)


def test_a_blank_key_file_stops_the_boot(tmp_path):
    key = tmp_path / "session.key"
    key.write_text("   \n", encoding="utf-8")
    config = load_config({"DASH_KEY_PATH": str(key)})

    with pytest.raises(RuntimeError, match=re.escape(str(key))):
        resolve_session_secret(config)


def test_the_reference_date_comes_from_the_environment():
    assert reference_date({"DASH_TODAY": "2026-09-05"}) == date(2026, 9, 5)


def test_a_missing_reference_date_falls_back_to_the_clock():
    assert reference_date({}) == date.today()


def test_an_unreadable_reference_date_is_refused():
    with pytest.raises(ValueError):
        reference_date({"DASH_TODAY": "05/09/2026"})
