from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from src.database import Base, get_session
from src.main import create_app


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Banco real, em memória, um por teste.

    Motivo: `StaticPool` mantém a MESMA conexão em todo o teste. Sem ele, cada
    checkout do pool abre um banco em memória novo e vazio, e a tabela criada
    no setup some antes da primeira consulta.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as opened, opened.begin():
        yield opened

    await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Cliente assíncrono desde o primeiro teste.

    Motivo: trocar de cliente depois obriga a reescrever toda a suíte, porque
    o cliente síncrono roda o laço de eventos por fora e as fixtures
    assíncronas deixam de valer.
    """
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as opened:
        yield opened
    app.dependency_overrides.clear()
