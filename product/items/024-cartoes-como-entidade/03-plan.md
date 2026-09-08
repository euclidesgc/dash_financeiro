# Plano — 024-cartoes-como-entidade

**Item:** `024-cartoes-como-entidade` · **Trilha:** rápida · **Fonte aprovada:**
`01-brief.md` (RF-01 a RF-08) · **Terreno:** `00-discovery.md` · Duas fases, em
sequência.

> **Todo fato de código deste plano foi lido no arquivo citado**, com linha. Os
> números de dinheiro que aparecem em critério são **construídos pelo próprio
> teste** sobre base em diretório temporário — nenhum critério se compara com a
> base do dono, que o validador não tem. O único número herdado é o
> R$ 16.744,62 de cartão fora da escada, que vem do `01-brief.md` e não é
> remedido aqui.

## Objetivo

Ao fim das duas fases o cartão de crédito é uma entidade do painel, com limite,
taxa mensal, dia de fechamento e dia de vencimento — os quatro vazios até o dono
informar, e os quatro editáveis em `/configuracao`. A **taxa mensal do cartão
tem uma casa só**: a escada de dívida a lê de lá, o campo de taxa de `/dividas`
escreve nela, e a tabela `debts` deixa de guardar taxa de cartão. Informada a
taxa, o cartão entra na escada na posição que a taxa dele determina; não
informada, a escada é exatamente a de hoje. Fechamento e vencimento são
guardados e não movem número nenhum: quem os usa é o item `026`.

A quebra é por **contrato, não por tela**. A fase 1 fixa onde o dado mora
(`cards`), quem o cria (a derivação a partir das contas de crédito, refeita a
cada carga), quem o lê (a escada) e quem o escreve (a gramática de digitação e o
campo de taxa de `/dividas`). A fase 2 põe a tela em cima disso. Invertida a
ordem, a tela definiria a forma do dado pelo formulário, e a premissa errada de
contrato se espalharia para a escada, para o marco "dívidas caras zeradas" de
`/objetivo` e para a lista de dívidas sem taxa de uma vez só — os três consomem
`ladder()`/`without_rate()` sem saber que existe cartão.

## O terreno, lido no código

| Sítio | Hoje | O que muda |
|---|---|---|
| `app/migrations/sql/001_schema.sql:17-25` | `accounts` guarda `id`, `name`, `type`, `subtype`, `institution`, `balance_cents`, `updated_at` | **nada**: é espelho da fonte, reescrito a cada carga |
| `app/migrations/sql/005_debts.sql:1-17` | `debts` guarda `monthly_rate_bp` por dívida, com `UNIQUE (kind, name)` e `account_id TEXT` sem chave estrangeira | a coluna fica, para os degraus que não são cartão; a de cartão esvazia |
| `app/debts/ladder.py:39-67` | `rebuild` apaga `debts`, reconstrói e preserva a taxa digitada por um mapa `(kind, name)` relido de `debts` | ganha a reconciliação dos cartões antes de reconstruir; o mapa não muda |
| `app/debts/ladder.py:70-90` | `_from_accounts` monta um degrau por conta com saldo negativo de tipo `BANK` ou `CREDIT`, com `monthly_rate_bp: None` | **nada**: o cartão continua nascendo sem taxa em `debts` |
| `app/debts/ladder.py:164-183` | `ladder` e `without_rate` filtram `debts.monthly_rate_bp` | passam a ler a taxa efetiva do degrau, que para cartão vem de `cards` |
| `app/debts/ladder.py:190-198` | `set_rate` escreve `debts.monthly_rate_bp` pelo id do degrau | passa a desviar o degrau de cartão para `cards` |
| `app/routers/debts.py:118-123` | `_debt` monta `SELECT * FROM debts WHERE id = ?` para a simulação | passa a chamar o leitor de degrau, com a taxa efetiva |
| `app/settings/typed.py:21-59` | `parse_money` lê `1.234,56`; `parse_rate` lê por cento ao mês e recusa fora de 0 a 100 | são reusados como estão; falta um leitor de dia do mês |
| `app/routers/settings.py:171-187` | `_context` monta a tela `/configuracao` | ganha uma chave |
| `app/templates/configuracao.html:76-85` | `<section id="metas">` fecha na linha 85, e `<section id="beneficiarios">` abre na 86 | um `{% include %}` entra entre as duas |

Quatro fatos decidem o desenho e não se re-discutem:

- **`accounts` é reescrita a cada carga** (`app/ingest/loader.py:136`, upsert por
  `id`), e por isso o que o dono informa não pode morar lá — é a decisão do
  `00-discovery.md`.
- **A sincronização chama `rebuild`** (`app/sync/__init__.py:101-104`, dentro de
  `_after`), então a reconciliação dos cartões pendurada em `rebuild` alcança
  toda conta de crédito que aparecer numa carga futura, sem que este item toque
  em `app/sync/`.
