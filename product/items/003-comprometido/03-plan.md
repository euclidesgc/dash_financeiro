# Plano — O que já está comprometido

**Item:** `003-comprometido` · **Trilha:** rápida · **Brief:** `01-brief.md`
(aprovado em 2026-09-06)


> **Este plano não é reescrito.** Os números que os seus critérios cobram —
> `−R$ 12.802,64`, `R$ 374,82`, 96 séries, 6 parcelamentos vivos — eram os
> corretos quando cada fase foi medida, e os veredictos em `05-veredictos/`
> citam a saída daqueles comandos. Reescrevê-los tornaria os veredictos
> inverificáveis. O item `011` corrigiu quatro defeitos do motor e mudou esses
> números; o presente do produto está em `00-discovery.md` e `01-brief.md`.

## Objetivo

Ao fim das três fases o dono abre uma tela e vê quanto do mês seguinte já está
vendido antes de o mês começar: as assinaturas que se repetem, com valor médio,
meses seguidos, última cobrança e a ação "não uso mais" que se desfaz; os
parcelamentos que ainda têm parcela a vencer, com mês de término e quanto de
caixa cada um devolve ao acabar; e o calendário dos próximos 45 dias, com o que
sai em cada dia e a declaração de que a data é previsão do histórico.

A quebra é por **contrato**, não por camada. A fase 1 fixa a forma do dado — a
tabela `commitments`, a chave da série, a janela de vida, o dia previsto e o mês
de término — porque premissa errada aqui se espalha de uma vez para os três
blocos da tela e para a projeção do item `004`, que soma a mesma tabela. A fase 2
veste a tela sobre um motor já provado, e é onde a marca do dono vira mecanismo.
A fase 3 acrescenta o calendário, que é a leitura mais cara de errar: ele é o
único bloco em que o mesmo dinheiro pode aparecer duas vezes no mesmo dia.

Convenções que atravessam o plano e que os comandos dos critérios assumem:

- Identificadores de código em inglês; texto de interface, mensagem de erro e
  parâmetro de URL em pt-BR (norma 16, seguindo o `senha` do formulário de login
  e o `eixo` da tela de Gastos).
- O caminho do banco vem de `DASH_DB_PATH`; o arquivo de ambiente vem de
  `DASH_ENV_FILE`. **Nenhum comando deste plano lê o `.env` do dono**: todo
  comando que carrega configuração declara `DASH_ENV_FILE=/dev/null` e, quando
  precisa de credencial, declara a própria na linha.
- Banco de verificação sempre em `/tmp`, nunca em `data/`. O ambiente é `.venv/`
  na raiz.
- `python -m app.ingest` prepara a base inteira — migração, carga, taxonomia e
  compromissos; `python -m app.query "<select …>"` é o instrumento de evidência
  de banco, somente leitura; `python -m app.auth.seed` cria o usuário.
- `python -m app` sobe o servidor em `127.0.0.1:8000`, e a porta é fixa em
  `app/__main__.py`. Critério que precise de um segundo banco no ar ao mesmo
  tempo sobe o servidor por
  `uvicorn.run(create_app(), host='127.0.0.1', port=<outra>, proxy_headers=False)`
  e diz a porta.
- A sessão se obtém com **um único** `POST /login` com a senha correta, e o
  cookie se reusa em todas as chamadas: cinco senhas erradas do mesmo IP em
  quinze minutos fecham a porta.
- **A data de referência entra explícita em todo lugar.** A tela recebe `data`
  como parâmetro de consulta e as funções de leitura recebem `today`, ambos com
  a data corrente como padrão. Todo critério deste plano passa `2026-09-05`, que
  é a data em que a base foi medida: sem isso o teste passa hoje e falha em
  outubro.
- **A detecção não recebe data; a leitura recebe.** Nada do que `commitments`
  grava depende de "hoje" — meses observados, dia previsto, parcelas restantes e
  mês de término saem das linhas de `transactions`. Quem depende da data é a
  janela de vida e o calendário, e os dois são leitura. Limitar a detecção a
  `date <= hoje` mudaria a contagem de séries por causa das linhas com data
  futura que a base já traz (fatura de cartão parcelada adiante), e o número de
  RF-12 é medido com elas dentro.
- **Vivo é `installments_left > 0` E a última ocorrência no mês da data de
  referência ou no anterior.** O predicado de mês sozinho pega 12 séries, das
  quais 6 já terminaram de pagar; os critérios abaixo carregam os dois lados.
- `commitments` guarda **toda** série detectada — as recorrentes e as parceladas,
  vivas ou não. Vivo é condição de leitura: mês da última ocorrência igual ao mês
  da data de referência ou ao anterior.
- Valor em centavos inteiros, negativo = dinheiro saindo (invariante 22). Na
  tela, **o que sai aparece negativo com o sinal `−` colado** (`−R$ 12.427,82`) e
  **o que deixa de sair aparece positivo** — economia projetada e caixa liberado
  são dinheiro voltando, e escrevê-los com `−` inverteria o que a tela diz.
- O total comprometido do mês é a soma do valor médio das séries recorrentes não
  dispensadas mais a soma da parcela dos parcelamentos vivos.

## Fase 1 — Motor de compromissos (python)

**Objetivo da fase:** toda série de compromisso passa a ser derivada das linhas
de `transactions` e gravada em `commitments`, com janela de vida, dia previsto,
mês de término e caixa devolvido — sem nenhuma tela.

**Critérios de aceite:**

Salvo onde o critério prepara o próprio, os comandos desta fase correm contra o
banco preparado por `rm -f /tmp/dash-003-f1.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-003-f1.sqlite .venv/bin/python -m
app.ingest`, e levam o prefixo `rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-003-f1.sqlite`.

- [ ] `comando` — RF-01
      `.venv/bin/python -m app.query "select (select count(*) from sqlite_master
      where type='table' and name in ('commitments','commitment_dismissals')),
      (select count(*) from pragma_table_info('commitments') where name in
      ('kind','series_key','description','account','amount_cents','months_observed','months_consecutive','last_seen_date','due_day','last_installment','installment_total','installments_left','ends_month','dismissed'))"`
      imprime `2 14`
