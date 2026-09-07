from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

# Motivo: sem convenção declarada, o SQLAlchemy nomeia índice e restrição de um
# jeito e o banco de outro, e a migração que renomeia um índice anônimo não tem
# como ser escrita — o Alembic gera `None` no lugar do nome.
NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


engine = create_async_engine(settings.database_url, future=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Uma requisição, uma transação: a sessão é a unidade de trabalho.

    Motivo: `session.begin()` confirma na saída limpa e desfaz em qualquer
    exceção. Sem esse escopo, cada serviço decide quando confirmar, e a
    requisição que falha no meio deixa metade do trabalho gravado.
    """
    async with session_factory() as session, session.begin():
        yield session
