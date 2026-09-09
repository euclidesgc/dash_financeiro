# Plano — 025-financiamentos-na-tela

**Item:** `025-financiamentos-na-tela` · **Trilha:** rápida ·
**Fonte aprovada:** `01-brief.md` · **Terreno:** `00-discovery.md` ·
Duas fases, em sequência.

> **A origem de cada número deste plano está declarada**, e nenhum é remedido
> aqui. Os do veículo em 05/09/2026 — saldo `-3917636`, taxa `163`, prazo `45`,
> parcela `-123533` — são os que `tests/test_debts.py:15-18` já afirma sobre a
> carga de hoje. Os do imóvel vêm do arquivo e do número congelado do projeto:
> `saldo_devedor: 238585.18` → `-23858518`, `prazo_restante_meses: 370`, e
> `0,72% ao mês` → `72` pontos-base, que é o que `docs/plano.md:44` e `:371`
> registram medido em 05/09/2026. A suíte tem 526 testes e leva ~41s. Todo
> comando roda com `DASH_ENV_FILE=/dev/null`, e a data de referência do processo
> se fixa com `DASH_TODAY=2026-09-05`.

## Objetivo

Ao fim das duas fases o financiamento do imóvel e o do veículo moram numa tabela
do banco, se editam em `/configuracao` e não dependem de nenhum arquivo em
`data/manual/`. A escada de dívidas continua com os mesmos degraus, com os mesmos
saldos, as mesmas taxas e os mesmos prazos que tinha lendo os dois JSON — é o que
o item existe para não quebrar. Numa máquina que nunca recebeu os contratos o
painel sobe igual, sem financiamento nenhum, e o dono informa na tela.

A quebra é por **contrato, não por tela**: a fase 1 fixa a forma do dado — a
tabela, a importação e a conta que consome os dois — e é ela que carrega o
critério numérico que decide o item. A fase 2 só olha para a tela, e chega depois
de o número já estar provado. Invertida a ordem, um erro de importação apareceria
primeiro como campo errado no formulário, e a correção seria feita no lugar
errado.

## O terreno, lido no código

| Sítio | Hoje | O que muda |
|---|---|---|
| `app/debts/ladder.py:93-101` `_from_contracts(today)` | lê os dois arquivos por `_read` | passa a ler a tabela `financings`, e recebe a conexão |
| `app/debts/ladder.py:104-111` `_read` | abre `data/manual/<arquivo>`; ausente é degrau ausente | sai de `ladder.py` e vira a semente de `app/financings/` |
| `app/debts/ladder.py:114-128` `_mortgage` | saldo informado; taxa anual → mensal na leitura | consome a linha da tabela; a conversão anual→mensal acontece **uma vez**, na importação |
| `app/debts/ladder.py:131-145` `_vehicle` | saldo = valor presente das parcelas não vencidas | a mesma conta, agora em `app/financings/`, alimentada pela tabela |
| `app/debts/ladder.py:148-157` `_paid` | conta parcelas vencidas até `today` | ganha o ajuste do dia do mês (ver decisões) |
| `app/debts/ladder.py:42-57` `rebuild` | preserva a taxa digitada por `(kind, name)` sobre qualquer valor recalculado | passa a preservar **só** onde o valor recalculado é nulo |
| `tests/test_migrations.py:32-44` e `:71` | `EXPECTED_MIGRATIONS` e `EXPECTED_TABLES` listados à mão, e `max(version)` afirmado como `"011"` | ganham a migração e a tabela novas |
| `app/routers/settings.py:171-187` `_context` | monta o contexto de `/configuracao` | ganha uma chave |
| `app/templates/configuracao.html:86` | abre `<section id="beneficiarios">` | ganha, imediatamente antes, uma linha de `{% include %}` |

Quatro fatos do código decidem o desenho e não se re-discutem:

1. **A escada apaga e reescreve `debts` a cada reconstrução**
   (`app/debts/ladder.py:46`). Por isso os financiamentos não podem morar em
   `debts` — é a decisão que o discovery já tomou.
2. **O formulário de taxa de `/dividas` só aparece na seção "Sem taxa
   informada"** (`app/templates/dividas.html:54-98`), que lista apenas degraus
   com `monthly_rate_bp IS NULL`. Um financiamento sempre tem taxa, então nunca
   aparece ali: `/configuracao` não vira segunda casa de um campo que já se edita
   em outro lugar.
3. **Nada lê `debts.source` para decidir coisa alguma** — nenhum template e
   nenhum módulo de `app/`; a coluna só é escrita.
4. **Existe um guarda de esquema que reprova por construção quando uma migração
   nova entra:** `tests/test_migrations.py` compara a lista de arquivos aplicados
   e a lista de tabelas criadas com literais escritos à mão, e afirma que a maior
   versão é `"011"`. Migração nova sem esse arquivo atualizado é suíte vermelha,
   e o arquivo é o mesmo que os outros itens simultâneos vão tocar.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| Onde mora a entidade? | O discovery já decidiu "tabela própria" | tabela `financings`, criada por `app/migrations/sql/014_financings.sql` |
