# SPEC 022 — setup-secrets-pluggy-credentials

Estado atual: `docs/setup-secrets.md` veio do modelo do harness e cita `DATABASE_URL`, `SECRET_KEY`, `APP_ENV`, `CORS_ORIGINS` e um `gitleaks` no CI, nada disso existente. As variáveis reais são as lidas em `app/config.py` (`load_config`) e `app/sync/__init__.py` (`DASH_SYNC_SOURCE`).

## Decisões

- **D1** — A página é reescrita no presente (norma 7), em três grupos: acesso ao painel, sincronização com a Pluggy, opcionais. Cada linha diz se é segredo e onde se obtém.
- **D2** — `DASH_SYNC_SOURCE=` entra no `.env.example`, vazio: `_first` trata vazio como ausente, então o padrão `arquivo` segue valendo.
- **D3** — Variáveis de caminho usadas só por scripts e testes (`DASH_TRANSACTIONS_PATH`, `DASH_ACCOUNTS_GLOB`, `DASH_TODAY`) ficam fora da página: não são configuração de quem instala.

## Arquivos afetados

- `docs/setup-secrets.md`, `.env.example` (alterar)

## Skills aplicáveis

nenhuma de código.
