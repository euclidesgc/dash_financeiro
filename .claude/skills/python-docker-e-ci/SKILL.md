---
name: python-docker-e-ci
description: "Imagem e integração contínua: build em dois estágios com uv, camada de dependência separada, processo não-root, e o fluxo que roda lint, tipos, testes e migração."
user-invocable: false
---

# Imagem e integração contínua

## Quando esta skill vale

Vale ao criar o Dockerfile e o fluxo de CI, e sempre que um passo novo entra na
régua. Ela define a forma da imagem e a ordem dos portões.

Não vale para configurar as ferramentas que os passos executam — isso é das
skills `python-ruff`, `python-tipagem-estrita` e `python-uv`.

## A regra da imagem

**Dois estágios, uv por cópia de imagem com versão fixa, dependência em camada
separada do código, processo não-root.**

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/
```

A ordem dentro do estágio de construção não é preferência:

```dockerfile
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev
```

Primeiro o que muda pouco, depois o que muda a cada commit.

## Por quê

**A separação de camadas é a diferença entre um build de segundos e um de
minutos.** Copiar `src` antes de instalar invalida a camada de dependências a
cada linha alterada, e toda construção reinstala a árvore inteira.

**`--no-dev` na imagem não é economia de disco, é superfície.** Verificador de
tipos, formatador e framework de teste dentro da imagem de produção são código
executável que ninguém revisou naquele contexto.

**Não-root é a diferença entre execução remota de código e controle do host.**
Um processo de aplicação nunca precisa de root, e o custo de declarar o usuário
é uma linha.

**O uv entra por cópia de imagem com versão fixa, não por script de
instalação.** Script baixado durante o build resolve para a versão do dia, e
duas construções do mesmo commit passam a produzir árvores diferentes — o
defeito mais difícil de investigar que existe, porque o código está idêntico.

## A regra do fluxo

Os passos, nesta ordem, e cada um falando por si:

| Passo | Comando | O que ele prova |
|---|---|---|
| Dependências | `uv sync --frozen` | O lock bate com a declaração |
| Lint | `uv run ruff check .` | Nenhum apontamento de regra |
| Formatação | `uv run ruff format --check .` | O commit já veio formatado |
| Tipos | `uv run mypy --strict src` | Nenhuma assinatura mentindo |
| Testes | `uv run pytest` | O comportamento afirmado se sustenta |
| Migração | `alembic upgrade head`, `check`, `downgrade base` | O esquema sobe, está em dia e desce |

**A migração é medida subindo e descendo.** `alembic check` sozinho aprova um
`downgrade` que nunca foi executado, e migração que não desce é descoberta no
dia do rollback, que é o pior dia possível.

## Exemplo

**Errado** — um estágio só, root, e o lock ignorado:

```dockerfile
FROM python:3.12
COPY . /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "src.main:app"]
```

A imagem carrega o repositório inteiro, incluindo `tests/`, `.git` e o que mais
estiver na pasta; instala fora do lock; e roda como root.

**Certo** — o template desta skill, com os dois estágios e o usuário próprio:

```dockerfile
RUN useradd --create-home --uid 10001 app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER app
```

## Erros comuns

- **`uv sync` sem `--frozen` no CI.** Reresolve silenciosamente e instala uma
  árvore diferente da revisada.
- **`ruff check --fix` no runner.** O job passa consertando, e a correção não
  entra em commit nenhum.
- **Passo que não encontra nada e sai zero.** Um passo de teste que não achou
  arquivo é indistinguível de um que passou; diga em voz alta que não havia o
  que medir.
- **`.dockerignore` ausente.** Sem ele, `.venv` e `.git` entram no contexto de
  build, e a imagem cresce por engano.
- **Fixar `latest` na imagem base ou no uv.** Reprodutibilidade some, e a
  quebra chega num dia em que ninguém tocou no projeto.

## Ponteiros

- `templates/Dockerfile` — os dois estágios, com cache de camada e usuário
  próprio.
- `templates/ci-python.yml` — o fluxo completo, com a guarda que não deixa
  portão passar por não ter medido nada.
- Como o ambiente é declarado e travado: skill `python-uv`.
- O que cada portão de qualidade cobra: skills `python-ruff` e
  `python-tipagem-estrita`.
