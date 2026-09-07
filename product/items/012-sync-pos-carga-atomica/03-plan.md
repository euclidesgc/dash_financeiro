# Plano — 012-sync-pos-carga-atomica

**Trilha:** rápida · **Brief:** `01-brief.md` · Uma fase.

## Fase 1 — A pós-carga dentro do tratamento de erro

**Critérios de aceite:**

- [ ] `comando` — RF-01, RF-02, RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_sync.py` sai com código 0, e o arquivo contém um teste que
      substitui `app.sync._after` por algo que levanta exceção, chama
      `synchronise`, e afirma que o resultado tem `status == "failed"`, que a
      **última** linha de `sync_runs` está com `failed`, que a mensagem gravada
      traz `pós-carga falhou`, e que `readable` dessa mensagem traz
      `não foram recalculados`
- [ ] `estrutural` — RF-01
      Em `app/sync/__init__.py`, a chamada a `_after` está dentro de um bloco
      `try`, e o `except` correspondente chama uma função que executa `UPDATE
      sync_runs SET status = 'failed'`
- [ ] `comportamental` — RF-05
      *Dado* o banco `/tmp/dash-012.sqlite` preparado por `rm -f
      /tmp/dash-012.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-012.sqlite DASH_TODAY=2026-09-05 .venv/bin/python -m
      app.ingest`
      *Quando* `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-012.sqlite DASH_TODAY=2026-09-05 .venv/bin/python -m
      app.sync` é executado
      *Então* o comando sai com código 0, imprime uma linha começando por
      `sync ok`, e `select status from sync_runs order by id desc limit 1`
      devolve `ok`

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz sai com código 0
- [ ] `comando` — portão de lint
      `rtk proxy bash scripts/lint.sh` sai com código 0

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Envolver `_after` em `try` e acrescentar `_demote` em
      `app/sync/__init__.py`.
- [ ] 1.2 Acrescentar o padrão `pós-carga falhou` a `readable`.
- [ ] 1.3 O teste em `tests/test_sync.py`.

## Validações de campo pendentes

Nenhuma.