| Qual a chave? | O não-escopo do brief diz que não há cadastro genérico de contrato: existem dois tipos e só | `kind TEXT NOT NULL PRIMARY KEY`, com `mortgage` e `vehicle`. A chave é o que faz a importação ser idempotente sem contador |
| O nome do degrau é coluna? | RF-01 lista os campos e não inclui nome; os dois nomes são fixos e já são literais em `app/debts/ladder.py:119` e `:135` | não é coluna: `NAMES` em `app/financings/__init__.py`, um por tipo |
| Sinal dos valores em centavos | Invariante 22, e `debts.balance_cents` já é negativo | `financings.balance_cents` e `payment_cents` são **negativos**. A negação acontece uma vez, na entrada — na importação e na escrita da tela |
| O que vira `debts.source`? | Depois do item a linha vem da tabela; manter o nome do arquivo faria a coluna citar uma origem que ninguém lê mais | `source = "financings"` nos dois degraus. A comparação de RF-02 cobre `kind`, `name`, `balance_cents`, `monthly_rate_bp`, `term_months` e `payment_cents`; `source` muda por decisão |
| O que `term_months` significa? | Os dois contratos dizem prazos diferentes: o app da CAIXA mostra **restante** (370), a cédula do Safra mostra **contratado** (60), e a escada de hoje já consome os dois assim | a coluna guarda o prazo como o contrato daquele tipo o declara; o rótulo na tela difere por tipo, e o prazo restante do veículo continua derivado da data do primeiro vencimento |
| Onde mora a importação, se migração é SQL puro? | `app/migrations/runner.py` executa `.sql` instrução a instrução e não lê JSON, e ele está fora do escopo deste item | a semente é Python, em `app/financings/store.py`, chamada pela reconstrução da escada e **guardada pela tabela vazia**: importada uma vez, o disco não é mais consultado |
| Quem ganha quando existem arquivo e linha? | RF-03 pede uma origem só | a **tabela**. Com a tabela não vazia os arquivos nem são abertos |
| A preservação da taxa digitada continua valendo para os financiamentos? | O comentário de `app/debts/ladder.py:55-56` diz por que ela existe: é a única coisa da tela que **nenhuma fonte produz de novo**. Um financiamento passa a ter fonte | a preservação passa a valer só onde o valor recalculado é nulo — os degraus de conta e cartão. Sem isso, a taxa editada na tela nunca chegaria à escada, e RF-06 nasceria quebrado |
| Onde mora a fórmula do valor presente? | Norma 23: cálculo é função determinística e testada, com uma casa só; a tela precisa mostrar o saldo calculado e a escada precisa gravá-lo | `app/financings/math.py`. `app/debts/ladder.py` importa; `app/financings/` **não** importa nada de `app/debts/`, e é isso que evita o ciclo |
| E `RATE_SCALE`, que `app/debts/simulate.py:3` importa de `ladder`? | Duas definições do mesmo 10000 é como elas divergem | a constante passa a ser definida em `app/financings/money.py`; `app/debts/ladder.py` a importa e continua usando em `monthly_interest_cents`, então o import de `simulate.py` segue resolvendo e nenhum arquivo fora do escopo é tocado |
| O dia do vencimento acima de 28 | `app/debts/ladder.py:153` monta `date(year, month, first.day)`: com dia 31 isso levanta `ValueError` em fevereiro. Hoje o arquivo traz dia 11 e o defeito nunca disparou; com a data digitada na tela ele vira um 500, e RF-08 diz nunca 500 | `_paid` passa a limitar o dia ao último do mês. Com dia até 28 nada muda |
| Taxa zero | `parse_rate("0")` devolve `0`, e o valor presente divide por ela | a escrita de financiamento recusa taxa nula ou zero, com frase em pt-BR. Um financiamento sem taxa não teria degrau na escada, que ordena por taxa |
| Contrato com todas as parcelas vencidas | `prazo - pagas` fica ≤ 0, e a fórmula devolve saldo **positivo** — um degrau de dívida com sinal invertido, contra o invariante 22 | prazo restante ≤ 0 é **nenhum degrau**: contrato quitado não é dívida |
| Como se lê a data do primeiro vencimento? | A gramática do item `015` (`app/settings/typed.py`) não tem leitor de data, e o arquivo está fora do escopo deste item | `app/financings/typed.py::parse_due_date`, em ISO, levantando o `InvalidValueError` de `app.settings.typed` — um tipo de recusa só no caminho de escrita |
| Quem renderiza `/configuracao` depois de gravar um financiamento? | `app/routers/settings.py` é a única casa do contexto da tela, e remontá-lo no outro router faria a mesma tela responder duas coisas conforme o formulário postado — concretamente, a lista de beneficiários sumindo numa recusa de financiamento | `app/routers/financings.py` importa `_answer` e `_text` de `app.routers.settings` e não monta contexto nenhum |
| A tela ganha CSS novo? | `app/static/css/` está fora do escopo deste item, e a linguagem visual manda o valor vir do token | **nenhuma** classe nova e nenhum arquivo de estilo tocado: a seção reusa as classes que `app/templates/configuracao.html` já usa |
| Portão novo em `scripts/gates/`? | Nada aqui é regra de lint nem invariante de repositório | nenhum. Quem executa todo instrumento novo deste plano é `pytest`, que o CI já roda, e a migração é aplicada por `app/migrate.py::run_migrations`, que `app/main.py:41` já chama e que `tests/test_migrations.py` já vigia |

## A linguagem visual da seção nova

A seção segue `product/00-linguagem-visual.md` sem exceção, e dentro dela segue o
idioma que `app/templates/configuracao.html` já estabeleceu — porque é a mesma
tela, e um segundo idioma na mesma página seria a tela dizendo que aquela parte
veio de outro lugar:

- **Estrutura:** `<section id="financiamentos" class="panel panel-wide">` com
  `section-title` e `lede`, e um `<article class="setting">` por financiamento,
  dentro de `<div class="settings">` — exatamente a forma dos blocos "Fatos" e
  "Metas".
- **Rótulo** em versalete pela classe `eyebrow`/`field-label`; campo em
  `field-input`, que já garante o `--text-base` que impede o zoom do navegador de
  celular ao focar.
- **Cifra** em `figure cifra`, que traz `tabular-nums` de `tokens.css`. O saldo
  calculado do veículo é uma cifra **sem cor semântica**: pela régua da
  linguagem visual, `--color-negative` marca o número que pede decisão, e este é
  um número que se lê. O sinal `−` vem colado pelo filtro `brl`, e é ele que diz
  que é saída.
- **Escala graduada:** nenhuma. A seção não mede distância a percorrer, e a régua
  diz que onde não há distância não há marcação.
- **Estado vazio como convite:** sem financiamento, a seção mostra os dois
  formulários e a frase do que preencher — não uma caixa dizendo que não há nada.
- **Escrita:** pt-BR, frase em caixa baixa com maiúscula inicial, sem exclamação;
  o botão diz `Salvar` e a resposta diz `Salvo.`, como o resto da tela.

---

## Fase 1 — A entidade e a importação sem perda de número (api)

**Objetivo da fase:** os dois financiamentos moram numa tabela do banco,
importados uma vez dos arquivos, e a escada reconstruída a partir dela tem
exatamente os degraus que tinha lendo os arquivos.

**Critérios de aceite:**

- [ ] `comando` — RF-01
      `rtk proxy mkdir -p /tmp/025-fase1 && rtk proxy rm -f
      /tmp/025-fase1/dash.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/025-fase1/dash.sqlite .venv/bin/python -c "
      from app.migrate import run_migrations
      from app.db import connect
      run_migrations()
      c = connect()
      found = {r[1]: (r[2], r[3], r[5]) for r in c.execute('PRAGMA table_info(financings)')}
      assert found == {'kind': ('TEXT', 1, 1), 'monthly_rate_bp': ('INTEGER', 1, 0),
      'term_months': ('INTEGER', 1, 0), 'balance_cents': ('INTEGER', 0, 0),
      'payment_cents': ('INTEGER', 0, 0), 'first_due_date': ('TEXT', 0, 0)}, found"`
      sai com código `0`. As colunas de `PRAGMA table_info` lidas são nome, tipo,
      `notnull` e `pk`, e o comando levanta `AssertionError` com código `1` se
      faltar coluna, sobrar coluna, ou se o tipo, a obrigatoriedade ou a chave
      primária divergirem
- [ ] `estrutural` — RF-01
      Existe `app/migrations/sql/014_financings.sql`, e é o **único** arquivo
      novo em `app/migrations/sql/`: a pasta contém exatamente
      `001_schema.sql`, `002_session_epoch.sql`, `003_taxonomy.sql`,
      `004_commitments.sql`, `005_debts.sql`, `006_sync_semantics.sql`,
      `007_plan.sql`, `008_facts.sql`, `009_advisor.sql`, `010_settings.sql`,
      `011_payee_names.sql` e `014_financings.sql`. E a lista
      `EXPECTED_MIGRATIONS` de `tests/test_migrations.py` traz esses mesmos doze
      nomes, a lista `EXPECTED_TABLES` do mesmo arquivo contém `financings`, e a
      maior versão que ele afirma é `"014"`
