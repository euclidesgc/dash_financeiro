# Plano — 005-dividas-e-simuladores

**Trilha:** rápida · **Brief:** `01-brief.md` · Uma fase (ver `D1`).

## Fase 1 — Escada de taxa, taxa editável e simulador

**Objetivo da fase:** as dívidas se leem ordenadas pela taxa mensal, a taxa que
ninguém sabe é campo na tela, e o simulador responde o que um aporte elimina.

**Critérios de aceite:**

O banco é preparado por `rm -f /tmp/dash-005.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-005.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-005.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-005.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-005.key .venv/bin/python -m app`. O cookie vem de um
único `POST /login`.

- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-09
      Com `Q` valendo `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-005.sqlite .venv/bin/python -m app.query`:
      `Q "select kind, count(*), sum(balance_cents) from debts group by kind
      order by kind"` imprime `card 4 -1674462`, `mortgage 1 -23858518`,
      `overdraft 2 -1119018` e `vehicle 1 -3917636`;
      `Q "select kind, monthly_rate_bp from debts where monthly_rate_bp is not
      null order by kind"` imprime exatamente duas linhas, `mortgage 72` e
      `vehicle 163`; e
      `Q "select count(*) from debts where monthly_rate_bp is null"` imprime `6`
- [ ] `comando` — RF-14 a RF-19
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_debts.py` sai com código 0, e o arquivo contém: um teste que
      afirma que o valor presente de 45 parcelas de `123533` centavos a `163`
      pontos-base vale `3917636`; um teste que afirma que um aporte igual ao
      saldo quita o degrau, elimina todas as parcelas e devolve sobra zero; um
      teste que afirma que um aporte maior que o saldo devolve o excedente como
      sobra e nenhuma parcela negativa; um teste que afirma que um degrau sem
      prazo devolve `parcelas_eliminadas = 0` e juros evitados iguais a
      `aporte × taxa`; e um teste que afirma que aporte zero é recusado
- [ ] `comportamental` — RF-06, RF-07, RF-08, RF-23
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/dividas"` é executado
      *Então* a resposta é `200`; o bloco `id="escada"` traz exatamente dois
      elementos com `data-degrau`, na ordem `vehicle` e depois `mortgage`, com
      `data-taxa` valendo `163` e `72`; e o bloco `id="sem-taxa"` traz seis
      elementos com `data-degrau`
- [ ] `comportamental` — RF-10, RF-11, RF-12
      *Dado* o servidor rodando e um cookie válido
      *Quando* a taxa do degrau `overdraft` de maior saldo é gravada por `rtk
      proxy curl -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/dividas/taxa --data-urlencode "degrau=<id>"
      --data-urlencode "taxa=3,52"`, depois com `taxa=-1`, e depois com
      `taxa=` vazia
      *Então* a primeira resposta é `200` e traz o degrau dentro de
      `id="escada"`, no **topo**, com `data-taxa="352"`; a segunda é `400`, traz
      a string `-1` na mensagem de recusa e **não** muda `data-taxa`; e a
      terceira é `200` e devolve o degrau para `id="sem-taxa"`
- [ ] `comportamental` — RF-14, RF-15, RF-16
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/dividas/simular --data-urlencode "degrau=<id do
      vehicle>" --data-urlencode "aporte=10000,00"` é executado
      *Então* a resposta é `200`, o bloco `id="simulacao"` traz um número de
      parcelas eliminadas **maior que 0 e menor que 45**, um valor de juros
      evitados **maior que R$ 0,00**, e a frase que nomeia o degrau simulado
- [ ] `comportamental` — RF-20, RF-21, RF-22
      *Dado* o servidor rodando e um cookie válido
      *Quando* a tela é buscada, o campo de saldo de quitação é gravado por `rtk
      proxy curl -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/dividas/parametro --data-urlencode "nome=quitacao"
      --data-urlencode "valor=35000,00"`, e a tela é buscada de novo
      *Então* a primeira leitura traz `−R$ 39.176,36` e `−R$ 1.235,33` no bloco
      `id="duster"`, e a segunda traz `R$ 35.000,00` e a diferença
      `R$ 4.176,36` como desconto da quitação