- **Três consumidores leem a escada sem saber de cartão:**
  `app/plan/timeline.py:58-66` (`expensive_debts`, o marco "dívidas caras
  zeradas"), `app/routers/plan.py:74-75` (`unrated`/`unrated_cents`) e
  `app/advisor/gaps.py:33` (o consultor para de perguntar a taxa do cartão
  quando não há degrau sem taxa). Os três passam a enxergar o cartão com taxa
  **sem serem tocados**, porque consomem `ladder()`/`without_rate()`.
- **`tests/test_plan.py:83` e `:127` inserem degrau `kind = 'card'` direto em
  `debts`, com taxa e sem `account_id`.** Não existe cartão para esses degraus, e
  eles pertencem a outro item; a leitura da taxa efetiva tem de continuar
  respondendo por eles.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| Como a escada lê a taxa de cartão sem quebrar degrau de cartão sem conta | `tests/test_plan.py:83` e `:127` inserem cartão sem `account_id` | `COALESCE(cards.monthly_rate_bp, debts.monthly_rate_bp)` num `LEFT JOIN` por `account_id`. Para o cartão real a casa é `cards`, porque `debts.monthly_rate_bp` nunca mais é escrita para ele; para o degrau sem conta a leitura cai na coluna antiga |
| O limite é positivo ou negativo | Invariante 22 rege **dinheiro que se move**; um teto não se move. `plan_facts` já guarda o saldo de quitação positivo (`tests/test_settings.py:23`, `SETTLEMENT_CENTS = 3500000`) | `limit_cents` positivo, em centavos inteiros |
| Campo vazio limpa ou é recusado | RF-01 diz que os quatro são opcionais; `parse_rate("")` já devolve `None` para limpar o degrau (`app/settings/typed.py:47-48`) | valor vazio **limpa** o campo, nos quatro |
| Onde mora o leitor de dia do mês | `app/settings/typed.py` é a gramática do item `015` e está fora do escopo desta rodada (item simultâneo) | `app/cards/typed.py`, que **importa** `parse_money`, `parse_rate` e `InvalidValueError` de `app/settings/typed.py` e só acrescenta o dia. Pendência registrada no fim |
| Onde mora o SQL de junção dos cartões | A norma 33 põe junção em `app/queries`, que está fora do escopo; `app/debts/ladder.py` e `app/debts/observed.py` já guardam o SQL do próprio domínio | `app/cards/store.py`, junto do domínio |
| A reconciliação apaga cartão de conta que sumiu | A carga é upsert por `id` e nunca apaga conta (`app/ingest/loader.py:136`) | `INSERT OR IGNORE`, só insere. Nunca atualiza, nunca apaga — é o que faz RF-03 e RF-08 valerem por construção |
| Cartão com saldo zero ou positivo | `_from_accounts` (`app/debts/ladder.py:73-77`) só monta degrau com `balance_cents < 0` | ganha entidade e campos editáveis, e **não** ganha degrau enquanto não dever nada. A taxa fica guardada para quando dever |
| Qual atributo marca o cartão no HTML | `tests/test_configuracao_screen.py:64` compara o conjunto de `data-config` da página com o catálogo do item `015`: um `data-config` a mais reprova | `data-cartao`, nunca `data-config` |
| Quem responde a recusa da escrita de cartão | `/configuracao` tem um único montador de contexto (`app/routers/settings.py:171`), e um segundo renderizaria a recusa numa tela sem a tabela de beneficiários e sem as metas | `app/routers/cards.py` importa `_answer` de `app.routers.settings`. Não há ciclo: `settings` importa `app.cards.store`, e `app.cards` não importa router nenhum |
| Linguagem visual da seção nova | `product/00-linguagem-visual.md` é canônico e o `017` já fixou os tokens de medida | a seção reusa a gramática de `app/templates/configuracao.html`; **nenhuma classe nova, nenhum token novo, nenhuma folha de estilo tocada** |
| Portão novo | Norma 20 e o `016` | nenhum: `scripts/gates/` não é tocado, e quem executa tudo o que este plano cria é `pytest`, que o CI já roda |

---

## Fase 1 — A entidade, e a casa única da taxa (api)

**Objetivo da fase:** existe a tabela `cards` com os quatro campos do dono, todo
cartão da base tem a sua linha, a escada lê a taxa de cartão de lá e o campo de
taxa de `/dividas` escreve lá — e nenhuma tela mudou.

**Critérios de aceite:**

- [ ] `estrutural` — RF-01
      Existe `app/migrations/sql/013_cards.sql`. Sobre uma base criada aplicando
      os arquivos de `app/migrations/sql/` por `app.migrations.runner.apply_migrations`,
      `PRAGMA table_info('cards')` devolve exatamente as colunas `account_id`,
      `limit_cents`, `monthly_rate_bp`, `closing_day` e `due_day`, nesta ordem,
      com `account_id` marcada como chave primária e as quatro restantes
      anuláveis; e `PRAGMA foreign_key_list('cards')` devolve uma linha apontando
      para a tabela `accounts`. Nenhuma outra migração da pasta cria tabela
      chamada `cards`
- [ ] `estrutural` — RF-01, RF-04
      `app/cards/catalog.py` exporta `FIELDS` com exatamente quatro entradas, de
      `name` igual a `limite`, `taxa`, `fechamento` e `vencimento`, nesta ordem,
      cada uma com as chaves `column`, `label` e `unit`, e as quatro `column`
      valendo `limit_cents`, `monthly_rate_bp`, `closing_day` e `due_day`
      respectivamente; os quatro `label` são `Limite`, `Taxa mensal`,
      `Dia do fechamento` e `Dia do vencimento`. `app/cards/store.py` exporta
      `reconcile`, `read` e `write`. `app/cards/typed.py` exporta `parse_day` e
      **importa** `parse_money` e `parse_rate` de `app.settings.typed`, sem
      redefinir nenhuma das duas
- [ ] `comportamental` — RF-02, RF-06
      *Dado* um banco em diretório temporário com as migrações de versão menor
      que `013` aplicadas, duas contas inseridas em `accounts` —
      `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)` e
      `('acc-corrente', 'Conta corrente', 'BANK', -100000)` — e uma linha em
      `debts` com `kind = 'card'`, `name = 'Cartão Azul'`,
      `account_id = 'acc-cartao-1'` e `monthly_rate_bp = 900`
      *Quando* a pasta inteira de migrações é aplicada, o que aplica
      `013_cards.sql` sobre essa base já povoada
      *Então* `SELECT account_id, monthly_rate_bp FROM cards` devolve exatamente
      uma linha, `('acc-cartao-1', 900)` — a conta de crédito ganhou cartão e a
      taxa que o dono já tinha digitado veio junto —; e
      `SELECT monthly_rate_bp FROM debts WHERE name = 'Cartão Azul'` devolve
      `None`, porque a taxa de cartão passou a ter uma casa só. A conta de tipo
      `BANK` **não** produz linha em `cards`. A migração é exercida sobre base
      com linha, e não sobre base vazia, porque é a base do dono que já tem
      conta e degrau
- [ ] `comportamental` — RF-02, RF-03, RF-08
      *Dado* um banco em diretório temporário com todas as migrações aplicadas,
      a variável `DASH_MANUAL_DIR` apontando para uma pasta inexistente (sem ela
      os contratos de `data/manual/` entram na escada e a contagem deixa de ser
      só das contas), uma conta `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)`,
      e `app.debts.ladder.rebuild` já executada uma vez, seguida da escrita dos
      quatro campos do cartão `acc-cartao-1` com os valores `12.000,00`, `12,5`,
      `3` e `10`
      *Quando* uma segunda conta de crédito
      `('acc-cartao-2', 'Cartão Roxo', 'CREDIT', -32100)` é inserida em
      `accounts` — o que uma carga posterior faz — e `app.debts.ladder.rebuild`
      é executada de novo
      *Então* `SELECT account_id FROM cards ORDER BY account_id` devolve
      `acc-cartao-1` e `acc-cartao-2`, e
      `SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards
      WHERE account_id = 'acc-cartao-1'` devolve `(1200000, 1250, 3, 10)` —
      os quatro campos atravessaram a reconstrução inteiros, e a linha do cartão
      novo nasceu com os quatro nulos
- [ ] `comportamental` — RF-06, RF-07
      *Dado* o mesmo banco em diretório temporário, com `DASH_MANUAL_DIR`
      apontando para pasta inexistente, as contas
      `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)` e
      `('acc-corrente', 'Conta corrente', 'BANK', -100000)`, `rebuild` já
      executada, e a taxa `3,52` gravada no degrau da conta corrente
      *Quando* a taxa do cartão `acc-cartao-1` é escrita como `12,5` e
      `app.debts.ladder.ladder` e `app.debts.ladder.without_rate` são lidas; e
      depois a taxa do mesmo cartão é escrita como string vazia e as duas são
      lidas de novo
      *Então* na primeira leitura `ladder` devolve dois degraus, o primeiro com
      `name` igual a `Cartão Azul` e `monthly_rate_bp` igual a `1250` e o
      segundo com `352` — o cartão entra na escada acima do cheque especial,
      pela taxa —, e `without_rate` não traz nenhum degrau de `kind` igual a
      `card`; na segunda leitura `ladder` devolve um degrau só, o da conta
      corrente, e `without_rate` traz o `Cartão Azul` de volta
- [ ] `comportamental` — RF-06, RF-07
      *Dado* o painel servido a partir deste repositório com sessão autenticada,
      sobre banco em diretório temporário com `DASH_MANUAL_DIR` apontando para
      pasta inexistente, uma conta `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)`
      e `app.debts.ladder.rebuild` já executada, e `IDENTIFICADOR` sendo o valor
      de `SELECT id FROM debts WHERE kind = 'card'`
      *Quando* `POST /dividas/taxa` é enviada com `degrau=IDENTIFICADOR` e
      `taxa=12,5`, e em seguida `GET /dividas` e
      `POST /dividas/simular` com `degrau=IDENTIFICADOR` e `aporte=1.000,00`
      *Então* a primeira responde `200`;
      `SELECT monthly_rate_bp FROM cards WHERE account_id = 'acc-cartao-1'`
      devolve `1250` e `SELECT monthly_rate_bp FROM debts WHERE id = IDENTIFICADOR`
      devolve `None` — a escrita foi para a casa única, e não para as duas; o
      HTML de `GET /dividas` contém `data-taxa="1250"` dentro do trecho que vai
      de `id="escada"` até o `</section>` seguinte, e **não** contém
      `data-degrau="IDENTIFICADOR"` no trecho que vai de `id="sem-taxa"` até o
      `</section>` seguinte; e a resposta da simulação é `200` e **não** contém
      a frase `Informe a taxa primeiro.`, que é o que a tela responde hoje para
      qualquer cartão
- [ ] `comportamental` — RF-07
      *Dado* um banco em diretório temporário com todas as migrações aplicadas,
      `DASH_MANUAL_DIR` apontando para uma pasta que contém
      `cdc_safra_veiculo.json` com `{"prazo_meses": 60,
      "juros_efetivo_mensal_pct": 1.63, "valor_parcela": 1235.33,
      "primeiro_vencimento": "2025-06-11"}`, e uma conta
      `('acc-corrente', 'Conta corrente', 'BANK', -100000)`
      *Quando* `app.debts.ladder.rebuild` é executada com `today` igual a
      `date(2026, 9, 5)`, a taxa `3,52` é gravada no degrau da conta corrente, e
      `rebuild` é executada de novo com a mesma data
      *Então* `app.debts.ladder.ladder` devolve dois degraus: o da conta
      corrente com `monthly_rate_bp` igual a `352` — a taxa digitada sobreviveu
      à reconstrução, pelo caminho que ela já usava — e o do veículo com
      `monthly_rate_bp` igual a `163`, `term_months` igual a `45` e
      `balance_cents` igual a `-3917636`. Nenhum degrau que não é cartão muda de
      valor por causa desta fase
- [ ] `comportamental` — RF-04, RF-05
      *Dado* um banco em diretório temporário com todas as migrações aplicadas e
      uma conta `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)` com a
      linha correspondente em `cards`
      *Quando* os quatro campos são escritos com `12.000,00`, `12,5`, `3` e
      `10`, e depois cada um é escrito de novo com um valor fora da gramática —
      `5000.00` no limite, `200` na taxa, `32` no fechamento e `3,5` no
      vencimento
      *Então* a primeira escrita deixa
      `SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards`
      igual a `(1200000, 1250, 3, 10)`; cada uma das quatro seguintes levanta
      `app.settings.typed.InvalidValueError`, com a mensagem contendo o valor
      digitado e, respectivamente, as frases `Escreva na forma 1.234,56`,
      `Use de 0 a 100% ao mês`, `Use um dia do mês, de 1 a 31` e
      `Use um dia do mês, de 1 a 31`; e a leitura da tabela depois das quatro
      recusas devolve de novo `(1200000, 1250, 3, 10)` — nenhuma recusa gravou.
      A restrição `CHECK` do esquema é exercida à parte, inserindo
      `closing_day = 32` por SQL cru e afirmando que o SQLite levanta
      `sqlite3.IntegrityError`: sem isso a restrição poderia estar ausente e o
      teste do leitor passaria assim mesmo
- [ ] `comando` — RF-01 a RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_cards.py tests/test_debts.py tests/test_migrations.py
      tests/test_plan.py` sai com código `0`. `tests/test_cards.py` é novo e
      traz a migração sobre base povoada, a reconciliação na reconstrução, a
      leitura da escada, a gramática dos quatro campos e a recusa da restrição
      `CHECK`. `tests/test_migrations.py` tem `013_cards.sql` em
      `EXPECTED_MIGRATIONS` e `cards` em `EXPECTED_TABLES`. E as funções
      `test_a_rate_typed_by_the_owner_survives_the_reload` e
      `test_the_vehicle_step_is_built_by_the_loader_and_not_by_the_test`
      continuam existindo em `tests/test_debts.py`, e
      `test_the_mortgage_never_enters_the_expensive_ladder` e
      `test_a_month_that_goes_entirely_to_the_debt_does_not_feed_the_reserve` em
      `tests/test_plan.py`, com esses mesmos nomes: são elas que afirmam a
      escada de hoje, e apagar uma delas faria o comando sair `0` sem provar
      nada

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Criar `app/migrations/sql/013_cards.sql`: a tabela e a mudança da
      taxa de casa.**
      Três comandos, nesta ordem:
      ```sql
      CREATE TABLE cards (
          account_id TEXT PRIMARY KEY REFERENCES accounts(id),
          limit_cents INTEGER,
          monthly_rate_bp INTEGER,
          closing_day INTEGER,
          due_day INTEGER,
          CHECK (closing_day IS NULL OR closing_day BETWEEN 1 AND 31),
          CHECK (due_day IS NULL OR due_day BETWEEN 1 AND 31)
      );

      INSERT INTO cards (account_id, monthly_rate_bp)
      SELECT a.id,
             (SELECT MAX(d.monthly_rate_bp) FROM debts d
               WHERE d.kind = 'card' AND d.account_id = a.id)
        FROM accounts a WHERE a.type = 'CREDIT';

      UPDATE debts SET monthly_rate_bp = NULL
       WHERE kind = 'card' AND account_id IS NOT NULL;
      ```
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-01, RF-02, RF-06. O número `013` é o único que este
      item pode usar: `012`, `014` e `015` estão reservados a itens
      simultâneos. A tabela é separada de `accounts` porque `accounts` é upsert
      da fonte a cada carga (`app/ingest/loader.py:136`) e coluna do dono ali
      seria apagada em silêncio. O `UPDATE` final é o que faz a taxa ter **uma**
      casa em vez de duas, e ele é restrito a `account_id IS NOT NULL` porque
      degrau de cartão sem conta não teve para onde mudar — anular a taxa dele
      perderia o valor. `MAX(...)` porque um subselect sem agregação escolheria
      uma linha qualquer se houvesse duas, e a determinação do valor não pode
      depender da ordem física da tabela. Os dois `CHECK` são a segunda barreira
      do dia do mês: o leitor de 1.3 recusa o que vem da tela, e o `CHECK`
      recusa o que vier por qualquer outro caminho.

- [ ] **1.2 — Criar `app/cards/catalog.py`: os quatro campos, com nome, coluna,
      rótulo e unidade.**
      Método:
      ```python
      LIMIT = "limite"
      RATE = "taxa"
      CLOSING = "fechamento"
      DUE = "vencimento"
      DAY = "dia"

      FIELDS = (
          {"name": LIMIT, "column": "limit_cents", "label": "Limite", "unit": CENTS, ...},
          {"name": RATE, "column": "monthly_rate_bp", "label": "Taxa mensal", "unit": BASIS_POINTS, ...},
          {"name": CLOSING, "column": "closing_day", "label": "Dia do fechamento", "unit": DAY, ...},
          {"name": DUE, "column": "due_day", "label": "Dia do vencimento", "unit": DAY, ...},
      )
      BY_NAME = {item["name"]: item for item in FIELDS}
      ```
      `CENTS` e `BASIS_POINTS` são importados de `app.settings.catalog`; `DAY` é
      novo e nasce aqui. Cada entrada traz também o texto de ajuda que a tela
      imprime.
      *Considerando 1.1:* as quatro colunas são as da tabela recém-criada.
      *Justificativa:* RF-01, RF-04. O catálogo é o que permite uma rota só para
      os quatro campos, com o mesmo formato de recusa por nome que
      `app/settings/store.py:58-68` já usa; sem ele seriam quatro rotas ou um
      `if` de quatro braços dentro do router, que a norma 30 não quer lá. O
      rótulo concorda em gênero com a frase que o leitor monta:
      `app/settings/typed.py:29` escreve `{field} inválido` e `:52` escreve
      `{field} inválida`, então `Limite` e `Dia do…` são masculinos e
      `Taxa mensal` é feminina — trocar o rótulo por um de outro gênero produz
      "Taxa mensal inválido" na tela.

- [ ] **1.3 — Criar `app/cards/typed.py`: o dia do mês, e o despacho por
      unidade.**
      Método:
      ```python
      MIN_DAY = 1
      MAX_DAY = 31

      def parse_day(typed: str, field: str = "Dia") -> int | None
      def parse(unit: str, typed: str, field: str) -> int | None
      ```
      `parse_day` devolve `None` para vazio, recusa o que não é inteiro e o que
      cai fora de 1 a 31 com `InvalidValueError` dizendo
      `{field} inválido: “{typed}”. Use um dia do mês, de 1 a 31.`; `parse`
      devolve `None` para vazio antes de despachar, e despacha `CENTS` para
      `parse_money`, `BASIS_POINTS` para `parse_rate` e `DAY` para `parse_day`.
      *Considerando 1.2:* a unidade vem da entrada do catálogo.
      *Justificativa:* RF-01, RF-04, RF-05. Dinheiro e taxa **não** ganham
      leitor novo: são os do item `015`, importados de `app/settings/typed.py`,
      porque duas gramáticas para o mesmo campo é o defeito que aquele item
      fechou. O vazio é interceptado antes do despacho porque `parse_money`
      recusa vazio (`app/settings/typed.py:38`, o valor precisa ser maior que
      zero) e aqui os quatro campos são opcionais por RF-01 — sem essa
      interceptação o dono não conseguiria apagar um limite digitado errado.

- [ ] **1.4 — Criar `app/cards/store.py`: reconciliar, ler e escrever.**
      Método:
      ```python
      def reconcile(conn: sqlite3.Connection) -> int
      def read(conn: sqlite3.Connection) -> list[dict]
      def write(conn: sqlite3.Connection, account_id: str, field: str, typed: str) -> int | None
      ```
      `reconcile` roda
      `INSERT OR IGNORE INTO cards (account_id) SELECT id FROM accounts WHERE type = ?`
      com `CREDIT` de `app.accounts`, e **não** dá commit. `read` junta `cards`
      com `accounts` por `account_id` e devolve, por cartão, o identificador, o
      nome, a instituição, o saldo e a lista dos quatro campos na ordem do
      catálogo, cada um com `name`, `label`, `unit` e `value`. `write` resolve a
      entrada pelo catálogo — nome desconhecido levanta `InvalidValueError`
      nomeando o que foi pedido —, lê o valor pela unidade e grava com
      `INSERT INTO cards (account_id, <coluna>) VALUES (?, ?)
      ON CONFLICT(account_id) DO UPDATE SET <coluna> = excluded.<coluna>`,
      seguido de `conn.commit()`.
      *Considerando 1.2 e 1.3.*
      *Justificativa:* RF-01 a RF-05, RF-08. `INSERT OR IGNORE` é o que faz RF-03
      e RF-08 valerem por construção: a reconciliação só cria, nunca atualiza e
      nunca apaga, então nenhuma carga e nenhuma reconstrução alcança o que o
      dono digitou. O `ON CONFLICT` na escrita existe porque o cartão pode ser
      escrito antes de a reconciliação ter passado por ele, e um `UPDATE` que
      não acerta linha nenhuma devolveria `200` sobre uma tela que recarrega
      como se tivesse salvo — o mesmo defeito que
      `app/debts/ladder.py:190-198` já comenta. O nome da coluna vem do
      catálogo, nunca do pedido: a string do formulário não chega ao texto do
      SQL. O commit é aqui e não no router, pela norma 30. Comentário novo neste
      arquivo carrega marca de justificativa (`motivo:`, `decisão:`,
      `invariante:`), que é o que `scripts/gates/gate3_no_comments.sh` aceita em
      arquivo sem dívida tolerada.

- [ ] **1.5 — Modificar `app/debts/ladder.py`: a escada passa a ler a taxa de
      cartão de `cards`, e `set_rate` a escrever lá.**
      Quatro mudanças, e nenhuma outra:
      `rebuild` ganha `reconcile(conn)` como primeira instrução, antes da
      releitura do mapa de taxas — o commit continua sendo o do fim da função;
      `_COLUMNS` vira a fonte do degrau com a taxa efetiva,
      ```python
      _STEPS = (
          "SELECT d.id, d.kind, d.name, d.balance_cents, "
          "COALESCE(c.monthly_rate_bp, d.monthly_rate_bp) AS monthly_rate_bp, "
          "d.term_months, d.payment_cents, d.source, d.account_id "
          "FROM debts d LEFT JOIN cards c ON c.account_id = d.account_id"
      )
      ```
      e `ladder` e `without_rate` passam a `SELECT * FROM ({_STEPS})` com o
      mesmo filtro e a mesma ordenação de hoje; nasce
      `def step(conn: sqlite3.Connection, debt_id: int) -> dict | None`, lendo
      da mesma fonte por `id`; e `set_rate` passa a ler `kind` e `account_id` do
      degrau antes de escrever — degrau ausente continua levantando
      `DebtNotFoundError`, degrau de `kind` igual a `CARD` com `account_id`
      preenchido chama `store.write(conn, account_id, RATE, typed)`, e todo o
      resto segue no `UPDATE debts` de hoje.
      **Não são tocados:** `_from_accounts`, `_from_contracts`, `_mortgage`,
      `_vehicle`, `_paid`, `_read`, `_cents`, `manual_dir`,
      `monthly_interest_cents` e `main`.
      *Considerando 1.4.*
      *Justificativa:* RF-02, RF-03, RF-06, RF-07, RF-08. A reconciliação mora
      em `rebuild` e não em `_from_accounts` porque `_from_accounts` só olha
      conta com saldo negativo (`app/debts/ladder.py:75`) e RF-02 pede **toda**
      conta de crédito, inclusive a que não deve nada; e porque `rebuild` é o
      que a sincronização chama (`app/sync/__init__.py:104`), o que faz a conta
      de crédito nova ganhar cartão sem este item tocar em `app/sync/`. O mapa
      de preservação por `(kind, name)` (`app/debts/ladder.py:42-45`) **não
      muda**: com `debts.monthly_rate_bp` nula para cartão, ele devolve nulo
      para cartão e continua devolvendo a taxa digitada do cheque especial, que
      é o comportamento que RF-07 manda não mexer. O `COALESCE` existe por um
      caso medido: `tests/test_plan.py:83` e `:127` inserem degrau de cartão sem
      `account_id`, e uma leitura que só olhasse `cards` apagaria a taxa deles e
      quebraria dois testes de outro item. `step` nasce para o router parar de
      montar `SELECT` (norma 30) e, sem ele, a simulação de `/dividas` recusaria
      um cartão que tem taxa, dizendo "Informe a taxa primeiro"
      (`app/debts/simulate.py:14`).

- [ ] **1.6 — Modificar `app/routers/debts.py`: a simulação lê o degrau pelo
      leitor.**
      `_debt` (linhas 118-123) deixa de montar
      `SELECT * FROM debts WHERE id = ?` e passa a chamar `step(conn, ...)`,
      mantendo `_identifier` e a devolução de `None` para degrau inexistente. O
      import de `app.debts.ladder` ganha `step`.
      *Considerando 1.5.*
      *Justificativa:* RF-06, RF-07, norma 30. Sem esta etapa a taxa aparece na
      escada e some na simulação, porque as duas leituras passariam a ter fontes
      diferentes — que é exatamente o defeito de duas casas, de volta pela porta
      dos fundos.

- [ ] **1.7 — Criar `tests/test_cards.py` e ajustar
      `tests/test_migrations.py`.**
      `tests/test_cards.py`: a migração sobre base povoada, no molde de
      `tests/test_settings.py:30-47` (copiar para uma pasta temporária só os
      `.sql` de versão menor que `013`, aplicar, inserir conta e degrau,
      aplicar a pasta cheia); a reconciliação criando o cartão da conta nova e
      preservando os quatro campos da antiga; a escada com e sem taxa; o
      desvio de `set_rate`; a gramática dos quatro campos e as quatro recusas;
      a `CHECK` do dia recusando `32` por SQL cru; e os dois percursos por
      `fastapi.testclient.TestClient` sobre `/dividas`. Em
      `tests/test_migrations.py`, `013_cards.sql` entra em `EXPECTED_MIGRATIONS`
      na posição numérica, `cards` entra em `EXPECTED_TABLES` em ordem
      alfabética (entre `advisor_questions` e `categories`), e a asserção de
      `max(version)` (linha 71) passa a comparar com
      `EXPECTED_MIGRATIONS[-1].split("_")[0]` em vez do literal `"011"`.
      *Considerando 1.1 a 1.6.* Quem executa é `pytest`, que o CI já roda:
      nenhum portão novo entra em `scripts/gates/` e o `gates_runner.sh` não é
      tocado.
      *Justificativa:* RF-01 a RF-08. A migração é exercida sobre base com linha
      porque é a base do dono que tem conta e degrau, e o caso vazio provaria
      só que o `CREATE TABLE` roda. A `CHECK` é uma restrição verificável, e
      restrição sem teste que a veja recusar é restrição que pode ter sido
      escrita errada e ninguém saber. O literal `"011"` vira derivação da lista
      porque quatro itens simultâneos acrescentam migração ao mesmo arquivo, e
      um literal a mais é um conflito de merge a mais para cada um deles.

---

## Fase 2 — A seção de cartões em `/configuracao` (api)

**Objetivo da fase:** `/configuracao` mostra um bloco por cartão da base, com os
quatro campos editáveis, e a taxa digitada ali é a mesma que a escada de
`/dividas` usa.

**Linguagem visual.** A seção segue `product/00-linguagem-visual.md`, canônico, e
os tokens de medida do item `017` em `app/static/css/tokens.css`. Ela reusa a
gramática que `app/templates/configuracao.html` já tem — painel largo, título de
seção, `lede`, bloco `setting` com o que é à esquerda e o valor à direita, campo
com rótulo em versalete e botão discreto —, e **não** cria classe, token, folha
de estilo nem elemento de assinatura. A tentação a recusar é desenhar o cartão
como um cartão de banco, com retângulo arredondado e bandeira: o documento diz
que o produto é um instrumento graduado e não um app de banco, que a escala é o
único ornamento e que ela só aparece onde há distância a percorrer — e aqui não
há distância nenhuma, só quatro números que o dono informa. A cifra usa a classe
de algarismo tabular que as outras telas usam; o estado vazio é convite, com o
que fazer escrito.

**Critérios de aceite:**

- [ ] `estrutural` — RF-04
      `app/routers/cards.py` define `router` e registra um `POST` no caminho
      `/configuracao/cartao`; `app/cards/catalog.py` exporta `ACTION` valendo
      `/configuracao/cartao`; `app/main.py` chama
      `app.include_router(cards.router)`; e `app/templates/configuracao.html`
      contém a linha `{% include "fragments/configuracao_cartoes.html" %}`
      exatamente uma vez, depois do `</section>` que fecha a seção de `id`
      igual a `metas` e antes da abertura da seção de `id` igual a
      `beneficiarios`
- [ ] `comportamental` — RF-01, RF-02, RF-04
      *Dado* o painel servido a partir deste repositório com sessão autenticada,
      sobre banco em diretório temporário com as contas
      `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)`,
      `('acc-cartao-2', 'Cartão Roxo', 'CREDIT', -32100)` e
      `('acc-corrente', 'Conta corrente', 'BANK', -100000)`, e
      `app.debts.ladder.rebuild` já executada
      *Quando* `GET /configuracao` é buscada
      *Então* a resposta é `200`, o HTML traz `id="cartoes"` exatamente uma vez,
      contém `data-cartao="acc-cartao-1"` e `data-cartao="acc-cartao-2"` e
      **não** contém `data-cartao="acc-corrente"`; traz os oito atributos
      `data-campo="limite"`, `data-campo="taxa"`, `data-campo="fechamento"` e
      `data-campo="vencimento"` (quatro por cartão); os oito campos vêm com
      `data-valor=""`, porque nada foi informado; e a página continua trazendo
      `id="fatos"`, `id="metas"` e `id="beneficiarios"` uma vez cada.
      *E quando* a mesma requisição é feita sobre uma base cujo único registro
      em `accounts` é a conta de tipo `BANK`, *então* a resposta é `200`, o HTML
      traz `id="cartoes"` e, dentro dele, `class="empty"` com a frase
      `Nenhum cartão na base.` — a seção vazia diz o que fazer em vez de sumir
- [ ] `comportamental` — RF-01, RF-04
      *Dado* o painel servido com sessão autenticada sobre banco em diretório
      temporário com a conta
      `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)` e
      `app.debts.ladder.rebuild` já executada
      *Quando* quatro `POST /configuracao/cartao` são enviados, todos com
      `cartao=acc-cartao-1`, e com os pares
      (`campo=limite`, `valor=12.000,00`), (`campo=taxa`, `valor=12,5`),
      (`campo=fechamento`, `valor=3`) e (`campo=vencimento`, `valor=10`)
      *Então* as quatro respostas são `200` e trazem a palavra `Salvo.`;
      `SELECT limit_cents, monthly_rate_bp, closing_day, due_day FROM cards
      WHERE account_id = 'acc-cartao-1'` devolve `(1200000, 1250, 3, 10)`; e o
      HTML da quarta resposta contém `data-campo="limite" data-valor="1200000"`,
      `data-campo="taxa" data-valor="1250"`,
      `data-campo="fechamento" data-valor="3"`,
      `data-campo="vencimento" data-valor="10"`, e as cifras `R$ 12.000,00` e
      `12,50%`
- [ ] `comportamental` — RF-05
      *Dado* o painel servido com sessão autenticada sobre banco em diretório
      temporário com a conta
      `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)` e
      `app.debts.ladder.rebuild` já executada
      *Quando* `POST /configuracao/cartao` é enviada com
      `cartao=acc-cartao-1`, `campo=limite` e `valor=5000.00`, e depois com
      `cartao=acc-cartao-1`, `campo=fechamento` e `valor=32`
      *Então* as duas respostas são `400` — nunca `500` —, as duas contêm
      `id="recusa"`, a primeira contém `5000.00` e a frase
      `Escreva na forma 1.234,56`, a segunda contém `32` e a frase
      `Use um dia do mês, de 1 a 31`, as duas continuam trazendo `id="metas"` e
      `id="beneficiarios"` (a tela responde de pé, com a seção inteira), e
      `SELECT limit_cents, closing_day FROM cards WHERE account_id = 'acc-cartao-1'`
      devolve `(None, None)`
- [ ] `comportamental` — RF-05
      *Dado* o mesmo painel, com a mesma base e a mesma sessão
      *Quando* `POST /configuracao/cartao` é enviada com
      `cartao=acc-inexistente`, `campo=limite` e `valor=12.000,00`, e depois com
      `cartao=acc-cartao-1`, `campo=bandeira` e `valor=roxo`
      *Então* as duas respostas são `400`, as duas contêm `id="recusa"`, a
      primeira nomeia `acc-inexistente` e a segunda nomeia `bandeira`, e
      `SELECT COUNT(*) FROM cards WHERE limit_cents IS NOT NULL` devolve `0`
- [ ] `comportamental` — RF-06
      *Dado* o painel servido com sessão autenticada sobre banco em diretório
      temporário com `DASH_MANUAL_DIR` apontando para pasta inexistente, a conta
      `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)` e
      `app.debts.ladder.rebuild` já executada, e `IDENTIFICADOR` sendo o valor
      de `SELECT id FROM debts WHERE kind = 'card'`
      *Quando* `POST /configuracao/cartao` grava `cartao=acc-cartao-1`,
      `campo=taxa`, `valor=12,5`, e em seguida `GET /dividas` é buscada; e
      depois `POST /dividas/taxa` grava `degrau=IDENTIFICADOR`, `taxa=9`, e
      `GET /configuracao` é buscada
      *Então* o HTML de `GET /dividas` contém `data-taxa="1250"` no trecho que
      vai de `id="escada"` até o `</section>` seguinte, e o HTML de
      `GET /configuracao` contém `data-campo="taxa" data-valor="900"` — a mesma
      taxa atravessa as duas telas nos dois sentidos porque só existe uma casa.
      Hoje as duas telas não têm como discordar, porque uma delas não existe
- [ ] `estrutural` — RF-04
      `app/templates/fragments/configuracao_cartoes.html` não contém a sequência
      `<style`, nem a sequência `style=`, nem nenhum literal de cor começando
      por `#` seguido de três ou seis dígitos hexadecimais; e cada nome que ele
      usa em atributo `class` — entre eles `panel`, `panel-wide`,
      `section-title`, `lede`, `settings`, `setting`, `setting-what`,
      `setting-name`, `setting-value`, `setting-figure`, `setting-absent`,
      `form`, `field`, `field-label`, `field-input`, `button`, `button-quiet`,
      `button-small`, `eyebrow`, `stack-tight`, `sr-only`, `empty`,
      `empty-title` e `cifra` — aparece como seletor de classe em
      `app/static/css/app.css` ou em `app/static/css/tokens.css`. Nenhum dos
      dois arquivos de estilo ganha regra nova
