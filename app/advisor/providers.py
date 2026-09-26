import sqlite3

from app.advisor import config as gemini_setup
from app.advisor.anthropic_provider import DEFAULT_MODEL, AnthropicProvider
from app.advisor.gemini_provider import DEFAULT_MODEL as DEFAULT_GEMINI_MODEL
from app.advisor.gemini_provider import GeminiProvider
from app.advisor.provider import ChatProvider
from app.config import Config, load_config

MISSING_KEY = (
    "O consultor precisa de uma chave de IA. Coloque ANTHROPIC_API_KEY no arquivo .env "
    "(passo a passo em docs/setup-secrets.md), ou a chave do Gemini em GEMINI_API_KEY ou na tela "
    "Configuração, e reinicie o painel. O resto do painel funciona sem ela."
)


def select_provider(conn: sqlite3.Connection, config: Config | None = None) -> ChatProvider | None:
    settings = config or load_config()
    if settings.anthropic_api_key:
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.advisor_model or DEFAULT_MODEL,
        )
    setup = gemini_setup.current(conn)
    if setup.api_key:
        model = settings.advisor_gemini_model or DEFAULT_GEMINI_MODEL
        return GeminiProvider(api_key=setup.api_key, model=model)
    return None
