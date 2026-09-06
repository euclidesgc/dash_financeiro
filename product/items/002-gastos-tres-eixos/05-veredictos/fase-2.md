# Veredicto — 002-gastos-tres-eixos, fase 2

VEREDICTO: APROVADO

Portões
  lint/analyze: não avaliado — o despacho e o próprio bloco de critérios ("A DoD
                global é do CI e não se repete aqui") excluem a DoD global deste
                julgamento.
  testes:       OK (informativo) — `rtk proxy env DASH_ENV_FILE=/dev/null
                .venv/bin/python -m pytest -q` → `204 passed, 2 warnings in 7.41s`

Banco sob verificação: `rm -f /tmp/dash-002-f2.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f2.sqlite .venv/bin/python -m
app.ingest` → `ingested transactions=1942 accounts=12` / `taxonomy seeded:
groups=10 natures=3 essentialities=3 crossings=2 rules=80` / `classified 1942:
changed=1942 without_rule=7`, exit 0.

Critérios de aceite
  [x] RF-15, RF-16 — agregação por grupo → `True -10377233 732`, exit 0
  [x] RF-17 — agregação por categoria → `52` seguido, na ordem, de
      `School -1299218 20` / `Real estate financing -1235881 5` /
      `Services -877412 48` / `Loans and financing -787050 7` /
      `Transfers -622071 21` / `Transfer - Bank Slip -523959 1` /
      `Groceries -501764 84` / `Transfer - PIX -468515 58` /
      `Eating out -436013 60` / `Shopping -417870 84`
  [x] RF-10, RF-18 — agregação por beneficiário → `317` seguido de
      `debito prestacao hab -1235881 5` / `pagamento de boleto sociedade de
      assistencia e cultura sagra -1088005 7` / `pagamento de boleto safra cfi
      s a -749738 6`
  [x] RF-19 — transferências a terceiros contam como gasto → `-468515 58 -523959 1`
  [x] RF-20, RF-21 — cinco eixos, mesmo total, nenhuma linha positiva →
      `5 {-10377233} 0`
  [x] RF-23 — período inválido, provocado diretamente sem passar pela suíte →
      `período inválido: fim (2026-01-31) anterior a inicio (2026-03-01)` e
      `data inválida: inicio (2026-13-01)`; `isinstance(e,
      app.queries.axes.InvalidPeriodError)` → `True` nas duas
  [x] RF-24 — eixo desconhecido → `eixo inválido: cor. Eixos aceitos: grupo,
      categoria, beneficiario, natureza, essencialidade`
  [x] RF-25 — cruzamento `corte` → `variável × supérfluo 0 0 0`, exit 0.
      Cumprido pela letra, e satisfeito no vazio — ver o primeiro apontamento
  [x] RF-26 — cruzamento `piso` → `fixa × essencial -4187960 -697993`, com a
      média conferida à mão: `round(-4187960/6) = -697993`
  [x] RF-27 — série de treze meses → `13 2025-08 2026-08 -1921711`
  [x] RF-28 — mês sem gasto vale zero e não some. O teste nomeado foi lido:
      a fixture monta gasto em 2026-01 e 2026-03, e as três linhas de 2026-02
      são receita, transferência interna e par estorno/estornado — todas fora do
      filtro. Corroborado por fora: `monthly_series(conn, end_month='2020-06')`,
      janela sem nenhuma transação, devolveu 13 pontos, todos zero — os pontos
      vêm do `WITH months(month) AS (VALUES …) LEFT JOIN`, não do que existe
  [x] RF-29, RF-30 — drill-down → `20 -1299218 True`; o total das 20 transações
      reconcilia com a célula `School -1299218 20`
  [x] RF-22 — nenhum número congelado em código de `app/` → nenhuma linha; e a
      busca repetida sem restrição de extensão, para alcançar o arquivo de dados
      novo, também não achou nada

Instrumentos do implementer
  RF-28 depende da suíte por construção do próprio critério; mitigado pela
  leitura do teste e pela corroboração independente descrita acima. Os outros
  doze critérios foram executados contra `/tmp/dash-002-f2.sqlite`.

Apontamentos
  `app/taxonomy/seed.json` + `app/queries/crossings.py` — **o cruzamento `corte`
  é estruturalmente vazio**, e por isso RF-25 passa no vácuo. A essencialidade
  `supérfluo` existe na taxonomia e o cruzamento é definido contra ela, mas
  nenhuma das 1942 transações a recebe: `SELECT essentiality, count(*) FROM
  transactions GROUP BY essentiality` devolve só `('essencial', 478)` e
  `('importante', 1464)`, porque as 80 regras semeadas se dividem em 20
  `essencial` e 60 `importante` e nenhuma atribui `supérfluo`. Consequência: o
  cruzamento que existe para responder "o que dá para cortar" devolve zero
  linhas e total zero para qualquer período, e o comando de RF-25 não distingue
  isso de um cruzamento funcionando — `ordenado` é vacuamente verdadeiro sobre
  lista vazia e `soma == total` vira `0 == 0`. O código desta fase está correto;
  o buraco é da classificação. Quem receber esta fase deve saber que o `corte`
  está mudo antes de construir tela em cima dele.

  Escopo do commit — o despacho declara o trabalho em `app/queries/**` e
  `tests/**`, e o diff também altera documentos de processo do item. Não abri
  nenhum deles; registro que o ponteiro é mais largo que o escopo declarado.

Envelope: o despacho veio limpo — objetivo, treze critérios tipados e a nota da
DoD. Nada de plano, spec ou histórico.
