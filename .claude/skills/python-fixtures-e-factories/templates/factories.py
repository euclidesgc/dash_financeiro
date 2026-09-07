import factory
from src.posts.constants import PostStatus
from src.posts.models import Post


class PostFactory(factory.Factory):  # type: ignore[misc]
    """Fábrica do agregado, para o teste declarar só o que ele afirma.

    Motivo: com todo campo escrito à mão em cada teste, acrescentar uma coluna
    obrigatória quebra dezenas de testes que nada tinham a ver com ela.
    """

    class Meta:
        model = Post

    title = factory.Sequence(lambda n: f"Post {n}")
    body = "Body of the post."
    status = PostStatus.DRAFT
