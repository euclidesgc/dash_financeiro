# Plano — 019-reclassificacao-a-partir-do-lancamento

**Item:** `019-reclassificacao-a-partir-do-lancamento` · **Trilha:** rápida ·
**Fonte aprovada:** `01-brief.md`, RF-01 a RF-08 · **Terreno:** `00-discovery.md`
(08/09/2026) · Duas fases, em sequência.

> **Sobre os números deste plano.** Os do terreno vêm do brief aprovado, medidos
> na base de 05/09/2026, e não são remedidos aqui. Os dos critérios são
> produzidos pelos lançamentos que o próprio critério declara no *Dado* —
> nenhum número deste documento é lembrado de cabeça.

## Objetivo

Ao fim das duas fases a correção de classificação começa onde o erro aparece: no
lançamento aberto no drill-down de `/gastos`, o dono escolhe grupo e categoria da
árvore, cria grupo novo ali mesmo se nenhum servir, e a tela diz **antes de
gravar** quantos lançamentos e quanto dinheiro a correção alcança. A correção
vira regra sobre o beneficiário, escrita dentro da mesma transação que
reclassifica a base, e a tela seguinte já mostra os totais novos.

A quebra é por **contrato, não por tela**. O item inteiro depende de uma
igualdade: o conjunto que a prévia conta e o conjunto que a gravação alcança têm
de ser o mesmo, ou o item nasce mentindo — e essa igualdade é propriedade da
consulta e do casamento da regra, não da página. Por isso a fase 1 fixa as duas
coisas juntas e sozinhas: um gabarito de consulta que a prévia, o resultado e a
apuração de quem já segurava o beneficiário compartilham, e um casamento
**exato** (`^` + `re.escape(payee)` + `$`) que faz o conjunto do SQL e o conjunto
do regex coincidirem por construção. A fase 2 consome as duas e não decide mais
nada sobre alcance.

## O terreno

| Sítio | Hoje | O que falta |
|---|---|---|
| `app/routers/rules.py` (`/regras`) | a única porta de correção, no vocabulário de quem escreve regra: tipo de casamento e expressão regular | uma porta no lançamento, no vocabulário de quem olha o gasto |
| `app/templates/fragments/gastos_detalhe.html:18-25` | a lista imprime data, descrição, conta e valor | abrir o lançamento para corrigir |
| `app/queries/axes.py:64-76` (`transactions_of`) | devolve `date`, `description`, `account` e `amount_cents` | `id` e `payee` — sem eles a linha não sabe dizer quem corrigir |
| `app/taxonomy/rules.py:94-104` (`_write`) | escrita e `classify_all` já partilham uma transação, com `rollback` no erro | uma entrada que case por beneficiário e decida sozinha entre criar e atualizar |
| `app/queries/` | `aggregate`, `transactions_of`, `crossing`, `residue`, `total_spending_cents` | a consulta de alcance, uma só, que prévia e resultado leem |
| `app/routers/spending.py:169-178` (`_detail_context`) | monta a lista aberta e nada mais | o bloco de correção do lançamento pedido |

Três fatos do código decidem o desenho e não se re-discutem:

- **A precedência é por id, e a primeira expressão que casa vence.**
  `app/taxonomy/classify.py:63-77` lê as regras com `ORDER BY id`, e `:51-60`
  percorre as expressões antes das categorias devolvendo a primeira que casa.
  Uma regra de descrição escrita agora nasce com o maior id, logo com a **menor**
  precedência entre as expressões — é daí que vem a diferença que RF-06 manda a
  tela nomear. E como o casamento é exato, a expressão de id menor pega o
  beneficiário inteiro ou não pega nenhuma linha dele: a diferença é `N → 0`,
  nunca uma fração.
- **`payee` é sempre `[a-z ]*`.** Nada em `app/ingest/` escreve a coluna; quem a
  preenche é `app/taxonomy/classify.py:94-101`, com `normalize_description`, que
  derruba acento, dígito e pontuação (`app/ingest/normalize.py:14-23`).
- **A semente não roda em operação normal.** `seed_taxonomy` só é chamada por
  `python -m app.taxonomy.seed`: nem `create_app` (`app/main.py:41-71`) nem a
  pós-carga da sincronização (`app/sync/__init__.py:101-104`) a invocam. Isso
  importa porque `app/taxonomy/seed.py:85-88` e `:104-107` apagam grupo que a
  semente não declara e repõem as regras dele no escape — o que fica registrado
  como pendência, não como fase.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| Sobre o que a regra casa, em SQL e em regex | a prévia conta com `payee = ?` e a gravação casa com expressão; qualquer folga entre as duas é exatamente a mentira que RF-02 proíbe | `match_value` é `^` + `re.escape(payee)` + `$`. Casamento exato: o conjunto que o SQL conta e o que o regex pega são o mesmo, e `mercado livre pago` não entra em `mercado livre` |
