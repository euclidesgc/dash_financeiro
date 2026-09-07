---
name: python-sqlalchemy-sync
description: "SQLAlchemy síncrono quando se justifica: o par rota def mais Session, a URL sem driver assíncrono, os casos legítimos e o anti-padrão de sessão síncrona dentro de async def."
user-invocable: false
---

# SQLAlchemy síncrono, quando se justifica

## Quando esta skill vale

Vale nos casos em que o caminho assíncrono não está disponível ou não compensa:

1. **A rota é `def`** porque a biblioteca do corpo dela é bloqueante — o par
   coerente é sessão síncrona, e está na skill
   `python-rota-sync-io-bloqueante`.
2. **O código não roda numa requisição**: comando de linha, tarefa agendada,
   carga de dados, `migrations/env.py` em modo offline.
3. **O driver assíncrono não existe** para aquele banco.

Fora desses três, a norma é a skill `python-sqlalchemy-async-repository`.

## A regra

**Sessão síncrona anda com rota `def`, e nunca com `async def`.**

```python
sync_engine = create_engine(sync_database_url(), future=True)
sync_session_factory = sessionmaker(sync_engine)
```

**A URL precisa perder o driver assíncrono**, e a troca fica num lugar só:

```python
def sync_database_url() -> str:
    return settings.database_url.replace("+asyncpg", "+psycopg").replace("+aiosqlite", "")
```

**As demais regras não mudam:** a consulta continua no repositório, o serviço
continua sem SQL, e o router continua sem consulta — o portão G7 vale igual.

## Por quê

**Sessão síncrona dentro de `async def` é anti-padrão nomeado na fonte
primária, e é o pior dos dois mundos.** A chamada bloqueia o laço de eventos —
parando toda a aplicação — sem oferecer nada em troca, já que o `await` da rota
sugere concorrência que não existe ali.

**A URL é a armadilha silenciosa.** `create_engine` com `postgresql+asyncpg://`
falha no boot com uma mensagem sobre `await` que não diz o que fazer, e a
correção intuitiva — trocar para `create_async_engine` — desfaz a decisão
consciente de ser síncrono. Centralizar a conversão evita o vaivém.

**O caminho síncrono não é dívida.** Para um comando de carga que roda uma vez
por dia, concorrência não vale a complexidade; a forma síncrona é mais simples
de ler, de depurar e de testar.

## Exemplo

**Errado** — o par misturado:

```python
@router.get("/reports")
async def reports(session: Session = Depends(get_sync_session)) -> list[ReportRead]:
    return session.execute(select(Report)).scalars().all()
```

Rota assíncrona com sessão síncrona: bloqueia o laço a cada requisição. E
`Depends()` como argumento padrão ainda é reprovado por `B008`.

**Certo** — o par coerente, e a rota assumindo que é síncrona:

```python
class SyncPostRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, limit: int, offset: int) -> Sequence[Post]:
        rows = self._session.execute(
            select(Post).order_by(Post.created_at.desc()).limit(limit).offset(offset)
        )
        return rows.scalars().all()
```

## Os dois engines convivem, e isso tem custo

Um projeto com os dois caminhos mantém dois pools de conexão. Some os dois
limites antes de dimensionar o banco: o teto de conexões é do servidor, não da
aplicação, e descobrir isso sob carga custa uma indisponibilidade.

Quando o caminho síncrono existir só para um comando que roda fora do processo
da API, prefira construir o engine dentro do comando e descartá-lo no fim, em
vez de deixá-lo global.

## Erros comuns

- **Adotar o síncrono "porque é mais simples" numa API que já é assíncrona.** O
  teto do threadpool de 40 threads passa a valer para as rotas que o usam.
- **`session.query(...)`.** É a API 1.x; na 2.x a forma é `select()` mais
  `execute()`, síncrona ou não.
- **Reaproveitar a mesma `Session` entre threads.** Ela não é segura para isso,
  e o defeito aparece como dado de outra requisição.
- **Esquecer de fechar a sessão** num comando de linha. A conexão fica presa
  até o processo morrer.
- **Deixar a conversão de URL espalhada.** Cada chamador escreve a sua, e uma
  delas fica para trás quando o banco muda.

## Ponteiros

- `templates/repository-sync.py` — o repositório síncrono, com a conversão de
  URL isolada e o engine declarado.
- A rota que combina com esta forma: skill `python-rota-sync-io-bloqueante`.
- A norma do pack: skill `python-sqlalchemy-async-repository`.