- [ ] `comando` — RF-01, RF-02, RF-04, RF-05, RF-06
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_cartoes_screen.py tests/test_configuracao_screen.py
      tests/test_route_guard.py` sai com código `0`.
      `tests/test_cartoes_screen.py` é novo e traz a listagem por conta de
      crédito, a seção vazia, a escrita dos quatro campos, as duas recusas de
      gramática, as duas recusas de nome desconhecido e a ida e volta da taxa
      entre `/configuracao` e `/dividas`. E as funções
      `test_the_screen_lists_the_catalogue_in_two_blocks`, em
      `tests/test_configuracao_screen.py`, e
      `test_every_registered_route_requires_session`, em
      `tests/test_route_guard.py`, continuam existindo com esses mesmos nomes: a
      primeira compara o conjunto de `data-config` da página com o catálogo do
      item `015` e a segunda exige sessão de toda rota registrada — são
      exatamente o que a seção nova pode quebrar, e apagar uma delas faria o
      comando sair `0` sem provar nada

- [ ] `estrutural` — RF-04
      `app/settings/catalog.py` já não diz que a taxa mensal dos cartões "é um
      campo por dívida na tela de dívidas, e não uma linha aqui": o texto de
      `help` da entrada `taxa-cartao` nomeia as duas telas em que o campo existe
      e diz que as duas escrevem no mesmo lugar. O arquivo continua exportando
      `CATALOG` com o mesmo número de entradas de antes e `CARD_RATE` com o mesmo
      valor — a frase muda, a estrutura do catálogo não

**Critérios de integração** — nenhum deles se verifica com uma fase só: a fase 1
não tem tela que grave, e a fase 2 não tem onde gravar sem a casa que a fase 1
cria.

- [ ] `comportamental` — RF-06, RF-07
      *Dado* um banco em diretório temporário com **todas** as migrações
      aplicadas em sequência, `DASH_MANUAL_DIR` apontando para pasta
      inexistente, as contas `('acc-cartao-1', 'Cartão Azul', 'CREDIT', -1674462)`
      e `('acc-corrente', 'Conta corrente', 'BANK', -100000)`,
      `app.debts.ladder.rebuild` já executada, a taxa `3,52` gravada no degrau
      da conta corrente, e o painel servido com sessão autenticada
      *Quando* `GET /dividas` é lida; depois `POST /configuracao/cartao` grava a
      taxa `12,5` no cartão `acc-cartao-1`; e `GET /dividas` é lida de novo
      *Então* na primeira leitura `app.debts.ladder.without_rate` traz **um**
      degrau, o do cartão, e `app.debts.ladder.ladder` traz **um**, o da conta
      corrente; e na segunda `without_rate` traz **zero** degraus e `ladder` traz
      **dois**, com o cartão à frente pela taxa. O que se prova é a costura: a
      escrita entrou pela tela da fase 2 e saiu pela leitura que a fase 1 mudou
- [ ] `comportamental` — RF-06
      *Dado* o mesmo banco e o mesmo painel
      *Quando* `app.advisor.gaps` é consultada sobre qual fato ausente mais move
      a projeção **antes** de qualquer gravação; depois
      `POST /configuracao/cartao` grava a taxa `12,5` no cartão; e ela é
      consultada de novo
      *Então* na primeira consulta a taxa do cartão **está** entre os fatos
      perguntados, e na segunda **não** está. As duas leituras juntas são o
      critério: a primeira prova que a pergunta existe e que a consulta alcança
      alguma coisa, e só por isso a ausência na segunda significa "respondida"
      em vez de "nunca houve"

- [ ] `estrutural` — RF-06
      `app/advisor/gaps.py` continua exportando o mesmo símbolo público que
      exporta hoje, e o arquivo **não** é tocado por este item: a pergunta some
      porque a escada deixou de ter degrau sem taxa, não porque alguém apagou a
      pergunta

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **2.1 — Acrescentar `ACTION` a `app/cards/catalog.py` e `screen` a
      `app/cards/store.py`.**
      `ACTION = "/configuracao/cartao"` no catálogo, e
      `def screen(conn: sqlite3.Connection) -> dict` devolvendo
      `{"action": ACTION, "cards": read(conn)}`.
      *Considerando:* a leitura e o catálogo da fase anterior.
      *Justificativa:* RF-04. O caminho mora no catálogo, e não no router, pelo
      mesmo motivo que `app/settings/catalog.py:22-24` guarda `DEBTS_SCREEN`,
      `SIMULATOR_SCREEN` e `SETTINGS_SCREEN`: a tela precisa do endereço da ação
      e o router precisa do endereço da rota, e um literal repetido nos dois é
      um formulário que posta para lugar nenhum na primeira renomeação. É
      também o que evita o ciclo de import — `app/routers/settings.py` importa
      de `app.cards`, e `app/routers/cards.py` importa de `app.routers.settings`.

- [ ] **2.2 — Criar `app/routers/cards.py`: uma rota, quatro campos.**
      Método:
      ```python
      @router.post(ACTION)
      def store_field(
          request: Request,
          cartao: Annotated[str, Form()] = "",
          campo: Annotated[str, Form()] = "",
          valor: Annotated[str, Form()] = "",
      ) -> Response
      ```
      Abre a conexão, chama `store.write`, devolve
      `_answer(request, conn, done=SAVED)` em caso de escrita e
      `_answer(request, conn, notice=str(refusal), status_code=400)` quando
      `InvalidValueError` sobe — `_answer` e `SAVED` importados de
      `app.routers.settings`. Cartão que não existe em `cards` é recusado por
      `store.write`, nomeando o identificador pedido.
      *Considerando 2.1.*
      *Justificativa:* RF-04, RF-05, normas 29 e 30. Uma rota e não quatro
      porque o catálogo já diz qual campo é qual, e quatro rotas seriam quatro
      lugares para o mesmo tratamento de recusa. O router não monta consulta nem
      dá commit: quem grava é `app/cards/store.py`. Reusar `_answer` é o que
      mantém a recusa **com a tela inteira de pé** — um render próprio
      devolveria `/configuracao` sem fatos, sem metas e sem beneficiários, que é
      a tela caindo com outro nome. O arquivo não pode conter a expressão
      `date.today()`: `tests/test_route_guard.py:75-79` varre `app/routers/`
      atrás dela e reprova nomeando o arquivo.

- [ ] **2.3 — Criar `app/templates/fragments/configuracao_cartoes.html`.**
      `<section id="cartoes" class="panel panel-wide">`, título `Cartões`, uma
      `lede` dizendo que os quatro campos são o que a fonte não manda e que a
      taxa é o que põe o cartão na escada de dívida, e um `article` por cartão
      com `data-cartao="{{ card['account_id'] }}"`, o nome e a instituição à
      esquerda e os quatro campos à direita. Cada campo é um `form` que posta
      `cartao` (oculto), `valor` e `campo` (no `name`/`value` do botão, como
      `app/templates/configuracao.html:33-34` já faz), envolto num elemento com
      `data-campo="{{ field['name'] }}" data-valor="{{ field['value'] if field['value'] is not none else '' }}"`,
      nesta ordem. O valor formatado sai por `{{ field['value']|unidade(field['unit']) }}`
      e o valor do campo por `{{ field['value']|digitado(field['unit']) }}`;
      campo sem valor imprime `Ausente`. Sem cartão, um bloco `empty` com
      `Nenhum cartão na base.` e a frase que diz que os cartões nascem das
      contas de crédito na sincronização seguinte.
      *Considerando 2.1 e 2.2.*
      *Justificativa:* RF-01, RF-02, RF-04, normas 16 e 27. O atributo é
      `data-cartao` e nunca `data-config`, porque
      `tests/test_configuracao_screen.py:64` compara o conjunto de `data-config`
      da página com o catálogo do item `015` e um a mais reprova. O fragmento
      **não** usa a macro `setting` de `app/templates/configuracao.html:4-50`: a
      macro fala de `moves`, `help`, `stored` e `screen`, que o campo de cartão
      não tem, e macro de template incluído é dependência que se descobre
      quebrada só na renderização. Os dois filtros `unidade` e `digitado`
      (`app/routers/render.py:53-80`) já devolvem o inteiro cru para unidade que
      não conhecem, então o dia atravessa os dois sem que
      `app/routers/render.py` seja tocado, e o rótulo é quem diz que aquilo é um
      dia.

- [ ] **2.4 — Modificar `app/routers/settings.py` e
      `app/templates/configuracao.html`: uma chave e um include.**
      Em `_context` (linhas 171-187), a chave `"cards": screen(conn)`. Em
      `configuracao.html`, a linha
      `{% include "fragments/configuracao_cartoes.html" %}` imediatamente depois
      do `</section>` da linha 85, que fecha a seção de `id` igual a `metas`.
      *Considerando 2.1 e 2.3.*
      *Justificativa:* RF-04. A seção entra depois das metas e antes dos
      beneficiários porque a ordem da tela é a ordem de quanto a resposta move o
      número (`app/settings/catalog.py:26-28`), e a taxa do cartão decide a
      ordem da escada de dívida — fica junto do que decide, e não no fim, atrás
      de trinta linhas de tabela de beneficiários. As três rotas que já existem
      em `app/routers/settings.py` passam a renderizar a seção sem nenhuma outra
      mudança, porque todas respondem pelo mesmo `_answer`.

- [ ] **2.5 — Modificar `app/main.py`: registrar o router.**
      `cards` entra na lista de import de `app.routers` (linhas 8-20, em ordem
      alfabética, entre `auth` e `commitments`) e
      `app.include_router(cards.router)` entra junto das outras chamadas.
      *Considerando 2.2.*
      *Justificativa:* RF-04, norma 24. Sem o registro a rota não existe e o
      formulário posta para `404`. Registrada, ela passa a ser varrida por
      `tests/test_route_guard.py:37-48`, que exige sessão de toda rota
      registrada — é assim que a rota nova nasce atrás do guarda sem que este
      plano peça nada a mais.

- [ ] **2.6 — Criar `tests/test_cartoes_screen.py`.**
      Cliente `TestClient` com base em `tmp_path`, `SESSION_SECRET` de teste e
      sessão aberta, no molde de `tests/test_configuracao_screen.py:32-49`;
      contas inseridas direto em `accounts` e `app.debts.ladder.rebuild`
      chamada, que é o que cria as linhas de `cards`. Os casos: a listagem e a
      ausência da conta de tipo `BANK`; a seção vazia; a escrita dos quatro
      campos com leitura por SQL; as duas recusas de gramática com a tela de pé;
      as duas recusas de nome desconhecido; e a ida e volta da taxa entre
      `/configuracao` e `/dividas`.
      *Considerando 2.1 a 2.5.* Quem executa é `pytest`, que o CI já roda.
      *Justificativa:* RF-01, RF-02, RF-04, RF-05, RF-06. A ida **e** a volta da
      taxa é o teste que decide o item: uma só direção passaria com duas casas
      espelhadas na escrita, que é o defeito que o `015` fechou e que este item
      pode reintroduzir. A conta de tipo `BANK` no meio das duas de crédito é o
      controle negativo, sem o qual uma seção que listasse todas as contas
      passaria.

---

- [ ] **2.7 — `app/settings/catalog.py`: a frase que envelhece no mesmo diff que
      a faz envelhecer.**
      Método: reescrever o texto de `help` da entrada `CARD_RATE`, que hoje diz
      que a taxa do cartão "é um campo por dívida na tela de dívidas, e não uma
      linha aqui", para nomear as duas telas em que o campo existe e dizer que
      as duas escrevem no mesmo lugar. `stored` continua `False`, `screen`
      continua apontando para `/dividas`, e nenhuma outra entrada muda.
      Justificativa: depois da etapa 2.2 o campo está três seções abaixo, na
      mesma tela que imprime essa frase. Tela que descreve errado a si mesma é a
      classe de defeito que este projeto persegue desde o `012`, e a
      reconciliação vai no mesmo trabalho que cria a divergência (norma 8).

## Execução sugerida

1. **Fase 1, bloqueante.** Ela fixa a forma do dado — a tabela, os quatro
   campos, a unidade de cada um e a casa única da taxa — e a fase 2 só renderiza
   e escreve o que a fase 1 definiu. Toca `app/migrations/sql/013_cards.sql`,
   `app/cards/catalog.py`, `app/cards/typed.py`, `app/cards/store.py`,
   `app/debts/ladder.py`, `app/routers/debts.py`, `tests/test_cards.py` e
   `tests/test_migrations.py`.
2. **Fase 2 depois da 1.** Toca `app/cards/catalog.py`, `app/cards/store.py`,
   `app/routers/cards.py`, `app/templates/fragments/configuracao_cartoes.html`,
   `app/routers/settings.py`, `app/templates/configuracao.html`, `app/main.py` e
   `tests/test_cartoes_screen.py`.

As duas **não** correm em paralelo: a fase 2 importa três nomes que a fase 1
cria e reescreve dois arquivos dela, e um par de worktrees produziria conflito
em `app/cards/` mais um veredicto falso na frente que fizesse merge primeiro.

**Pontos de encontro com os outros cinco itens simultâneos**, todos de conflito
trivial e nenhum de comportamento: `tests/test_migrations.py` (as duas listas de
constantes, uma linha cada), `app/main.py` (um import e um `include_router`) e
`app/templates/configuracao.html` (uma linha de `include`). A migração deste item
é **exatamente** `013_cards.sql`; `012`, `014` e `015` estão reservados. Nenhum
arquivo de `app/taxonomy/`, `app/queries/`, `app/advisor/`, `app/financings/`,
`app/routers/spending.py` e `app/routers/reference.py` é tocado, e a função
`_from_contracts` de `app/debts/ladder.py` fica como está.

## Pendências que viram item de roadmap

- **A linha `taxa-cartao` do catálogo de `/configuracao` passa a dizer meia
  verdade.** `app/settings/catalog.py:31-47` descreve a taxa mensal dos cartões
  com `screen` igual a `/dividas` e `stored` igual a `False`, e a tela imprime
  "Não é uma linha aqui: é uma taxa por dívida (…) o campo está em /dividas"
  (`app/templates/configuracao.html:43-46`). Depois deste item o campo também
  está em `/configuracao`, três seções abaixo, na mesma tela. Corrigir a frase
  exige tocar `app/settings/catalog.py`, que pertence a um item simultâneo e
  está fora do escopo desta rodada. A informação continua correta — a taxa
  **é** por dívida e se edita em `/dividas` —, e o que envelheceu é o "não é uma
  linha aqui".
- **O consultor tem duas telas para a mesma resposta.**
  `app/advisor/gaps.py:33` só para de perguntar a taxa do cartão quando nenhum
  degrau está sem taxa, e a pergunta aponta para `/dividas`. Continua
  funcionando, e continua apontando para uma das duas telas que respondem.
- **O limite, o fechamento e o vencimento não movem número nenhum neste item.**
  RF-01 pede que existam e sejam editáveis; quem os usa para projetar a fatura é
  o item `026`. Enquanto ele não chegar, são três campos que a tela guarda e
  ninguém lê.
- **`debts.monthly_rate_bp` continua existindo para degrau de cartão.** Ela fica
  nula para todo cartão com conta, e a leitura por `COALESCE` só cai nela para
  degrau de cartão inserido sem `account_id` — o que hoje só acontece em
  `tests/test_plan.py:83` e `:127`. Quando esses dois testes passarem a montar o
  cartão a partir de uma conta, o `COALESCE` pode virar leitura direta de
  `cards`.
- **O leitor de dia do mês mora fora da gramática do item `015`.**
  `app/cards/typed.py` importa dinheiro e taxa de `app/settings/typed.py` e só
  acrescenta o dia, porque este item não abre aquele arquivo. Quando uma segunda
  tela precisar de dia do mês, o leitor sobe para a gramática única.

## Validações de campo pendentes

Nenhuma. Todo comportamento deste item se observa por chamada de função, por
consulta SQL a banco em diretório temporário e por requisição HTTP com leitura do
HTML devolvido; nada depende de aparelho físico, permissão de plataforma ou rede
real. O contraste e o foco da seção nova são os das classes que ela reusa, já
medidos por `tests/test_contrast.py` sobre `app/static/css/tokens.css`, que esta
fase não toca.
