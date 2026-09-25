# PLAN 020 — jinja-sync-button-exclusive-lock

Branch: `feature/020-jinja-sync-button-exclusive-lock`

Decisões registradas aqui:

- **O primeiro commit da branch marca a 019 como `done`** (mergeada em `develop` no PR #26).

## Fase 1 — Botão da tela de resumo pela trava única

Ao final: o botão de atualizar da tela de resumo recusa uma segunda atualização simultânea com o mesmo aviso da tela nova.

- [x] T1.1 — Trava no `POST /sincronizar`
  - Arquivos: `app/routers/summary.py`, `app/templates/fragments/resumo_sincronizacao.html` (alterar)
  - O que fazer: D1, D2 e D3 da SPEC.
  - Skills: python-tratamento-de-erros
  - Complexidade: baixa
- [x] T1.2 — Testes
  - Arquivos: `tests/test_sync_api.py` (alterar)
  - O que fazer: com `app.sync.exclusive._LOCK` segura, `POST /sincronizar` responde 409, a página traz "Já existe uma atualização em andamento." e `sync_runs` não ganha linha; com a trava livre, a trava fica livre de novo depois do `POST /sincronizar` e a página traz o resultado em `id="aviso-sincronizacao"`, sem a frase sobre data.
  - Skills: python-testes-de-integracao-httpx
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — `grep -n "synchronise(" app/routers/summary.py` só encontra `exclusive_synchronise(`. (estrutural)
- [x] CA1.4 — Com a trava de `app/sync/exclusive.py` segura, `POST /sincronizar` autenticado responde 409, o HTML contém "Já existe uma atualização em andamento." e a contagem de `sync_runs` não muda. (comportamental)
- [x] CA1.5 — Com a trava livre e a base vazia, `POST /sincronizar` grava uma linha em `sync_runs` com `triggered_by = 'screen'`, a página traz "Sincronizado." em `id="aviso-sincronizacao"` sem "A tela responde pela data de hoje." e, ao fim, `is_synchronising()` é falso. (comportamental)

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