- [ ] `comportamental` — RF-01, RF-02
      *Dado* um diretório temporário `M` com dois arquivos JSON: em
      `financiamento_caixa.json`, `{"prazo_restante_meses": 370, "saldo_devedor":
      238585.18, "juros_efetivos_aa_pct": 8.9899}`; em
      `cdc_safra_veiculo.json`, `{"prazo_meses": 60, "juros_efetivo_mensal_pct":
      1.63, "valor_parcela": 1235.33, "primeiro_vencimento": "2025-06-11"}` — e
      uma base SQLite nova em diretório temporário, com as migrações aplicadas,
      sem nenhuma linha em `accounts`, com `DASH_MANUAL_DIR` apontando para `M`
      *Quando* `app.debts.ladder.rebuild(conn, today=date(2026, 9, 5))` é chamada
      **duas vezes seguidas** e depois `app.debts.ladder.ladder(conn)` é lida
      *Então* a leitura devolve exatamente dois degraus, nesta ordem, com estes
      valores exatos: o primeiro com `kind` igual a `vehicle`, `name` igual a
      `CDC do veículo`, `balance_cents` igual a `-3917636`, `monthly_rate_bp`
      igual a `163`, `term_months` igual a `45` e `payment_cents` igual a
      `-123533`; o segundo com `kind` igual a `mortgage`, `name` igual a
      `Financiamento imobiliário`, `balance_cents` igual a `-23858518`,
      `monthly_rate_bp` igual a `72`, `term_months` igual a `370` e
      `payment_cents` igual a `None`. E `SELECT COUNT(*) FROM financings` devolve
      `2` — a segunda reconstrução não reimportou nem duplicou. Estes seis
      valores por degrau são os que a carga por arquivo produz hoje; o critério
      os carrega para que a comparação não dependa de ler o código
- [ ] `comportamental` — RF-03
      *Dado* a mesma base e o mesmo diretório `M` do critério anterior, e a
      tabela `financings` já preenchida antes de qualquer reconstrução com a
      linha `kind='mortgage'`, `monthly_rate_bp=1000`, `term_months=12`,
      `balance_cents=-10000000`, `payment_cents=NULL`, `first_due_date=NULL`
      *Quando* `app.debts.ladder.rebuild(conn, today=date(2026, 9, 5))` é chamada
      e `app.debts.ladder.ladder(conn)` é lida
      *Então* a escada tem exatamente **um** degrau, com `kind` igual a
      `mortgage`, `monthly_rate_bp` igual a `1000`, `term_months` igual a `12` e
      `balance_cents` igual a `-10000000`; `SELECT COUNT(*) FROM financings`
      devolve `1`. Os dois arquivos estão no disco e nenhum dos dois entrou: com
      linha na tabela, a origem é uma só
- [ ] `estrutural` — RF-03
      `app/debts/ladder.py` não contém nenhuma das cadeias `import json`,
      `MORTGAGE_FILE`, `VEHICLE_FILE`, `DASH_MANUAL_DIR`, `manual_dir` nem
      `.json`; e `app/financings/store.py` define `MANUAL_DIR` valendo
      `DASH_MANUAL_DIR`, `MORTGAGE_FILE` valendo `financiamento_caixa.json` e
      `VEHICLE_FILE` valendo `cdc_safra_veiculo.json`
- [ ] `comportamental` — RF-04
      *Dado* uma base SQLite nova em diretório temporário com as migrações
      aplicadas, `DASH_MANUAL_DIR` apontando para um diretório que **não existe**,
      `financings` vazia, e uma única linha em `accounts` com `id='a'`,
      `type='BANK'`, `balance_cents=-1000`
      *Quando* `app.debts.ladder.rebuild(conn, today=date(2026, 9, 5))` é chamada
      *Então* a chamada não levanta exceção e devolve `1`;
      `app.debts.ladder.ladder(conn)` devolve lista vazia;
      `app.debts.ladder.without_rate(conn)` devolve uma linha; e
      `SELECT COUNT(*) FROM financings` devolve `0`
- [ ] `comportamental` — RF-06
      *Dado* uma base nova em diretório temporário, `DASH_MANUAL_DIR` apontando
      para diretório inexistente, uma linha em `accounts` com `id='a'`,
      `type='BANK'`, `balance_cents=-1000`, e uma linha em `financings` com
      `kind='mortgage'`, `monthly_rate_bp=72`, `term_months=370`,
      `balance_cents=-23858518`
      *Quando* `rebuild(conn, today=date(2026, 9, 5))` é chamada; depois
      `UPDATE debts SET monthly_rate_bp = 352 WHERE kind = 'overdraft'` e
      `UPDATE financings SET monthly_rate_bp = 500 WHERE kind = 'mortgage'` são
      executados; e `rebuild(conn, today=date(2026, 9, 5))` é chamada de novo
      *Então* o degrau de `kind` igual a `mortgage` tem `monthly_rate_bp` igual a
      `500` — a taxa nova da tabela vence a que estava em `debts` —, e o degrau
      de `kind` igual a `overdraft` tem `monthly_rate_bp` igual a `352` — a taxa
      digitada num degrau que nenhuma fonte reproduz continua sobrevivendo à
      reconstrução. As duas metades andam juntas: apagar a preservação faria a
      segunda falhar, e mantê-la como está faz a primeira falhar
- [ ] `comportamental` — RF-07, RF-08
      *Dado* uma base nova em diretório temporário, `DASH_MANUAL_DIR` apontando
      para diretório inexistente, sem linha em `accounts`, e uma linha em
      `financings` com `kind='vehicle'`, `monthly_rate_bp=163`,
      `term_months=12`, `balance_cents=NULL`, `payment_cents=-100000`,
      `first_due_date='2026-01-31'`
      *Quando* `app.debts.ladder.rebuild(conn, today=date(2026, 9, 5))` é chamada
      *Então* a chamada **não levanta exceção** e devolve `1`, e o único degrau
      tem `term_months` igual a `4` e `balance_cents` menor que `0`. Um
      vencimento no dia 31 tem de atravessar fevereiro: sem o ajuste do dia,
      montar a data da segunda parcela levanta `ValueError` e a reconstrução
      inteira cai
- [ ] `comportamental` — RF-07
      *Dado* uma base nova em diretório temporário, `DASH_MANUAL_DIR` apontando
      para diretório inexistente, sem linha em `accounts`, e uma linha em
      `financings` com `kind='vehicle'`, `monthly_rate_bp=163`,
      `term_months=60`, `balance_cents=NULL`, `payment_cents=-123533`,
      `first_due_date='2025-06-11'`; e, num segundo caso, a mesma linha com
      `term_months=12` e `first_due_date='2020-01-10'`
      *Quando* `rebuild(conn, today=date(2026, 9, 5))` e depois
      `rebuild(conn, today=date(2026, 10, 5))` são chamadas no primeiro caso, e
      `rebuild(conn, today=date(2026, 9, 5))` no segundo
      *Então* no primeiro caso a leitura depois da primeira chamada tem
      `term_months` igual a `45` e `balance_cents` igual a `-3917636`, e depois
      da segunda tem `term_months` igual a `44` e `balance_cents` estritamente
      maior que `-3917636` e ainda menor que `0` — o saldo diminui sozinho
      conforme a parcela vence, sem ninguém digitar nada; e no segundo caso
      `rebuild` devolve `0`, `ladder(conn)` devolve lista vazia e
      `SELECT COUNT(*) FROM financings` continua devolvendo `1` — contrato com
      todas as parcelas vencidas não é degrau, e não vira saldo de sinal
      invertido
- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-06, RF-07
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_debts.py tests/test_financings.py tests/test_migrations.py` sai
      com código `0`, e `tests/test_financings.py` define funções de teste que
      exercitam: a escada reconstruída a partir da tabela contra a escada
      reconstruída a partir dos dois JSON sobre a mesma base e com
      `today=date(2026, 9, 5)`, comparando campo a campo; a máquina sem arquivo e
      sem linha; a tabela vencendo o arquivo; a taxa nova da tabela alcançando a
      escada; o vencimento no dia 31; e o contrato com todas as parcelas
      vencidas. `tests/test_debts.py` mantém a função
      `test_the_vehicle_step_is_built_by_the_loader_and_not_by_the_test` com as
      constantes `VEHICLE_BALANCE = 3917636`, `PAYMENT = 123533`,
      `RATE_BP = 163` e `TERM = 45` intactas — a única mudança permitida nela é
      de onde vêm os nomes `MANUAL_DIR` e `VEHICLE_FILE`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Criar `app/migrations/sql/014_financings.sql`.**
      > Reconciliado em D-005.
      ```sql
      CREATE TABLE financings (
          kind TEXT NOT NULL PRIMARY KEY,
          monthly_rate_bp INTEGER NOT NULL,
          term_months INTEGER NOT NULL,
          balance_cents INTEGER,
          payment_cents INTEGER,
          first_due_date TEXT,
          CHECK (kind != 'vehicle' OR (payment_cents IS NOT NULL AND first_due_date IS NOT NULL))
      );
      ```
      O `CHECK` garante a completude estrutural da linha de veículo — ela não
      existe sem parcela e sem data de primeiro vencimento —, e é rede de
      segurança nunca alcançada em uso normal, porque a tela da fase 2 exige os
      dois campos antes de escrever. Essa garantia é outra coisa da recusa de
      RF-08, que continua sendo da camada que fala pt-BR e trata da gramática do
      campo digitado, não da completude da linha. Sem índice: a tabela tem no
      máximo duas linhas.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-01. O número `014` é o reservado a este item; `012`,
      `013` e `015` pertencem a itens que correm ao mesmo tempo, e
      `app/migrations/runner.py:37` deriva a versão do prefixo do nome do
      arquivo — dois itens com o mesmo prefixo fazem o segundo ser pulado em
      silêncio. Os comentários do arquivo, se houver, são do tipo que a norma 11
      admite — o porquê que o código não mostra —, e `005_debts.sql:5-10` já traz
      exatamente esse estilo.

- [ ] **1.2 — Modificar `tests/test_migrations.py`: o guarda do esquema conhece
      a tabela nova.**
      `014_financings.sql` entra em `EXPECTED_MIGRATIONS` (linhas 32-44),
      `financings` entra em `EXPECTED_TABLES` na posição alfabética (entre
      `essentialities` e `login_attempts`), e a asserção de
      `test_second_run_applies_nothing` (linha 71) passa a esperar `"014"` como
      maior versão.
      *Considerando 1.1.*
      *Justificativa:* RF-01. É o executor do instrumento criado em 1.1: a
      migração é aplicada por `app/migrate.py::run_migrations`, e quem prova que
      ela cria o que promete e que não é aplicada duas vezes é este arquivo, que
      `pytest` roda no CI. Sem esta etapa, três testes que hoje passam ficam
      vermelhos e a fase inteira parece quebrada por um motivo que não é o dela.

- [ ] **1.3 — Criar `app/financings/__init__.py`, `app/financings/money.py` e
      `app/financings/math.py`: os tipos, as constantes e a conta.**
      `__init__.py` define `MORTGAGE = "mortgage"`, `VEHICLE = "vehicle"`,
      `KINDS = (MORTGAGE, VEHICLE)` e
      `NAMES = {MORTGAGE: "Financiamento imobiliário", VEHICLE: "CDC do veículo"}`
      — os dois nomes literais que `app/debts/ladder.py:119` e `:135` usam hoje,
      e que RF-02 exige idênticos. `money.py` define `RATE_SCALE = 10000`,
      `CENTS_IN_UNIT = 100` e `MONTHS_IN_YEAR = 12`. `math.py` define:
      ```python
      def monthly_from_yearly_bp(yearly_pct: float) -> int
      def instalments_due(first_due: date, term_months: int, today: date) -> int
      def remaining_months(first_due: date, term_months: int, today: date) -> int
      def present_value_cents(payment_cents: int, monthly_rate_bp: int, left: int) -> int
      ```
      `instalments_due` limita o dia ao último do mês (`calendar.monthrange`);
      `remaining_months` devolve `term_months - instalments_due(...)`, nunca
      abaixo de zero; `present_value_cents` devolve valor **negativo** e devolve
      `0` quando `left` é `0`.
      *Considerando 1.1.*
      *Justificativa:* RF-01, RF-07, RF-08, invariante 22, norma 23. A conta sai
      de `app/debts/ladder.py` porque a tela da fase 2 precisa exibir o mesmo
      saldo que a escada grava, e duas implementações da mesma fórmula divergem
      no dia em que uma das duas for corrigida. O limite do dia existe porque
      `app/debts/ladder.py:153` monta `date(year, month, first.day)` e um
      contrato com vencimento no dia 31 derruba a reconstrução em fevereiro — que
      hoje não acontece só porque o arquivo traz dia 11. O piso em zero existe
      porque com prazo restante negativo a fórmula devolve saldo positivo, e um
      degrau de dívida com sinal invertido contradiz o invariante 22. O módulo
      **não importa nada de `app/debts/`**: a dependência é de mão única, e é
      isso que impede o ciclo com `ladder.py`.

- [ ] **1.4 — Criar `app/financings/store.py`: a leitura e a semente.**
      Constantes `MANUAL_DIR = "DASH_MANUAL_DIR"`, `DEFAULT_MANUAL = "data/manual"`,
      `MORTGAGE_FILE = "financiamento_caixa.json"`,
      `VEHICLE_FILE = "cdc_safra_veiculo.json"` e a função `manual_dir()` —
      transplantadas de `app/debts/ladder.py:20-23` e `:35-36` sem mudança de
      valor, porque `tests/test_debts.py` já as usa por nome para apontar o
      diretório temporário. Funções:
      ```python
      def read_all(conn: sqlite3.Connection) -> list[dict]
      def read(conn: sqlite3.Connection, kind: str) -> dict | None
      def seed_from_manual(conn: sqlite3.Connection) -> int
      ```
      `seed_from_manual` **retorna cedo** se `SELECT COUNT(*) FROM financings`
      for maior que zero — só então abre o disco. De `financiamento_caixa.json`
      lê `prazo_restante_meses`, `saldo_devedor` e `juros_efetivos_aa_pct`, e
      grava `kind='mortgage'`, `monthly_rate_bp=monthly_from_yearly_bp(...)`,
      `term_months=prazo_restante_meses`,
      `balance_cents=-round(saldo_devedor * 100)`, `payment_cents=NULL`,
      `first_due_date=NULL`. De `cdc_safra_veiculo.json` lê `prazo_meses`,
      `juros_efetivo_mensal_pct`, `valor_parcela` e `primeiro_vencimento`, e
      grava `kind='vehicle'`,
      `monthly_rate_bp=round(juros_efetivo_mensal_pct * 100)`,
      `term_months=prazo_meses`, `balance_cents=NULL`,
      `payment_cents=-round(valor_parcela * 100)`,
      `first_due_date=primeiro_vencimento`. Arquivo ausente é financiamento
      ausente, nunca carga quebrada. A escrita é `INSERT OR IGNORE`, e o `commit`
      é daqui — não do router (norma 30).
      *Considerando 1.3:* a conversão anual→mensal vem de `math.py`, e é a mesma
      expressão de `app/debts/ladder.py:115-116`, aplicada uma vez.
      *Justificativa:* RF-01, RF-02, RF-03, RF-04. A guarda pela tabela vazia é o
      que faz "importação única" ser um fato do código e não uma promessa: depois
      da primeira reconstrução bem-sucedida, `data/manual/` nunca mais é aberto.
      Numa máquina sem os arquivos a guarda continua caindo no disco a cada
      reconstrução — dois `is_file()` — até a tela gravar o primeiro
      financiamento, e aí para para sempre.

- [ ] **1.5 — Modificar `app/debts/ladder.py`: a escada passa a ler a tabela.**
      Saem `import json`, `import os`, `from pathlib import Path`, as constantes
      `MANUAL_DIR`, `DEFAULT_MANUAL`, `MORTGAGE_FILE`, `VEHICLE_FILE`,
      `BASIS_POINTS`, `MONTHS_IN_YEAR`, e as funções `manual_dir`, `_read`,
      `_paid` e `_cents`. `MORTGAGE`, `VEHICLE` e `RATE_SCALE` passam a vir de
      `app.financings` e `app.financings.money` e continuam sendo atributos do
      módulo, porque `app/routers/debts.py:12`, `app/plan/timeline.py:5` e
      `app/debts/simulate.py:3` os importam daqui e esses três arquivos estão
      fora do escopo. `_from_contracts(today)` vira
      `_from_financings(conn, today)`, que chama
      `store.seed_from_manual(conn)`, lê `store.read_all(conn)` e devolve um
      degrau por linha: o do imóvel com o `balance_cents` e o `term_months` da
      linha e `payment_cents` nulo; o do veículo com `term_months` igual a
      `remaining_months(...)`, `balance_cents` igual a
      `present_value_cents(...)` e `payment_cents` igual ao da linha, e **sem
      degrau nenhum** quando o prazo restante é zero. `source` vale
      `"financings"` nos dois. Em `rebuild`, a linha 57 passa a usar a taxa
      preservada **apenas** quando `row["monthly_rate_bp"] is None`, e o
      comentário de `:55-56` é reescrito para dizer isso.
      *Considerando 1.3 e 1.4.*
      *Justificativa:* RF-02, RF-03, RF-06, RF-07. `_from_accounts` **não é
      tocada**: ela pertence a outro item que corre em paralelo. A condição nova
      na preservação da taxa é o ponto mais fácil de errar da fase: mantida como
      está, a taxa que o dono editar na tela nunca alcança a escada, porque o
      valor que já está em `debts` sempre vence; apagada por inteiro, a taxa
      digitada num cheque especial se perde a cada sincronização, que é
      exatamente o defeito que o comentário de hoje existe para evitar.

- [ ] **1.6 — Criar `tests/test_financings.py` e ajustar `tests/test_debts.py`.**
      Em `tests/test_financings.py`: a escada das duas origens sobre a mesma base
      — a implementação de referência que lê os dois JSON escrita no próprio
      teste, comparada campo a campo com a escada vinda da tabela, com
      `today=date(2026, 9, 5)`; a reconstrução chamada duas vezes seguidas; a
      máquina sem arquivo e sem linha; a tabela vencendo o arquivo; a taxa nova
      da tabela alcançando a escada ao lado da taxa digitada de conta que
      sobrevive; o vencimento no dia 31; o contrato com todas as parcelas
      vencidas; e o saldo do veículo encolhendo entre `2026-09-05` e
      `2026-10-05`. Em `tests/test_debts.py`, as três referências a
      `ladder_module.MANUAL_DIR` (linhas 104, 117 e 149) e a
      `ladder_module.VEHICLE_FILE` (linha 139) passam a apontar para
      `app.financings.store`; **nenhuma asserção e nenhuma das quatro constantes
      do topo do arquivo mudam**.
      *Considerando 1.5.*
      *Justificativa:* RF-02, RF-03, RF-04, RF-06, RF-07. As quatro constantes de
      `tests/test_debts.py:15-18` são o oráculo que existia antes deste item:
      elas afirmam os quatro números do degrau do veículo sobre a carga de hoje,
      e mantê-las intactas é o que transforma um teste antigo na prova de que a
      importação não mexeu em número. Quem executa todos eles é `pytest`, que o
      CI já roda; nenhum arquivo entra em `scripts/gates/`.

---

## Fase 2 — Os dois financiamentos na tela (api)

**Objetivo da fase:** os campos dos dois financiamentos se editam em
`/configuracao`, gravar reconstrói a escada na mesma requisição, e valor fora da
gramática é recusado com a tela de pé.

**Critérios de aceite:**

- [ ] `estrutural` — RF-05
      `app/templates/fragments/configuracao_financiamentos.html` existe e contém
      `id="financiamentos"`; `app/templates/configuracao.html` contém
      exatamente uma linha
      `{% include "fragments/configuracao_financiamentos.html" %}`, e a primeira
      linha não vazia depois dela é a que abre `<section id="beneficiarios"`;
      `app/main.py` contém `app.include_router(financings.router)`; e
      `git diff --name-only main -- app/static/css` não imprime nenhuma linha
- [ ] `estrutural` — RF-05, RF-08
      `app/routers/financings.py` existe, define `router`, registra a rota
      `POST /configuracao/financiamento`, contém a linha de import
      `from app.routers.settings import answer, text`, e **não** contém as
      cadeias `TemplateResponse`, `def _context` nem `conn.execute` — a tela tem
      um renderizador só, e o router não monta consulta (norma 30)
- [ ] `comportamental` — RF-05
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-09-05` e `DASH_ENV_FILE=/dev/null` no ambiente do
      processo, banco em diretório temporário, usuário semeado, sessão
      autenticada, e a tabela `financings` com as duas linhas
      `kind='mortgage'`, `monthly_rate_bp=72`, `term_months=370`,
      `balance_cents=-23858518` e `kind='vehicle'`, `monthly_rate_bp=163`,
      `term_months=60`, `payment_cents=-123533`,
      `first_due_date='2025-06-11'`
      *Quando* `GET /configuracao` é buscada
      *Então* a resposta é `200`, e no recorte do HTML que vai de
      `id="financiamentos"` até o primeiro `</section>` depois dele aparecem:
      `data-financiamento="mortgage"`, um `<input` com `name="saldo"` e
      `value="238.585,18"`, um com `name="taxa"` e `value="0,72"`, um com
      `name="prazo"` e `value="370"`; e `data-financiamento="vehicle"`, um
      `<input` com `name="taxa"` e `value="1,63"`, um com `name="parcela"` e
      `value="1.235,33"`, um com `name="prazo"` e `value="60"`, e um com
      `name="vencimento"` e `value="2025-06-11"`. O recorte é declarado porque a
      tela inteira já traz outros campos de valor em reais, e lido sem recorte o
      critério passaria pelo formulário errado
