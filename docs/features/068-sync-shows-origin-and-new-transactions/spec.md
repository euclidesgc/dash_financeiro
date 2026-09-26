# SPEC 068 — sync-shows-origin-and-new-transactions

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `sync_runs` ganha a coluna `origin` (`pluggy` ou `file`), gravada por `synchronise`; `GET/POST /api/sync` devolvem `origin` e `new_transactions` (de `sync_runs.transactions_count`, que já é o número de lançamentos que entraram na execução); o `SyncPanel` monta a linha "Buscou na Pluggy · 25 lançamentos novos". |
| R2 | Função pura `describeOrigin` no front: 0 → "nenhum lançamento novo", 1 → "1 lançamento novo", N → "N lançamentos novos". |
| R3 | A linha não usa `accounts_count`; a API não expõe contagem de contas. |
| R4 | Em execução com `status = 'failed'`, a API devolve `new_transactions: null` e a linha mostra só a origem ("Buscou na Pluggy"). `_record_failed` e `_record_failure` gravam a origem tentada. |
| R5 | A migração não preenche linhas antigas: `origin` fica `NULL` e o painel omite a linha. |
| R6 | `ingest` passa a aceitar `record=False`; `python -m app.ingest` (chamado por `scripts/dev.sh`) carrega sem gravar em `sync_runs`. O rótulo do gatilho `command` deixa de ser "Feita pela rotina diária" (rotina que não existe) e passa a "Feita por comando no terminal" (D5). |

## Decisões técnicas

### D1 — Origem em coluna própria, não no `source`

- Escolha: migração `025_sync_origin.sql` adiciona `origin TEXT NULL CHECK (origin IS NULL OR origin IN ('pluggy', 'file'))`. `synchronise` deriva a origem de `config.sync_source` (`pluggy` → `pluggy`, `arquivo` → `file`) e a repassa a `ingest(..., origin=...)`, a `_record_failed` e a `_record_failure`. `_record_run` grava a coluna.
- Alternativa descartada: reinterpretar `source` (hoje sempre o caminho do arquivo) — motivo: mudaria o sentido de um dado histórico e não distinguiria linhas antigas (R5).

### D2 — Contagem vem de `transactions_count`, não do texto da mensagem

- Escolha: `SyncRun.new_transactions = transactions_count` quando `status = 'ok'` e `origin` não é nulo; senão `null`.
- Alternativa descartada: extrair `transactions=N` de `message` por regex — motivo: a coluna numérica já existe desde a migração 006 com exatamente essa semântica (lançamentos que entraram).

### D3 — A subida pelo F5 não grava execução

- Escolha: parâmetro `record: bool = True` em `ingest`; com `False`, nem o caminho de sucesso nem `_fail` chamam `_record_run` e `run_id` fica `None`. `app/ingest/__main__.py` chama com `record=False` (o `trigger` continua obrigatório na assinatura e passa `COMMAND`, sem efeito). Falha continua indo para stderr e sai com código 1.
- Alternativa descartada: tirar `python -m app.ingest` do `scripts/dev.sh` — motivo: a base recém-migrada subiria sem lançamentos nem classificação. Descartada também: novo gatilho `startup` com filtro na leitura — motivo: continuaria enchendo o histórico, que o R6 proíbe.
- Coerência com o resumo (`app/routers/summary.py::_sync`, que usa `last_runs` para idade dos dados e aviso de falha): sem a linha da subida, a idade passa a contar do último "Atualizar agora" (ou de `python -m app.sync`), que é quando os dados de fato mudaram — a subida relê o mesmo arquivo. Nenhuma mudança no resumo.

### D4 — Texto montado no front, a API devolve dados

- Escolha: `origin: 'pluggy' | 'file' | null` e `new_transactions: number | null` em `SyncRun`; o texto pt-BR sai de `src/features/sync/utils/describe-origin.ts`.
- Alternativa descartada: API devolver a frase pronta — motivo: o padrão atual (`triggered_by` → `TRIGGER_LABELS`) já traduz no front; a frase no back misturaria apresentação no router.

Sem contrato OpenAPI versionado no repositório: o contrato é o modelo Pydantic `SyncRun` e o tipo espelho em `src/features/sync/types/sync-status.ts`, alterados juntos.

