from collections.abc import Sequence

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.posts.models import Post


def sync_database_url() -> str:
    """A mesma base, pelo driver síncrono.

    Motivo: a URL do projeto nomeia o driver assíncrono, e um `create_engine`
    síncrono com `+asyncpg` falha no boot com uma mensagem sobre `await` que
    não diz o que fazer. A troca fica num lugar só, e não espalhada em cada
    chamador.
    """
    return settings.database_url.replace("+asyncpg", "+psycopg").replace("+aiosqlite", "")


sync_engine = create_engine(sync_database_url(), future=True)
sync_session_factory = sessionmaker(sync_engine)


class SyncPostRepository:
    """Repositório síncrono, para o caminho que roda no threadpool."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, limit: int, offset: int) -> Sequence[Post]:
        rows = self._session.execute(
            select(Post).order_by(Post.created_at.desc()).limit(limit).offset(offset)
        )
        return rows.scalars().all()
