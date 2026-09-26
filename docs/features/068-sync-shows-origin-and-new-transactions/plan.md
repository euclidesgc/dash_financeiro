# PLAN 068 — sync-shows-origin-and-new-transactions

Branch: `feature/068-sync-shows-origin-and-new-transactions`

## Fase 1 — API grava e devolve a origem e os lançamentos novos de cada atualização

- [x] T1.1 — Coluna `origin` em `sync_runs` e gravação pela ingestão, com opção de não gravar execução
  - Arquivos: `app/migrations/sql/025_sync_origin.sql` (criar); `app/ingest/loader.py` (alterar); `app/ingest/__main__.py` (alterar)
  - O que fazer: a migração adiciona `origin TEXT NULL CHECK (origin IS NULL OR origin IN ('pluggy', 'file'))` a `sync_runs`, sem preencher linhas existentes. Em `loader.py`, `ingest` ganha os parâmetros nomeados `origin: Literal['pluggy', 'file'] | None = None` e `record: bool = True`; `_fail` recebe os mesmos; `_record_run` grava `origin`. Com `record=False`, nem o sucesso nem `_fail` chamam `_record_run` e o `run_id` devolvido é `None`. `app/ingest/__main__.py` chama `ingest(..., trigger=COMMAND, record=False)`; falha continua indo para stderr com código de saída 1.
  - Skills: —
  - Complexidade: média

- [x] T1.2 — `synchronise` resolve e repassa a origem; a API expõe `origin` e `new_transactions`
  - Arquivos: `app/sync/__init__.py` (alterar); `app/routers/sync.py` (alterar)
  - O que fazer: `synchronise` deriva a origem de `config.sync_source` (`pluggy` → `'pluggy'`, `arquivo` → `'file'`) e a passa a `ingest(..., origin=...)`, `_record_failed` e `_record_failure`, que gravam a coluna `origin`. O modelo Pydantic `SyncRun` ganha `origin: Literal['pluggy', 'file'] | None` e `new_transactions: int | None`, este igual a `transactions_count` quando `status == 'ok'` e `origin` não é nulo, senão `None`. `GET /api/sync` e `POST /api/sync` devolvem os dois campos. Nenhuma contagem de contas é exposta. `app/routers/summary.py` não muda.
  - Skills: —
  - Complexidade: média

- [x] T1.3 — Testes da fase 1
  - Arquivos: `tests/test_migrations.py`, `tests/test_ingest.py`, `tests/test_sync.py`, `tests/test_sync_api.py` (alterar)
  - O que fazer: casos
    - `test_migrations.py`: `test_025_adds_nullable_origin_column`, `test_025_keeps_existing_runs_with_null_origin`, `test_025_rejects_unknown_origin`;
    - `test_ingest.py`: `test_ingest_records_origin`, `test_ingest_without_record_writes_no_run_on_success`, `test_ingest_without_record_writes_no_run_on_failure`, `test_ingest_without_record_returns_none_run_id`;
    - `test_sync.py`: `test_synchronise_records_pluggy_origin_on_success`, `test_synchronise_records_file_origin_on_success`, `test_synchronise_records_origin_on_pluggy_failure`, `test_synchronise_records_origin_on_unreadable_source`;
    - `test_sync_api.py`: `test_get_sync_returns_origin_and_new_transactions`, `test_post_sync_returns_origin_and_new_transactions`, `test_new_transactions_zero_when_nothing_entered`, `test_failed_run_has_null_new_transactions`, `test_legacy_run_has_null_origin_and_new_transactions`, `test_sync_payload_has_no_accounts_count`.
  - Skills: —
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — (estrutural) Existe `app/migrations/sql/025_sync_origin.sql` com `origin TEXT NULL` e `CHECK (origin IS NULL OR origin IN ('pluggy', 'file'))`, sem `UPDATE` em `sync_runs`.
- [x] CA1.2 — (estrutural) `ingest` em `app/ingest/loader.py` aceita `origin` e `record: bool = True`; `app/ingest/__main__.py` chama `ingest` com `record=False`.
- [x] CA1.3 — (estrutural) `SyncRun` em `app/routers/sync.py` tem `origin: Literal['pluggy', 'file'] | None` e `new_transactions: int | None`, e nenhum campo de contagem de contas.
- [x] CA1.4 — (comportamental) Com `record=False`, `ingest` não insere linha em `sync_runs`, nem em sucesso nem em falha; provado por `test_ingest_without_record_writes_no_run_on_success` e `test_ingest_without_record_writes_no_run_on_failure`.
- [x] CA1.5 — (comportamental) Execução com falha devolve `new_transactions: null` e `origin` preenchida; linha anterior à 025 devolve `origin: null` e `new_transactions: null`; provado pelos testes `test_failed_run_has_null_new_transactions` e `test_legacy_run_has_null_origin_and_new_transactions`.
- [x] CA1.6 — (comando) `pytest tests/test_migrations.py tests/test_ingest.py tests/test_sync.py tests/test_sync_api.py` passa com todos os casos nomeados em T1.3; `bash scripts/lint.sh` e `bash scripts/gates/gates_runner.sh` passam; cobertura ≥ 80% em `app/ingest/loader.py`, `app/sync/__init__.py` e `app/routers/sync.py`.

