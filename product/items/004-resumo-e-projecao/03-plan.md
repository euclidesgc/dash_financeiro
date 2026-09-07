# Plano — 004-resumo-e-projecao

**Item:** `004-resumo-e-projecao` · **Trilha:** rápida · **Brief:** `01-brief.md`

Duas fases, em sequência. A fase 2 renderiza o que a fase 1 devolve, e um
contrato de retorno inventado no template seria refeito ao encontrar o real.

## Fase 1 — Motor de projeção

**Objetivo da fase:** as três posições, os três números do mês e a série diária
de 45 dias existem como função determinística e testada.

**Critérios de aceite:**

O banco desta fase é preparado por `rm -f /tmp/dash-004-f1.sqlite && rtk proxy
env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-004-f1.sqlite
DASH_TODAY=2026-09-05 .venv/bin/python -m app.ingest`.

- [ ] `comando` — RF-01, RF-02, RF-03, RF-04
      Com `P` valendo `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-004-f1.sqlite .venv/bin/python -c`, o trecho
      `import sqlite3; from app.projection.position import positions;
      c=sqlite3.connect('/tmp/dash-004-f1.sqlite'); c.row_factory=sqlite3.Row;
      print(positions(c))` imprime um mapa cujo `consolidated_cents` vale
      `-2744971`, cujo `cash_cents` vale `-1070509`, cujo `card_cents` vale
      `-1674462`, e em que `cash_cents + card_cents == consolidated_cents`
- [ ] `comando` — RF-05, RF-06, RF-07, RF-08
      O mesmo trecho para `app.projection.monthly.monthly(c,
      today=date(2026,9,5))` imprime `income_cents` igual a `1222621`,
      `spending_cents` igual a `-1767746`, `leftover_cents` igual a `-545125`, e
      `months` igual a `['2026-03', '2026-04', '2026-05', '2026-06', '2026-07',
      '2026-08']`
- [ ] `comando` — RF-10, RF-12, RF-13, RF-14, RF-15
      O mesmo trecho para `app.projection.forecast.forecast(c,
      today=date(2026,9,5))` imprime um mapa em que `days` tem **46** elementos,
      o primeiro com `date == '2026-09-05'` e `balance_cents == -2744971`, o
      último com `date == '2026-10-20'` e `balance_cents == -3444179`;
      `worst["date"]` vale `'2026-10-13'` e `worst["balance_cents"]` vale
      `-4072295`; `delta_cents` vale `-699208`; e `variable_cents` vale `-965067`
- [ ] `comando` — RF-16
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_projection.py` sai com código 0, e o arquivo contém um teste que
      monta um banco temporário com uma conta de saldo conhecido e nenhum
      lançamento, e afirma que a projeção devolve 46 dias todos com o mesmo
      saldo; e outro que afirma que a soma das três parcelas de um dia é igual à
      diferença entre o saldo daquele dia e o do dia anterior, para **todos** os
      dias da série
- [ ] `estrutural` — RF-10
      `app/projection/forecast.py` importa a janela de `app.commitments.calendar`
      e **não** declara constante própria de horizonte: `rtk proxy grep -REn
      --exclude-dir=__pycache__ "WINDOW_DAYS|HORIZON|\b45\b" app/projection`
      imprime ao menos uma linha citando `WINDOW_DAYS` e nenhuma linha que
      atribua `45` a um nome

**Critérios de integração:**

- [ ] `comando` — portão local, no lugar do CI que este repositório não tem
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q`
      executado na raiz sai com código 0
