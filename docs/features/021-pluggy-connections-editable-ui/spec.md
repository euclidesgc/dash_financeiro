# SPEC 021 — pluggy-connections-editable-ui

Estado atual:

- `app/sync/fetch.py` · `fetch_from_pluggy(config)` chama `itens_salvos()` de `ingestao/pluggy_extract.py`, que lê `data/item_ids.txt`, `data/item_id.txt` e `PLUGGY_ITEM_ID`. Lista vazia vira `PluggyFetchError(NO_ITEMS)`.
- `app/sync/__init__.py` · `synchronise` chama `fetch_from_pluggy(config)` quando a fonte é `pluggy`.
- Nenhuma tabela guarda as conexões; a SPA (`src/`) tem Saldos, Gastos e Categorias.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `GET /api/pluggy-connections` (D3) e tela `/app/connections` (D5). |
| R2 | `POST /api/pluggy-connections` com validação em `add_connection` (D2); 422 para formato, 409 para duplicado. |
| R3 | `DELETE /api/pluggy-connections/{item_id}` (D3); confirmação na tela (D5). |
| R4 | Estado vazio na tela; `NO_ITEMS` com o texto novo (D4). |
| R5 | `synchronise` lê a tabela e passa os ids a `fetch_from_pluggy` (D4). |
| R6 | `python -m app.sync.connections <arquivo>` com `INSERT OR IGNORE` (D2). |

## Decisões

- **D1** — Migração `app/migrations/sql/024_pluggy_connections.sql`: `pluggy_connections (item_id TEXT PRIMARY KEY, created_at TEXT NOT NULL)`. Sem importação automática na migração: `conftest.py` e o seed do e2e rodam as migrações com o diretório do projeto como corrente, e ler `data/item_ids.txt` ali faria a base de teste depender da máquina.
- **D2** — Domínio em `app/sync/connections.py`: `add_connection(conn, raw) -> str` (tira espaços, exige UUID `8-4-4-4-12` hexadecimal, grava em minúsculas; `InvalidItemIdError`, `DuplicateConnectionError`), `remove_connection(conn, item_id)` (`ConnectionNotFoundError`) e `import_file(conn, path) -> int` (linhas válidas, `INSERT OR IGNORE`, devolve quantas entraram). Cada função dá o próprio commit. `__main__` do módulo recebe o caminho do arquivo e imprime a contagem.
- **D3** — Leitura em `app/queries/pluggy_connections.py` (`list_connections`, `ConnectionRow`); router `app/routers/pluggy_connections.py` com prefixo `/api/pluggy-connections`, traduzindo as exceções de D2 em 422, 409 e 404. Login antes da rota vem do guarda global.
- **D4** — `fetch_from_pluggy(config, item_ids, *, transport=None)` recebe a lista; `synchronise` a lê com `list_connections`. `NO_ITEMS = "pluggy: nenhuma conexão cadastrada; cadastre em Conexões."`. `app/sync/fetch.py` deixa de importar `itens_salvos`.
- **D5** — Feature `src/features/pluggy-connections/` (api, components, types), rota `src/app/routes/connections.tsx` em `paths.connections = '/connections'`, link "Conexões" em `AppHeader`. Formulário com React Hook Form + Zod espelhando a regra de D2; lista com estados de carregando, erro com nova tentativa e vazio; remoção com confirmação, no molde de `category-item.tsx`. Mocks MSW em `src/testing/mocks/handlers.ts` com `resetConnections`.
- Alternativa descartada: continuar lendo o arquivo quando a tabela está vazia — manteria duas fontes da mesma lista e a tela mentiria sobre o que a atualização busca.

## Arquivos afetados

- `app/migrations/sql/024_pluggy_connections.sql`, `app/migrations/NUMBERING.md`, `app/sync/connections.py`, `app/queries/pluggy_connections.py`, `app/routers/pluggy_connections.py` (criar/alterar)
- `app/sync/fetch.py`, `app/sync/__init__.py`, `app/main.py` (alterar)
- `tests/test_pluggy_connections.py` (criar), `tests/test_sync_fetch.py`, `tests/test_sync.py` (alterar conforme a assinatura)
- `src/features/pluggy-connections/**`, `src/app/routes/connections.tsx`, `src/app/router.tsx`, `src/config/paths.ts`, `src/components/layouts/app-header.tsx`, `src/testing/mocks/handlers.ts`, `src/testing/setup.ts`
- `e2e/connections.spec.ts` (criar), `docs/setup-secrets.md` se citar o arquivo

## Skills aplicáveis

python-tratamento-de-erros, python-testes-de-integracao-httpx, python-testes-unitarios, br:forms, br:api-requests, br:api-mocking, br:component-testing, br:e2e-testing, br:interface-design.