| O alcance é do período aberto ou de toda a base | regra não tem período — `app/routers/rules.py:53-72` já mede assim, sem janela | toda a base, e a tela diz `em toda a base` para não ser lida como o período |
| Qual número a tela chama de "mudaram de fato" | `classify_all` devolve linhas cuja tupla mudou na base inteira, inclusive troca de regra sem troca de grupo: responde outra pergunta | o alcance da regra escrita, medido pelo mesmo gabarito da prévia |
| Onde mora a consulta de alcance | norma 33: junção e agregação em SQL, em `app/queries` | `app/queries/reach.py`, com um gabarito só |
| Onde mora a escrita | `app/taxonomy/rules.py` já é o módulo de escrita de regra, e o `_write` dele já partilha a transação com `classify_all` — o que o item `012` fechou | `correct_payee` ali, reusando `_write` |
| Onde mora a rota | a tela é `/gastos`, e norma 29 põe o router do domínio junto do domínio | `POST /gastos/correcao`, em `app/routers/spending.py` |
| O que o campo de categoria faz | RF-01 pede que o dono escolha grupo **e** categoria; RF-07 manda recusar categoria fora do grupo; `category_rules` (`app/migrations/sql/003_taxonomy.sql:25-33`) não tem coluna de categoria e o não-escopo do brief proíbe mexer na árvore | o formulário carrega os dois, o servidor confere a coerência e recusa o par incoerente, e o que a regra grava é o **grupo**. A categoria não é persistida — lacuna registrada no retorno |
| Migração | nada muda de esquema: `category_groups` já aceita linha nova, e a árvore é consumida como está | **nenhuma**. O número `017_` continua livre |
| Nome dos campos do formulário | `/gastos` já fala pt-BR nos parâmetros (`eixo`, `inicio`, `fim`, `chave`, `data`), e norma 16 põe a interface em pt-BR | `grupo`, `grupo_novo`, `categoria`, `natureza`, `essencialidade`; o lançamento viaja em `corrigir`, como `chave` viaja hoje |
| De onde vem o beneficiário da regra | um `payee` vindo do corpo deixaria gravar regra sobre coisa que o dono não viu | do lançamento apontado por `corrigir`, lido no servidor |
| Select de categoria dependente do grupo por htmx | exigiria rota que devolve só um `<select>` e um segundo caminho de leitura da árvore; sem htmx a tela ficaria sem troca de grupo | não: um `<select>` de grupo e um de categoria com `<optgroup>` por grupo. A coerência é do servidor, que é onde RF-07 a cobra |
| Corpo com UTF-8 cru | `app/routers/rules.py:264-272` já trata o mojibake do urlencoded, e `natureza`, `essencialidade` e nome de grupo novo carregam acento | o mesmo auxiliar, promovido a público, importado pela rota nova (norma 20) |
| CSS novo | `app/static/css/` está fora do escopo declarado do item, e a linguagem visual é canônica em `product/00-linguagem-visual.md` | nenhuma regra nova: o bloco usa `.form`, `.field`, `.field-label`, `.field-input`, `.controls`, `.notice`, `.notices`, `.button`, `.button-quiet`, `.cifra`, `.lede`, `.section-title` e `.row-open`, que já existem |
| Marca semântica na cifra nova | `tests/test_gastos_screen.py:148-156` fixa o conjunto exato de cifras com `negative`, e a linguagem visual reserva a cor ao número que pede decisão | nenhuma cifra do bloco novo leva `negative`; o sinal `−` colado ao número faz o trabalho |

**Linguagem visual.** A fase 2 segue `product/00-linguagem-visual.md`, que é
canônico: face monoespaçada na cifra, rótulo em versalete no campo, foco visível
sem `outline` zerado, mensagem de erro que diz o que aconteceu e qual é o próximo
ato, nenhum hexadecimal fora de `tokens.css`. Os tokens de medida (`--measure`,
`--measure-wide`) vieram do item `017`, e o bloco novo mora dentro do painel
largo que ele estabeleceu, sem declarar medida própria.

---

## Fase 1 — O alcance e a regra a partir do beneficiário (api)

**Objetivo da fase:** uma consulta só responde quanto uma correção alcança, e uma
função só grava a regra do beneficiário — criando ou atualizando — dentro da
transação que reclassifica a base.

**Critérios de aceite**

- [ ] `estrutural` — existe `app/queries/reach.py` exportando `payee_reach`,
      `category_reach`, `rule_reach` e `holders`. As três primeiras executam a
      mesma constante de módulo `_REACH`, que traz `count(*) AS entries`,
      `coalesce(sum(amount_cents), 0) AS amount_cents` e o predicado `SPENDING`
      importado de `app.queries.spending`; o que varia entre elas é só o filtro
      que entra no gabarito, e nenhuma das três monta instrução própria no
      corpo <!-- RF-02, RF-06 -->
- [ ] `comportamental` —
      *Dado* um banco temporário migrado por `app.migrate.run_migrations`,
      semeado por
      `seed_taxonomy(conn, tests.conftest.narrowed(load_seed(), []))` — sem regra
      nenhuma —, carregado por `tests.conftest.load` com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`,
      e com `app.taxonomy.classify.classify_all(conn)` executado — é ele que
      preenche `payee` a partir da descrição normalizada
      *Quando* `app.queries.reach.payee_reach(conn, "mercado livre")`,
      `app.queries.reach.payee_reach(conn, "mercado livre pago")` e
      `app.queries.reach.category_reach(conn, "Categoria da fonte")` são chamadas
      *Então* a primeira devolve `entries` igual a `2` e `amount_cents` igual a
      `-15000`; a segunda devolve `entries` igual a `1` e `amount_cents` igual a
      `-2500`; e a terceira devolve `entries` igual a `3` e `amount_cents` igual
      a `-17500` — o beneficiário que começa com o mesmo texto é medição à parte,
      e a primeira não o soma <!-- RF-02 -->
- [ ] `comportamental` —
      *Dado* um banco temporário migrado por `app.migrate.run_migrations`,
      semeado por `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra
      nenhuma —, carregado com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`,
      com `classify_all(conn)` executado, e `PESSOAL` sendo o valor de
      `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando*
      `app.taxonomy.rules.correct_payee(conn, payee="mercado livre", group_id=PESSOAL, nature="variável", essentiality="supérfluo")`
      é chamada
      *Então* o resultado traz `entries` igual a `2` e `amount_cents` igual a
      `-15000` — os mesmos dois números que
      `app.queries.reach.payee_reach(conn, "mercado livre")` devolve antes da
      chamada; `app.taxonomy.rules.expression_for("mercado livre")` começa com
      `^` e termina com `$`;
      `SELECT match_value FROM category_rules WHERE match_kind = 'description'`
      devolve uma linha só, igual a essa expressão;
      `SELECT count(*) FROM transactions WHERE rule_id = (SELECT id FROM
      category_rules WHERE match_kind = 'description')` devolve `2`; e a linha de
      `pluggy_id = 't-mlp'` continua com `rule_id` nulo <!-- RF-02, RF-03 -->