- [ ] `comportamental` — RF-07
      *Dado* o painel servido com o ambiente e a base do critério anterior
      *Quando* `GET /configuracao` é buscada
      *Então* no recorte que vai de `data-financiamento="vehicle"` até o
      primeiro `</article>` depois dele aparece o texto `−R$ 39.176,36` e
      **não** aparece nenhum `<input` com `name="saldo"` — o saldo do veículo é
      número calculado e mostrado, nunca campo digitável
- [ ] `comportamental` — RF-04
      *Dado* o painel servido com o mesmo ambiente, banco em diretório
      temporário, usuário semeado, transações carregadas, sessão autenticada e a
      tabela `financings` **vazia**
      *Quando* `GET /configuracao` é buscada e, na mesma execução, `GET /dividas`
      *Então* as duas respondem `200`; o HTML da primeira contém
      `id="financiamentos"` e, no recorte até o `</section>` seguinte, um
      `<input` com `name="saldo"` de `value` vazio e um com `name="parcela"` de
      `value` vazio; e o HTML da segunda **não** contém `data-financiamento`
      nem a cadeia `CDC do veículo`
- [ ] `comportamental` — RF-05, RF-06
      *Dado* o painel servido com o ambiente e a base do terceiro critério desta
      fase
      *Quando* `POST /configuracao/financiamento` é enviada com os campos
      `tipo=mortgage`, `saldo=200.000,00`, `taxa=5,00` e `prazo=300`
      *Então* a resposta é `200` e contém `Salvo.`; e, lida **antes de qualquer
      outra requisição**, a consulta
      `SELECT monthly_rate_bp, term_months, balance_cents FROM financings WHERE
      kind = 'mortgage'` devolve `500`, `300` e `-20000000`, e a consulta
      `SELECT monthly_rate_bp, balance_cents FROM debts WHERE kind = 'mortgage'`
      devolve `500` e `-20000000` — a escada foi reconstruída na mesma
      requisição, e não na seguinte
