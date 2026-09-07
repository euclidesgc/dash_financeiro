FROM python:3.12-slim-bookworm AS builder

# Motivo: o uv vem por COPY de uma imagem com versão fixa em vez de por script
# de instalação. Script baixado no build resolve para a versão do dia, e duas
# construções do mesmo commit passam a produzir árvores diferentes.
COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Motivo: as dependências entram numa camada própria, antes do código. Sem esta
# separação, trocar uma linha de `src/` invalida a camada de instalação e cada
# build reinstala a árvore inteira.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12-slim-bookworm AS runtime

# Motivo: processo de aplicação não precisa de root, e um contêiner que roda
# como root transforma qualquer execução remota de código em controle do host.
RUN useradd --create-home --uid 10001 app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
