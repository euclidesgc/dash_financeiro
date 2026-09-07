import csv
import io
from collections.abc import Sequence

from src.posts.models import Post


def render_posts_csv(posts: Sequence[Post]) -> str:
    """Serialização em CSV, síncrona porque a biblioteca é síncrona.

    Motivo: `csv` não tem versão aguardável. Envolvê-la em `async def` não a
    torna concorrente — só a coloca dentro do laço de eventos, onde ela passa a
    bloquear todas as outras requisições enquanto escreve.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "title", "status"])
    for post in posts:
        writer.writerow([post.id, post.title, post.status])
    return buffer.getvalue()
