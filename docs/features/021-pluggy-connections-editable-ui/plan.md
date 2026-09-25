# PLAN 021 — pluggy-connections-editable-ui

Branch: `feature/021-pluggy-connections-editable-ui`

Decisões registradas aqui:

- **O primeiro commit da branch marca a 020 como `done`** (mergeada em `develop` no PR #27).

## Fase 1 — Conexões na base e na atualização

Ao final: a API lista, cadastra e remove conexões, e a atualização pela Pluggy busca as conexões da base.

- [x] T1.1 — Tabela, domínio, consulta e router
  - Arquivos: `app/migrations/sql/024_pluggy_connections.sql`, `app/migrations/NUMBERING.md`, `app/sync/connections.py`, `app/queries/pluggy_connections.py`, `app/routers/pluggy_connections.py`, `app/main.py`
  - O que fazer: D1, D2 e D3 da SPEC.
  - Skills: python-tratamento-de-erros
  - Complexidade: média
- [x] T1.2 — Atualização lê a base
  - Arquivos: `app/sync/fetch.py`, `app/sync/__init__.py`
  - O que fazer: D4 da SPEC.
  - Skills: python-tratamento-de-erros
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `tests/test_pluggy_connections.py`, `tests/test_sync_fetch.py`
  - O que fazer: API (lista vazia, cadastro, 422, 409, 404, 401 sem sessão), `import_file` idempotente e `synchronise` com a fonte `pluggy` passando os ids da base.
  - Skills: python-testes-de-integracao-httpx
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `grep -rn "itens_salvos\|item_ids.txt" app/` não encontra nada. (estrutural)
- [x] CA1.3 — Autenticado, `POST /api/pluggy-connections` com `{"item_id": " 3F2504E0-4F89-11D3-9A0C-0305E82C3301 "}` responde 201 com `item_id` em minúsculas; repetir responde 409 "Essa conexão já está cadastrada."; `{"item_id": "abc"}` responde 422 com a mensagem de formato; `GET` lista a conexão; `DELETE` responde 204 e um segundo `DELETE` 404; sem sessão, `GET` responde 401. (comportamental)
- [x] CA1.4 — `import_file` com um arquivo de duas linhas válidas, uma repetida e uma inválida grava 2 conexões e, rodado de novo, grava 0. (comportamental)
- [x] CA1.5 — Com a fonte `pluggy` e a tabela vazia, `synchronise` grava falha com "nenhuma conexão cadastrada; cadastre em Conexões."; com uma conexão cadastrada, a busca recebe exatamente esse id. (comportamental)

## Fase 2 — Tela de conexões

Ao final: o dono abre "Conexões" no menu, vê, cadastra e remove conexões.

- [x] T2.1 — Feature, rota e menu
  - Arquivos: `src/features/pluggy-connections/**`, `src/app/routes/connections.tsx`, `src/app/router.tsx`, `src/config/paths.ts`, `src/components/layouts/app-header.tsx`, `src/testing/mocks/handlers.ts`, `src/testing/setup.ts`
  - O que fazer: D5 da SPEC.
  - Skills: br:forms, br:api-requests, br:api-mocking, br:interface-design
  - Complexidade: média
- [x] T2.2 — Testes
  - Arquivos: `src/features/pluggy-connections/components/__tests__/*`, `src/components/layouts/__tests__/app-header.test.tsx`, `e2e/connections.spec.ts`
  - O que fazer: carregando, erro com nova tentativa, vazio, cadastro válido, recusa de formato sem chamar a API, 409 no campo, remoção com confirmação e cancelamento; e2e cadastra, recarrega, remove e deixa a base como achou.
  - Skills: br:component-testing, br:e2e-testing
  - Complexidade: média

### Critérios de aceite da fase 2

- [x] CA2.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA2.2 — `src/features/pluggy-connections/` não importa de outra feature nem de `src/app/`. (estrutural)
- [x] CA2.3 — O menu tem o link "Conexões" para `/connections`, marcado como atual nessa rota. (comportamental)
- [x] CA2.4 — Na tela, "abc" mostra a mensagem de formato sem chamar a API; um identificador válido aparece na lista e o campo esvazia; um duplicado mostra "Essa conexão já está cadastrada." no campo; remover pede confirmação e, confirmado, a conexão some; sem conexões aparece "Nenhuma conexão cadastrada.". (comportamental)

## DoD da entrega

- [x] DoD1 — Todas as tarefas e critérios do plano marcados
- [x] DoD2 — Suíte de testes inteira passa
- [x] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [x] DoD4 — Tipos de todos os `tsconfig` sem erros
- [x] DoD5 — Console dos testes sem erro nem aviso
- [x] DoD6 — `build` passa
- [x] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [x] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [x] DoD9 — Nenhuma worktree ou branch temporária sobrando