- [ ] `comportamental` — RF-06
      *Dado* o painel servido com o ambiente e a base do terceiro critério desta
      fase, e `GET /dividas` buscada antes de qualquer escrita
      *Quando* `POST /configuracao/financiamento` é enviada com `tipo=mortgage`,
      `saldo=200.000,00`, `taxa=5,00`, `prazo=300`, e em seguida `GET /dividas` é
      buscada de novo
      *Então* na primeira leitura de `/dividas`, no recorte que vai de
      `id="escada"` até o primeiro `</section>` depois dele, o primeiro
      `<tr data-degrau=` traz `data-taxa="163"`; e na segunda leitura, no mesmo
      recorte, o primeiro `<tr data-degrau=` traz `data-taxa="500"` — a ordem da
      escada mudou porque o número mudou, e a tela seguinte já mostra a nova
- [ ] `comportamental` — RF-08
      *Dado* o painel servido com o ambiente e a base do terceiro critério desta
      fase
      *Quando* `POST /configuracao/financiamento` é enviada com `tipo=mortgage`,
      `saldo=abc`, `taxa=0,72`, `prazo=370`
      *Então* a resposta é `400`, o HTML contém `id="recusa"` e, dentro dele, a
      cadeia `abc`; o HTML continua contendo `id="financiamentos"` e
      `id="beneficiarios"` — a tela fica de pé inteira; e
      `SELECT balance_cents FROM financings WHERE kind = 'mortgage'` continua
      devolvendo `-23858518`
- [ ] `comportamental` — RF-08
      *Dado* o painel servido com o ambiente e a base do terceiro critério desta
      fase
      *Quando* `POST /configuracao/financiamento` é enviada três vezes, cada uma
      numa requisição: `tipo=vehicle`, `taxa=1,63`, `parcela=1.235,33`,
      `prazo=60`, `vencimento=31/01/2026`; depois `tipo=vehicle`, `taxa=0`,
      `parcela=1.235,33`, `prazo=60`, `vencimento=2025-06-11`; depois
      `tipo=carro`, `taxa=1,63`, `parcela=1.235,33`, `prazo=60`,
      `vencimento=2025-06-11`
      *Então* as três respondem `400` e nenhuma responde `500`; as três contêm
      `id="recusa"`, a primeira com a cadeia `31/01/2026`, a segunda com uma
      frase sobre a taxa e a terceira com a cadeia `carro`; e, depois das três,
      `SELECT monthly_rate_bp, first_due_date FROM financings WHERE
      kind = 'vehicle'` continua devolvendo `163` e `2025-06-11`