### D5 — Rótulo do gatilho `command` diz a verdade

- Escolha: em `TRIGGER_LABELS` de `sync-panel.tsx`, `command` passa a "Feita por comando no terminal". O valor `command` no banco e na API não muda; depois do D3, a única origem dele é `python -m app.sync` rodado à mão.
- Alternativa descartada: renomear o valor `command` no banco — motivo: exigiria migrar o CHECK da 023 e os dados antigos sem ganho para quem lê a tela.

## Interface

Tela de Atualização, painel "Atualização dos registros" (`SyncPanel`), sem tela nova. No bloco à esquerda do cartão, a ordem passa a ser:

1. "Última atualização: <data e hora>" (inalterado).
2. **Nova linha**, só quando `last_run.origin` não é nulo, em `text-sm text-gray-600` (mesma receita da linha do gatilho):
   - sucesso: "Buscou na Pluggy · 25 lançamentos novos", "Buscou na Pluggy · 1 lançamento novo", "Releu o arquivo local · nenhum lançamento novo";
   - falha: "Buscou na Pluggy" ou "Releu o arquivo local" (sem contagem; o alerta de falha continua abaixo, inalterado).
3. Linha do gatilho: "Você pediu pelo botão “Atualizar agora”" (`screen`, inalterado) ou **"Feita por comando no terminal"** (`command`, antes "Feita pela rotina diária").
4. Selo de estado (inalterado).

Estados carregando, erro, vazio ("Nenhuma atualização feita por este painel ainda") e em andamento: inalterados. Receitas usadas: texto secundário do `docs/design.md`. Nenhuma receita nova.

## Arquivos

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `app/migrations/sql/025_sync_origin.sql` | coluna `origin` nula com CHECK | — |
| alterar | `app/ingest/loader.py` | parâmetros `origin` e `record` em `ingest`/`_fail`; `_record_run` grava `origin` e é pulado com `record=False` | — |
| alterar | `app/ingest/__main__.py` | chama `ingest(..., record=False)` | — |
| alterar | `app/sync/__init__.py` | `synchronise` resolve a origem e a repassa; `_record_failed`/`_record_failure` gravam `origin` | — |
| alterar | `app/routers/sync.py` | `SyncRun` ganha `origin` e `new_transactions` | — |
| alterar | `tests/test_ingest.py` | `record=False` não grava linha (sucesso e falha); `origin` gravada | — |
| alterar | `tests/test_sync.py` | origem gravada em sucesso, falha da Pluggy e fonte ilegível | — |
| alterar | `tests/test_sync_api.py` | `origin`/`new_transactions` no payload; `null` em linha antiga e em falha | — |
| alterar | `tests/test_migrations.py` | 025 aplica e linhas antigas ficam com `origin` nulo | — |
| alterar | `src/features/sync/types/sync-status.ts` | `SyncOrigin`, `origin`, `new_transactions` | — |
| criar | `src/features/sync/utils/describe-origin.ts` | função pura origem + contagem → frase | `unit-testing` |
| criar | `src/features/sync/utils/__tests__/describe-origin.test.ts` | 0, 1, N, falha, nulo | `unit-testing` |
| alterar | `src/features/sync/components/sync-panel.tsx` | nova linha entre data e gatilho; rótulo de `command` vira "Feita por comando no terminal" | `interface-design`, `component-robustness` |
| alterar | `src/features/sync/components/__tests__/sync-panel.test.tsx` | linha presente em sucesso/falha, ausente com `origin` nulo; `command` mostra "Feita por comando no terminal" e não "Feita pela rotina diária" | `component-testing`, `api-mocking` |
| alterar | `src/testing/mocks/handlers.ts` | `fakeSyncStatus` com `origin` e `new_transactions` | `api-mocking` |

## Estimativa de tamanho

Jornadas: 1 · Telas novas: 0 · Linhas alteradas (sem testes): ~90 · Fases previstas: 2 (back + migração; front)

## Dívida encontrada

- `sync_runs.source` guarda o caminho do arquivo consolidado mesmo quando a execução foi à Pluggy; o nome promete a origem e não a entrega. Esta fatia não o altera (D1).
