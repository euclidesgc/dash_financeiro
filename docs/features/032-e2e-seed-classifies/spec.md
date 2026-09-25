# SPEC 032 — e2e-seed-classifies

Trigésima segunda fatia, dívida técnica. A base do e2e é montada por um trecho Python escrito dentro de `scripts/e2e-backend.sh` (`uv run python -c '…'`): migra, cria o usuário `e2e`, semeia a taxonomia, chama `ingest` e apaga `sync_runs`. Desde a 024 o recebedor (`payee`) nasce na carga, mas a classificação (`classify_all`: `rule_id`, `group_id`, `nature`, `essentiality` e o registro das categorias Pluggy em `categories`) só roda no pós-carga de `synchronise` (`app/sync/__init__.py::_after`). A base do e2e fica, até alguém apertar "Atualizar" numa prova, num estado que a produção nunca tem. Sem interface.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/taxonomy/classify.py` · `classify_all(conn) -> int`: devolve quantas linhas mudou; exige o fallback semeado (`MissingFallbackError`).
- `app/ingest/loader.py` · `ingest(...) -> IngestResult`: já dá `commit`; `status != "ok"` quando recusa.
- `app/sync/__init__.py` · `synchronise` chama `classify_all` só depois de `ingest` com `ok`.
- `tests/` já é importável como `tests.*` (`pythonpath = ["."]`); `from tests.conftest import …` é o padrão.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `seed` chama `classify_all(conn)` depois do `ingest` com `ok`, antes do `commit` final (D1, D2). |
| R2 | Teste: depois de `seed`, `classify_all(conn)` devolve `0` (D3). |
| R3 | `seed` mantém o `DELETE FROM sync_runs` com o `# Reason:` atual (D1). |
| R4 | `seed` devolve o `IngestResult` sem classificar quando `status != "ok"`; `main` sai com `1` (D2). |

## Decisões técnicas

### D1 — O seed do e2e sai do shell para `tests/e2e_seed.py`

- Escolha: módulo `tests/e2e_seed.py` com `seed(conn: sqlite3.Connection) -> IngestResult` (usuário, taxonomia, carga, classificação, limpeza de `sync_runs`) e `main() -> int` (`run_migrations()`, `connect()`, `seed`, `close`; `0` se `ok`, `1` senão), rodado por `uv run python -m tests.e2e_seed`. `scripts/e2e-backend.sh` troca o bloco `python -c` por essa linha; exports e o resto do script não mudam.
- Motivo: código dentro de string de shell não passa por `ruff` nem por teste; sem teste, R1 e R2 não têm prova. `tests/` é a casa de fixture e já é coberto pelo `ruff` de `scripts/lint.sh`.
- Alternativa descartada: só acrescentar `classify_all(conn)` ao `python -c` — motivo: a mudança ficaria sem teste que a prove.
- Alternativa descartada: módulo em `app/` — motivo: dado e senha de fixture não pertencem ao pacote da aplicação.

### D2 — Classificar só depois de uma carga `ok`, na mesma ordem de `synchronise`

- Escolha: `if result.status != "ok": return result` antes de `classify_all`. Espelha `synchronise`, que só roda `_after` com `ok`.
- Alternativa descartada: chamar `_after` inteiro (classificação, compromissos, escada) — motivo: `_after` é privado de `app/sync`, e compromissos e escada estão fora do escopo do PRD.

### D3 — Prova de paridade por idempotência

- Escolha: `tests/test_e2e_seed.py` roda `seed` numa base temporária migrada e afirma: nenhuma linha com `group_id`, `nature` ou `essentiality` nulo; ao menos uma linha com `rule_id` não nulo; `classify_all(conn) == 0` em seguida; `sync_runs` vazia; usuário `e2e` existe. Outro teste troca `tests/data/e2e_transactions.json` por uma lista com linha sem `id` (via `monkeypatch` no carregador do módulo) e afirma `status != "ok"` e nenhuma linha classificada.

## Contrato

Sem mudança de API nem de OpenAPI.

## Interface

Sem interface.

## Arquivos

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `tests/e2e_seed.py` | `seed` e `main` (D1, D2) | `python-tipagem-estrita` |
| alterar | `scripts/e2e-backend.sh` | bloco `python -c` vira `uv run python -m tests.e2e_seed` (D1) | — |
| criar | `tests/test_e2e_seed.py` | testes de R1, R2, R3, R4 (D3) | `python-testes-unitarios` |

## Estimativa de tamanho

Jornadas: 0 novas · Telas novas: 0 · Linhas (sem testes): ~45 · Fases previstas: 1. Nenhum sinal de "grande demais".

## Dívida encontrada

- nenhuma