- [ ] `comando` — RF-04, RF-05, RF-06, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_configuracao_financiamentos.py tests/test_configuracao_screen.py`
      sai com código `0`, e `tests/test_configuracao_financiamentos.py` define
      funções de teste que exercitam a leitura dos dois formulários preenchidos,
      o saldo calculado do veículo sem campo, a seção sem financiamento nenhum, a
      gravação que reordena a escada de `/dividas` na leitura seguinte, e as
      quatro recusas: valor em reais fora da gramática, data fora do ISO, taxa
      zero e tipo desconhecido

**Critérios de integração** — nenhum dos dois se verifica com uma fase só: a
fase 1 cria a casa e não tem tela que escreva nela, e a fase 2 escreve numa casa
que só existe depois da fase 1.

- [ ] `comportamental` — RF-01, RF-02, RF-05, RF-06
      *Dado* um banco em diretório temporário com **todas** as migrações
      aplicadas em sequência, `DASH_MANUAL_DIR` apontando para a pasta que
      contém os dois arquivos JSON de contrato, a escada reconstruída com
      `today` igual a `date(2026, 9, 5)`, e o painel servido com sessão
      autenticada
      *Quando* `GET /dividas` é lida e os degraus são anotados; depois
      `POST` na rota de gravação de financiamento corrige o saldo devedor do
      imóvel para um valor menor que o importado; e `GET /dividas` é lida de novo
      *Então* a primeira leitura traz os dois degraus de contrato com os valores
      que a importação produziu, a segunda traz o degrau do imóvel com o saldo
      novo, e os demais degraus são idênticos nas duas — o número entrou pela
      tela da fase 2 e saiu pela leitura que a fase 1 mudou, e nada mais se moveu
- [ ] `comportamental` — RF-04, RF-05, RF-07
      *Dado* um banco em diretório temporário com todas as migrações aplicadas e
      `DASH_MANUAL_DIR` apontando para uma pasta **vazia**, e o painel servido
      com sessão autenticada
      *Quando* `GET /configuracao` é lida; depois os campos do financiamento do
      veículo são gravados pela tela com taxa, parcela, prazo e primeiro
      vencimento iguais aos do arquivo de contrato; e a escada é reconstruída
      com `today` igual a `date(2026, 9, 5)`
      *Então* a primeira leitura mostra a seção com o estado vazio e a tela
      responde `200` — a máquina sem contrato sobe; e o degrau produzido depois
      da gravação tem exatamente o mesmo `balance_cents`, `monthly_rate_bp`,
      `term_months` e `payment_cents` que o degrau importado do arquivo tem no
      critério de RF-02. Digitar na tela e importar do arquivo chegam ao mesmo
      número, ou uma das duas origens está mentindo

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **2.1 — Criar `app/financings/typed.py`: a leitura dos campos digitados.**
      ```python
      def parse_due_date(typed: str, field: str = "Primeiro vencimento") -> date
      def read_form(kind: str, typed: dict[str, str]) -> dict
      ```
      `parse_due_date` aceita ISO `AAAA-MM-DD` e levanta o `InvalidValueError` de
      `app.settings.typed` com o valor digitado na frase, em pt-BR. `read_form`
      despacha por tipo: para `mortgage` exige saldo (`parse_money`), taxa
      (`parse_rate`) e prazo (`parse_months`); para `vehicle` exige taxa,
      parcela (`parse_money`), prazo e primeiro vencimento. Tipo fora de
      `KINDS`, taxa ausente e taxa zero são recusados com frase própria. Saldo e
      parcela saem negativos.
      *Considerando 1.3* (os tipos e os nomes) *e a gramática do item `015`*,
      que é `app/settings/typed.py` e não é tocada.
      *Justificativa:* RF-05, RF-08. O leitor de data mora aqui porque
      `app/settings/typed.py` está fora do escopo deste item e porque data não é
      unidade do catálogo do `015` — que só conhece centavos, pontos-base e
      meses. A taxa zero é recusada aqui, e não na conta: o valor presente
      divide pela taxa, e `parse_rate("0")` devolve `0` sem reclamar. A negação
      acontece nesta borda, uma vez, como manda o invariante 22.

- [ ] **2.2 — Acrescentar `write` e `section` a `app/financings/store.py`.**
      ```python
      def write(conn: sqlite3.Connection, kind: str, typed: dict[str, str]) -> None
      def section(conn: sqlite3.Connection, *, today: date) -> dict
      ```
      `write` lê os campos por `read_form`, grava com `INSERT OR REPLACE` e dá
      `commit`. `section` devolve uma entrada por tipo de `KINDS`, sempre as
      duas, com: o rótulo do tipo, os valores já na forma digitável de cada
      unidade, e — só no veículo — `balance_cents` e `remaining_months`
      calculados para `today`. Tipo sem linha na tabela devolve entrada com
      valores nulos.
      *Considerando 2.1* e *1.3* (a conta do saldo do veículo é a mesma que a
      escada grava, e vem de `math.py`).
      *Justificativa:* RF-05, RF-06, RF-07. `section` devolve **sempre os dois
      tipos** para que a seção vazia seja um convite com dois formulários, e não
      uma caixa dizendo que não há nada — é o que a linguagem visual pede de
      estado vazio. O saldo do veículo sai daqui calculado, e não de uma segunda
      fórmula no template: o número que a tela mostra e o que a escada grava são
      o mesmo.

- [ ] **2.3 — Criar `app/routers/financings.py`: a rota de escrita.**
      `router = APIRouter()`, `SCREEN = "/configuracao"`,
      `FINANCING = f"{SCREEN}/financiamento"`, e um `POST` com os campos
      `tipo`, `saldo`, `taxa`, `parcela`, `prazo` e `vencimento` em
      `Annotated[str, Form()] = ""`. O corpo abre a conexão, passa os valores por
      `_text`, chama `store.write`, chama
      `app.debts.ladder.rebuild(conn, today=reference_date())` e responde
      `_answer(request, conn, done="Salvo.")`; `InvalidValueError` responde
      `_answer(request, conn, notice=str(refusal), status_code=400)`.
      *Considerando 2.1 e 2.2.*
      *Justificativa:* RF-05, RF-06, RF-08, normas 29 e 30. O router fica em
      `app/routers/`, um por domínio, e traduz HTTP: quem monta a consulta e dá
      o `commit` é `store`. `_answer` e `_text` são importados de
      `app.routers.settings` porque `/configuracao` tem um contexto só —
      remontá-lo aqui faria a lista de beneficiários sumir da tela toda vez que
      uma recusa de financiamento respondesse. A reconstrução da escada é
      chamada **na mesma requisição** porque é o que RF-06 pede, e
      `reference_date()` é a data que o resto das telas usa.

- [ ] **2.4 — Criar
      `app/templates/fragments/configuracao_financiamentos.html`.**
      `<section id="financiamentos" class="panel panel-wide">` com
      `section-title`, um `lede` que diz que estes são os dois contratos e que o
      saldo do veículo o painel calcula, e `<div class="settings">` com um
      `<article class="setting" data-financiamento="{{ tipo }}">` por
      financiamento. Cada artigo traz `setting-what` com o nome e o texto de
      apoio, e `setting-value` com o formulário: no imóvel, `saldo`, `taxa` e
      `prazo`; no veículo, `taxa`, `parcela`, `prazo` e `vencimento` — este com
      `type="date"` —, mais o saldo calculado em
      `<p class="figure cifra">` com o filtro `brl`. Botão
      `button button-quiet button-small` escrito `Salvar`. Rótulos: **Saldo
      devedor, em reais**, **Por cento ao mês**, **Prazo restante, em meses** no
      imóvel; **Por cento ao mês**, **Valor da parcela, em reais**, **Prazo do
      contrato, em meses**, **Primeiro vencimento** no veículo. Os valores
      digitáveis usam os filtros `digitado` e `numero` que
      `app/routers/render.py` já registra. Nenhuma classe nova, nenhum
      hexadecimal, nenhum `style=` embutido.
      *Considerando 2.2:* o fragmento só lê a chave que `section` devolve.
      *Justificativa:* RF-05, RF-07, norma 27 e `product/00-linguagem-visual.md`.
      Os dois prazos têm rótulos diferentes porque os dois documentos dizem
      coisas diferentes — o app da CAIXA mostra prazo restante, a cédula do
      Safra mostra prazo contratado — e pedir "prazo" sem dizer qual é como o
      número entra errado. `type="date"` no vencimento garante o ISO no caminho
      normal; o caminho forjado é o que a recusa de 2.1 cobre.

- [ ] **2.5 — Modificar `app/routers/settings.py` e
      `app/templates/configuracao.html`: a seção entra na tela.**
      Em `_context`, uma chave nova:
      `"financings": financings_store.section(conn, today=reference_date())`.
      Em `configuracao.html`, uma linha
      `{% include "fragments/configuracao_financiamentos.html" %}` imediatamente
      antes da linha 86, que abre `<section id="beneficiarios"`. Mais nada nos
      dois arquivos.
      *Considerando 2.2 e 2.4.*
      *Justificativa:* RF-05. A posição é entre "Metas" e "Beneficiários" porque
      financiamento é fato do mundo com número que envelhece, como os de cima, e
      a lista de beneficiários é longa e empurra para baixo qualquer coisa posta
      depois dela. Os dois arquivos pertencem a itens que correm em paralelo, e
      é por isso que a mudança aqui é de uma linha em cada.

- [ ] **2.6 — Modificar `app/main.py`: o router entra.**
      `financings` entra na lista de import de `app.routers` e ganha
      `app.include_router(financings.router)` junto dos outros.
      *Considerando 2.3.*
      *Justificativa:* RF-05. Sem isso `POST /configuracao/financiamento`
      responde `404`, e a guarda de sessão de `tests/test_route_guard.py` só
      alcança rota registrada.

- [ ] **2.7 — Criar `tests/test_configuracao_financiamentos.py`.**
      Fixture no molde de `tests/test_configuracao_screen.py:32-48`:
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` em `tmp_path`, `SESSION_SECRET`,
      `DASH_TODAY=2026-09-05`, usuário semeado, transações carregadas e
      `TestClient` autenticado. Testes: os dois formulários preenchidos a partir
      da tabela; o saldo calculado do veículo presente e sem campo; a seção sem
      financiamento nenhum; a gravação do imóvel reordenando a escada de
      `/dividas` na leitura seguinte, com a consulta a `debts` feita logo depois
      do `POST`; e as quatro recusas de RF-08, cada uma conferindo que a linha da
      tabela não mudou.
      *Considerando 2.1 a 2.6.*
      *Justificativa:* RF-04, RF-05, RF-06, RF-07, RF-08. Quem executa é
      `pytest`, que o CI já roda; nenhum arquivo entra em `scripts/gates/` e
      `scripts/gates/gates_runner.sh` não é tocado. O arquivo é novo em vez de
      crescer dentro de `tests/test_configuracao_screen.py` porque aquele arquivo
      é de outro assunto e está no caminho de outros itens simultâneos.

