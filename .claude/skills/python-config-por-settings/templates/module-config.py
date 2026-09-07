from pydantic_settings import BaseSettings, SettingsConfigDict


class PostsSettings(BaseSettings):
    """Configuração do módulo `posts`, e só dela.

    Motivo: um `BaseSettings` global obriga todo módulo a ser importado para
    que qualquer variável seja lida, e uma variável ausente derruba o processo
    por causa de um módulo que aquele processo nem usa.
    """

    model_config = SettingsConfigDict(env_prefix="POSTS_", env_file=".env", extra="ignore")

    page_size: int = 20
    max_page_size: int = 100


settings = PostsSettings()