- [ ] `comando` — RF-24
      `rtk proxy grep -REn --exclude-dir=__pycache__
      "2744971|1070509|1674462|1222621|1767746|545125|3444179|4072295|699208|965067"
      app/projection app/routers` não imprime nenhuma linha, em nenhum dos dois
      fluxos de saída

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Criar `app/projection/position.py` com `positions(conn) -> dict`,
      devolvendo `consolidated_cents`, `cash_cents` e `card_cents` a partir de
      `accounts`, agrupados pelo `type`.
      Justificativa: RF-01 a RF-04 — as três posições são a base de tudo, e
      confundi-las é o erro que destrói a tela: R$ 16.744,62 dos R$ 27.449,71 são
      dívida de cartão a 51% ao ano, não saldo de conta.
- [ ] 1.2 Criar `app/projection/monthly.py` com `monthly(conn, *, today)`,
      devolvendo renda, gasto e sobra medianos dos seis meses completos
      anteriores, e a lista dos meses usados.
      Justificativa: RF-05 a RF-08 — a mediana neutraliza os R$ 42.210,26 de
      03/2026 sem que ninguém precise decidir à mão o que é atípico, e devolver
      os meses usados é o que torna a régua auditável na tela.
- [ ] 1.3 Criar `app/projection/forecast.py` com `forecast(conn, *, today)`,
      somando por dia o compromisso datado, a renda no dia mediano de entrada e o
      gasto variável diluído; devolvendo a série, o pior ponto e o delta.
      Justificativa: RF-10 a RF-15 — sem a parcela variável a linha sobe
      R$ 7.276,37 em 45 dias e o painel diz que o déficit se fecha sozinho, que é
      a forma mais cara de errar numa tela que existe para ser acreditada.
- [ ] 1.4 Escrever `tests/test_projection.py`.
      Justificativa: RF-16 — nenhum destes erros quebra a tela; todos produzem
      uma linha plausível e errada.

## Fase 2 — Tela de Resumo

**Objetivo da fase:** a rota `/` serve o Resumo, com as três posições, os três
números do mês, a linha do tempo de 45 dias e o caminho para o resto do painel.

**Critérios de aceite:**

O banco é o `/tmp/dash-004-f2.sqlite`, preparado pelos mesmos dois comandos do
`003` (`app.ingest` com `DASH_TODAY=2026-09-05`, depois `app.auth.seed` com
`LOGIN=teste PASSORD=senha-teste-9k2`), e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-004-f2.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-004-f2.key .venv/bin/python -m app`. O cookie
`dash_session` vem de um único `POST /login`.

- [ ] `comportamental` — RF-01 a RF-04, RF-20
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/?data=2026-09-05"` é executado
      *Então* a resposta é `200` e o HTML traz as strings `−R$ 27.449,71`,
      `−R$ 10.705,09` e `−R$ 16.744,62`, cada uma ao lado do seu rótulo
- [ ] `comportamental` — RF-05, RF-07, RF-08, RF-09
      *Dado* o servidor rodando e um cookie válido
      *Quando* a mesma requisição a `/?data=2026-09-05` é executada
      *Então* o HTML traz `R$ 12.226,21`, `−R$ 17.677,46` e `−R$ 5.451,25`, e a
      frase que nomeia a janela de seis meses da qual os três saem
- [ ] `comportamental` — RF-11, RF-14, RF-15, RF-18
      *Dado* o servidor rodando e um cookie válido
      *Quando* a mesma requisição a `/?data=2026-09-05` é executada e o bloco
      `id="projecao"` é recortado da resposta
      *Então* o bloco traz `−R$ 27.449,71` como ponto de partida,
      `−R$ 34.441,79` como chegada em `20/10/2026`, `−R$ 40.722,95` como pior
      ponto em `13/10/2026`, e a frase que declara sobre qual posição a linha
      corre
- [ ] `comportamental` — RF-19
      *Dado* `http://127.0.0.1:8000/?data=2026-09-05` aberta no Chromium com
      sessão válida
      *Quando* `document.querySelectorAll("#projecao [data-dia]")` é percorrido
      *Então* há ao menos um elemento; todo `data-dia` está entre `2026-09-05` e
      `2026-10-20`, em ordem crescente e sem repetição; e em cada elemento
      `Number(el.dataset.saldo)` é igual ao `data-saldo` do anterior somado a
      `Number(el.dataset.entra) + Number(el.dataset.sai) + Number(el.dataset.variavel)`