---

## Execução sugerida

1. **Fase 1, bloqueante.** Ela fixa a forma do dado que a fase 2 consome e
   carrega o critério numérico que decide o item. Toca
   `app/migrations/sql/014_financings.sql`, `tests/test_migrations.py`,
   `app/financings/__init__.py`, `app/financings/money.py`,
   `app/financings/math.py`, `app/financings/store.py`, `app/debts/ladder.py`,
   `tests/test_financings.py` e `tests/test_debts.py`.
2. **Fase 2 depois da 1.** Toca `app/financings/typed.py`,
   `app/financings/store.py`, `app/routers/financings.py`,
   `app/templates/fragments/configuracao_financiamentos.html`,
   `app/templates/configuracao.html`, `app/routers/settings.py`,
   `app/main.py` e `tests/test_configuracao_financiamentos.py`.

As duas **não** são paralelas. A fase 2 escreve dentro de
`app/financings/store.py`, que a fase 1 cria, e todos os seus critérios de tela
leem a tabela que a fase 1 define — num par de worktrees a fase 2 nasceria contra
um esquema que ainda não existe.

Dentro do item, as duas fases tocam dez arquivos que **nenhum dos outros cinco
itens simultâneos toca**, e quatro que eles tocam: `app/main.py` (uma linha),
`app/routers/settings.py` (uma chave), `app/templates/configuracao.html` (uma
linha, antes de `<section id="beneficiarios"`) e `tests/test_migrations.py`.
Este último é o único ponto de **conflito garantido**: todo item que traz
migração acrescenta um nome a `EXPECTED_MIGRATIONS`, uma tabela a
`EXPECTED_TABLES` e muda a versão máxima afirmada na linha 71. O conflito é de
lista e se resolve juntando as duas entradas e reescrevendo a versão máxima como
a maior das duas; quem faz merge depois é quem resolve, e a resolução se confere
rodando `pytest tests/test_migrations.py`. `_from_accounts` de
`app/debts/ladder.py` não é tocada, e `app/taxonomy/`, `app/queries/`,
`app/advisor/`, `app/cards/`, `app/routers/spending.py` e
`app/routers/reference.py` não são abertos.

## Pendências que viram item de roadmap

- **O estado vazio de `/dividas` continua mandando o dono para
  `data/manual/`.** `app/templates/dividas.html:18-20` diz que os degraus de
  contrato nascem de arquivo naquela pasta, e depois deste item isso deixa de ser
  verdade: a frase certa aponta para `/configuracao`. O arquivo pertence a um
  item que corre em paralelo e por isso não é tocado aqui.
- **`financas/cdc_veiculo.py:12` e `financas/financiamento_sac.py:10` continuam
  lendo os dois JSON.** São roteiros de análise fora de `app/`, e RF-03 fala de
  `app/debts/ladder.py`. Numa máquina sem os arquivos eles já falham hoje, e este
  item não muda isso — mas passam a ser a única coisa do repositório que ainda
  depende de uma origem que o painel abandonou.
- **Não existe como apagar um financiamento pela tela.** Nenhum RF pede, e
  `parse_money` recusa zero: um contrato quitado só sai da escada quando o prazo
  restante zera sozinho, o que acontece no veículo e não acontece no imóvel.
- **A semente só importa enquanto a tabela está vazia.** Uma máquina que recebeu
  um dos dois arquivos, importou, e depois recebeu o outro nunca importa o
  segundo — o dono o informa na tela. É o preço de "importação única" ser um fato
  do código.
- **`tests/test_migrations.py` lista o esquema à mão.** Toda migração nova obriga
  a editar três literais no arquivo, e com seis itens simultâneos isso é seis
  conflitos de merge no mesmo lugar. Derivar as listas do banco recém-migrado
  tiraria o conflito — e tiraria também o guarda, que é ter escrito à mão o que
  se espera. A troca é de outro item.

## Validações de campo pendentes

Nenhuma bloqueia o item. Duas coisas deste plano só se observam fora de um
validador, e ficam registradas aqui em vez de virar fase:

- **A renderização da seção nova em aparelho físico**, nas larguras de 375 a
  1920 e nos dois temas. Os critérios cobrem a marcação e as classes; que o
  bloco não estoure a linha num celular real é observação de olho.
- **A importação sobre a base de verdade do dono**, que é a única execução em que
  os dois arquivos de `data/manual/` são os do contrato e não cópias de teste.
  Os critérios provam a importação sobre cópias com os mesmos valores; a
  execução real acontece uma vez, na primeira reconstrução depois do merge.