- [ ] `comportamental` —
      *Dado* um banco temporário migrado por `app.migrate.run_migrations`,
      semeado por
      `seed_taxonomy(conn, narrowed(load_seed(), [tests.conftest.rule("description", "^mercado", "Financeiro", "fixa", "essencial")]))`
      — uma regra só —, carregado com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`,
      com `classify_all(conn)` executado, e `PESSOAL` sendo o valor de
      `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando*
      `app.taxonomy.rules.correct_payee(conn, payee="mercado livre", group_id=PESSOAL, nature="variável", essentiality="supérfluo")`
      é chamada
      *Então* o resultado traz `entries` igual a `0`;
      `SELECT count(*) FROM category_rules` devolve `2`, e a regra nova existe
      com `match_kind` igual a `description`;
      `app.queries.reach.payee_reach(conn, "mercado livre")` continua devolvendo
      `entries` igual a `2`, porque a prévia não depende de regra; e
      `app.queries.reach.holders`, chamada com `payee="mercado livre"` e com o
      `rule_id` que a correção devolveu, entrega exatamente uma linha, cujo
      `match_value` é `^mercado` — a regra de id menor continua pegando o
      beneficiário <!-- RF-06 -->
- [ ] `comportamental` —
      *Dado* um banco temporário migrado por `app.migrate.run_migrations`,
      semeado por `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra
      nenhuma —, carregado com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`,
      com `classify_all(conn)` executado, e `ANTES` sendo o valor de
      `SELECT count(*) FROM category_rules` nesse ponto
      *Quando* `app.taxonomy.rules.correct_payee` é chamada duas vezes com
      `payee="mercado livre"`, `nature="variável"` e `essentiality="supérfluo"`,
      a primeira com o `group_id` de `Pessoal` e a segunda com o de
      `Assinaturas`
      *Então* depois da primeira `SELECT count(*) FROM category_rules` vale
      `ANTES + 1` e o resultado traz `created` igual a `True`; depois da segunda
      vale `ANTES + 1` de novo e o resultado traz `created` igual a `False`; e
      `SELECT g.name FROM category_rules AS r JOIN category_groups AS g ON g.id =
      r.group_id WHERE r.match_kind = 'description'` devolve uma linha só, igual
      a `Assinaturas` — corrigir de novo o mesmo beneficiário atualiza a regra em
      vez de abrir uma segunda que compete com ela <!-- RF-05 -->
- [ ] `comportamental` —
      *Dado* um banco temporário migrado por `app.migrate.run_migrations`,
      semeado por `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra
      nenhuma —, carregado com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`,
      com `classify_all(conn)` executado, e `TOPO` sendo o valor de
      `SELECT max(position) FROM category_groups`
      *Quando*
      `app.taxonomy.rules.correct_payee(conn, payee="mercado livre", group_id=None, new_group="Educação do filho", nature="variável", essentiality="supérfluo")`
      é chamada
      *Então*
      `SELECT position, is_fallback FROM category_groups WHERE name = 'Educação do filho'`
      devolve uma linha com `position` igual a `TOPO + 1` e `is_fallback` igual a
      `0`; a regra escrita aponta para o `id` dessa linha; e
      `SELECT count(*) FROM transactions WHERE group_id = (SELECT id FROM
      category_groups WHERE name = 'Educação do filho')` devolve `2` — o grupo
      novo existe na árvore e já carrega os lançamentos do beneficiário
      <!-- RF-04 -->
