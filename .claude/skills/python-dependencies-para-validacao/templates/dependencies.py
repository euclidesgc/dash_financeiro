from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.posts.config import settings
from src.posts.exceptions import PostNotFoundError
from src.posts.models import Post
from src.posts.repository import PostRepository
from src.posts.service import PostService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_repository(session: SessionDep) -> PostRepository:
    return PostRepository(session)


RepositoryDep = Annotated[PostRepository, Depends(get_repository)]


def get_service(repository: RepositoryDep) -> PostService:
    return PostService(repository)


ServiceDep = Annotated[PostService, Depends(get_service)]


async def valid_post_id(post_id: int, repository: RepositoryDep) -> Post:
    """A dependência valida contra o banco, não só injeta.

    Motivo: com a existência verificada aqui, toda rota que recebe `post_id`
    herda o 404 sem repeti-lo, e o corpo da rota trata só do caso em que o
    recurso existe.
    """
    post = await repository.get(post_id)
    if post is None:
        raise PostNotFoundError
    return post


PostDep = Annotated[Post, Depends(valid_post_id)]


def pagination(
    limit: Annotated[int, Query(ge=1, le=settings.max_page_size)] = settings.page_size,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> tuple[int, int]:
    return limit, offset


PaginationDep = Annotated[tuple[int, int], Depends(pagination)]