- [ ] `comando` — RF-01
      `rtk proxy grep -Ec "commitments" app/migrations/sql/001_schema.sql
      app/migrations/sql/002_session_epoch.sql app/migrations/sql/003_taxonomy.sql`
      imprime exatamente as três linhas
      `app/migrations/sql/001_schema.sql:0`,
      `app/migrations/sql/002_session_epoch.sql:0` e
      `app/migrations/sql/003_taxonomy.sql:0`
- [ ] `comando` — RF-02, RF-26, RF-37
      `rtk proxy grep -REin "recorrentes\.json|parcelamentos\.json|anthropic|mycon|totalpass|Serviços e assinaturas|Digital services|Dívidas e juros|1242782|12427|37482|109963|224569|246720|14106|12727"
      app "--include=*.py" "--include=*.sql" "--include=*.html"` não imprime
      nenhuma linha — o vocabulário e os nomes de assinatura vivem em JSON de
      dados, nunca em código
- [ ] `comportamental` — RF-03
      *Dado* o banco `/tmp/dash-003-f1.sqlite` carregado por `rm -f
      /tmp/dash-003-f1.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-f1.sqlite .venv/bin/python -m app.ingest`
      *Quando* `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-f1.sqlite .venv/bin/python -c "from datetime
      import date; from app.db import connect; from app.commitments.live import
      installments; c = connect(); print(len(installments(c, today=date(2026, 9,
      5))), len(installments(c, today=date(2027, 3, 1))))"` é executado
      *Então* a saída é a linha `6 0` — a mesma base lida em duas datas devolve
      conjuntos diferentes de parcelamento vivo, o que só acontece se a data for
      de fato o parâmetro que decide
- [ ] `comando` — RF-04
      `.venv/bin/python -m app.query "select (select count(*) from transactions
      where is_transfer = 1), (select count(*) from transactions where is_refund
      = 1), (select count(*) from commitments where amount_cents >= 0), (select
      count(*) from commitments c where not exists (select 1 from transactions t
      where t.payee = c.series_key and t.amount_cents < 0 and t.is_transfer = 0
      and t.is_refund = 0 and t.refunded_by is null))"` imprime `152 9 0 0`
- [ ] `comando` — RF-05
      `.venv/bin/python -m app.query "select (select count(distinct payee) from
      transactions where description glob 'OTICA BARDASSON E [0-9]*'), (select
      distinct payee from transactions where description glob 'OTICA BARDASSON E
      [0-9]*'), (select count(*) > 0 from commitments where series_key = 'otica
      bardasson e')"` imprime `1 otica bardasson e 1`
- [ ] `comportamental` — RF-06, RF-07
      *Dado* o banco `/tmp/dash-003-marca.sqlite` carregado por `rm -f
      /tmp/dash-003-marca.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-marca.sqlite .venv/bin/python -m app.ingest`,
      com a série marcada por `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-marca.sqlite .venv/bin/python -c "from app.db
      import connect; from app.commitments.mark import dismiss; c = connect();
      dismiss(c, 'anthropic claude subsan franciscousa'); c.commit()"`, e a
      leitura `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-marca.sqlite .venv/bin/python -m app.query
      "select kind, series_key, amount_cents, months_observed,
      months_consecutive, last_seen_date, due_day, last_installment,
      installment_total, installments_left, ends_month, dismissed from
      commitments order by kind, series_key, installment_total, amount_cents" >
      /tmp/dash-003-antes.txt`
      *Quando* `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-marca.sqlite .venv/bin/python -m
      app.commitments.engine` é executado mais duas vezes seguidas e a mesma
      consulta é gravada em `/tmp/dash-003-depois.txt`
      *Então* as duas execuções saem com código 0, `rtk proxy diff
      /tmp/dash-003-antes.txt /tmp/dash-003-depois.txt` não imprime nenhuma
      linha, `rtk proxy wc -l < /tmp/dash-003-depois.txt` imprime `151`, e `rtk
      proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-marca.sqlite .venv/bin/python -m app.query
      "select count(*) from commitments where dismissed = 1"` imprime `1`
- [ ] `comando` — RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_commitments_atomicity.py` sai com código 0, e o teste
      `tests/test_commitments_atomicity.py::test_a_failed_recompute_leaves_no_row_changed`
      monta um banco temporário com `commitments` já preenchida, substitui
      `app.commitments.series.installment_series` por uma função que levanta
      `RuntimeError`, chama `app.commitments.engine.recompute` esperando a
      exceção, e afirma que a contagem de linhas de `commitments` e a lista
      ordenada de `(kind, series_key, amount_cents, installments_left,
      ends_month, dismissed)` são idênticas às lidas antes da chamada
- [ ] `comando` — RF-09, RF-10
      `.venv/bin/python -m app.query "select (select count(*) from commitments
      where kind = 'recurring'), (select sum(amount_cents) from commitments where
      kind = 'recurring'), (select amount_cents from commitments where kind =
      'recurring' order by amount_cents limit 1), (select months_observed from
      commitments where kind = 'recurring' order by amount_cents limit 1),
      (select months_consecutive from commitments where kind = 'recurring' order
      by amount_cents limit 1), (select substr(last_seen_date, 1, 7) from
      commitments where kind = 'recurring' order by amount_cents limit 1),
      (select description from commitments where kind = 'recurring' order by
      amount_cents limit 1)"` imprime
      `55 -1242782 -246720 9 4 2026-08 DEBITO PRESTACAO HAB`
- [ ] `comando` — RF-11
      `.venv/bin/python -m app.query "select (select count(*) > 0 from
      commitments c where c.kind = 'recurring' and exists (select 1 from
      transactions t join category_groups g on g.id = t.group_id where t.payee =
      c.series_key and g.name = 'Serviços e assinaturas')), (select count(*) from
      commitments where dismissed = 1), (select sum(amount_cents) from
      commitments c where c.kind = 'recurring' and exists (select 1 from
      transactions t where t.payee = c.series_key and t.category in ('Digital
      services', 'Services', 'Telecommunications', 'Internet', 'Wellness and
      fitness', 'Online Courses')))"` imprime `1 0 -224569`
