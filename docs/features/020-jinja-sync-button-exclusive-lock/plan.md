# PLAN 020 — jinja-sync-button-exclusive-lock

Branch: `feature/020-jinja-sync-button-exclusive-lock`

Decisões registradas aqui:

- **O primeiro commit da branch marca a 019 como `done`** (mergeada em `develop` no PR #26).

## Fase 1 — Botão da tela de resumo pela trava única

Ao final: o botão de atualizar da tela de resumo recusa uma segunda atualização simultânea com o mesmo aviso da tela nova.

- [ ] T1.1 — Trava no `POST /sincronizar`
  - Arquivos: `app/routers/summary.py` (alterar)
  - O que fazer: D1 e D2 da SPEC.
  - Skills: python-tratamento-de-erros
  - Complexidade: baixa
- [ ] T1.2 — Testes
  - Arquivos: `tests/test_sync_api.py` (alterar)
  - O que fazer: com `app.sync.exclusive._LOCK` segura, `POST /sincronizar` responde 409, a página traz "Já existe uma atualização em andamento." e `sync_runs` não ganha linha; com a trava livre, a trava fica livre de novo depois do `POST /sincronizar`.
  - Skills: python-testes-de-integracao-httpx
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [ ] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [ ] CA1.3 — `grep -n "synchronise(" app/routers/summary.py` só encontra `exclusive_synchronise(`. (estrutural)
- [ ] CA1.4 — Com a trava de `app/sync/exclusive.py` segura, `POST /sincronizar` autenticado responde 409, o HTML contém "Já existe uma atualização em andamento." e a contagem de `sync_runs` não muda. (comportamental)
- [ ] CA1.5 — Com a trava livre, `POST /sincronizar` grava uma linha em `sync_runs` com `triggered_by = 'screen'` e, ao fim, `is_synchronising()` é falso. (comportamental)

## DoD da entrega

- [ ] DoD1 — Todas as tarefas e critérios do plano marcados
- [ ] DoD2 — Suíte de testes inteira passa
- [ ] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [ ] DoD4 — Tipos de todos os `tsconfig` sem erros
- [ ] DoD5 — Console dos testes sem erro nem aviso
- [ ] DoD6 — `build` passa
- [ ] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [ ] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [ ] DoD9 — Nenhuma worktree ou branch temporária sobrando
