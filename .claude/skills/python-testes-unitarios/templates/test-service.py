from collections.abc import Sequence

import pytest
from src.posts.constants import PostStatus
from src.posts.exceptions import PostAlreadyPublishedError, PostNotFoundError
from src.posts.models import Post
from src.posts.schemas import PostCreate
from src.posts.service import PostService
from tests.factories import PostFactory


class FakePostRepository:
    """Dublê em arquivo de teste, com a mesma forma do repositório real."""

    def __init__(self, posts: list[Post] | None = None) -> None:
        self.posts = posts or []

    async def get(self, post_id: int) -> Post | None:
        return next((p for p in self.posts if p.id == post_id), None)

    async def list(self, limit: int, offset: int) -> Sequence[Post]:
        return self.posts[offset : offset + limit]

    async def add(self, post: Post) -> Post:
        post.id = len(self.posts) + 1
        self.posts.append(post)
        return post


def make_service(posts: list[Post] | None = None) -> PostService:
    return PostService(FakePostRepository(posts))  # type: ignore[arg-type]


async def test_um_post_criado_nasce_como_rascunho() -> None:
    service = make_service()

    created = await service.create(PostCreate(title="First", body="Body"))

    assert created.status is PostStatus.DRAFT
    assert created.published_at is None


async def test_publicar_marca_o_instante_da_publicacao() -> None:
    post = PostFactory(id=1)
    service = make_service([post])

    published = await service.publish(1)

    assert published.status is PostStatus.PUBLISHED
    assert published.published_at is not None


async def test_publicar_um_post_inexistente_levanta_erro_de_dominio() -> None:
    service = make_service()

    with pytest.raises(PostNotFoundError):
        await service.publish(404)


async def test_publicar_duas_vezes_e_conflito_e_nao_repeticao_silenciosa() -> None:
    post = PostFactory(id=1, status=PostStatus.PUBLISHED)
    service = make_service([post])

    with pytest.raises(PostAlreadyPublishedError):
        await service.publish(1)


async def test_a_listagem_respeita_o_recorte_pedido() -> None:
    posts = [PostFactory(id=n) for n in range(1, 6)]
    service = make_service(posts)

    page = await service.list(limit=2, offset=2)

    assert [p.id for p in page] == [3, 4]
