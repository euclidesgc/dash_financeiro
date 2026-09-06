from app.config import DEFAULT_DB_PATH, load_config


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
