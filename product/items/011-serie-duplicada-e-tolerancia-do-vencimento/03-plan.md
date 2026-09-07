# Plano — 011-serie-duplicada-e-tolerancia-do-vencimento

Uma fase. Os quatro defeitos vivem no mesmo pacote, são medidos pela mesma base
e mudam os mesmos números; separá-los produziria três validações cegas do mesmo
motor.

## Fase 1 — Integridade das séries de compromisso

**Objetivo da fase:** o comprometido conta cada dívida uma vez só, conta só o que
ainda vai sair da conta, e o calendário não esconde vencimento.

**Critérios de aceite:**

O banco desta fase é preparado por `rm -f /tmp/dash-011-f1.sqlite && rtk proxy
env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-011-f1.sqlite
DASH_TODAY=2026-09-05 .venv/bin/python -m app.ingest && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-011-f1.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`, e o servidor por
`rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-011-f1.sqlite
LOGIN=teste PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-011-f1.key .venv/bin/python -m app`. O cookie
`dash_session` vem de um único `POST /login` com
`login=teste&senha=senha-teste-9k2`.

- [ ] `comando` — RF-02, RF-07, RF-25
      `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-011-f1.sqlite
      .venv/bin/python -m app.query "select kind, count(*) from commitments group
      by kind order by kind"` imprime exatamente duas linhas, `installment` com
      **74** e `recurring` com **51**, somando 125; e
      `... .venv/bin/python -m app.query "select count(*) from commitments where
      kind = 'recurring' and series_key in ('cp amigao macae', 'jim com',
      'mercadolivre merca', 'mercadolivre prod')"` imprime **0**
- [ ] `comportamental` — RF-03, RF-24, RF-25
      *Dado* o servidor rodando contra `/tmp/dash-011-f1.sqlite` e um cookie
      `dash_session` válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/comprometido?data=2026-09-05"` é executado
      *Então* a resposta é `200`, o HTML traz a string `−R$ 9.553,00` como total
      comprometido e `R$ 0,00` como economia projetada, **não** traz a string
      `−R$ 12.802,64`, e o bloco `id="parcelamentos"` traz `R$ 233,76` como caixa
      liberado
- [ ] `comando` — RF-01, RF-04
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_commitments_precedence.py` sai com código 0, e o arquivo contém
      um teste que monta um banco temporário com uma série parcelada cobrada
      **dentro** da janela e sem parcela a vencer (`installments_left = 0`) e
      afirma que `recompute` não grava linha `recurring` para aquela chave, e
      outro teste que monta a mesma série cobrada **fora** da janela e afirma que
      a linha `recurring` daquela chave é gravada
- [ ] `comando` — RF-05, RF-06, RF-08, RF-09
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_commitments_series.py` sai com código 0, e o arquivo contém um
      teste que monta seis parcelas `n/6` do mesmo beneficiário com a primeira
      valendo `-13647` centavos e as outras `-13643`, e afirma que uma única
      série é detectada, com `installment_total = 6`, `last_installment = 6`,
      `installments_left = 0` e `amount_cents = -13643`; e outro teste que monta
      dois grupos `n/12` do mesmo beneficiário, um de `-2707` e outro de `-4960`,
      e afirma que **duas** séries são detectadas
- [ ] `comando` — RF-10, RF-11, RF-12, RF-13, RF-14
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_commitments_calendar.py` sai com código 0, e o arquivo contém,
      além dos casos que já existem, um teste que afirma que um lançamento a 20
      dias do dia previsto **não** apaga a previsão daquele mês (as duas entradas
      aparecem) e um teste que afirma que uma série com dia previsto 29 e
      lançamento no dia 1º do mês seguinte aparece **uma** vez só
- [ ] `comando` — RF-22, RF-23
      `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-011-f1.sqlite
      .venv/bin/python -m app.query "select count(*) from commitments where kind
      = 'recurring' and last_seen_date >= '2026-08-01'"` imprime **26**, e
      `... "select count(*) from commitments where kind = 'recurring' and
      last_seen_date > '2026-09-30'"` imprime um número **maior que 0**, provando
      que série com cobrança datada no futuro existe na base e é contada como
      viva
- [ ] `comportamental` — RF-15
      *Dado* o servidor rodando contra `/tmp/dash-011-f1.sqlite` e um cookie
      válido
      *Quando* a resposta de `/comprometido?data=2026-09-05` é lida e o bloco
      `id="calendario"` é recortado
      *Então* existe exatamente um elemento com `data-serie="jim com"` no bloco,
      ele está dentro do dia `data-dia="2026-09-08"`, o seu `data-centavos` vale
      `-13643`, e o texto daquela entrada traz `já lançado na conta` e não traz
      `previsto pelo histórico`
