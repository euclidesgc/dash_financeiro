from collections.abc import Sequence

from src.posts.constants import PostStatus
from src.posts.exceptions import PostAlreadyPublishedError, PostNotFoundError
from src.posts.models import Post
from src.posts.repository import PostRepository
from src.posts.schemas import PostCreate


class PostService:
    def __init__(self, repository: PostRepository) -> None:
        self._repository = repository

    async def create(self, payload: PostCreate) -> Post:
        """Nascer como rascunho é regra de negócio, e por isso é escrita aqui.

        Motivo: `default=` no `mapped_column` só age no INSERT. Deixar a regra
        lá faz o objeto recém-construído ter `status=None` até o flush, e o
        serviço passa a decidir sobre um estado que ainda não existe.
        """
        post = Post(title=payload.title, body=payload.body, status=PostStatus.DRAFT)
        return await self._repository.add(post)

    async def list(self, limit: int, offset: int) -> Sequence[Post]:
        return await self._repository.list(limit=limit, offset=offset)

    async def publish(self, post_id: int) -> Post:
        post = await self._repository.get(post_id)
        if post is None:
            raise PostNotFoundError
        if post.status is PostStatus.PUBLISHED:
            raise PostAlreadyPublishedError
        post.publish()
        return post