- [ ] `comportamental` —
      *Dado* um banco temporário migrado por `app.migrate.run_migrations`,
      semeado por `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra
      nenhuma —, carregado com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`,
      com `classify_all(conn)` executado — é ele que registra `Categoria da
      fonte` na tabela `categories` sob o grupo de escape —, e `PESSOAL` sendo o
      valor de `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando* `app.taxonomy.rules.correct_payee` é chamada quatro vezes, todas
      com `nature="variável"` e `essentiality="supérfluo"`: com
      `payee="mercado livre"` e `group_id=9999`; com `payee="mercado livre"`,
      `group_id=PESSOAL` e `category="Categoria da fonte"`; com
      `payee="beneficiario que nao existe"` e `group_id=PESSOAL`; e por fim com
      `payee="mercado livre"` e `group_id=PESSOAL`
      *Então* as três primeiras levantam `app.taxonomy.rules.RuleError` com as
      mensagens `grupo inválido: 9999`,
      `categoria fora do grupo: Categoria da fonte` e
      `beneficiário desconhecido: beneficiario que nao existe`; depois das três,
      `SELECT count(*) FROM category_rules WHERE match_kind = 'description'`
      devolve `0` e `SELECT count(*) FROM category_groups` devolve o mesmo valor
      que antes delas; e a quarta chamada responde sem levantar e leva essa mesma
      contagem de regras a `1` — o controle positivo, sem o qual as duas
      contagens passariam num banco vazio <!-- RF-07 -->
- [ ] `comportamental` —
      *Dado* um banco temporário migrado por `app.migrate.run_migrations`,
      semeado por `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra
      nenhuma —, carregado com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`,
      com `classify_all(conn)` executado, e em seguida
      `app.taxonomy.classify.classify_all` substituída por `monkeypatch.setattr`
      por uma função que apaga a classificação da primeira linha e então levanta
      `RuntimeError`
      *Quando*
      `app.taxonomy.rules.correct_payee(conn, payee="mercado livre", group_id=None, new_group="Educação do filho", nature="variável", essentiality="supérfluo")`
      é chamada e o `RuntimeError` sobe
      *Então* `SELECT count(*) FROM category_rules` e
      `SELECT count(*) FROM category_groups` valem o mesmo que antes da chamada;
      `SELECT count(*) FROM category_groups WHERE name = 'Educação do filho'`
      devolve `0`; e
      `SELECT id, rule_id, group_id, nature, essentiality FROM transactions ORDER BY id`
      devolve linha por linha o mesmo que antes da chamada — a escrita da regra,
      a criação do grupo e a reclassificação são uma transação só <!-- RF-03 -->
- [ ] `estrutural` — a instrução de `transactions_of`, em `app/queries/axes.py`,
      seleciona `t.id AS id` e `t.payee AS payee` ao lado de `date`,
      `description`, `account` e `amount_cents`, e `tests/test_axes.py` afirma
      que a linha devolvida traz as seis chaves <!-- RF-01 -->
- [ ] `comando` — `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m
      pytest -q tests/test_reach.py tests/test_corrections.py tests/test_axes.py
      tests/test_rules.py tests/test_rules_atomicity.py tests/test_classify.py
      tests/test_taxonomy_seed.py tests/test_taxonomy_tree.py` sai com código
      `0`. Quem executa é o `pytest` que o CI já roda: nenhum portão novo entra
      em `scripts/gates/` e `gates_runner.sh` não é tocado
      <!-- RF-02, RF-03, RF-04, RF-05, RF-06, RF-07 -->

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Criar `app/queries/reach.py`: um gabarito, quatro perguntas.**
      Método:
      ```python
      _REACH = (
          "SELECT count(*) AS entries, coalesce(sum(amount_cents), 0) AS amount_cents "
          f"FROM transactions WHERE {SPENDING} AND {{filtro}}"
      )

      def payee_reach(conn, payee: str) -> sqlite3.Row
      def category_reach(conn, category: str) -> sqlite3.Row
      def rule_reach(conn, rule_id: int) -> sqlite3.Row
      def holders(conn, *, payee: str, rule_id: int) -> list[sqlite3.Row]
      ```
      As três primeiras formatam `_REACH` com `payee = ?`, `category = ?` e
      `rule_id = ?`. `holders` é a única instrução própria do módulo: junta
      `transactions` com `category_rules` pelo `rule_id`, filtra o beneficiário e
      exclui a regra dada, devolvendo `id` e `match_value` em `ORDER BY r.id`.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-02 e RF-06. A prévia e o resultado saírem de instruções
      diferentes é a única forma de o item mentir sem que ninguém perceba: dois
      textos de SQL divergem na primeira manutenção, e a tela passa a prometer um
      número e entregar outro. `SPENDING` vem de `app.queries.spending` porque
      transferência entre contas próprias e estorno não são gasto (invariante
      25), e é repetindo o predicado que ele se perde numa das consultas. Norma
      33: a agregação mora em `app/queries`.

- [ ] **1.2 — Modificar `app/taxonomy/seed.json`: as quatro recusas novas.**
      Em `messages`, acrescentar `unknown_payee`
      (`beneficiário desconhecido: {value}`), `invalid_category`
      (`categoria inválida: {value}`), `category_outside_group`
      (`categoria fora do grupo: {value}`) e `duplicate_group`
      (`já existe um grupo com esse nome: {value}`).
      *Considerando:* nada antes.
      *Justificativa:* RF-07. As mensagens de recusa da taxonomia já moram aí e
      saem por `app.taxonomy.seed.message`; escrever a frase nova dentro do
      código faria a mesma tela dizer duas coisas para defeitos irmãos. Cada uma
      termina em `{value}` porque `tests/test_taxonomy_seed.py:90-92` percorre
      todas as chaves e exige que a mensagem termine no valor recusado.

- [ ] **1.3 — Modificar `app/taxonomy/rules.py`: a correção a partir do
      beneficiário.**
      Método:
      ```python
      def expression_for(payee: str) -> str          # "^" + re.escape(payee) + "$"

      @dataclass(frozen=True)
      class Correction:
          rule_id: int
          created: bool
          group_id: int
          reclassified: int
          entries: int
          amount_cents: int

      def correct_payee(conn, *, payee: str, group_id: int | None,
                        new_group: str = "", category: str = "",
                        nature: str, essentiality: str) -> Correction
      ```
      Na ordem: recusa `payee` que não existe em `transactions`
      (`UnknownPayeeError`); com `new_group` não vazio, insere o grupo com
      `position` igual a `max(position) + 1` e `is_fallback` zero, recusando nome
      já existente (`DuplicateGroupError`); com `category` não vazia, lê o
      `group_id` dela em `categories` e recusa quando ela não existe ou pertence
      a outro grupo (`CategoryOutsideGroupError`); procura a regra de
      `match_kind` `description` com `match_value` igual a
      `expression_for(payee)` e chama `update_rule` quando acha, `create_rule`
      quando não. Toda recusa faz `conn.rollback()` antes de subir, para o
      `INSERT` do grupo pendente não continuar visível na mesma conexão. O
      alcance devolvido é `app.queries.reach.rule_reach` sobre a regra escrita.
      *Considerando 1.1* (o alcance sai do gabarito) *e 1.2* (as frases).
      *Justificativa:* RF-03, RF-04, RF-05, RF-06, RF-07. O casamento exato é o
      que sustenta RF-02: `payee` é sempre `[a-z ]*`
      (`app/taxonomy/classify.py:94-101` com `app/ingest/normalize.py:14-23`),
      então `re.escape` não muda nada em uso normal e fecha a porta do dia em que
      mudar. Reusar `create_rule` e `update_rule` é o que põe a escrita dentro do
      `_write` que já partilha a transação com `classify_all`
      (`app/taxonomy/rules.py:94-104`) — o "sucesso mentiroso" que o item `012`
      fechou volta por qualquer segundo caminho de escrita. O `rollback` na
      recusa existe porque o grupo é inserido antes da validação da regra, e a
      conexão é a mesma com que a tela se redesenha.

- [ ] **1.4 — Modificar `app/queries/axes.py`: a linha aberta diz quem é.**
      `transactions_of` (linhas 64-76) passa a selecionar `t.id AS id` e
      `t.payee AS payee` junto das quatro colunas de hoje. Nada mais muda:
      `_KEYS`, `_FROM` e `_WINDOW` ficam como estão.
      *Considerando:* nada antes; é independente de 1.1 a 1.3.
      *Justificativa:* RF-01. Sem `id` a linha não tem como apontar o lançamento
      a corrigir, e sem `payee` a tela não tem como dizer sobre quem a regra vai
      casar. As duas colunas já existem na tabela e no índice
      (`app/migrations/sql/003_taxonomy.sql:44` e `:54`).

- [ ] **1.5 — Criar `tests/test_reach.py`.**
      Os três lançamentos (`Mercado Livre` duas vezes e `Mercado Livre Pago`),
      semeados sem regra: alcance por beneficiário, pelo beneficiário irmão de
      prefixo e pela categoria de origem; alcance de regra depois de uma escrita;
      `holders` com e sem regra concorrente. Uma transferência e um estorno do
      mesmo beneficiário entram na base para provar que nenhum dos dois soma.
      *Considerando 1.1.*
      *Justificativa:* RF-02, RF-06 e invariante 25. O par de prefixo é o que
      separa casamento exato de casamento por começo — sem ele, uma regra
      `^mercado livre` passa por todos os outros critérios e leva junto um
      beneficiário que a prévia não contou.

- [ ] **1.6 — Criar `tests/test_corrections.py` e ampliar `tests/test_axes.py`.**
      Em `tests/test_corrections.py`: a gravação com alcance igual à prévia; a
      regra concorrente de id menor; a segunda correção que atualiza em vez de
      criar; o grupo novo com posição e escape; as três recusas com a quarta
      chamada válida ao lado; e a atomicidade, com `classify_all` substituída por
      `monkeypatch.setattr` por uma função que escreve metade e levanta — a mesma
      forma de `tests/test_rules_atomicity.py:35-40`. Em `tests/test_axes.py`: a
      linha de `transactions_of` traz `id` e `payee`.
      *Considerando 1.3* e *1.4.*
      *Justificativa:* RF-01 a RF-07. Quem executa é o `pytest` que o CI já roda;
      nenhum portão novo entra em `scripts/gates/` e o `gates_runner.sh` não é
      tocado. A atomicidade tem teste próprio porque o `_write` só protege o que
      passa por ele: a criação do grupo é escrita nova na mesma conexão, e sem a
      medição ela fica de fora do `rollback` sem ninguém notar.

---

## Fase 2 — A correção dentro do lançamento aberto (api)

**Objetivo da fase:** no drill-down de `/gastos` o dono abre um lançamento, lê
quanto a correção alcança, escolhe grupo e categoria — ou cria grupo novo — e
grava, com a tela dizendo em seguida quantos lançamentos mudaram de fato.

**Critérios de aceite**

- [ ] `estrutural` — `app/routers/spending.py` registra a rota
      `POST /gastos/correcao`, importa `correct_payee` de `app.taxonomy.rules` e
      `payee_reach`, `category_reach` e `holders` de `app.queries.reach`, e não
      monta instrução SQL própria para medir alcance. Existe
      `app/templates/fragments/gastos_correcao.html`, e nem ele nem
      `app/templates/fragments/gastos_detalhe.html` trazem atributo `style=`,
      elemento `<style` ou cor em hexadecimal — a folha de estilo do projeto não
      é tocada <!-- RF-01, RF-03 -->
- [ ] `comportamental` —
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário,
      `SESSION_SECRET` fixado, `DASH_TODAY=2026-09-05` no ambiente do processo e
      sessão autenticada, sobre uma base semeada por
      `seed_taxonomy(conn, tests.conftest.narrowed(load_seed(), []))` — sem regra
      nenhuma — carregada com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`
      e classificada por `classify_all(conn)`, com `ALVO` sendo
      `SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'`
      *Quando* `GET /gastos?eixo=grupo&chave=Outros&corrigir=<ALVO>` é buscada e,
      na mesma execução, `GET /gastos?eixo=grupo&chave=Outros` e
      `GET /gastos?eixo=grupo&chave=Outros&corrigir=999999`
      *Então* a primeira responde `200` e contém `id="correcao"`, `name="grupo"`,
      `name="categoria"`, `name="natureza"`, `name="essencialidade"`,
      `name="grupo_novo"` e o texto `mercado livre`; no trecho entre
      `id="alcance"` e o `</p>` seguinte estão `2 lançamento`, `−R$ 150,00` e
      `em toda a base`, e no trecho entre `id="alcance-categoria"` e o `</p>`
      seguinte estão `3 lançamento` e `−R$ 175,00`; a segunda responde `200` e
      não traz `id="correcao"`; a terceira responde `200` e também não traz
      `id="correcao"`; e o total impresso entre `id="tabela"` e o `id="detalhe"`
      seguinte é `−R$ 175,00` nas três — abrir a correção não move total nenhum
      <!-- RF-01, RF-02, RF-08 -->
