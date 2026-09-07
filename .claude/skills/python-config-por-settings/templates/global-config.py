from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    env: str = "local"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    cors_origins: list[str] = []


settings = AppSettings()
