# SPEC 018 — sync-runs-source-field

`sync_runs.source` guarda o caminho do arquivo lido (ou `pluggy`, quando a busca na Pluggy falha), e nada registra quem disparou a execução. A coluna `source` continua como está — ela diz **o que** foi lido, e isso ajuda a diagnosticar falha de fonte —; a origem do disparo ganha coluna própria.

O que o código já faz e esta SPEC reaproveita:

- `app/sync/__init__.py` · `synchronise`, chamada pelo comando diário (`python -m app.sync`), pela rota `POST /api/sync/run` (via `exclusive_synchronise`) e pelo botão Jinja `POST /sincronizar` (`app/routers/summary.py`).
- `app/ingest/loader.py` · `ingest` escreve a linha de `sync_runs` do sucesso e das falhas de carga (`_record_run`); `app/ingest/__main__.py` é a carga manual pelo terminal.
- `app/routers/sync.py` · `SyncRun`, a resposta de `GET /api/sync/status` e `POST /api/sync/run`.
- `src/features/sync/components/sync-panel.tsx` · o painel "Atualização dos registros".

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | Coluna `sync_runs.triggered_by` (D1); `synchronise` e `ingest` exigem `trigger` (D2); cada ponto de entrada passa o seu (D3). |
| R2 | `SyncRun.triggered_by` na API (D4) e uma linha no painel (D5). |
| R3 | Linhas antigas ficam com `NULL`; API devolve `null`; o painel omite a linha (D1, D5). |
| R4 | `_record_failed` (sync) e `_fail` (carga) gravam `triggered_by` (D2). |

## Decisões

- **D1** — Migração `023_sync_trigger.sql`: `ALTER TABLE sync_runs ADD COLUMN triggered_by TEXT NULL CHECK (triggered_by IS NULL OR triggered_by IN ('screen', 'command'))`. Nulo só para o passado, como a `006` fez com as contagens: inventar a origem de uma execução antiga seria pior que não tê-la. `app/migrations/NUMBERING.md` passa a apontar `024` como a próxima.
- **D2** — `app/ingest/trigger.py` define `Trigger = Literal["screen", "command"]`, `SCREEN` e `COMMAND`. `ingest(..., trigger: Trigger)` e `synchronise(conn, *, trigger: Trigger, today=None)` recebem o parâmetro **obrigatório**: um padrão escondido faria um ponto de entrada novo gravar a origem errada sem ninguém ver. `exclusive_synchronise` repassa.
- **D3** — `app/sync.main` e `app/ingest/__main__.main` passam `COMMAND`; `POST /api/sync/run` e `POST /sincronizar` passam `SCREEN`.
- **D4** — `SyncRun.triggered_by: Literal["screen", "command"] | None`; `src/features/sync/types/sync-status.ts` espelha.
- **D5** — Abaixo de "Última atualização: …", em texto secundário: `screen` → "Pedida na tela"; `command` → "Feita pela rotina diária"; `null` → nada. O texto fica num `<p>` separado para não mudar o texto que o e2e e o usuário já leem na linha da data.

## Arquivos afetados

- `app/migrations/sql/023_sync_trigger.sql` (criar), `app/migrations/NUMBERING.md`
- `app/ingest/trigger.py` (criar), `app/ingest/loader.py`, `app/ingest/__main__.py`
- `app/sync/__init__.py`, `app/sync/exclusive.py`, `app/routers/sync.py`, `app/routers/summary.py`
- `src/features/sync/types/sync-status.ts`, `src/features/sync/components/sync-panel.tsx`, `src/testing/mocks/handlers.ts` (e o dado falso de status)
- testes: `tests/test_sync.py`, `tests/test_sync_api.py`, `tests/test_ingest.py`, `tests/test_migrations.py`, `src/features/sync/components/__tests__/sync-panel.test.tsx`, `e2e/sync.spec.ts`

## Skills aplicáveis

python-tipagem-estrita, python-schemas-pydantic-v2, python-testes-de-integracao-httpx, br:component-testing, br:interface-design, br:e2e-testing.
