---
name: python-fixtures-e-factories
description: "Fixtures do pytest e fábricas com factory_boy: escopo declarado, conftest por nível, fábrica no lugar de objeto escrito à mão e o teste que declara só o que afirma."
user-invocable: false
---

# Fixtures e fábricas

## Quando esta skill vale

Vale sempre que um teste precisa de estado: um objeto de domínio, uma sessão de
banco, um cliente HTTP, um relógio fixo.

Não vale para decidir o que afirmar — isso é das skills
`python-testes-unitarios` e `python-testes-de-integracao-httpx`.

## A regra

**Fábrica para objeto de domínio, fixture para recurso.**

```python
class PostFactory(factory.Factory):
    class Meta:
        model = Post

    title = factory.Sequence(lambda n: f"Post {n}")
    body = "Body of the post."
    status = PostStatus.DRAFT
```

**O teste sobrescreve só o que ele afirma:**

```python
post = PostFactory(status=PostStatus.PUBLISHED)
```

**A fixture declara escopo.** O padrão é `function`, e subir para `session` é
decisão com razão escrita.

**`conftest.py` fica no nível em que a fixture serve** — a de banco na raiz de
`tests/`, a específica de um assunto na pasta dele.

## Por quê

**A fábrica é o que faz um campo novo não quebrar quarenta testes.** Com todo
objeto escrito à mão, acrescentar uma coluna obrigatória obriga a editar cada
caso — inclusive os que nada tinham a ver com aquele campo. Com a fábrica, muda
uma linha.

**A sobrescrita seletiva é o que torna o teste legível.** Quando o caso declara
só `status=PostStatus.PUBLISHED`, o leitor sabe imediatamente que essa é a única
coisa que importa ali; quando declara os oito campos, todos parecem importantes
e nenhum é.

**Escopo largo é a causa mais comum de teste que só falha na suíte inteira.**
Uma fixture `session` que devolve o mesmo objeto para todos os casos deixa o
primeiro modificá-lo e o quinto falhar — e rodar o quinto sozinho passa, o que
manda a investigação para o lugar errado.

## Exemplo

**Errado** — objeto escrito à mão em cada caso, e estado vazando:

```python
@pytest.fixture(scope="session")
def post() -> Post:
    return Post(id=1, title="First", body="Body", status=PostStatus.DRAFT)


async def test_publish(post: Post) -> None:
    post.publish()
    assert post.status is PostStatus.PUBLISHED


async def test_new_post_is_draft(post: Post) -> None:
    assert post.status is PostStatus.DRAFT
```

O segundo caso falha se o primeiro rodar antes, e passa se rodar sozinho.

**Certo** — fábrica por caso, e cada teste com o seu objeto:

```python
async def test_publicar_marca_o_instante_da_publicacao() -> None:
    post = PostFactory(id=1)
    service = make_service([post])

    published = await service.publish(1)

    assert published.status is PostStatus.PUBLISHED
```

## `Sequence` para o que precisa ser único

```python
title = factory.Sequence(lambda n: f"Post {n}")
```

Valor fixo em campo com restrição de unicidade faz o segundo objeto do mesmo
teste falhar na inserção — e o erro que aparece é do banco, não do que estava
sendo verificado.

## A fixture assíncrona e o `yield`

```python
@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as opened, opened.begin():
        yield opened

    await engine.dispose()
```

O que vem depois do `yield` é a limpeza, e ela roda mesmo quando o teste falha.
Sem `engine.dispose()`, as conexões se acumulam e a suíte acaba esbarrando no
limite do banco — sintoma que aparece só quando a suíte fica grande.

Com `asyncio_mode = "auto"` no `pyproject.toml`, nenhum caso precisa de
decorador de marcação.

## Erros comuns

- **`scope="session"` para ganhar velocidade.** Troca segundos por uma classe
  de falha que só aparece na suíte inteira.
- **Fábrica que grava no banco por padrão.** Em teste unitário não há banco;
  `factory.Factory` constrói em memória, e a persistência é do caso que a quer.
- **`conftest.py` na raiz com tudo.** Toda fixture passa a ser carregada por
  todo teste, e a origem de uma delas fica impossível de achar.
- **Fixture que devolve mutável compartilhado.** Um caso altera e o outro
  observa.
- **Dado aleatório sem semente.** A falha não se reproduz, e o teste vira
  ruído.

## Ponteiros

- `templates/factories.py` — a fábrica do agregado, com sequência no campo
  único.
- `templates/conftest.py` — as fixtures de sessão e de cliente, com limpeza.
- Onde as fábricas são usadas: skills `python-testes-unitarios` e
  `python-testes-de-integracao-httpx`.
