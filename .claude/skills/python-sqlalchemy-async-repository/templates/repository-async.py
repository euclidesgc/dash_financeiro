from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.posts.models import Post


class PostRepository:
    """Único ponto do módulo que fala SQL.

    Motivo: com a consulta confinada aqui, trocar coluna ou índice é uma
    mudança de um arquivo. Espalhada pelo serviço e pelo router, a mesma troca
    obriga a reler o módulo inteiro para descobrir quem consultava o quê.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, post_id: int) -> Post | None:
        return await self._session.get(Post, post_id)

    async def list(self, limit: int, offset: int) -> Sequence[Post]:
        rows = await self._session.execute(
            select(Post).order_by(Post.created_at.desc()).limit(limit).offset(offset)
        )
        return rows.scalars().all()

    async def add(self, post: Post) -> Post:
        self._session.add(post)
        await self._session.flush()
        return post