- [ ] `comportamental` —
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário,
      `DASH_TODAY=2026-09-05` e sessão autenticada, sobre uma base semeada por
      `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra nenhuma —
      carregada com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`
      e classificada, com `ALVO` sendo
      `SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'` e `PESSOAL` sendo
      `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando*
      `POST /gastos/correcao?eixo=grupo&inicio=2026-09-01&fim=2026-09-05&chave=Outros&corrigir=<ALVO>`
      é enviada com o corpo `grupo=<PESSOAL>`, `categoria` vazia, `grupo_novo`
      vazio, `natureza=variável` e `essencialidade=supérfluo`
      *Então* a resposta é `200`; o trecho entre `id="resultado"` e o `</p>`
      seguinte contém `2 lançamento` e `Pessoal`;
      `SELECT count(*) FROM category_rules WHERE match_kind = 'description'`
      devolve `1`;
      `SELECT count(*) FROM transactions WHERE rule_id = (SELECT id FROM
      category_rules WHERE match_kind = 'description')` devolve `2`; e na própria
      resposta a tabela do eixo `grupo` traz uma linha `Pessoal` com
      `−R$ 150,00` enquanto o total do período segue `−R$ 175,00` — o que muda os
      números é a regra, e ela reparte sem criar nem sumir com dinheiro
      <!-- RF-03, RF-06, RF-08 -->
- [ ] `comportamental` —
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário,
      `DASH_TODAY=2026-09-05` e sessão autenticada, sobre uma base semeada por
      `seed_taxonomy(conn, narrowed(load_seed(), [rule("description", "^mercado", "Financeiro", "fixa", "essencial")]))`
      — uma regra só — carregada com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`
      e classificada, com `ALVO` sendo
      `SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'` e `PESSOAL` sendo
      `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando*
      `POST /gastos/correcao?eixo=grupo&inicio=2026-09-01&fim=2026-09-05&chave=Financeiro&corrigir=<ALVO>`
      é enviada com `grupo=<PESSOAL>`, `natureza=variável` e
      `essencialidade=supérfluo`
      *Então* a resposta é `200`; o trecho entre `id="resultado"` e o `</p>`
      seguinte contém `0 dos 2 lançamentos previstos`, o texto `^mercado` e
      `href="/regras"`; `SELECT count(*) FROM category_rules` devolve `2`; e
      `SELECT count(*) FROM transactions WHERE group_id = (SELECT id FROM
      category_groups WHERE name = 'Pessoal')` devolve `0` — a tela nomeia a
      regra de precedência maior em vez de deixar a correção parecer quebrada
      <!-- RF-06 -->
- [ ] `comportamental` —
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário,
      `DASH_TODAY=2026-09-05` e sessão autenticada, sobre uma base semeada por
      `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra nenhuma —
      carregada com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`
      e classificada, com `ALVO` sendo
      `SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'`
      *Quando*
      `POST /gastos/correcao?eixo=grupo&inicio=2026-09-01&fim=2026-09-05&chave=Outros&corrigir=<ALVO>`
      é enviada com o corpo montado como bytes UTF-8 crus e cabeçalho
      `content-type: application/x-www-form-urlencoded`, trazendo `grupo` vazio,
      `grupo_novo=Educação do filho`, `natureza=variável` e
      `essencialidade=supérfluo`
      *Então* a resposta é `200`;
      `SELECT count(*) FROM category_groups WHERE name = 'Educação do filho'`
      devolve `1`;
      `SELECT nature FROM category_rules WHERE match_kind = 'description'`
      devolve `variável`; e a própria resposta traz `Educação do filho` dentro do
      `<select` de `name="grupo"` — o grupo novo passa a existir na árvore como
      qualquer outro, e o corpo com acento chega inteiro <!-- RF-04, RF-01 -->
