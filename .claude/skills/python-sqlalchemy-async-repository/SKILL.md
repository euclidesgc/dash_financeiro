---
name: python-sqlalchemy-async-repository
description: "SQLAlchemy 2.x assíncrono com repositório: AsyncSession, SQL-first com agregação no banco, convenção de nomes de tabela e índice, e o tipo do ORM confinado ao repositório."
user-invocable: false
---

# SQLAlchemy assíncrono com repositório

## Quando esta skill vale

Vale para toda leitura e escrita no banco desta stack. É a norma de persistência
do pack.

A forma síncrona existe para o caso em que a biblioteca obriga, e está na skill
`python-sqlalchemy-sync`.

## A regra

**A API assíncrona é a norma:** `create_async_engine`, `async_sessionmaker`,
`AsyncSession`.

**Toda consulta mora no repositório.** É o único arquivo do domínio que importa
`select` e chama `session.execute`.

**SQL primeiro, Pydantic depois.** Junção, agregação, contagem e formato
aninhado se resolvem na consulta; o Pydantic valida a resposta, não a monta.

**A convenção de nomes é declarada no metadata**, não deixada ao acaso.

## Por quê

**Agregar em Python o que o banco agrega é a diferença entre uma consulta e mil.**
Buscar cem posts e, para cada um, buscar o autor é o problema do `N+1`: ele não
aparece com dez linhas na base de desenvolvimento e derruba a aplicação com dez
mil em produção. A fonte primária é explícita: faça a junção e a agregação em
SQL, inclusive a construção de objeto aninhado por função JSON do banco.

**A convenção de nomes existe porque migração precisa de nome.** Sem ela, o
SQLAlchemy nomeia índice e restrição de um jeito e o banco de outro; o Alembic
gera `None` no lugar do nome, e a migração que renomeia um índice anônimo
simplesmente não pode ser escrita.

**O tipo do ORM confinado ao repositório é o que permite mudar o esquema sem
caçar usos.** Quando o objeto `Post` circula até o router, uma coluna renomeada
quebra arquivos que ninguém associou ao banco.

## Convenção de nomes

| Elemento | Forma |
|---|---|
| Tabela | singular, `snake_case`: `post`, `post_like` |
| Agrupamento por módulo | prefixo: `payment_account`, `payment_bill` |
| Instante | sufixo `_at`: `created_at`, `published_at` |
| Data sem hora | sufixo `_date` |
| Chave estrangeira | mesmo nome da coluna referenciada em todas as tabelas |

```python
NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
```

## Exemplo

**Errado** — consulta no serviço, agregação em Python, sessão síncrona:

```python
async def list_with_authors(self) -> list[dict]:
    posts = self._session.query(Post).all()
    saida = []
    for post in posts:
        author = self._session.query(Author).get(post.author_id)
        saida.append({"title": post.title, "author": author.name})
    return saida
```

`query()` é a API antiga, `.get()` dentro do laço é o `N+1`, e a sessão síncrona
dentro de `async def` bloqueia o laço de eventos — os três estão na tabela de
anti-padrões da fonte primária.

**Certo** — uma consulta, no repositório, com a junção no banco:

```python
class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, limit: int, offset: int) -> Sequence[Post]:
        rows = await self._session.execute(
            select(Post).order_by(Post.created_at.desc()).limit(limit).offset(offset)
        )
        return rows.scalars().all()
```

## `flush` e `commit` fazem coisas diferentes

`flush` manda o `INSERT` e devolve o identificador gerado, **dentro** da
transação corrente. `commit` fecha a transação. O repositório usa `flush`
quando precisa do identificador; quem confirma é o escopo da requisição, na
skill `python-unit-of-work`.

## Erros comuns

- **`encode/databases`.** Está em modo de manutenção; a fonte primária diz para
  não adotá-lo em projeto novo.
- **`session.query(...)`.** É a API 1.x; a 2.x é `select()` mais `execute()`.
- **Repositório devolvendo `Row` ou `dict` cru.** O chamador passa a depender da
  posição das colunas.
- **`lazy="select"` num relacionamento acessado em laço.** É o `N+1` disfarçado
  de atributo; use `selectinload` ou `joinedload` explícito.
- **Índice criado direto no banco, sem migração.** O ambiente seguinte não o
  tem, e a mesma consulta tem dois planos.
- **Tabela no plural.** Quebra a convenção e o prefixo por módulo deixa de
  ordenar a listagem do esquema.

## Ponteiros

- `templates/repository-async.py` — o repositório completo.
- `templates/models.py` — a tabela, com tipos mapeados e transição de estado.
- `templates/database.py` — engine, fábrica de sessão e a convenção de nomes.
- Quem confirma a transação: skill `python-unit-of-work`.
- Como o esquema muda: skill `python-alembic-migracoes`.
- A forma síncrona: skill `python-sqlalchemy-sync`.