- [ ] `comando` — RF-12, RF-13, RF-16, RF-17
      `.venv/bin/python -m app.query "select (select count(*) from commitments
      where kind = 'installment'), (select count(*) from commitments where kind =
      'installment' and substr(last_seen_date, 1, 7) in ('2026-09', '2026-08') and
      installments_left > 0), (select sum(amount_cents) from commitments where
      kind = 'installment' and substr(last_seen_date, 1, 7) in ('2026-09',
      '2026-08') and installments_left > 0), (select count(*) from commitments
      where kind = 'installment' and series_key like 'ipva%' and
      substr(last_seen_date, 1, 7) in ('2026-09', '2026-08') and
      installments_left > 0), (select
      installments_left from commitments where kind = 'installment' and
      series_key like 'ipva%'), (select count(*) from commitments r where r.kind
      = 'recurring' and exists (select 1 from commitments i where i.kind =
      'installment' and i.series_key = r.series_key and substr(i.last_seen_date,
      1, 7) in ('2026-09', '2026-08') and i.installments_left > 0))"` imprime
      `96 6 -37482 0 2 0`, com todas as subconsultas de série viva exigindo
      também `installments_left > 0`
- [ ] `comando` — RF-14, RF-15
      `.venv/bin/python -m app.query "select (select installments_left from
      commitments where kind = 'installment' and amount_cents = -12727 and
      installment_total = 24), (select ends_month from commitments where kind =
      'installment' and amount_cents = -12727 and installment_total = 24),
      (select last_installment from commitments where kind = 'installment' and
      amount_cents = -12727 and installment_total = 24), (select ends_month from
      commitments where kind = 'installment' and amount_cents = -14106 and
      installment_total = 3), (select installments_left from commitments where
      kind = 'installment' and amount_cents = -14106 and installment_total = 3)"`
      imprime `22 2028-06 2 2026-10 2`
- [ ] `comando` — RF-18
      `.venv/bin/python -m app.query "select (select count(*) from commitments
      where due_day is null), (select count(*) from commitments c where not
      exists (select 1 from transactions t where t.payee = c.series_key and
      cast(strftime('%d', t.date) as integer) = c.due_day))"` imprime `0 0`
