---
name: python-rota-async-io-nao-bloqueante
description: "Rota async def para I/O aguardável: a regra de decisão da fonte primária, o que nunca entra no laço de eventos e como a família ASYNC do ruff cobra isso por máquina."
user-invocable: false
---

# Rota `async def` para I/O aguardável

## Quando esta skill vale

Vale ao escrever qualquer rota cujo corpo espera por rede ou banco **através de
um cliente aguardável**: `AsyncSession` do SQLAlchemy, `httpx.AsyncClient`,
cliente assíncrono de fila ou de cache.

Quando o cliente disponível é bloqueante, a forma é outra e está na skill
`python-rota-sync-io-bloqueante`.

## A regra de decisão

A fonte primária do pack resume a escolha em quatro linhas, e não há uma quinta:

| O corpo da rota faz | A rota é |
|---|---|
| I/O aguardável, com cliente assíncrono | `async def` |
| I/O bloqueante, sem cliente assíncrono | `def` |
| Os dois misturados | `async def` mais `run_in_threadpool` |
| Trabalho de CPU acima de 50 ms | sai para worker |

**Dentro de um `async def`, nada bloqueia.** A lista do que não entra é curta e
literal: `time.sleep`, `requests`, `open`, sessão síncrona de ORM, qualquer SDK
sem versão aguardável.

## Por quê

**O laço de eventos é um só.** Uma chamada bloqueante dentro de `async def` não
atrasa aquela requisição: ela para **todas**, incluindo as que não têm relação
nenhuma com o código bloqueante. O sintoma é a aplicação inteira ficar lenta sob
carga, sem erro em lugar nenhum e sem um pico que aponte o culpado.

**É o defeito que mais aparece em código de API escrito por modelo**, e está
nomeado como anti-padrão na fonte primária: `requests.get()` dentro de `async
def`, `time.sleep()` dentro de `async def`, sessão síncrona de ORM dentro de
`async def`. Por isso a família `ASYNC` do ruff está ligada — a regra é cobrada
por máquina antes da revisão, e não depende de alguém lembrar dela.

**A dependência também é rota.** Uma dependência bloqueante trava o laço
exatamente como o corpo da rota, e ela roda em toda requisição que a declara.

## Exemplo

**Errado** — três bloqueios dentro de uma corrotina:

```python
@router.get("/{post_id}")
async def get_post(post_id: int) -> PostRead:
    time.sleep(0.2)
    profile = requests.get(f"https://api.example.com/authors/{post_id}").json()
    with open("audit.log", "a") as handle:
        handle.write(f"{post_id}\n")
    return PostRead(**profile)
```

Enquanto essas três linhas rodam, nenhuma outra requisição da aplicação avança.

**Certo** — tudo aguardável, e o corpo da rota sem decisão:

```python
@router.get("/{post_id}", response_model=PostRead)
async def get_post(post: PostDep) -> object:
    return post
```

E, quando a rota precisa de rede além do banco, o cliente é assíncrono:

```python
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

## Quando parte do corpo é bloqueante

Não se muda a rota para `def` por causa de uma linha: envolve-se a linha.

```python
@router.get("/posts-live.csv", response_class=PlainTextResponse)
async def posts_live_csv(service: ServiceDep, pagination: PaginationDep) -> str:
    limit, offset = pagination
    posts = await service.list(limit=limit, offset=offset)
    return await run_in_threadpool(render_posts_csv, posts)
```

A leitura do banco é aguardável e fica no laço; a serialização é bloqueante e
sai para o threadpool.

## Erros comuns

- **`async def` numa rota que só faz trabalho síncrono.** Não ganha nada e
  perde o threadpool que a forma `def` daria de graça.
- **`asyncio.run` dentro de uma rota.** Já existe um laço rodando; a chamada
  levanta erro ou cria um segundo laço que não enxerga o primeiro.
- **Dependência síncrona que faz I/O.** Bloqueia igual, e roda em toda
  requisição que a declara.
- **Trabalho de CPU jogado em `run_in_threadpool`.** O bloqueio de CPU não é
  liberado pelo interpretador; o threadpool satura e o problema piora.
- **Silenciar um apontamento da família `ASYNC` com `noqa`.** Ele está
  apontando exatamente a classe de defeito que esta skill existe para impedir.

## Ponteiros

- `templates/router-async.py` — o router assíncrono completo, com dependências
  que validam e nenhuma decisão no corpo.
- A forma síncrona e quando ela é a certa: skill
  `python-rota-sync-io-bloqueante`.
- A família de lint que cobra esta regra: skill `python-ruff`.
- Por que o corpo da rota não decide: skill `python-estrutura-por-dominio`.
