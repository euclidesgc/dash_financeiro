# Plano — 013-objetivo-cenario-vazio-e-ponto-espurio

**Trilha:** rápida · **Brief:** `01-brief.md` · Uma fase.

## Fase 1 — A lista vazia nomeada e o ponto espúrio impedido

**Critérios de aceite:**

O banco é preparado por `rm -f /tmp/dash-013.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-013.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-013.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-013.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-013.key .venv/bin/python -m app`.

- [ ] `comportamental` — RF-01
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/objetivo?data=2026-09-05"` é executado
      *Então* a resposta é `200` e traz o bloco `id="alavanca-vazia"` com a
      string `a lista de corte` e a frase que diz que o cenário base devolve o
      mesmo número do conservador
- [ ] `comportamental` — RF-02, RF-03
      *Dado* o servidor rodando e um cookie válido, e o banco recém-preparado
      *Quando* `/objetivo?data=0001-01-01` é buscada, depois
      `/objetivo?data=2026-09-05`, depois `/objetivo?data=2026-10-05`, e por fim
      `/objetivo?data=2026-09-05` de novo
      *Então* a primeira resposta é `200`, traz `id="recusa"` e a string `não
      gravou ponto`; e `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-013.sqlite .venv/bin/python -m app.query "select
      distinct reference_date from plan_snapshots order by reference_date"`
      imprime **exatamente duas** linhas, `2026-09-05` e `2026-10-05` — a data de
      hoje **não** aparece
- [ ] `comando` — RF-01, RF-02
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_plan.py` sai com código 0, e o arquivo contém um teste que
      afirma que a leitura com data recusada traz `não gravou ponto` e deixa a
      série com só as duas datas aceitas, e outro que afirma que a tela traz o
      bloco `id="alavanca-vazia"` nomeando a lista de corte

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz sai com código 0
- [ ] `comando` — portão de lint
      `rtk proxy bash scripts/lint.sh` sai com código 0

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 `_reference` de `app/routers/plan.py` devolve também se a data foi
      aceita, e a gravação passa a depender disso.
- [ ] 1.2 O contexto ganha as alavancas vazias, e o template as nomeia.
- [ ] 1.3 Os dois testes em `tests/test_plan.py`.

## Validações de campo pendentes

Nenhuma.