- [ ] `comportamental` — RF-25
      *Dado* um banco preparado só com `app.migrate` e `app.auth.seed`, sem
      ingestão nenhuma, e o servidor subido contra ele
      *Quando* `GET /dividas` é buscada com cookie válido
      *Então* a resposta é `200` e o HTML traz `Nenhuma dívida na base.` e um
      `href` que leva o dono a outra tela do painel
- [ ] `comportamental` — RF-24
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado, sessão
      válida e `http://127.0.0.1:8000/dividas` carregada
      *Quando* a janela é ajustada para 375, 768 e 1440 px de largura, com altura
      800, uma vez carregando já naquela largura e uma vez redimensionando com a
      página aberta
      *Então* nas seis medições `document.documentElement.scrollWidth <=
      window.innerWidth` avalia como `true`, e para todo elemento de
      `document.querySelectorAll("#escada *")` `animationDuration` e
      `transitionDuration` valem `0s`
- [ ] `estrutural` — RF-24
      Existem `product/items/005-dividas-e-simuladores/06-capturas/dividas-375.png`,
      `dividas-1440.png` e `dividas-dark-1440.png`, todos no mesmo diretório e
      cada um com mais de 1024 bytes
- [ ] `comportamental` — RF-26
      *Dado* o servidor rodando e um cookie válido
      *Quando* `GET /?data=2026-09-05` é buscada
      *Então* o HTML traz `href="/dividas"`
- [ ] `comportamental` — RF-05
      *Dado* um banco preparado com `DASH_MANUAL_DIR` apontando para um diretório
      vazio
      *Quando* `app.ingest` é executado contra ele
      *Então* o comando sai com código 0 e `select count(*) from debts where
      kind in ('mortgage', 'vehicle')` devolve `0`

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q`
      executado na raiz sai com código 0
- [ ] `comando` — RF-13, RF-27
      `rtk proxy grep -REn --exclude-dir=__pycache__
      "1119018|1674462|23858518|3917636|123533|3\.52|0\.0352|\b(352|163|72)\b"
      app/debts app/routers/debts.py app/templates/dividas.html` não imprime
      nenhuma linha, em nenhum dos dois fluxos de saída
- [ ] `comando` — RF-24
      `rtk proxy grep -REn "#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(" app/templates
      app/static/css/app.css` não imprime nenhuma linha
- [ ] `comportamental` — RF-23
      *Dado* nenhuma sessão
      *Quando* `rtk proxy curl -s -o /dev/null -w "%{http_code}"
      http://127.0.0.1:8000/dividas` é executado
      *Então* a resposta é `302` e o cabeçalho `location` é `/login`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Migração `005_debts.sql` com a tabela `debts` e a tabela
      `plan_parameters` de dois campos (nome, valor em centavos).
      Justificativa: RF-01, RF-20 — o que só o humano sabe precisa de onde
      morar, e `plan_facts` completo é do item `008`; aqui basta o par nome-valor.
- [ ] 1.2 `app/debts/ladder.py`: a carga que cria os degraus a partir de
      `accounts` e de `data/manual/*.json`, e a leitura ordenada por taxa.
      Justificativa: RF-02 a RF-06, RF-08 — o saldo do CDC nasce de cálculo e
      não de cópia, e degrau sem taxa não entra na escada.
- [ ] 1.3 `app/debts/simulate.py`: parcelas eliminadas por valor presente e
      juros evitados.
      Justificativa: RF-14 a RF-19 — dividir aporte por parcela erraria, porque
      cada parcela carrega juros diferentes.
- [ ] 1.4 `app/routers/debts.py` e `app/templates/dividas.html`, com os
      `data-degrau` e `data-taxa` que tornam a ordem verificável.
      Justificativa: RF-06 a RF-12, RF-23 — ordem exibida só é verificável se a
      taxa estiver legível ao lado.
- [ ] 1.5 `tests/test_debts.py`.
      Justificativa: RF-19 — nenhum destes erros quebra a tela; todos produzem
      um número plausível e errado.
- [ ] 1.6 As três capturas.
      Justificativa: RF-24.

## Validações de campo pendentes

Nenhuma.
