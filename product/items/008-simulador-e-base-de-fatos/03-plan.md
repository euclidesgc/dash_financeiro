# Plano — 008-simulador-e-base-de-fatos

**Trilha:** rápida · **Brief:** `01-brief.md` · Uma fase.

## Fase 1 — O simulador e a base de fatos

**Critérios de aceite:**

O banco é preparado por `rm -f /tmp/dash-008.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-008.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-008.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-008.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-008.key .venv/bin/python -m app`.

- [ ] `comportamental` — RF-01, RF-02
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/simulador?data=2026-09-05"` é executado
      *Então* a resposta é `200`, o HTML traz um `form` com
      `action="/simulador"` e `method="post"`, e traz os campos `tipo`, `mensal`,
      `unico`, `prazo` e `nome`
- [ ] `comportamental` — RF-03, RF-07, RF-09
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/simulador --data-urlencode "tipo=receita"
      --data-urlencode "mensal=5.000,00" --data-urlencode "data=2026-09-05"
      --data-urlencode "nome=Vender o carro"` é executado
      *Então* a resposta é `200`; o bloco `id="resposta"` traz
      `data-mensal="500000"`, `data-dias=""` e a frase que diz que a sobra é
      **menor que os juros da escada**, **sem** a palavra `negativo`; e o bloco
      `id="guardados"` traz um `data-cenario="Vender o carro"`
- [ ] `comportamental` — RF-08
      *Dado* o servidor rodando e um cookie válido
      *Quando* o mesmo `POST` é feito com `mensal=abc`, depois com
      `tipo=outra-coisa`, e depois com `prazo=meio ano`
      *Então* as três respostas são `400`; a primeira traz `Valor mensal
      inválido` na recusa, a segunda traz `outra-coisa`, a terceira traz
      `Prazo inválido`; e `select count(*) from scenarios` não muda
- [ ] `comando` — RF-03, RF-04, RF-05, RF-06, RF-10, RF-12
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_whatif.py` sai com código 0, e o arquivo contém: um teste que
      afirma que receita soma e despesa subtrai; um que afirma que uma receita
      aproxima (dias negativos) e outro que uma despesa afasta (dias positivos);
      um que afirma que transformar "nunca" em data devolve `days_delta is
      None`; um que afirma que um efeito de zero devolve o **mesmo** número de
      meses antes e depois; um que afirma que cenário sem nome é recusado; e um
      que afirma que fato com validade no passado é marcado vencido
- [ ] `comportamental` — RF-11, RF-12
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/simulador/fato --data-urlencode "nome=quitacao-cdc"
      --data-urlencode "rotulo=Saldo de quitação do CDC" --data-urlencode
      "valor=35.000,00" --data-urlencode "validade=2026-08-01"` é executado
      *Então* a resposta é `200`, o bloco `id="fatos"` traz
      `data-fato="quitacao-cdc"`, `R$ 35.000,00` e a palavra `vencido`
- [ ] `comportamental` — RF-14, RF-15, RF-16
      *Dado* o servidor rodando e um cookie válido
      *Quando* `POST /simulador` é feito com `mensal=5000.00`, depois com
      `mensal=inf`, `mensal=nan`, `mensal=1e3` e `mensal=0,004`
      *Então* as cinco respostas são `400`, **nenhuma** é `500`, e a primeira
      traz a string `1.234,56` na mensagem de recusa
- [ ] `comportamental` — RF-17, RF-19
      *Dado* o servidor rodando e um cookie válido
      *Quando* `POST /simulador/fato` é feito com `validade=banana` e depois com
      `validade=2026-08-01` mais `data=2026-09-05`
      *Então* a primeira é `400` e traz `Validade inválida`; a segunda é `200`,
      marca o fato como `vencido`, e o formulário devolvido traz
      `value="2026-09-05"` no campo `data`
- [ ] `comando` — RF-18
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_whatif.py` sai com código 0, e o arquivo contém um teste que
      afirma que um **prazo** de dois meses deixa o objetivo **mais distante** do
      que o mesmo efeito sem prazo, e que um **valor único** o deixa mais próximo
- [ ] `comportamental` — RF-13
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado, sessão
      válida e `http://127.0.0.1:8000/simulador?data=2026-09-05` carregada
      *Quando* a janela é ajustada para 375, 768 e 1440 px, altura 800, uma vez
      carregando já naquela largura e uma vez redimensionando
      *Então* nas seis medições `document.documentElement.scrollWidth <=
      window.innerWidth` avalia como `true`, e todo elemento de
      `document.querySelectorAll("#formulario *")` tem `animationDuration` e
      `transitionDuration` iguais a `0s`
- [ ] `estrutural` — RF-13
      Existem `product/items/008-simulador-e-base-de-fatos/06-capturas/simulador-375.png`,
      `simulador-1440.png` e `simulador-dark-1440.png`, cada um com mais de 1024
      bytes

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz sai com código 0
- [ ] `comando` — portão de lint
      `rtk proxy bash scripts/lint.sh` sai com código 0
- [ ] `comando` — RF-04
      `rtk proxy grep -c "from app.plan.timeline import" app/plan/whatif.py`
      imprime `1`, e `rtk proxy grep -REn --exclude-dir=__pycache__ "def
      simulate" app/plan` imprime **uma** linha só
- [ ] `comportamental` — RF-01 guarda
      *Dado* nenhuma sessão
      *Quando* `rtk proxy curl -s -o /dev/null -w "%{http_code}"
      http://127.0.0.1:8000/simulador` é executado
      *Então* a resposta é `302`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Migração `008_facts.sql` com `plan_facts` e `scenarios`.
- [ ] 1.2 `app/plan/whatif.py` e o parâmetro `extra_monthly_cents` em
      `app/plan/timeline.simulate`.
- [ ] 1.3 `app/routers/whatif.py` e `app/templates/simulador.html`.
- [ ] 1.4 `tests/test_whatif.py`.
- [ ] 1.5 As três capturas.

## Validações de campo pendentes

Nenhuma.