- [ ] `comportamental` — RF-18
      *Dado* o banco `/tmp/dash-011-e2e.sqlite` preparado do zero pelos mesmos
      dois comandos, o servidor subido com ele e um cookie de um único login
      *Quando* a tela é lida, as três dispensas são enviadas por `rtk proxy curl
      -s -o /dev/null -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/comprometido/dispensar --data-urlencode
      "serie=<chave>" --data-urlencode "data=2026-09-05"`, com `<chave>` valendo
      `anthropic claude subsan franciscousa`, `pagamento de boleto mycon` e
      `totalpasssao paulobra`, e a tela é lida de novo
      *Então* a primeira leitura traz `R$ 0,00` de economia projetada e a segunda
      traz `R$ 1.099,63`, sem reingestão e sem reinício de processo
- [ ] `estrutural` — RF-05, RF-11, RF-22
      As três tolerâncias existem como constante nomeada em escopo de módulo, com
      o valor declarado no brief: `2%` para o desvio que separa duas compras,
      `10` dias para a distância que realiza uma previsão, e um mês para o
      alcance do piso de vida. Nenhuma delas aparece como literal no meio de uma
      expressão

**Critérios de integração:**

- [ ] `comando` — portão local, no lugar do CI que este repositório não tem
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q`
      executado na raiz sai com código 0
- [ ] `comando` — RF-19
      `rtk proxy grep -REn --exclude-dir=__pycache__
      "955300|12802|23376|37482|36861|426618|273997|109963|\b(74|51|125|26|66|96)\b"
      app/commitments app/routers/commitments.py` não imprime nenhuma linha, em
      nenhum dos dois fluxos de saída
- [ ] `comando` — RF-20
      `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-011-f1.sqlite
      DASH_TODAY=2026-09-05 .venv/bin/python -m app.commitments.engine` executado
      **duas vezes seguidas** imprime a mesma contagem nas duas, e
      `select count(*) from commitments` devolve o mesmo número antes e depois
- [ ] `estrutural` — RF-21
      Nenhum documento aprovado de `product/items/003-comprometido/` afirma mais
      `−R$ 12.802,64`, `R$ 374,82`, `96 séries` ou `6 parcelamentos vivos` como
      número corrente, e cada trecho reescrito tem âncora de uma linha para o
      item `011`. `docs/plano.md` permanece byte a byte igual

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Em `app/commitments/live.py`, trocar `live_months` por um piso de data
      (`live_floor`), e passar `subscriptions`, `installments` e `totals` a
      comparar `last_seen_date` com esse piso. `totals` passa a somar só o que é
      vivo.
      Justificativa: RF-22, RF-23, RF-24 — o conjunto de dois meses marca como
      morto o que está no futuro, e são 10 séries; o piso resolve os dois lados
      com uma comparação só. Somar série morta no total é o mesmo erro que o
      `003` já corrigiu para parcelamento.
- [ ] 1.2 Em `app/commitments/series.py`, agrupar parcelamento por
      `(beneficiário, total de parcelas)` e separar dentro do grupo por
      tolerância relativa; `last_installment` passa a ser a maior parcela vista
      do grupo inteiro, e `amount_cents` o valor da última ocorrência.
      Justificativa: RF-05 a RF-09 — a chave por valor exato parte uma compra em
      duas por causa do arredondamento da primeira parcela, e a metade velha
      "deve" parcelas de uma compra já quitada.
- [ ] 1.3 Em `app/commitments/engine.py`, a precedência do parcelamento sobre a
      recorrência passa a olhar só a janela de vida, não `installments_left`.
      Justificativa: RF-01 a RF-04 — no mês em que a última parcela cai, a série
      deixa de ter parcela a vencer, a precedência solta, e a linha recorrente
      ressuscita R$ 368,61/mês de dívida encerrada.
- [ ] 1.4 Em `app/commitments/calendar.py`, casar lançamento com previsão por
      distância entre datas, com tolerância, cada previsão realizada no máximo
      uma vez.
      Justificativa: RF-10 a RF-15 — a chave por mês esconde vencimento, e a
      comparação exata mostra o mesmo dinheiro duas vezes. A distância precisa
      atravessar a virada do mês, ou a borda mede a coisa errada.
- [ ] 1.5 Escrever `tests/test_commitments_precedence.py` e
      `tests/test_commitments_series.py`, e acrescentar os dois casos novos a
      `tests/test_commitments_calendar.py`.
      Justificativa: RF-01 a RF-15 — nenhum destes erros quebra a tela; todos
      produzem um número plausível e errado.
- [ ] 1.6 Ajustar os testes existentes que afirmam os números antigos, e
      reconciliar `00-discovery.md`, `01-brief.md` e `03-plan.md` do `003`.
      Justificativa: RF-21 e a norma 8 — reconciliação de documento no mesmo PR
      da mudança, reescrita no presente, sem cicatriz.

## Validações de campo pendentes

Nenhuma.
