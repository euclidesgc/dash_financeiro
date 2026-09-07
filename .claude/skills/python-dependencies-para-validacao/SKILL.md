---
name: python-dependencies-para-validacao
description: "Dependência que valida, não só injeta: forma Annotated, encadeamento, cache por requisição, dependência assíncrona e o mesmo nome de variável de caminho entre rotas."
user-invocable: false
---

# Dependência que valida

## Quando esta skill vale

Vale sempre que uma rota precisa de algo verificado **antes** de o corpo dela
começar: o recurso existe, o usuário pode, a paginação está na faixa, a sessão
está aberta.

Não vale para validar a **forma** do corpo da requisição — isso é do schema, na
skill `python-schemas-pydantic-v2`.

## A regra

**A forma é `Annotated`, sempre:**

```python
SessionDep = Annotated[AsyncSession, Depends(get_session)]
PostDep = Annotated[Post, Depends(valid_post_id)]
```

**`Depends()` como argumento padrão não é aceito** — e o ruff reprova com
`B008`, que é chamada de função como valor padrão.

**A dependência faz mais que injetar: ela valida.** A verificação de existência
no banco, a checagem de permissão e a faixa da paginação moram aqui.

```python
async def valid_post_id(post_id: int, repository: RepositoryDep) -> Post:
    post = await repository.get(post_id)
    if post is None:
        raise PostNotFoundError
    return post
```

## Por quê

**Com a existência verificada na dependência, toda rota que recebe `post_id`
herda o 404 sem repeti-lo.** O corpo da rota passa a tratar só do caso em que o
recurso existe, e o caminho de erro deixa de ser copiado — que é onde ele
diverge: uma rota devolve 404, a outra 400, e a terceira esquece de verificar.

**Dependência é cacheada por requisição.** Duas rotas que declaram a mesma
`Depends(x)` a executam **uma vez** por requisição, não duas. Isso é o que
torna barato decompor: `valid_post_id` pode depender de `get_repository`, que
depende de `get_session`, sem que a sessão seja aberta três vezes.

**A dependência deve ser `async def` quando não faz I/O bloqueante.** Uma
dependência `def` é despachada para o threadpool, e para uma função que só monta
um objeto isso é troca de contexto paga sem contrapartida.

**O nome da variável de caminho é contrato entre rotas.** `valid_post_id` só
serve às rotas que chamam o parâmetro de `post_id`. Uma rota que o chame de `id`
não reaproveita nada, e ganha uma dependência quase idêntica ao lado.

## Exemplo

**Errado** — injeção sem validação, e a forma antiga:

```python
@router.get("/{post_id}")
async def get_post(post_id: int, db: AsyncSession = Depends(get_session)) -> PostRead:
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404)
    return PostRead.model_validate(post)
```

Três problemas numa assinatura: `Depends()` como padrão (`B008`), a sessão
entregue crua ao corpo da rota, e a verificação de existência repetida em toda
rota que receber um identificador.

**Certo** — a cadeia declarada uma vez, e a rota sem caminho de erro:

```python
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_repository(session: SessionDep) -> PostRepository:
    return PostRepository(session)


RepositoryDep = Annotated[PostRepository, Depends(get_repository)]
PostDep = Annotated[Post, Depends(valid_post_id)]


@router.get("/{post_id}", response_model=PostRead)
async def get_post(post: PostDep) -> object:
    return post
```

## A paginação também é dependência

```python
def pagination(
    limit: Annotated[int, Query(ge=1, le=settings.max_page_size)] = settings.page_size,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> tuple[int, int]:
    return limit, offset
```

O teto vem da configuração do módulo, não de um número solto na assinatura. Sem
o `le`, um `limit=1000000` é um caminho de indisponibilidade que qualquer
cliente pode acionar.

## Erros comuns

- **Dependência que devolve `None` em vez de levantar.** Empurra a verificação
  para o corpo da rota, que é de onde ela veio.
- **Dependência que levanta `HTTPException`.** Quando ela vive no domínio, a
  taxonomia é a de domínio; a tradução para HTTP acontece numa fronteira só.
- **Uma dependência gigante que faz tudo.** Perde o cache por partes e o reúso;
  decompor é o que torna a cadeia barata.
- **`Depends` dentro de `Annotated` mais valor padrão de `Depends` junto.** A
  segunda forma ganha silenciosamente, e a leitura do código mente.
- **Nome de variável de caminho diferente entre rotas do mesmo recurso.**
  Impede o reúso e multiplica dependências quase iguais.

## Ponteiros

- `templates/dependencies.py` — a cadeia completa: sessão, repositório,
  serviço, validação de identificador e paginação com teto.
- A validação da forma do corpo: skill `python-schemas-pydantic-v2`.
- De onde vem o teto de paginação: skill `python-config-por-settings`.
- A regra de lint que cobra a forma `Annotated`: skill `python-ruff`.