- [ ] `comportamental` — RF-21
      *Dado* o servidor rodando e um cookie válido
      *Quando* a mesma requisição a `/?data=2026-09-05` é executada
      *Então* o HTML traz `href="/gastos"`, `href="/comprometido"` e
      `href="/regras"`
- [ ] `comportamental` — RF-23
      *Dado* um banco preparado só com `app.migrate` e `app.auth.seed`, sem
      ingestão nenhuma, e o servidor subido contra ele
      *Quando* `GET /?data=2026-09-05` é buscada com cookie válido
      *Então* a resposta é `200`, o HTML traz `Nenhum lançamento na base.` e um
      `href` que leva o dono ao próximo ato
- [ ] `comportamental` — RF-22
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado, sessão
      válida e `http://127.0.0.1:8000/?data=2026-09-05` carregada
      *Quando* a janela é ajustada para as larguras 375, 768 e 1440 px, com
      altura de 800, uma vez carregando já naquela largura e uma vez
      redimensionando com a página aberta
      *Então* nas seis medições `document.documentElement.scrollWidth <=
      window.innerWidth` avalia como `true`, e para todo elemento de
      `document.querySelectorAll("#projecao *")` `animationDuration` e
      `transitionDuration` valem `0s`
- [ ] `estrutural` — RF-22
      Existem os arquivos `product/items/004-resumo-e-projecao/06-capturas/resumo-375.png`,
      `resumo-1440.png` e `resumo-dark-1440.png`, todos no mesmo diretório e cada
      um com mais de 1024 bytes
- [ ] `comando` — RF-22
      `rtk proxy grep -REn "#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(" app/templates
      app/static/css/app.css` não imprime nenhuma linha

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q`
      executado na raiz sai com código 0
- [ ] `comando` — RF-24
      `rtk proxy grep -REn --exclude-dir=__pycache__
      "2744971|1070509|1674462|1222621|1767746|545125|3444179|4072295|699208|965067"
      app/projection app/routers app/templates` não imprime nenhuma linha
- [ ] `comportamental` — RF-20
      *Dado* nenhuma sessão
      *Quando* `rtk proxy curl -s -o /dev/null -w "%{http_code}"
      "http://127.0.0.1:8000/?data=2026-09-05"` é executado
      *Então* a resposta é `302`, e o cabeçalho `location` é `/login`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 2.1 Criar `app/routers/summary.py` servindo `GET /`, com `?data=`, e
      registrá-lo em `app/main.py` no lugar da rota provisória do `001`.
      Justificativa: RF-20 e D5 — a tela mínima do `001` foi registrada na
      entrega da fase 4 daquele item como provisória, a ser substituída por este.
- [ ] 2.2 Criar `app/templates/resumo.html` e os fragmentos das três posições, do
      mês e da projeção, com `data-dia`, `data-saldo`, `data-entra`, `data-sai` e
      `data-variavel` em cada dia.
      Justificativa: RF-19 — soma exibida só é verificável se as parcelas dela
      estiverem legíveis ao lado, e é assim que o `003` já se deixa medir.
- [ ] 2.3 Acrescentar em `app/static/css/app.css` as classes da linha do tempo,
      reusando a escala graduada de `tokens.css`.
      Justificativa: RF-17 e RF-22 — a escala é o elemento de assinatura e
      aparece onde existe distância a percorrer; nenhum valor de cor ou espaço
      nasce fora do token.
- [ ] 2.4 Gerar as três capturas em `06-capturas/`.
      Justificativa: RF-22 — a captura é a evidência que sobrevive à sessão, e
      densidade de tela só se julga vendo.

## Validações de campo pendentes

Nenhuma.