- [ ] `comando` — RF-19, RF-20
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_commitments_schedule.py` sai com código 0, e o arquivo traz o
      teste `test_an_even_number_of_days_takes_the_lower_middle`, que afirma
      `app.commitments.schedule.median_day([10, 12, 20, 22]) == 12`, e o teste
      `test_a_day_the_month_does_not_have_falls_on_its_last`, que afirma
      `app.commitments.schedule.on_month(31, date(2026, 11, 1)) == date(2026, 11,
      30)`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Criar `app/migrations/sql/004_commitments.sql` com
      `commitments(id INTEGER PRIMARY KEY, kind TEXT NOT NULL, series_key TEXT
      NOT NULL, description TEXT NOT NULL, account TEXT, amount_cents INTEGER NOT
      NULL, months_observed INTEGER, months_consecutive INTEGER, last_seen_date
      TEXT NOT NULL, due_day INTEGER, last_installment INTEGER, installment_total
      INTEGER NOT NULL DEFAULT 0, installments_left INTEGER, ends_month TEXT,
      dismissed INTEGER NOT NULL DEFAULT 0, UNIQUE (kind, series_key,
      installment_total, amount_cents))`,
      `commitment_dismissals(series_key TEXT PRIMARY KEY, dismissed_at TEXT NOT
      NULL)` e o índice `idx_commitments_series_key`.
      Justificativa: RF-01 e RF-07 — a marca do dono é coluna em `commitments`
      porque é ela que a tela lê junto com o valor, e é **também** tabela própria
      porque a recomputação apaga e reescreve as linhas: guardada só na linha,
      ela morreria na primeira recarga. `installment_total` nasce `NOT NULL
      DEFAULT 0` porque o SQLite trata `NULL` como distinto em `UNIQUE`, e uma
      série recorrente com o campo nulo se duplicaria a cada recomputação. A
      chave única carrega `amount_cents` porque a mesma descrição com o mesmo
      total de parcelas aparece em compras diferentes da base, com valor de
      parcela diferente, e sem ele duas compras viram uma.
- [ ] 1.2 Criar `app/commitments/series.py` com `recurring_series(conn) ->
      list[dict]` e `installment_series(conn) -> list[dict]`, ambas lendo
      `transactions` com o filtro `amount_cents < 0 AND is_transfer = 0 AND
      is_refund = 0 AND refunded_by IS NULL` importado de
      `app.queries.spending.SPENDING`, agrupando pela coluna `payee`. A série
      recorrente exige três ou mais meses distintos, três ou mais meses
      consecutivos e desvio relativo máximo de 0,35 em torno da média; a série
      parcelada agrupa por `(payee, installment_total, abs(amount_cents))`,
      lendo `installment_current` e `installment_total` e caindo no padrão `n/N`
      da descrição quando as colunas vierem vazias.
      Justificativa: RF-04, RF-05, RF-09 e RF-12 — `payee` já é a descrição
      normalizada com o marcador de parcela removido desde o item `002`, então a
      chave da série não se recalcula aqui; e o filtro de gasto vem da constante
      única de `app/queries/spending.py`, porque repetido em cada consulta ele é
      esquecido em uma e o comprometido passa a somar transferência. Os três
      cortes da recorrência são o que produz as 55 séries e os R$ 12.427,82 de
      RF-09: só o corte de três meses distintos deixaria entrar série de valor
      errático, cujo "valor médio" não prevê nada. O agrupamento do parcelamento
      carrega o total e o valor porque a mesma loja aparece na base com várias
      compras parceladas abertas ao mesmo tempo.
- [ ] 1.3 Criar `app/commitments/schedule.py` com `median_day(days: list[int]) ->
      int` (mediana com o **menor** dos dois centrais quando a contagem é par),
      `on_month(day: int, month: date) -> date` (grampeando no último dia do mês
      de destino) e `end_month(last_month: str, remaining: int) -> str`.
      Justificativa: RF-18, RF-19 e RF-20 — o menor dos dois centrais é o que
      mantém a promessa de que o dia previsto é um dia que a série teve; a média
      de dois dias centrais produziria um dia que nunca aconteceu. O grampo no
      último dia existe porque dia 31 não existe em novembro, e uma data
      inválida derrubaria o calendário inteiro em vez de errar um dia.
- [ ] 1.4 Criar `app/commitments/engine.py` com `recompute(conn) -> int` e CLI
      `python -m app.commitments.engine`. A recomputação apaga `commitments`,
      grava as séries recorrentes e as parceladas, e reaplica
      `commitment_dismissals` sobre a coluna `dismissed` — tudo na **mesma**
      transação SQL, com `rollback` em qualquer falha. Uma chave de série que
      produziu série parcelada **viva** não é gravada como recorrente.
      Justificativa: RF-06, RF-07, RF-08 e RF-17 — apagar e reescrever é o que
      torna a idempotência propriedade de construção em vez de promessa de
      `upsert`; e a marca reaplicada de tabela própria é o que sobrevive a isso.
      A precedência vale contra o parcelamento **vivo** porque é só ele que entra
      no total, e é lá que a dupla contagem custaria dinheiro: aplicada contra as
      100 séries detectadas, ela derrubaria séries recorrentes que a base mostra
      vivas há meses e o número de RF-09 cairia. Meia base recomputada é pior que
      nenhuma, porque o total continua somando e passa a mentir.
- [ ] 1.5 Criar `app/commitments/live.py` com `LIVE_MONTHS = 1`,
      `subscriptions(conn, *, today: date | None = None)`, `installments(conn, *,
      today: date | None = None)`, `released_cash(conn, *, today: date | None =
      None)` e `totals(conn, *, today: date | None = None)`, todas resolvendo
      `today` para `date.today()` quando ele não vem.
      Justificativa: RF-03, RF-13 e RF-15 — a data entra por parâmetro nomeado
      para que a mesma base produza o mesmo resultado em qualquer dia em que a
      verificação rode; sem isso o teste passa hoje e falha em outubro. A janela
      de vida mora aqui, e não na gravação, porque ela é a única coisa que muda
      quando o calendário vira o mês, e recomputar a base inteira para virar o
      mês seria caro e mudaria linhas que não mudaram.
- [ ] 1.6 Criar `app/commitments/mark.py` com `dismiss(conn, series_key) ->
      None`, `resume(conn, series_key) -> None` e `DismissRefusedError`, com a
      mensagem `Parcelamento contratado não para com um clique.`. A recusa vale
      para chave de série que não tem linha recorrente em `commitments`.
      Justificativa: RF-24, RF-25 e RF-27 — a marca é gravada pela chave da
      série, não pelo `id` da linha, porque a recomputação reescreve as linhas e
      um `id` guardado apontaria para outra coisa na semana seguinte. A recusa
      nasce no motor, e não na rota, porque ela é regra do produto: parcela
      contratada continua saindo mesmo com o clique dado.
- [ ] 1.7 Modificar `app/ingest/__main__.py` para chamar `recompute` depois da
      classificação bem-sucedida.
      Justificativa: RF-06 — a recomputação é idempotente, então rodar sempre não
      custa nada, e uma base carregada sem compromissos deixaria a tela vazia no
      intervalo entre dois comandos, que é exatamente o estado que ninguém
      entende ao abrir o painel.
- [ ] 1.8 Acrescentar em `tests/test_frozen_numbers.py` os valores em centavos
      deste item — `1242782`, `12427`, `37482`, `109963`, `224569`, `246720`,
      `14106` e `12727` — à varredura de `app/**`, mais uma segunda varredura,
      restrita aos arquivos deste item, que procura `55`, `100`, `32` e `6` como
      número isolado; e um caso que planta um desses números num arquivo
      temporário e afirma que o varredor o encontra.
      Justificativa: RF-37 e invariante 28 — a base envelhece no primeiro sync do
      item `006`, e um total dentro do código de produção faria a consulta do mês
      seguinte falhar por estar certa. As contagens pequenas só se varrem no
      escopo deste item porque `100` e `32` já existem legitimamente em
      `app/routers/render.py` e `app/config.py`, e um varredor que reprova o
      inocente é desligado na primeira semana. Sem o caso que reprova, um
      varredor quebrado passaria despercebido. Quem executa é o `pytest`, rodado
      pelo job `testes` de `.github/workflows/harness.yml`.
- [ ] 1.9 Criar `tests/test_commitments_series.py` (chave da série, exclusões,
      cortes da recorrência e agrupamento do parcelamento),
      `tests/test_commitments_schedule.py` (mediana par e dia inexistente),
      `tests/test_commitments_engine.py` (idempotência, sobrevivência da marca e
      precedência do parcelamento vivo) e
      `tests/test_commitments_atomicity.py` (a recomputação que falha no meio não
      deixa linha alterada), todos sobre bancos montados no próprio teste.
      Justificativa: RF-06, RF-08, RF-17 e RF-19 são os modos de falha caros de
      descobrir tarde, porque nenhum deles quebra a tela — todos produzem um
      total plausível e errado. Quem executa é o `pytest`, rodado pelo job
      `testes` de `.github/workflows/harness.yml`.

## Fase 2 — Tela de Comprometido (tela)

**Objetivo da fase:** existe `/comprometido`, com as assinaturas, os
parcelamentos vivos, o cronograma de caixa liberado, o total comprometido e a
marca "não uso mais" que se desfaz.

**Critérios de aceite:**

O banco desta fase é preparado por `rm -f /tmp/dash-003-f2.sqlite && rtk proxy
env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-003-f2.sqlite
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-003-f2.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-003-f2.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4 .venv/bin/python -m
app`. O cookie `dash_session` vem de um único `POST /login` com
`login=teste&senha=senha-teste-9k2`. Cada critério que **escreve** no banco
prepara o próprio arquivo pelos mesmos dois comandos e sobe o servidor contra
ele, para que a ordem de execução não mude o resultado de nenhum outro.

- [ ] `comportamental` — RF-30
      *Dado* o servidor rodando em `http://127.0.0.1:8000` contra
      `/tmp/dash-003-f2.sqlite` e um cookie `dash_session` obtido por um único
      `POST /login`
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/comprometido?data=2026-09-05"` é executado
      *Então* a resposta é `200` e o HTML traz os atributos `id="assinaturas"`,
      `id="parcelamentos"` e `id="caixa-liberado"`, a string `−R$ 12.802,64` como
      total comprometido e a string `R$ 0,00` como economia projetada
- [ ] `comportamental` — RF-31, RF-35
      *Dado* `http://127.0.0.1:8000/comprometido?data=2026-09-05` aberta no
      Chromium com sessão válida
      *Quando* `document.querySelectorAll("#assinaturas tbody tr")` é percorrido
      *Então* há 55 linhas; a primeira traz as strings `−R$ 2.467,20`, `4` e
      `/08/2026`; a sequência de `Math.abs(Number(tr.dataset.media))` é não
      crescente; `document.querySelectorAll("#assinaturas
      form[action='/comprometido/dispensar'] button").length` vale `55`; e o
      número de linhas cujo texto contém `Sem cobrança recente` é igual ao número
      impresso por `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-f2.sqlite .venv/bin/python -m app.query "select
      count(*) from commitments where kind = 'recurring' and
      substr(last_seen_date, 1, 7) not in ('2026-09', '2026-08')"`
- [ ] `comportamental` — RF-32, RF-33
      *Dado* `http://127.0.0.1:8000/comprometido?data=2026-09-05` aberta no
      Chromium com sessão válida
      *Quando* `document.querySelectorAll("#parcelamentos tbody tr")` é
      percorrido
      *Então* há 6 linhas; a sequência de
      `Math.abs(Number(tr.dataset.restante))` é não crescente; a linha que traz
      `−R$ 127,27` traz também `22` e `06/2028`; a linha que traz `−R$ 141,06`
      traz também `10/2026`; e o bloco `#caixa-liberado` traz `10/2026` ao lado
      de `R$ 141,06` e o total `R$ 374,82`
- [ ] `comportamental` — RF-24, RF-25
      *Dado* o servidor rodando contra `/tmp/dash-003-marca2.sqlite`, preparado
      pelos dois comandos de carga, e um cookie `dash_session` válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/comprometido/dispensar --data-urlencode "serie=<a
      chave>" --data-urlencode "data=2026-09-05"` é executado três vezes, com
      `anthropic claude subsan franciscousa`, `pagamento de boleto mycon` e
      `totalpasssao paulobra` no lugar de `<a chave>`, e em seguida `rtk proxy
      curl -s -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/comprometido/retomar --data-urlencode
      "serie=totalpasssao paulobra" --data-urlencode "data=2026-09-05"` é
      executado, sem reiniciar o processo do servidor
      *Então* a resposta da terceira dispensa traz `R$ 1.099,63` como economia
      projetada e `−R$ 11.703,01` como total comprometido, e a resposta da
      retomada traz `R$ 990,63` e `−R$ 11.812,01`
- [ ] `comportamental` — RF-27
      *Dado* o servidor rodando contra `/tmp/dash-003-recusa.sqlite`, preparado
      pelos dois comandos de carga, e um cookie `dash_session` válido
      *Quando* `rtk proxy curl -i -s -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/comprometido/dispensar --data-urlencode "serie=assai
      macae" --data-urlencode "data=2026-09-05"` é executado
      *Então* a resposta é `400`, o HTML traz a mensagem `Parcelamento contratado
      não para com um clique.` e a string `−R$ 12.802,64` como total
      comprometido, e `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-recusa.sqlite .venv/bin/python -m app.query
      "select count(*) from commitment_dismissals"` imprime `0`
- [ ] `comportamental` — RF-28, RF-29
      *Dado* o servidor rodando contra `/tmp/dash-003-bloco.sqlite`, preparado
      pelos dois comandos de carga e por `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-bloco.sqlite .venv/bin/python -c "from app.db
      import connect; from app.commitments.mark import dismiss; c = connect();
      [dismiss(c, k) for k in ('anthropic claude subsan franciscousa', 'pagamento
      de boleto mycon', 'totalpasssao paulobra')]; c.commit()"`, e um cookie
      `dash_session` válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/comprometido?data=2026-09-05"` é executado
      *Então* o HTML traz um bloco com `id="dispensadas"` contendo três linhas de
      dados, a string `R$ 1.099,63` e a frase `"Não uso mais" registra a decisão
      neste painel e não cancela nada no fornecedor.`
- [ ] `comportamental` — RF-36
      *Dado* o banco `/tmp/dash-003-vazio.sqlite` preparado por `rm -f
      /tmp/dash-003-vazio.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-vazio.sqlite .venv/bin/python -m app.migrate &&
      rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-vazio.sqlite LOGIN=teste
      PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`, e o servidor
      subido por `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-vazio.sqlite LOGIN=teste
      PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
      .venv/bin/python -c "import uvicorn; from app.main import create_app;
      uvicorn.run(create_app(), host='127.0.0.1', port=8021,
      proxy_headers=False)"`
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8021/comprometido?data=2026-09-05"` é executado com um
      cookie obtido por um único `POST http://127.0.0.1:8021/login`
      *Então* a resposta é `200`, o HTML não traz nenhuma linha `<tr>` de dados
      dentro de `#assinaturas` nem dentro de `#parcelamentos`, e traz a string
      `Nenhum compromisso detectado` seguida de um `<a>` com `href="/gastos"`
- [ ] `comando` — RF-37
      `rtk proxy grep -REn "1242782|12427|37482|109963|224569|246720|14106|12727|1280264|11703|\b(55|100|32|6)\b"
      app/commitments app/routers/commitments.py app/templates/comprometido.html
      app/templates/fragments/comprometido_assinaturas.html
      app/templates/fragments/comprometido_parcelamentos.html
      app/templates/fragments/comprometido_dispensadas.html` não imprime nenhuma
      linha, em nenhum dos dois fluxos de saída
- [ ] `comando` — RF-38
      `rtk proxy grep -REn "#[0-9a-fA-F]{3,8}|rgb\(|hsl\(" app/templates
      app/static/css "--include=*.html" "--include=*.css" --exclude=tokens.css`
      não imprime nenhuma linha
- [ ] `comportamental` — RF-38
      *Dado* `http://127.0.0.1:8000/comprometido?data=2026-09-05` aberta no
      Chromium com sessão válida
      *Quando* `document.querySelectorAll(".cifra")` é percorrido
      *Então* o conjunto tem mais de 50 elementos, para cada um
      `getComputedStyle(el).fontVariantNumeric` contém `tabular-nums`, e o texto
      de cada elemento casa com a expressão `^−?R\$ [\d.]+,\d{2}$`, com o sinal
      `−` (U+2212) colado ao `R$` em todo valor negativo
- [ ] `comportamental` — RF-39
      *Dado* `http://127.0.0.1:8000/comprometido?data=2026-09-05` aberta no
      Chromium com sessão válida
      *Quando* a janela é ajustada para as larguras de viewport 375, 768 e 1440
      px, com altura de 800 px, uma vez carregando a página já naquela largura e
      uma vez redimensionando a janela com a página aberta
      *Então* nas seis medições
      `document.documentElement.scrollWidth <= window.innerWidth` avalia como
      `true`
- [ ] `estrutural` — RF-39
      Existem os arquivos
      `product/items/003-comprometido/06-capturas/comprometido-375.png`,
      `comprometido-768.png`, `comprometido-1440.png`,
      `comprometido-dispensadas-1440.png`, `comprometido-vazio-375.png` e
      `comprometido-dark-1440.png`, todos no mesmo diretório e cada um com mais
      de 1024 bytes
- [ ] `comportamental` — RF-40, RF-41
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado, sessão
      válida e `http://127.0.0.1:8000/comprometido?data=2026-09-05` carregada
      *Quando* a tecla `Tab` move o foco, em sequência, para o primeiro botão
      "não uso mais" da lista de assinaturas e para o controle seguinte da mesma
      lista
      *Então* nos dois `getComputedStyle(el).outlineStyle` é diferente de `none`
      e `parseFloat(getComputedStyle(el).outlineWidth)` é maior ou igual a 2, e
      para todo elemento devolvido por `document.querySelectorAll("*")`
      `getComputedStyle(el).animationDuration` e
      `getComputedStyle(el).transitionDuration` valem `0s`, com a lista de
      assinaturas ainda em 55 linhas de dados

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 2.1 Carregar a skill `frontend-design` antes de escrever qualquer marcação
      ou folha de estilo, e reler `product/00-linguagem-visual.md`.
      Justificativa: invariante 27 — a linguagem visual é canônica e já existe
      desde o item `001`; escolher cor, escala ou raio nesta fase seria abrir uma
      segunda opinião ao lado do documento.
- [ ] 2.2 Criar `app/routers/commitments.py` com `GET /comprometido` (página
      inteira), `POST /comprometido/dispensar` e `POST /comprometido/retomar`
      (ambos devolvendo a tela reconstruída, com `400` quando a marca é
      recusada), todos lendo o parâmetro `data` e caindo em `date.today()`
      quando ele vem ausente ou ilegível.
      Justificativa: RF-24, RF-27 e RF-30 — a resposta do próprio `POST` já traz
      o total e a economia recalculados, porque exigir recarga faria o dono
      perder de vista o número que ele acabou de mudar; e a data ilegível cai no
      padrão em vez de derrubar a tela, seguindo o que `app/routers/spending.py`
      já faz com o período.
- [ ] 2.3 Registrar o router em `app/main.py` e acrescentar em
      `app/templates/home.html` um `<a href="/comprometido">`.
      Justificativa: sem o link a tela só se alcança digitando a URL; e a
      varredura de `tests/test_route_guard.py`, escrita no item `001`, passa a
      cobrir as três rotas novas sozinha — nenhuma delas pode nascer aberta
      (invariante 24).
- [ ] 2.4 Criar `app/templates/comprometido.html` e os fragmentos
      `app/templates/fragments/comprometido_assinaturas.html`,
      `comprometido_parcelamentos.html` e `comprometido_dispensadas.html`, com a
      ação "não uso mais" dentro de um `<form method="post"
      action="/comprometido/dispensar">` que funciona sem JavaScript, e com
      `data-media` (valor médio em centavos) em cada linha de assinatura e
      `data-restante` (centavos ainda comprometidos) em cada linha de
      parcelamento.
      Justificativa: RF-31, RF-32 e a régua de `product/00-linguagem-visual.md` —
      a tela precisa ser legível sem rede, e o `POST` nativo é o piso; a troca de
      fragmento por HTMX é o acréscimo por cima dele. Os atributos de dado
      existem porque ordenação exibida só é verificável se o número que ordena
      estiver legível ao lado do texto formatado.
- [ ] 2.5 Acrescentar em `app/static/css/app.css` as classes da tabela de
      compromissos, do bloco de dispensadas e do cronograma de caixa liberado,
      com o embrulho da tabela rolando em `overflow-x: auto` em vez do corpo da
      página.
      Justificativa: RF-39 — em 375 px uma tabela de cinco colunas empurra o
      corpo inteiro; o que rola tem de ser a tabela. Nenhum valor de cor ou de
      espaço nasce fora de `app/static/css/tokens.css` (RF-38).
- [ ] 2.6 Criar `tests/test_comprometido_screen.py` com `fastapi.testclient`: a
      resposta 200 com sessão, a ordenação das duas listas, a dispensa e a
      retomada mudando o total na mesma resposta, a recusa na linha de
      parcelamento e o estado vazio.
      Justificativa: os critérios de navegador provam a tela uma vez, na sessão
      em que ela foi feita; o teste é o que impede a fase seguinte de quebrá-la
      em silêncio. Quem executa é o `pytest`, rodado pelo job `testes` de
      `.github/workflows/harness.yml`.
- [ ] 2.7 Gerar as capturas em
      `product/items/003-comprometido/06-capturas/`: `comprometido-375.png`,
      `comprometido-768.png`, `comprometido-1440.png`,
      `comprometido-dispensadas-1440.png`, `comprometido-vazio-375.png` e
      `comprometido-dark-1440.png`.
      Justificativa: RF-39 — a captura é a evidência que sobrevive à sessão, e o
      estado vazio é o que mais some de revisão visual por não estar no caminho
      feliz.

## Fase 3 — Calendário de vencimentos (tela)

**Objetivo da fase:** a tela de Comprometido ganha o calendário dos próximos 45
dias, com o que sai em cada dia, a soma do dia e a declaração de que a data é
previsão do histórico.

**Critérios de aceite:**

O banco desta fase é preparado por `rm -f /tmp/dash-003-f3.sqlite && rtk proxy
env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-003-f3.sqlite
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-003-f3.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-003-f3.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4 .venv/bin/python -m
app`. O cookie `dash_session` vem de um único `POST /login` com
`login=teste&senha=senha-teste-9k2`.

- [ ] `comportamental` — RF-21
      *Dado* `http://127.0.0.1:8000/comprometido?data=2026-09-05` aberta no
      Chromium com sessão válida
      *Quando* `document.querySelectorAll("#calendario [data-dia]")` é percorrido
      *Então* o bloco `#calendario` traz as strings `05/09/2026` e `20/10/2026`;
      há ao menos um elemento com `data-dia`; todo `data-dia` está entre
      `2026-09-05` e `2026-10-20`, em ordem crescente e sem repetição; e em cada
      elemento `Number(el.dataset.total)` é igual à soma dos
      `Number(item.dataset.centavos)` dos seus descendentes com `[data-serie]`
- [ ] `comportamental` — RF-22
      *Dado* `http://127.0.0.1:8000/comprometido?data=2026-09-05` aberta no
      Chromium com sessão válida, e as séries sem cobrança recente lidas por `rtk
      proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-003-f3.sqlite
      .venv/bin/python -m app.query "select series_key from commitments where
      kind = 'recurring' and substr(last_seen_date, 1, 7) not in ('2026-09',
      '2026-08')"`
      *Quando* o texto de `#calendario` e os `data-serie` dos seus descendentes
      são lidos
      *Então* o texto traz o número de linhas impressas por aquele comando
      seguido das palavras `sem cobrança recente`, e nenhum `data-serie` do bloco
      é igual a qualquer uma das chaves que o comando imprimiu
- [ ] `comando` — RF-23
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_commitments_calendar.py` sai com código 0, e o teste
      `tests/test_commitments_calendar.py::test_an_entry_already_recorded_replaces_the_prediction`
      monta um banco temporário com uma série de `-10000` centavos em
      `2026-06-10`, `2026-07-10` e `2026-08-10` e uma quarta ocorrência de
      `-9000` em `2026-09-10`, chama
      `app.commitments.calendar.calendar(conn, today=date(2026, 9, 5))` e afirma
      que o dia `2026-09-10` tem exatamente uma entrada, com `amount_cents` igual
      a `-9000` e `predicted` igual a `False`
- [ ] `comportamental` — RF-34
      *Dado* o servidor rodando em `http://127.0.0.1:8000` contra
      `/tmp/dash-003-f3.sqlite` e um cookie `dash_session` válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/comprometido?data=2026-09-05"` é executado
      *Então* o HTML traz, dentro do bloco `id="calendario"`, a frase `A data de
      cada vencimento é previsão a partir do histórico, não data contratual.`
- [ ] `comportamental` — RF-30
      *Dado* o servidor rodando em `http://127.0.0.1:8000` contra
      `/tmp/dash-003-f3.sqlite` e um cookie `dash_session` válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/comprometido?data=2026-09-05"` é executado
      *Então* a resposta é `200` e o HTML traz os atributos `id="assinaturas"`,
      `id="parcelamentos"` e `id="calendario"`, a string `−R$ 12.802,64` como
      total comprometido e a string `R$ 0,00` como economia projetada
- [ ] `estrutural` — RF-39
      Existem os arquivos
      `product/items/003-comprometido/06-capturas/comprometido-calendario-375.png`,
      `comprometido-calendario-1440.png` e
      `comprometido-calendario-dark-1440.png`, todos no mesmo diretório e cada um
      com mais de 1024 bytes

**Critérios de integração:**

- [ ] `comando` — portão local, no lugar do CI que este repositório não tem
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q`
      executado na raiz sai com código 0
- [ ] `comando` — RF-37
      `rtk proxy grep -REn "1242782|12427|37482|109963|224569|246720|14106|12727|1280264|11703|\b(55|100|32|6)\b"
      app/commitments app/routers/commitments.py app/templates/comprometido.html
      app/templates/fragments/comprometido_assinaturas.html
      app/templates/fragments/comprometido_parcelamentos.html
      app/templates/fragments/comprometido_dispensadas.html
      app/templates/fragments/comprometido_calendario.html` não imprime nenhuma
      linha, em nenhum dos dois fluxos de saída
- [ ] `comportamental` — RF-21, RF-24
      *Dado* o banco `/tmp/dash-003-e2e.sqlite` preparado por `rm -f
      /tmp/dash-003-e2e.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-e2e.sqlite .venv/bin/python -m app.ingest && rtk
      proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-003-e2e.sqlite
      LOGIN=teste PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`, o
      servidor subido por `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-003-e2e.sqlite LOGIN=teste PASSORD=senha-teste-9k2
      SESSION_SECRET=segredo-de-teste-7h4 .venv/bin/python -m app`, e o cookie
      `dash_session` obtido de um único `rtk proxy curl -i -s -X POST
      http://127.0.0.1:8000/login -d "login=teste&senha=senha-teste-9k2"`
      *Quando* `http://127.0.0.1:8000/comprometido?data=2026-09-05` é buscada, as
      três dispensas são enviadas, uma por vez, por `rtk proxy curl -s -o
      /dev/null -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/comprometido/dispensar --data-urlencode
      "serie=<chave>" --data-urlencode "data=2026-09-05"`, com `<chave>` valendo
      `anthropic claude subsan franciscousa`, depois `pagamento de boleto mycon`
      e depois `totalpasssao paulobra`, e a tela é buscada de novo com a mesma
      data
      *Então* a primeira leitura traz `−R$ 12.802,64` e `R$ 0,00`, a segunda traz
      `−R$ 11.703,01` e `R$ 1.099,63`, e nas duas o bloco `#calendario` traz as
      strings `05/09/2026` e `20/10/2026`, sem que a ingestão tenha rodado de
      novo e sem que nenhum processo tenha sido reiniciado
- [ ] `comportamental` — RF-39, RF-41
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado, sessão
      válida e `http://127.0.0.1:8000/comprometido?data=2026-09-05` carregada
      *Quando* a janela é ajustada para as larguras de viewport 375, 768 e 1440
      px, com altura de 800 px, uma vez carregando a página já naquela largura e
      uma vez redimensionando a janela com a página aberta
      *Então* nas seis medições
      `document.documentElement.scrollWidth <= window.innerWidth` avalia como
      `true`, e para todo elemento devolvido por
      `document.querySelectorAll("#calendario *")`
      `getComputedStyle(el).animationDuration` e
      `getComputedStyle(el).transitionDuration` valem `0s`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 3.1 Criar `app/commitments/calendar.py` com `WINDOW_DAYS = 45` e
      `calendar(conn, *, today: date | None = None) -> list[Day]`, devolvendo um
      dia por data com vencimento entre a data de referência e ela mais 45 dias,
      cada dia com `total_cents` e as entradas (`series_key`, `description`,
      `amount_cents`, `predicted`). Uma ocorrência já lançada em `transactions`
      dentro da janela substitui a previsão da mesma série no mesmo dia.
      Justificativa: RF-21 e RF-23 — a base já traz lançamento com data futura,
      porque fatura de cartão chega parcelada adiante; somar a previsão por cima
      dele faria o mesmo dinheiro aparecer duas vezes no mesmo dia, que é o erro
      que destrói a confiança no calendário inteiro. A janela é a mesma de 45
      dias que a projeção do item `004` vai consumir, e ela sai daqui em vez de
      ser recortada na tela.
- [ ] 3.2 Criar `app/templates/fragments/comprometido_calendario.html`, incluído
      por `app/templates/comprometido.html`, com `data-dia` e `data-total` em
      cada dia, `data-serie` e `data-centavos` em cada entrada, a frase que
      declara a previsão e a contagem das séries recorrentes que ficaram de fora
      por falta de cobrança recente.
      Justificativa: RF-22, RF-34 e D2 — a mediana erra o dia, e um número que
      parece exato e não é destrói a confiança no resto da tela; dizer quantas
      séries ficaram de fora é o que impede o dono de ler um calendário curto
      como um mês tranquilo. Os atributos de dado existem porque soma exibida só
      é verificável se as parcelas dela estiverem legíveis ao lado.
- [ ] 3.3 Acrescentar em `app/static/css/app.css` as classes do calendário, com
      a lista de dias empilhando em uma coluna abaixo de 768 px.
      Justificativa: RF-39 — grade de calendário em 375 px é a forma mais rápida
      de produzir rolagem horizontal do corpo; e nenhum valor de cor ou de espaço
      nasce fora de `app/static/css/tokens.css` (RF-38).
- [ ] 3.4 Criar `tests/test_commitments_calendar.py`: a janela de 45 dias, a soma
      por dia, o lançamento já datado no lugar da previsão, a exclusão de série
      sem cobrança recente e o dia previsto grampeado no fim do mês.
      Justificativa: RF-21, RF-22 e RF-23 — nenhum desses erros quebra a tela;
      todos produzem um calendário plausível e errado, que é o jeito mais caro de
      errar num painel que existe para ser acreditado. Quem executa é o `pytest`,
      rodado pelo job `testes` de `.github/workflows/harness.yml`.
- [ ] 3.5 Gerar as capturas em
      `product/items/003-comprometido/06-capturas/`:
      `comprometido-calendario-375.png`, `comprometido-calendario-1440.png` e
      `comprometido-calendario-dark-1440.png`.
      Justificativa: RF-39 — a captura é a evidência que sobrevive à sessão, e o
      calendário é o bloco cuja densidade só se julga vendo.

## Execução sugerida

As três fases correm **em sequência**, sem paralelismo. A verificação foi feita
por interseção dos conjuntos de arquivos de cada fase, e ela é grande demais em
todos os pares:

1. **Fase 1** — bloqueante. Fixa o contrato que as outras duas consomem: a
   tabela `commitments`, a chave da série, a janela de vida, o dia previsto e o
   mês de término. Uma premissa errada aqui se espalha de uma vez para os três
   blocos da tela e para a projeção do item `004`.
2. **Fase 2** depois da fase 1 — a tela renderiza o que `app/commitments/live.py`
   e `app/commitments/mark.py` devolvem, e nenhuma das duas existe antes da
   migração `004`. Em paralelo, a tela não teria o que exibir, e um contrato de
   retorno inventado no template seria refeito ao encontrar o real.
3. **Fase 3** depois da fase 2 — o calendário é um bloco dentro de
   `app/templates/comprometido.html`, escreve em `app/static/css/app.css` e é
   verificado na mesma resposta que a fase 2 produz. Em worktrees paralelos isso
   seria conflito de merge em dois arquivos e dois critérios impossíveis de
   medir.

## Validações de campo pendentes

Nenhuma.
