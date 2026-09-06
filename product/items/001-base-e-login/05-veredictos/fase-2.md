# Veredicto — 001-base-e-login, fase 2

VEREDICTO: APROVADO

Portões
  lint/analyze: NÃO EXECUTÁVEL — nenhum linter/typechecker instalado ou declarado. `pyproject.toml` declara como dev deps apenas `pytest` e `httpx`; `import ruff|flake8|mypy|black` → todos `ABSENT`. Não presumo que passaria. Consistente com `.harness/config.json` (`"stacks": {}`, modo processo-apenas, Python sem pack).
  testes:       OK — `env DASH_DB_PATH=/tmp/dash-gate-tests.sqlite .venv/bin/python -m pytest -q` → `27 passed in 0.38s`
  gates:        OK — `bash scripts/gates/gates_runner.sh` → `✓ gates: limpos (árvore completa, 65 arquivo(s) considerados).`

Todos os comandos rodaram com `rtk proxy`, conforme o escape registrado em `.harness/config.json` → `command_quirks` (wrapper `rtk` enxuga a saída por hook global).

Critérios de aceite

  [x] RF-06/RF-10 `comando` — contagens e soma de saldos após carga limpa
      `rm -f /tmp/dash-f2.sqlite && env DASH_DB_PATH=/tmp/dash-f2.sqlite python -m app.ingest` → `ingested transactions=1942 accounts=12`, exit 0.
      Query → `1942 12 -2744971` (exigido `1942 12 -2744971`).

  [x] RF-07 `comando` — tipagem inteira
      Query typeof → `0`.

  [x] RF-08 `comando` — fidelidade de valor contra a fonte
      Comparação lançamento a lançamento com `data/processed/transacoes.json` → `0` divergências.

  [x] RF-09 `comportamental` — sinal em cartão
      Premissa conferida na fonte: `data/raw/v2_transactions_7486098e_2026-09-05_p2.json` traz `amount=-3310.23 type=CREDIT accountId=7486098e-…`; o consolidado traz `valor=3310.23`.
      Query `amount_cents` de `c5120b3b-cb76-4e35-b2ec-2b6784e80cd9` → `331023` (exigido `331023`).

  [x] RF-11 `comando` — sem `pluggy_id` duplicado
      Query group-by-having → `0`.

  [x] RF-12 `comportamental` — duas execuções sobre banco inexistente
      Run 1 → `ingested transactions=1942 accounts=12`, `RUN1_EXIT=0`. Run 2 → `ingested transactions=1942 accounts=12`, `RUN2_EXIT=0`.
      Query → `1942 12 2` (exigido `1942 12 2`).

  [x] RF-13 `comportamental` — SIGTERM e reinício
      `timeout -s TERM 4 python -m app` duas vezes; ambas subiram (`Uvicorn running on http://127.0.0.1:8000`) e encerraram limpo (`Application shutdown complete.` / `Finished server process`).
      Query após o ciclo → `1942` (antes: `1942`).

  [x] RF-14 `comando` — transferências com motivo
      Query → `152` (exigido `152`).

  [x] RF-15 `comportamental` — estorno e débito estornado
      Query → `9 8b073fe4-d7e9-47e9-a24e-f8b6fcbeac43 -246256` (exigido idem).

  [x] RF-16 `comando` — total de gasto bate com o cálculo sobre a fonte
      Saída → `-21860413 -21860413`, `EXIT=0`.

  [x] RF-17 `comportamental` — rejeição sem carga pela metade
      Fixture conferida: índice 1 sem `id`, índice 2 com `"valor": 10.005`, uma conta.
      `INGEST_EXIT=1`. Streams separados (`2>&1 1>/dev/null`) confirmam em **stderr**:
      `rejected index=1 reason=missing_pluggy_id description=LANCAMENTO SEM ID`
      `rejected index=2 reason=fractional_cents description=LANCAMENTO COM MILESIMO`
      (as linhas exigidas aparecem como prefixo, com `description=` acrescido — o critério pede "contém").
      Query `count(*) from transactions` → `0`.

  [x] RF-18 `comportamental` — rollback com id duplicado
      Fixture conferida: índice 0 e 2 com `id=fix-duplicada`, índice 1 `fix-unica`; três válidos.
      `INGEST_EXIT=1`. Query → `0 failed transactions accepted=3 written=2 accounts accepted=1 written=1` — começa por `0 failed` e contém `accepted=3 written=2`.

Instrumentos do implementer
  nenhum. Os doze critérios foram verificados por execução direta contra a fonte real e os bancos em `/tmp`. A suíte de `tests/` foi rodada apenas como portão, não como evidência de critério.

Apontamentos
  `/home/euclidesgc/development/dash_financeiro/app/ingest/loader.py:298-307` — `_count_present` conta linhas **presentes** na tabela para aqueles ids, não linhas gravadas pela execução. Efeito medido em `/tmp/dash-f2c.sqlite`: as duas execuções de RF-12 gravam `sync_runs.transactions_count = 1942`, embora a segunda não tenha inserido nenhuma linha nova (`1 ok 1942 12` / `2 ok 1942 12`). O campo lê-se como "quantas linhas existem depois da carga", não "quantas entraram" — quem for usar `sync_runs` para medir volume sincronizado vai ler o número errado. Nenhum critério desta fase cobre essa semântica e isso **não** altera o veredicto; registro para a fase que for consumir `sync_runs`.

Observações de despacho: o arquivo de critérios veio limpo — só o bloco de critérios, sem plano, spec ou histórico anexado. Nada a reportar de vazamento de envelope.
