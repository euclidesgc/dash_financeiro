# Plano — 007-objetivo-e-linha-do-tempo

**Trilha:** rápida · **Brief:** `01-brief.md` · Uma fase.

## Fase 1 — O objetivo, os três cenários e a linha do tempo

**Critérios de aceite:**

O banco é preparado por `rm -f /tmp/dash-007.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-007.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-007.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-007.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-007.key .venv/bin/python -m app`.

- [ ] `comportamental` — RF-01, RF-02, RF-05, RF-13
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/objetivo?data=2026-09-05"` é executado
      *Então* a resposta é `200`; o HTML traz `data-alvo="4187958"` e
      `R$ 41.879,58`; traz `R$ 6.979,93` como piso; e a frase que nomeia o
      cruzamento traz o rótulo que `select label from crossings where slug =
      'piso'` devolve
- [ ] `comportamental` — RF-03, RF-04, RF-05
      *Dado* a mesma resposta
      *Quando* os elementos com `data-cenario` do bloco `id="cenarios"` são lidos
      *Então* há exatamente três, na ordem `conservador`, `base`, `otimista`, com
      `data-resultado` valendo `-452321`, `-452321` e `-428945`, e o valor de
      cada um é maior ou igual ao do anterior
- [ ] `comportamental` — RF-08, RF-09, RF-10
      *Dado* a mesma resposta
      *Quando* os blocos `id="cenarios"` e `id="marcos"` são lidos
      *Então* os três `data-cenario` têm `data-meses` **vazio**; o texto traz
      `Nenhum cenário chega ao objetivo.` e `R$ 4.523,21`; e há exatamente três
      elementos `data-marco`, nomeados `resultado`, `dividas` e `reserva`, os
      três com `data-meses` vazio e o texto `não chega`
- [ ] `comportamental` — RF-11, RF-12
      *Dado* o servidor rodando e um cookie válido
      *Quando* `/objetivo?data=2026-09-05` é buscada **duas** vezes,
      `/objetivo?data=2026-10-05` uma vez, e `/objetivo?data=2026-09-05` de novo
      *Então* a última resposta traz exatamente dois elementos `data-ponto`, com
      os valores `2026-09-05` e `2026-10-05`, nessa ordem
- [ ] `comando` — RF-06, RF-07
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_plan.py` sai com código 0, e o arquivo contém: um teste que
      afirma que o alvo é seis vezes o piso; um que afirma que um mês negativo
      deixa os três marcos nulos e o "falta" igual ao resultado invertido; um que
      afirma que um mês positivo alcança o objetivo e devolve meses; um que
      afirma que uma dívida de tipo `mortgage` **não** entra na escada do
      objetivo enquanto uma de tipo `card` entra, com a taxa do imóvel **acima**
      do corte de 1% ao mês, para que o teste exercite a guarda e não a
      comparação de taxa; um que afirma que ler duas vezes no mesmo dia grava um
      ponto só; um que afirma que uma escada já limpa devolve `dividas == 0`; e
      um que afirma que um mês que vai inteiro para a dívida **não** alcança a
      reserva no mesmo mês. O teste do mês negativo afirma os **três** marcos
- [ ] `comportamental` — RF-15, RF-20, RF-18
      *Dado* o servidor rodando e um cookie válido
      *Quando* `GET /objetivo?data=0001-01-01` é buscada
      *Então* a resposta é `200`, **não** `500`; e a resposta de
      `/objetivo?data=2026-09-05` traz o bloco `id="sem-taxa-aviso"` com a
      contagem de dívidas sem taxa e a soma delas
- [ ] `comando` — RF-16, RF-17, RF-19, RF-22
      `rtk proxy grep -REn --exclude-dir=__pycache__ "\* 30" app/templates` não
      imprime nenhuma linha; e `rtk proxy grep -c "released_by_month"
      app/plan/timeline.py` imprime um número maior que 1
- [ ] `comportamental` — RF-21
      *Dado* o servidor rodando e um cookie válido
      *Quando* `/objetivo?data=2026-09-05` e `/objetivo?data=2026-10-05` são
      buscadas e a primeira é buscada de novo
      *Então* o bloco `id="linha-do-tempo"` traz dois elementos com `data-alvo`,
      e os dois valores são **diferentes** entre si
- [ ] `comportamental` — RF-14
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado, sessão
      válida e `http://127.0.0.1:8000/objetivo?data=2026-09-05` carregada
      *Quando* a janela é ajustada para 375, 768 e 1440 px de largura, altura
      800, uma vez carregando já naquela largura e uma vez redimensionando
      *Então* nas seis medições `document.documentElement.scrollWidth <=
      window.innerWidth` avalia como `true`, e todo elemento de
      `document.querySelectorAll("#cenarios *")` tem `animationDuration` e
      `transitionDuration` iguais a `0s`
- [ ] `estrutural` — RF-14
      Existem `product/items/007-objetivo-e-linha-do-tempo/06-capturas/objetivo-375.png`,
      `objetivo-1440.png` e `objetivo-dark-1440.png`, todos no mesmo diretório e
      cada um com mais de 1024 bytes

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz sai com código 0
- [ ] `comando` — portão de lint
      `rtk proxy bash scripts/lint.sh` sai com código 0
- [ ] `comando` — RF-14
      `rtk proxy grep -REn --exclude-dir=__pycache__
      "4187958|697993|452321|428945|23376" app` não imprime nenhuma linha, em
      nenhum dos dois fluxos de saída
- [ ] `comportamental` — RF-13 guarda
      *Dado* nenhuma sessão
      *Quando* `rtk proxy curl -s -o /dev/null -w "%{http_code}"
      http://127.0.0.1:8000/objetivo` é executado
      *Então* a resposta é `302`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Migração `007_plan.sql` com `plan_snapshots`.
- [ ] 1.2 `app/plan/objective.py`: piso, alvo, resultado mensal mediano e as
      alavancas.
- [ ] 1.3 `app/plan/timeline.py`: a simulação mês a mês, os três cenários, os
      marcos e o registro de snapshot.
- [ ] 1.4 `app/routers/plan.py` e `app/templates/objetivo.html`.
- [ ] 1.5 `tests/test_plan.py`.
- [ ] 1.6 As três capturas.

## Validações de campo pendentes

Nenhuma.