## Fase 2 — O painel mostra de onde veio e quantos lançamentos entraram

- [ ] T2.1 — Contrato do front, mock e frase da origem
  - Arquivos: `src/features/sync/types/sync-status.ts` (alterar); `src/testing/mocks/handlers.ts` (alterar); `src/features/sync/utils/describe-origin.ts` (criar)
  - O que fazer: em `sync-status.ts`, `export type SyncOrigin = 'pluggy' | 'file'` e `SyncRun` ganha `origin: SyncOrigin | null` e `new_transactions: number | null`. `fakeSyncStatus` em `handlers.ts` passa a ter `origin: 'pluggy'` e `new_transactions: 25` no `last_run`. Criar `export function describeOrigin(origin: SyncOrigin | null, newTransactions: number | null): string | null`: `null` se `origin` é nulo; prefixo "Buscou na Pluggy" (`pluggy`) ou "Releu o arquivo local" (`file`); com `newTransactions` nulo devolve só o prefixo; senão prefixo + " · " + "nenhum lançamento novo" (0), "1 lançamento novo" (1) ou "N lançamentos novos" (N > 1).
  - Skills: unit-testing, api-mocking
  - Complexidade: baixa

- [ ] T2.2 — Nova linha no `SyncPanel` e rótulo verdadeiro do gatilho `command`
  - Arquivos: `src/features/sync/components/sync-panel.tsx` (alterar)
  - O que fazer: no bloco à esquerda do cartão "Atualização dos registros", entre "Última atualização: <data e hora>" e a linha do gatilho, renderizar `describeOrigin(last_run.origin, last_run.new_transactions)` quando não for nula, com a mesma receita de texto secundário da linha do gatilho (`docs/design.md`). Ordem final: data, origem, gatilho, selo de estado. Em `TRIGGER_LABELS`, `command` passa a "Feita por comando no terminal"; `screen` segue "Você pediu pelo botão “Atualizar agora”". Estados carregando, erro, vazio ("Nenhuma atualização feita por este painel ainda"), em andamento e o alerta de falha ficam inalterados. Nenhuma receita nova.
  - Skills: interface-design, component-robustness
  - Complexidade: baixa

- [ ] T2.3 — Testes da fase 2
  - Arquivos: `src/features/sync/utils/__tests__/describe-origin.test.ts` (criar); `src/features/sync/components/__tests__/sync-panel.test.tsx` (alterar)
  - O que fazer: casos
    - `describe-origin.test.ts`: `returns null when origin is null`, `describes pluggy with many new transactions`, `describes pluggy with one new transaction`, `describes file with zero new transactions`, `returns only the origin when count is null`;
    - `sync-panel.test.tsx`: `shows origin and count after successful run`, `shows only origin after failed run`, `hides origin line when origin is null`, `shows command trigger as terminal command`, `origin line sits between last update and trigger`.
  - Skills: unit-testing, component-testing, api-mocking
  - Complexidade: baixa

### Critérios de aceite da fase 2

- [ ] CA2.1 — (estrutural) `src/features/sync/types/sync-status.ts` exporta `SyncOrigin = 'pluggy' | 'file'` e `SyncRun` tem `origin: SyncOrigin | null` e `new_transactions: number | null`; `fakeSyncStatus` em `src/testing/mocks/handlers.ts` tem os dois campos.
- [ ] CA2.2 — (estrutural) `src/features/sync/utils/describe-origin.ts` exporta `describeOrigin(origin: SyncOrigin | null, newTransactions: number | null): string | null`.
- [ ] CA2.3 — (comportamental) `describeOrigin('pluggy', 25)` = "Buscou na Pluggy · 25 lançamentos novos"; `describeOrigin('pluggy', 1)` = "Buscou na Pluggy · 1 lançamento novo"; `describeOrigin('file', 0)` = "Releu o arquivo local · nenhum lançamento novo"; `describeOrigin('pluggy', null)` = "Buscou na Pluggy"; `describeOrigin(null, 3)` = `null`.
- [ ] CA2.4 — (comportamental) `SyncPanel` mostra a linha de origem entre "Última atualização:" e a linha do gatilho, não a mostra com `origin` nulo, e com gatilho `command` mostra "Feita por comando no terminal" e não contém "Feita pela rotina diária"; provado pelos casos nomeados em `sync-panel.test.tsx`.
- [ ] CA2.5 — (estrutural) A linha de origem em `sync-panel.tsx` usa as mesmas classes de texto secundário da linha do gatilho (`text-sm text-gray-600`), sem `style={{…}}`.
- [ ] CA2.6 — (comando) `pnpm lint`, `pnpm typecheck` e `pnpm test` passam com todos os casos nomeados em T2.3; cobertura ≥ 80% em `describe-origin.ts` e `sync-panel.tsx`.

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
