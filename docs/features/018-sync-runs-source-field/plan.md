# PLAN 018 — sync-runs-source-field

Branch: `feature/018-sync-runs-source-field`

Decisões registradas aqui:

- **Coluna nova, não reaproveitar `source`**: `source` diz o que foi lido e segue útil no diagnóstico de fonte; a origem do disparo é outra pergunta.
- **Parâmetro obrigatório** em `ingest` e `synchronise`: sem padrão, todo ponto de entrada declara a origem.
- **O primeiro commit da branch marca a 037 como `done`** (mergeada em `develop` no PR #24).

## Fase 1 — Origem do disparo registrada e mostrada

Ao final: cada execução de sincronização ou carga grava `triggered_by`, a API devolve o campo e o painel diz de onde veio a última atualização.

- [ ] T1.1 — Esquema e gravação
  - Arquivos: `app/migrations/sql/023_sync_trigger.sql`, `app/ingest/trigger.py` (criar); `app/migrations/NUMBERING.md`, `app/ingest/loader.py`, `app/ingest/__main__.py`, `app/sync/__init__.py`, `app/sync/exclusive.py`, `app/routers/summary.py` (alterar)
  - O que fazer: D1, D2 e D3 da SPEC.
  - Skills: python-tipagem-estrita
  - Complexidade: baixa
- [ ] T1.2 — API e painel
  - Arquivos: `app/routers/sync.py`, `src/features/sync/types/sync-status.ts`, `src/features/sync/components/sync-panel.tsx`, `src/testing/mocks/handlers.ts` (alterar)
  - O que fazer: D4 e D5 da SPEC.
  - Skills: python-schemas-pydantic-v2, br:interface-design
  - Complexidade: baixa
- [ ] T1.3 — Testes
  - Arquivos: `tests/test_sync.py`, `tests/test_sync_api.py`, `tests/test_ingest.py`, `tests/test_migrations.py`, `src/features/sync/components/__tests__/sync-panel.test.tsx`, `e2e/sync.spec.ts` (alterar)
  - O que fazer: origem gravada no sucesso, na falha de fonte, na falha da Pluggy e pela carga manual; valor fora do domínio recusado pelo banco; API devolve `screen` depois de `POST /api/sync/run` e `null` para linha antiga; painel mostra cada rótulo e nada para `null`; e2e vê "Pedida na tela" depois do botão.
  - Skills: python-testes-de-integracao-httpx, br:component-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [ ] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [ ] CA1.3 — `synchronise` e `ingest` não têm valor padrão para `trigger`; `grep -rn "trigger=" app/` mostra `COMMAND` em `app/sync/__init__.py` (`main`) e `app/ingest/__main__.py`, e `SCREEN` em `app/routers/sync.py` e `app/routers/summary.py`. (estrutural)
- [ ] CA1.4 — Depois de `POST /api/sync/run`, `GET /api/sync/status` devolve `last_run.triggered_by == "screen"`; `main()` do comando grava `command`; uma falha de fonte grava a origem de quem pediu; uma linha sem origem sai como `null`; o banco recusa `triggered_by = 'outro'`. (comportamental)
- [ ] CA1.5 — O painel mostra "Pedida na tela" para `screen`, "Feita pela rotina diária" para `command` e nenhum dos dois para `null`. (comportamental)

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
