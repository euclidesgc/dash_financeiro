---
name: python-rota-sync-io-bloqueante
description: "Rota def para I/O bloqueante: o threadpool de 40 threads da FastAPI, quando a forma síncrona é a correta, o teto que ela impõe e a saturação que degrada tudo de uma vez."
user-invocable: false
---

# Rota `def` para I/O bloqueante

## Quando esta skill vale

Vale quando o corpo da rota depende de uma biblioteca **sem versão aguardável**:
um SDK antigo de pagamento, um cliente de sistema legado, uma serialização
pesada, um driver que só existe em versão síncrona.

Quando existe cliente assíncrono, a forma é `async def` e está na skill
`python-rota-async-io-nao-bloqueante`.

## A regra

**Declare a rota como `def`, sem `async`.** A FastAPI reconhece a função
síncrona e a executa num threadpool, fora do laço de eventos.

```python
@router.get("/posts.csv", response_class=PlainTextResponse)
def posts_csv(header: HeaderDep) -> str:
    return f"{header}\nid,title,status\n"
```

**Não envolva código bloqueante em `async def` só para "ficar moderno".** Isso
não o torna concorrente: apenas o coloca dentro do laço de eventos, que é o
único lugar onde ele faz estrago.

## Por quê

**A forma `def` é uma decisão correta, não um resquício.** Ela entrega
concorrência real para trabalho bloqueante sem exigir que a biblioteca seja
reescrita, e é o que a fonte primária recomenda para esse caso.

**O teto tem número: o threadpool tem 40 threads por padrão.** Enquanto as
requisições síncronas simultâneas couberem nele, tudo funciona. Quando passam
disso, elas passam a esperar umas pelas outras — e a degradação atinge **todas**
as rotas síncronas ao mesmo tempo, inclusive as rápidas, porque o recurso
escasso é compartilhado. É a diferença entre um endpoint lento e uma aplicação
lenta.

**Por isso a forma síncrona é escolha, não padrão.** Ela se justifica quando a
biblioteca obriga; quando existe alternativa aguardável, o teto de 40 deixa de
ser aceitável em troca de nada.

## Exemplo

**Errado** — bloqueante disfarçado de assíncrono:

```python
@router.get("/posts.csv")
async def posts_csv() -> str:
    return render_posts_csv(fetch_posts_sync())
```

A rota é uma corrotina e o corpo bloqueia. O laço de eventos para, e com ele
todas as rotas assíncronas da aplicação.

**Certo** — a rota assume o que ela é:

```python
@router.get("/posts.csv", response_class=PlainTextResponse)
def posts_csv(header: HeaderDep) -> str:
    return f"{header}\nid,title,status\n"
```

E a função bloqueante diz por que é bloqueante:

```python
def render_posts_csv(posts: Sequence[Post]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "title", "status"])
    for post in posts:
        writer.writerow([post.id, post.title, post.status])
    return buffer.getvalue()
```

## O caso misto

Quando só **parte** do corpo é bloqueante, a rota continua `async def` e a parte
bloqueante sai para o threadpool com `run_in_threadpool`. Mudar a rota inteira
para `def` por causa de uma linha joga a espera pelo banco — que era aguardável
— para dentro do threadpool também, e gasta uma thread para esperar rede.

## A sessão síncrona acompanha a rota síncrona

Se a rota é `def`, a sessão do SQLAlchemy é a síncrona. Misturar `AsyncSession`
com rota `def` é o anti-padrão inverso, e a skill
`python-sqlalchemy-sync` trata do par completo.

## Erros comuns

- **Escolher `def` por não conhecer o cliente assíncrono da biblioteca.**
  Verifique antes: aceitar o teto de 40 sem necessidade é caro.
- **Aumentar o threadpool como primeira resposta à lentidão.** Mais threads em
  trabalho bloqueante é mais troca de contexto; o problema volta com outra
  cara.
- **Trabalho de CPU em rota `def`.** O threadpool não ajuda em CPU; isso sai
  para worker.
- **`await` dentro de função `def`.** Não compila, e o conserto costuma ser
  transformar a rota em `async def` sem trocar o cliente bloqueante — voltando
  ao defeito original.

## Ponteiros

- `templates/router-sync.py` — a rota `def` e a rota mista com
  `run_in_threadpool`, lado a lado.
- `templates/service-bloqueante.py` — a função síncrona, com a razão de ser
  síncrona escrita nela.
- A forma assíncrona: skill `python-rota-async-io-nao-bloqueante`.
- A sessão que acompanha esta forma: skill `python-sqlalchemy-sync`.