- [ ] `comportamental` —
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário,
      `DASH_TODAY=2026-09-05` e sessão autenticada, sobre uma base semeada por
      `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra nenhuma —
      carregada com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`
      e classificada por `classify_all(conn)` — é ele que registra `Categoria da
      fonte` na tabela `categories` sob o grupo de escape —, com `ALVO` sendo
      `SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'` e `PESSOAL` sendo
      `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando* são enviadas, na mesma execução, quatro requisições para
      `POST /gastos/correcao?eixo=grupo&inicio=2026-09-01&fim=2026-09-05&chave=Outros`,
      todas com `natureza=variável` e `essencialidade=supérfluo`: uma com
      `corrigir=<ALVO>` e `grupo=9999`; outra com `corrigir=<ALVO>`,
      `grupo=<PESSOAL>` e `categoria=Categoria da fonte`; outra com
      `corrigir=999999` e `grupo=<PESSOAL>`; e por fim uma com `corrigir=<ALVO>`
      e `grupo=<PESSOAL>`
      *Então* as três primeiras respondem `400`, cada uma trazendo
      `id="erro-correcao"` com, na ordem, `grupo inválido: 9999`,
      `categoria fora do grupo: Categoria da fonte` e
      `beneficiário desconhecido`; depois das três,
      `SELECT count(*) FROM category_rules WHERE match_kind = 'description'`
      devolve `0`; e a quarta responde `200` e leva essa contagem a `1` — o
      controle positivo, que prova que a medição alcançava a tabela certa
      <!-- RF-07 -->
- [ ] `comando` — `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m
      pytest -q tests/test_gastos_correcao_screen.py tests/test_gastos_screen.py
      tests/test_regras_screen.py tests/test_route_guard.py` sai com código `0`,
      e `tests/test_gastos_correcao_screen.py` traz teste que abre a correção,
      teste que grava, teste que recusa e teste que envia o corpo em bytes UTF-8
      crus. Quem executa é o `pytest` que o CI já roda: nenhum portão novo entra
      em `scripts/gates/` e `gates_runner.sh` não é tocado
      <!-- RF-01, RF-02, RF-04, RF-06, RF-07 -->

**Critérios de integração**

- [ ] `comportamental` —
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário,
      `DASH_TODAY=2026-09-05` e sessão autenticada, em duas execuções sobre a
      mesma carga —
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`
      —, a primeira semeada por `seed_taxonomy(conn, narrowed(load_seed(), []))`
      e a segunda por
      `seed_taxonomy(conn, narrowed(load_seed(), [rule("description", "^mercado", "Financeiro", "fixa", "essencial")]))`,
      as duas classificadas, com `ALVO` sendo
      `SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'` e `PESSOAL` sendo
      `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando* em cada execução `GET /gastos?eixo=grupo&corrigir=<ALVO>` é
      buscada e, em seguida, `POST /gastos/correcao?eixo=grupo&corrigir=<ALVO>` é
      enviada com `grupo=<PESSOAL>`, `natureza=variável` e
      `essencialidade=supérfluo`
      *Então* nas duas execuções o trecho entre `id="alcance"` e o `</p>`
      seguinte traz `2 lançamento` e `−R$ 150,00` — a prévia é a mesma, porque
      não depende de regra —; os dois POST respondem `200`; na primeira execução
      o trecho entre `id="resultado"` e o `</p>` seguinte traz `2 lançamento`, e
      na segunda traz `0 dos 2 lançamentos previstos` e o texto `^mercado`. A
      prévia e o resultado saem da mesma medida, e a diferença entre eles tem
      nome <!-- RF-02, RF-06 -->
- [ ] `comportamental` —
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário,
      `DASH_TODAY=2026-09-05` e sessão autenticada, sobre uma base semeada por
      `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra nenhuma —
      carregada com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`
      e classificada, com `ALVO` sendo
      `SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'` e `PESSOAL` sendo
      `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando* `POST /gastos/correcao?eixo=grupo&corrigir=<ALVO>` é enviada com
      `grupo=<PESSOAL>`, `natureza=variável` e `essencialidade=supérfluo`
      *Então* a resposta é `200`;
      `SELECT g.name FROM transactions AS t JOIN category_groups AS g ON g.id =
      t.group_id WHERE t.payee = 'mercado livre'` devolve `Pessoal` nas duas
      linhas; e a mesma consulta com `t.payee = 'mercado livre pago'` devolve
      `Outros` na única linha dela — o beneficiário que só compartilha o começo
      do texto continua onde estava <!-- RF-02, RF-03 -->
- [ ] `comportamental` —
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário,
      `DASH_TODAY=2026-09-05` e sessão autenticada, sobre uma base semeada por
      `seed_taxonomy(conn, narrowed(load_seed(), []))` — sem regra nenhuma —
      carregada com
      `transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria="Categoria da fonte")`,
      `transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria="Categoria da fonte")`
      e
      `transaction("t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria="Categoria da fonte")`
      e classificada, e com `POST /gastos/correcao?eixo=grupo&corrigir=<ALVO>` já
      enviada com `grupo=<PESSOAL>`, `natureza=variável` e
      `essencialidade=supérfluo`, sendo `ALVO` o valor de
      `SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'` e `PESSOAL` o de
      `SELECT id FROM category_groups WHERE name = 'Pessoal'`
      *Quando* `GET /regras` é buscada
      *Então* a resposta é `200`; a linha da tabela de regras que contém
      `mercado` traz também `Pessoal`, `variável`, `supérfluo` e o número `2` de
      lançamentos alcançados; e
      `SELECT count(*) FROM category_rules WHERE match_kind = 'description'`
      devolve `1` — a porta nova escreve no mesmo conjunto que `/regras` continua
      editando <!-- RF-03, RF-05 -->
- [ ] `comando` — `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m
      pytest -q` sai com código `0`, com a suíte inteira do repositório
      exercitando as duas fases juntas
      <!-- RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08 -->

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **2.1 — Modificar `app/routers/rules.py`: o leitor de campo com acento
      fica público.**
      `_text` (linhas 264-272) passa a `form_text`, com o mesmo corpo e o mesmo
      comentário; as chamadas internas acompanham.
      *Considerando:* nada antes.
      *Justificativa:* RF-01 e RF-07, com norma 20. `natureza`,
      `essencialidade` e nome de grupo novo carregam acento, e o corpo urlencoded
      chega lido como latin-1: sem o mesmo tratamento, a rota nova recusa
      vocabulário válido pelo motivo errado — o defeito idêntico uma pasta ao
      lado, que já custou um item. O auxiliar fica em `app/routers/rules.py`
      porque é tradução de HTTP, que é o trabalho que a norma 30 reserva à camada
      de rota, e `app/routers/render.py` está fora do escopo declarado deste
      item.

- [ ] **2.2 — Modificar `app/routers/spending.py`: o lançamento aberto e a rota
      que grava.**
      `_detail_context` (linhas 169-178) passa a montar `context["correction"]`
      quando `request.query_params.get("corrigir")` nomeia um lançamento
      existente — antes do retorno curto de `key is None`, para a correção também
      abrir por URL digitada à mão. O contexto traz o lançamento, o beneficiário,
      o alcance por beneficiário (`payee_reach`) e por categoria de origem
      (`category_reach`), os grupos, as categorias com o grupo de cada uma, as
      naturezas, as essencialidades, o formulário e — quando houver — a recusa ou
      o resultado. Nasce a rota `POST /gastos/correcao`, que lê `corrigir` da
      query, tira o beneficiário do próprio lançamento, passa os campos por
      `form_text`, chama `correct_payee`, responde a página inteira com
      `status_code=200` no sucesso e `400` na recusa, e usa `holders` para nomear
      a regra que continua segurando o beneficiário quando o alcance sai menor
      que a prévia. As frases ficam em constantes de módulo, ao lado de
      `CANDIDATES` e `MONTH_LENGTH`.
      *Considerando 1.1, 1.3, 1.4* e *2.1.*
      *Justificativa:* RF-01 a RF-08. O beneficiário sai do lançamento e nunca do
      corpo: um `payee` digitado por fora deixaria gravar regra sobre coisa que o
      dono não viu. O POST responde a página inteira em vez de um fragmento
      porque a escrita move a tabela, o painel e o total ao mesmo tempo, e porque
      a tela precisa continuar respondendo sem htmx — é a mesma razão do botão de
      submissão que `app/templates/gastos.html:44-47` já explica. A rota não monta
      consulta (norma 30): alcance, agregação e vizinhança vêm de `app/queries`.

- [ ] **2.3 — Criar `app/templates/fragments/gastos_correcao.html`.**
      Um `<form method="post">` cuja `action` carrega `eixo`, `inicio`, `fim`,
      `chave`, `data` e `corrigir` na própria query, e cujo corpo traz `grupo`,
      `categoria` (com `<optgroup>` por grupo e uma primeira opção vazia),
      `grupo_novo`, `natureza` e `essencialidade`. Acima do formulário, dois
      parágrafos de alcance — `id="alcance"` e `id="alcance-categoria"` —, e
      abaixo dele `id="resultado"` ou `id="erro-correcao"`, conforme a resposta.
      Quando o lançamento pedido não existe, só a mensagem é renderizada. Os
      campos `grupo`, `natureza` e `essencialidade` abrem já marcados no que o
      lançamento carrega hoje.
      *Considerando 2.2.*
      *Justificativa:* RF-01, RF-02, RF-04, RF-06, RF-07 e norma 27. A linguagem
      visual é `product/00-linguagem-visual.md`: rótulo em versalete, campo nunca
      abaixo de `--text-base`, cifra em face monoespaçada com `.cifra`, mensagem
      que diz o que aconteceu e qual é o próximo ato, e nenhuma cor nova — o
      bloco só usa classes que `app/static/css/app.css` já declara, porque a
      folha está fora do escopo do item. Nenhuma cifra do bloco leva `negative`:
      `tests/test_gastos_screen.py:148-156` fixa o conjunto exato de cifras
      coloridas, e a régua reserva a cor ao número que pede decisão. O
      `<optgroup>` é a árvore de duas alturas desenhada honestamente, e a
      coerência entre grupo e categoria é conferida no servidor porque é lá que
      RF-07 a cobra.

- [ ] **2.4 — Modificar `app/templates/fragments/gastos_detalhe.html` e
      `app/templates/fragments/gastos_tabela.html`.**
      No detalhe, a descrição de cada linha vira um `<a class="row-open">` que
      leva a `?corrigir={{ row['id'] }}` mantendo `eixo`, `inicio`, `fim` e
      `chave`, com `hx-get` para o fragmento e `aria-label` dizendo que abre a
      correção daquele lançamento; abaixo da tabela, o
      `{% include "fragments/gastos_correcao.html" %}` quando houver correção. Na
      tabela, o `{% with %}` das linhas 56-59 passa a carregar também
      `correction=detail['correction']`.
      *Considerando 1.4* (a linha traz `id`) *e 2.3.*
      *Justificativa:* RF-01. A linha aberta é o único lugar onde o dono já está
      olhando o erro, e "abrir uma linha" é o gesto que a tela já ensina em
      `app/templates/fragments/gastos_tabela.html:31-36`. O link não vira coluna
      nova porque a lista chega a centenas de linhas e uma coluna de botões
      compete com a cifra, que é a protagonista. O `{% with %}` precisa do nome
      novo porque o fragmento de detalhe também é incluído de dentro da tabela, e
      o que não passa por ali chega vazio.

- [ ] **2.5 — Criar `tests/test_gastos_correcao_screen.py`.**
      Abertura do bloco com os dois alcances e o total intacto; gravação com o
      resultado, a regra e a repartição do eixo `grupo`; regra concorrente de id
      menor com o resultado nomeando-a; grupo novo com corpo em bytes UTF-8
      crus; as três recusas com a quarta requisição válida ao lado; o irmão de
      prefixo que fica onde estava; e `/regras` listando a regra escrita daqui.
      *Considerando 2.2, 2.3* e *2.4.*
      *Justificativa:* RF-01 a RF-08. Quem executa é o `pytest` que o CI já roda;
      nenhum portão novo entra em `scripts/gates/` e o `gates_runner.sh` não é
      tocado. A guarda de sessão da rota nova não ganha teste próprio porque
      `tests/test_route_guard.py:37-48` varre todas as rotas registradas e já
      cobra a que entrar.

---

## Execução sugerida

1. **Fase 1, bloqueante.** Ela fixa as duas coisas de que a fase 2 depende
   inteiramente: o gabarito de consulta que prévia e resultado partilham, e o
   casamento exato que faz o conjunto contado e o conjunto alcançado
   coincidirem. Premissa errada aí só aparece na tela, depois de escrita.
   Toca `app/queries/reach.py`, `app/queries/axes.py`, `app/taxonomy/rules.py`,
   `app/taxonomy/seed.json`, `tests/test_reach.py`, `tests/test_corrections.py`
   e `tests/test_axes.py`.
2. **Fase 2 depois da 1.** Toca `app/routers/spending.py`,
   `app/routers/rules.py`, `app/templates/fragments/gastos_correcao.html`,
   `app/templates/fragments/gastos_detalhe.html`,
   `app/templates/fragments/gastos_tabela.html` e
   `tests/test_gastos_correcao_screen.py`.

As duas **não** são paralelas, e a interseção de arquivos entre elas é vazia. A
dependência é de código: a fase 2 importa `correct_payee`, `payee_reach`,
`category_reach` e `holders`, e lê `id` e `payee` da linha aberta — num par de
worktrees ela nasceria vermelha, e o veredicto mediria a ausência da outra frente
em vez do trabalho dela.

## Rastreamento requisito → critério

| Requisito | Fase | Critérios que o cobrem |
|---|---|---|
| RF-01 | 1, 2 | estrutural (`transactions_of` traz `id` e `payee`); estrutural (rota e fragmento novos); comportamental (o bloco aberto traz os quatro campos e o beneficiário); comportamental (grupo novo com corpo em UTF-8 cru); comando (a suíte da tela) |
| RF-02 | 1, 2 | estrutural (gabarito único de consulta); comportamental (alcance por beneficiário, por irmão de prefixo e por categoria); comportamental (alcance da gravação igual à prévia); comportamental (os dois alcances na tela); integração (prévia igual nas duas execuções); integração (o irmão de prefixo não é arrastado) |
| RF-03 | 1, 2 | comportamental (a gravação e o alcance); comportamental (atomicidade com `classify_all` quebrada); comportamental (o POST grava e reparte); integração (o irmão de prefixo); integração (`/regras` lista a regra escrita daqui) |
| RF-04 | 1, 2 | comportamental (grupo novo com posição e escape); comportamental (grupo novo pela tela, com acento) |
| RF-05 | 1, 2 | comportamental (a segunda correção atualiza em vez de criar); integração (`/regras` mostra uma regra só) |
| RF-06 | 1, 2 | estrutural (gabarito único); comportamental (regra concorrente de id menor e `holders`); comportamental (o resultado nomeia a regra que segura); integração (a diferença entre prévia e resultado tem nome) |
| RF-07 | 1, 2 | comportamental (as três recusas com controle positivo, na função); comportamental (as três recusas com controle positivo, na tela) |
| RF-08 | 2 | comportamental (abrir a correção não move total nenhum); comportamental (o total do período segue igual depois da gravação, e só a repartição muda); comando (a suíte inteira) |

## Pendências que viram item de roadmap

- **A semente apaga o grupo criado pelo dono.** `app/taxonomy/seed.py:104-107`
  remove todo grupo que `seed.json` não declara, e `:85-88` repõe as regras dele
  no escape. Não roda em operação normal — nem `create_app` nem a pós-carga da
  sincronização chamam `seed_taxonomy` —, mas quem rodar
  `python -m app.taxonomy.seed` à mão perde o grupo novo e vê as correções
  voltarem para `Outros` em silêncio, que é exatamente o que este item existe
  para impedir. Separar o grupo do dono de um grupo de vocabulário aposentado
  exige marca no esquema, que é migração e requisito que o brief não pede.
- **A categoria escolhida não é gravada em lugar nenhum.** RF-01 manda o dono
  escolhê-la e RF-07 manda recusá-la quando não pertence ao grupo, mas
  `category_rules` não tem coluna para ela e o não-escopo do brief proíbe mexer
  na árvore. Registrar a folha escolhida na regra é migração e mudança de
  contrato.
- **A regra escrita aparece em `/regras` como expressão escapada.** O casamento
  exato é `^mercado\ livre$`, e a lista de regras imprime o `match_value` cru. É
  honesto e é o que a regra faz, mas é regex numa tela de que este item queria
  poupar o dono. Imprimir "beneficiário exato: mercado livre" é mudança na tela
  de regras, que o brief não pede.

## Validações de campo pendentes

- **O bloco de correção em 375px de largura.** Ele não declara medida própria e
  reusa `.controls` e `.field`, que o item `017` já exercita, mas a composição
  nova — dois `<select>`, um campo de texto e um botão dentro de `.detail-open`,
  que por sua vez vive dentro de `.table-scroll` — só o navegador prova. Não há
  critério tipado que a observe, e transformá-la em fase bloqueante travaria o
  item por algo que nenhum agent enxerga. Vai para "Validações de campo
  pendentes" do `roadmap.md` quando o item fechar.
