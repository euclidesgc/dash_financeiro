# Plano — 014-taxa-sugerida-pelos-juros-cobrados

**Trilha:** rápida · **Brief:** `01-brief.md` · Uma fase.

## Fase 1 — A taxa sugerida, com a faixa à vista

**Critérios de aceite:**

O banco é preparado por `rm -f /tmp/dash-014.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-014.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-014.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-014.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-014.key DASH_TODAY=2026-09-05 .venv/bin/python -m app`.

- [ ] `comando` — RF-01, RF-03, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-014.sqlite
      .venv/bin/python -c` com um trecho que abre o banco, chama
      `app.debts.observed.observed_rates(conn, today=date(2026, 9, 5))` e imprime
      o mapa, mostra **duas** contas: uma chamada `itau`, com `median_bp` igual a
      `671`, `lowest_bp` igual a `458`, `highest_bp` igual a `984` e `months`
      igual a `7`; e uma chamada `CAIXA`, com `median_bp` igual a `800` e
      `months` igual a `3`
- [ ] `comando` — RF-13, RF-14
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_observed_rates.py` sai com código 0, e o arquivo contém um teste
      que afirma que uma conta que posta cedo **cobra em atraso** e que o juro
      conta para o mês anterior; outro que faz o mesmo com o lançamento no **dia
      6** — o dia em que a conta real posta, e o que um corte fixo em cinco dias
      não alcançava; outro que afirma que conta que posta no fim do mês **não**
      cobra em atraso; outro que afirma que o **mês em curso** não entra; e outro
      que afirma que a mediana de uma contagem par é **arredondada**; outro que
      afirma que o mês mais antigo, truncado pela reconstrução, é medido contra os
      dias do **calendário** e não contra os dias reconstruídos; e outro que
      afirma que um mês cujo juro **líquido é positivo** não conta como cobrança
- [ ] `comando` — RF-15
      `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-014.sqlite
      .venv/bin/python -c` com um trecho que conta as tags do bloco
      `id="sem-taxa"` da resposta de `/dividas` imprime o **mesmo** número de
      `<td>` e de `</td>`
- [ ] `comportamental` — RF-09, RF-10
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      http://127.0.0.1:8000/dividas` é executado
      *Então* a resposta é `200`; o bloco `id="sem-taxa"` traz **exatamente
      dois** elementos com `data-sugerida`, com os valores `671` e `800` e os
      `data-faixa` `458-984` e `799-816`; o campo de taxa da linha do `itau` vem
      com `value="6,71"`; e **nenhuma** linha de cartão traz `data-sugerida`
- [ ] `comportamental` — RF-11
      *Dado* o servidor rodando e um cookie válido
      *Quando* a tela é buscada e, **sem** enviar nenhum `POST`, o banco é
      consultado por `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-014.sqlite .venv/bin/python -m app.query "select
      count(*) from debts where monthly_rate_bp is not null"`
      *Então* o resultado é `2` — as duas dívidas de contrato, e **nenhuma** das
      que receberam sugestão
- [ ] `comando` — RF-02, RF-04, RF-05, RF-06
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_observed_rates.py` sai com código 0, e o arquivo contém: um
      teste que afirma que a reconstrução para no primeiro lançamento e não
      inventa dias antes dele; um que afirma que mês sem juros cobrados não vira
      taxa; um que afirma que saldo abaixo do piso é descartado; um que afirma
      que menos meses que o mínimo não produz sugestão; um que afirma que a
      sugestão é a mediana e que o menor é menor que ela e o maior é maior; e um
      que afirma que lançamento de **mora** não produz sugestão

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz sai com código 0
- [ ] `comando` — portão de lint
      `rtk proxy bash scripts/lint.sh` sai com código 0
- [ ] `comando` — RF-12
      `rtk proxy grep -REn --exclude-dir=__pycache__ "\b(671|800|458|984|799|816)\b"
      app/debts app/routers/debts.py app/templates/dividas.html` não imprime
      nenhuma linha
- [ ] `estrutural` — RF-10
      Existem `product/items/014-taxa-sugerida-pelos-juros-cobrados/06-capturas/dividas-375.png`,
      `dividas-1440.png` e `dividas-dark-1440.png`, cada um com mais de 1024 bytes

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 `app/debts/observed.py`: a reconstrução do saldo diário, o filtro de
      mora, o piso de saldo, o mínimo de meses e a mediana com a faixa.
- [ ] 1.2 `app/routers/debts.py` e `app/templates/dividas.html`: o campo
      preenchido, a legenda com a origem e a faixa, e o parágrafo que explica por
      que cartão não tem sugestão.
- [ ] 1.3 `tests/test_observed_rates.py`.
- [ ] 1.4 As três capturas.

## Validações de campo pendentes

- A taxa contratada do cheque especial só o extrato confirma. A sugestão é
  estimativa declarada; confirmar é ato do dono.
