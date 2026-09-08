# Plano — 023-taxonomia-hierarquica-do-dono

**Item:** `023-taxonomia-hierarquica-do-dono` · **Trilha:** rápida ·
**Fonte aprovada:** `01-brief.md` (RF-01 a RF-08) · **Terreno:**
`00-discovery.md` · Duas fases, em sequência.

> **Toda contagem deste plano foi lida dos arquivos do repositório** em
> 07/09/2026: dez grupos e oitenta regras em `app/taxonomy/seed.json`
> (76 regras casam por categoria, 4 por expressão sobre o beneficiário), e 77
> chaves na seção `category_labels` do mesmo arquivo. Nenhuma delas é remedida
> aqui.
>
> **Um número deste terreno não é medido por critério nenhum.** O R$ 20.272,00
> da norma 25 — o quanto o painel mentiria se transferência entre contas
> próprias e estorno entrassem no total de gasto — está congelado em
> `docs/plano.md`, medido em 05/09/2026, e é a razão de o grupo `Não é gasto`
> existir. Ele fica aqui, como terreno; nenhum critério deste plano o afirma,
> porque nenhum comando deste plano o traz na saída.

## Objetivo

Ao fim das duas fases a classificação primária é uma árvore de duas alturas do
dono: doze grupos que ele reconhece, e dentro de cada um as categorias que a
fonte manda, ligadas por chave estrangeira e com o nome em português numa casa
só. **Nenhum total de gasto muda** — a mesma transação continua sendo a mesma
transação, pega pela mesma regra, com a mesma natureza e a mesma
essencialidade; o que muda é o grupo em que ela aparece e o nome com que a tela
a chama.

A quebra é por **contrato**, e o contrato aqui é o vocabulário de grupo: a fase
1 troca os dez grupos pelos doze do dono e remapeia as oitenta regras, porque
`app/taxonomy/seed.py:55` resolve o grupo de cada regra pelo **nome**
(`groups[entry["group"]]`) — trocar os nomes sem remapear as regras derruba a
semente com `KeyError`, e as duas edições são uma só. É nessa fase que um total
pode se mover sem ninguém ver, e é lá que RF-06 é medido. A fase 2 pendura as 77
categorias nesses grupos, mata a lista paralela de rótulos e leva a árvore até
a tela. Invertida a ordem, a fase da árvore teria de apontar cada categoria para
um grupo que ainda não existe.

## O terreno, lido no código

| Sítio | Hoje | O que falta |
|---|---|---|
| `app/migrations/sql/003_taxonomy.sql:20-23` | `categories` tem `id` e `name`, sem grupo | chave estrangeira para `category_groups` |
| `app/taxonomy/seed.json:2-53` | dez grupos, `Outros` como escape | os doze do dono |
| `app/taxonomy/seed.json:89-649` | 80 regras, cada uma com `group`, `nature`, `essentiality` | o `group` de cada uma remapeado |
| `app/taxonomy/seed.json:651-729` | `category_labels`, 77 rótulos numa lista paralela | virar campo da categoria na árvore |
| `app/taxonomy/seed.py:21-28` | grupos entram com `ON CONFLICT (name) DO NOTHING` | banco já semeado nunca recebe nome novo nem perde nome velho |
| `app/taxonomy/seed.py:48-61` | regras entram com `ON CONFLICT (match_kind, match_value) DO NOTHING` | banco já semeado nunca recebe o grupo remapeado |
| `app/taxonomy/classify.py:104-111` | `_record_categories` grava só o `name` | gravar também o grupo de escape (RF-08) |
| `app/routers/spending.py:33` e `app/routers/rules.py:25` | `LABELS` lê `category_labels` | ler a árvore |

Três fatos decidem o desenho e não se re-discutem:

- **`connect()` liga `PRAGMA foreign_keys = ON`** (`app/db.py:27`). Apagar uma
  linha de `category_groups` referenciada por `category_rules.group_id`, por
  `transactions.group_id` ou — depois da fase 2 — por `categories.group_id`
  levanta `FOREIGN KEY constraint failed`. Os quatro grupos que saem só podem
  ser apagados depois que ninguém os aponta.
- **`seed_taxonomy` não roda sozinha.** `app/main.py:41` chama
  `run_migrations()` e mais nada; quem semeia é o CLI
  `python -m app.taxonomy.seed`, e quem classifica é
  `python -m app.taxonomy.classify`. O banco do dono só recebe o vocabulário
  novo quando os dois rodam — e é por isso que a semente precisa saber
  reconciliar um banco que já tem o vocabulário antigo, em vez de só semear um
  vazio.
- **`tests/test_taxonomy_literals.py:51` proíbe qualquer termo do vocabulário
  como literal em `app/**.{py,sql,html}`.** A migração desta fase é DDL pura,
  sem um único nome de grupo ou de categoria, e a reconciliação da semente é
  escrita contra os dados de `seed.json`, nunca contra nomes escritos no código.

Um quarto fato governa a leitura das telas: **nenhum arquivo de `app/` mostra
nome de grupo vindo de `seed.json`.** O eixo de grupo lê
`category_groups.name` pela junção de `app/queries/axes.py:43`, e `/regras` lê a
mesma tabela; o rótulo que vem da semente é o da categoria, não o do grupo. É
esse fato que torna verificável o estado de um arranque em que só as migrações
rodaram.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| Onde a árvore mora | `00-discovery.md` | `categories` ganha `group_id`; `category_groups` é reescrita, não substituída |
| A migração é qual arquivo | Cinco itens rodam em worktree ao mesmo tempo, e `013`, `014` e `015` estão reservados | **exatamente** `app/migrations/sql/012_taxonomy_tree.sql`, e nenhum outro `.sql` novo |
| `categories` ganha coluna ou é reconstruída | SQLite aceita `ADD COLUMN` com `REFERENCES` só com valor padrão nulo, e `group_id` não aceita nulo | reconstruída na migração: `DROP` e `CREATE`. `categories` é tabela derivada — nada em `app/` a lê, e `classify_all` a repovoa |
| O rótulo vira coluna de `categories` | Uma coluna que nenhum leitor consulta é esquema morto; os dois routers montam `LABELS` no import, sem conexão | não. O rótulo é campo da entrada da categoria em `seed.json`, e `app/taxonomy/seed.py` expõe `category_labels()` |
| Banco já semeado recebe o vocabulário novo como | `ON CONFLICT DO NOTHING` nunca renomeia nem apaga | `seed_taxonomy` reconcilia: atualiza posição e escape dos grupos que ficam, insere os que entram, repõe as referências e apaga os que saem |
| A semente sobrescreve regra que o dono editou | Regra é editável em `/regras`, e `00-discovery.md` protege "este beneficiário é Transporte mesmo que a fonte chame de Compras" | a semente atualiza **só** o `group_id` das regras que ela declara. `nature` e `essentiality` de regra existente ficam intocadas (RF-07) |
| Regra escrita pelo dono apontando para grupo que sai | Não há como adivinhar o grupo novo dela | vai para o grupo de escape `Outros`, e continua existindo (RF-04) |
| A semente reclassifica os lançamentos | Reclassificar é o trabalho de `classify_all`, e os dois CLIs correm em sequência | a semente mexe em `transactions` só onde a chave estrangeira a obriga — os lançamentos presos a um grupo que vai ser apagado |
| Onde mora o "antes" de RF-06 | O validador não tem histórico do git | `tests/data/vocabulario_anterior.json`, cópia congelada da semente de hoje, semeada pelo próprio teste com inserção direta — guarda que compartilha código com o que guarda passa em verde depois de quebrada |
| Dois nomes de grupo colidem com texto de tela | `Assinaturas` está em `app/templates/fragments/comprometido_assinaturas.html:4` e `:17` e em `comprometido_dispensadas.html:13`; `Renda` está em `app/templates/fragments/resumo_mes.html:16` | a varredura de literais passa a ler, em `.html`, só as linhas com expressão Jinja (`{{` ou `{%`). O defeito que ela existe para pegar é **código decidindo por nome**; título de seção é cópia de interface, e é onde palavra em português deve estar |
| Os cinco eixos mudam | `00-discovery.md` | não. `app/queries/axes.json` e `app/queries/axes.py` ficam intocados |
| Algum template muda | `app/templates/fragments/celula.html:3-7` já imprime rótulo e chave crua a partir do mapa que a rota entrega | **nenhum** arquivo de `app/templates/` é tocado |
| O escape encolhe | RF-04 do brief manda não escrever regra nova | não. Encolher `Outros` é o item `019` |

---

## Fase 1 — Os grupos do dono, e as oitenta regras remapeadas (api)

**Objetivo da fase:** `category_groups` passa a ser a lista dos doze grupos do
dono, toda regra aponta para um deles, e os quatro números da mesma base são
idênticos antes e depois.

**Critérios de aceite:**

- [ ] `estrutural` — RF-03
      Em `app/taxonomy/seed.json`, a lista `groups` tem exatamente 12 entradas.
      Lidas em ordem crescente do campo `position`, os `name` são, nesta ordem:
      `Moradia`, `Transporte`, `Alimentação`, `Saúde`, `Educação`,
      `Assinaturas`, `Pessoal`, `Financeiro`, `Dependentes`, `Renda`,
      `Não é gasto`, `Outros`. Os `position` são os inteiros de 1 a 12, sem
      repetição. Exatamente uma entrada tem `is_fallback` verdadeiro, e o `name`
      dela é `Outros`.
- [ ] `comportamental` — RF-03, RF-04
      *Dado* um banco SQLite em diretório temporário com as migrações aplicadas
      por `app.migrate.run_migrations`, uma base de lançamentos carregada,
      semeado com o vocabulário de `tests/data/vocabulario_anterior.json` — que
      traz dez grupos, entre eles `Comer fora e lazer`,
      `Serviços e assinaturas`, `Dívidas e juros` e `Transferências` — e
      `app.taxonomy.classify.classify_all` já executado
      *Quando* `app.taxonomy.seed.seed_taxonomy(conn)` roda com a semente atual
      do repositório, e em seguida `classify_all(conn)` roda duas vezes
      *Então* `SELECT count(*) FROM category_groups` devolve `12`;
      `SELECT name FROM category_groups ORDER BY position` devolve exatamente
      `Moradia`, `Transporte`, `Alimentação`, `Saúde`, `Educação`,
      `Assinaturas`, `Pessoal`, `Financeiro`, `Dependentes`, `Renda`,
      `Não é gasto`, `Outros`, nessa ordem; `SELECT count(*) FROM
      category_rules` devolve `80` e `SELECT count(*) FROM transactions WHERE
      rule_id IS NOT NULL` devolve um número maior que zero — os dois são o
      controle positivo, e sem eles as contagens de zero que vêm a seguir
      passariam igual numa tabela vazia; `SELECT count(*) FROM category_rules AS
      r LEFT JOIN category_groups AS g ON g.id = r.group_id WHERE g.id IS NULL`
      devolve `0`; a semente não levanta exceção de chave estrangeira;
      `SELECT count(*) FROM transactions AS t JOIN category_rules AS r ON
      r.id = t.rule_id WHERE t.group_id != r.group_id` devolve `0` depois da
      primeira classificação; e a segunda chamada de `classify_all(conn)`
      devolve `0`
- [ ] `comportamental` — RF-04
      *Dado* um banco SQLite em diretório temporário com as migrações aplicadas,
      um lançamento de gasto carregado, semeado com o vocabulário de
      `tests/data/vocabulario_anterior.json`, e uma regra escrita por
      `app.taxonomy.rules.create_rule` com `match_kind` igual a `category`,
      `match_value` igual a `Categoria do dono`, apontando para o `id` do grupo
      chamado `Transferências` — nome que a semente atual não traz —, com o
      lançamento classificado por ela
      *Quando* `app.taxonomy.seed.seed_taxonomy(conn)` roda com a semente atual
      *Então* a regra continua existindo, com o mesmo `match_kind`,
      `match_value`, `nature` e `essentiality`; o `group_id` dela é o `id` da
      linha de `category_groups` com `is_fallback = 1`; o lançamento que ela
      pegou tem esse mesmo `group_id`; e `app.taxonomy.classify.classify_all(conn)`
      devolve `0`
- [ ] `comportamental` — RF-04, RF-07
      *Dado* os arquivos `tests/data/vocabulario_anterior.json` e
      `app/taxonomy/seed.json`
      *Quando* a lista `rules` dos dois é lida na ordem em que está no arquivo
      *Então* as duas listas têm 80 entradas; a sequência de tuplas
      `(match_kind, match_value, nature, essentiality)` é igual elemento a
      elemento, na mesma ordem, nas duas; e todo valor do campo `group` da lista
      nova é um de `Moradia`, `Transporte`, `Alimentação`, `Saúde`, `Educação`,
      `Assinaturas`, `Pessoal`, `Financeiro`, `Dependentes`, `Renda`,
      `Não é gasto`, `Outros`
- [ ] `comportamental` — RF-06, RF-07
      *Dado* dois bancos SQLite em diretórios temporários distintos, `antes` e
      `depois`, os dois com as migrações aplicadas e **a mesma** base carregada
      pelo mesmo caminho de ingestão: um lançamento de gasto para cada uma das
      76 regras de `match_kind` igual a `category` de
      `tests/data/vocabulario_anterior.json`, com a `categoria` do lançamento
      igual ao `match_value` da regra e valores em centavos distintos entre si,
      mais um lançamento marcado como transferência, um marcado como estorno, um
      de valor positivo e um cuja `categoria` nenhuma regra alcança; `antes`
      semeado por inserção direta a partir de
      `tests/data/vocabulario_anterior.json` e `depois` semeado por
      `app.taxonomy.seed.seed_taxonomy(conn)`; `classify_all` executado nos dois
      *Quando*, na mesma janela de datas nos dois bancos, são lidos
      `app.queries.spending.total_spending_cents(conn, start, end)`, a contagem
      de lançamentos que satisfazem `app.queries.spending.SPENDING` dentro da
      janela, e `app.queries.crossings.crossing` para os dois `slug` declarados
      na semente — `corte`, rotulado `variável × supérfluo`, e `piso`, rotulado
      `fixa × essencial`
      *Então* a contagem de lançamentos é maior que zero nos dois bancos — sem
      esse piso, a igualdade seguinte se cumpriria entre duas bases vazias —; o
      total em centavos e a contagem de lançamentos são iguais dígito a dígito
      nos dois bancos; para cada uma das duas travessias, `total_cents`,
      `monthly_average_cents` e a lista ordenada de
      `(key, amount_cents, entries)` são iguais elemento a elemento; e a leitura
      `SELECT t.pluggy_id, r.match_value, t.nature, t.essentiality FROM
      transactions AS t LEFT JOIN category_rules AS r ON r.id = t.rule_id ORDER
      BY t.pluggy_id` devolve listas iguais elemento a elemento nos dois bancos —
      cada lançamento continua pego pela mesma regra, com a mesma natureza e a
      mesma essencialidade
- [ ] `comportamental` — RF-03
      *Dado* um banco SQLite em diretório temporário com as migrações aplicadas
      e `app.taxonomy.seed.seed_taxonomy(conn)` executada com a semente atual
      *Quando* é lida `SELECT r.match_value, g.name FROM category_rules AS r
      JOIN category_groups AS g ON g.id = r.group_id WHERE r.match_kind =
      'category' AND r.match_value IN ('Same person transfer',
      'Same person transfer - CASH', 'Transfer - Internal')`
      *Então* a consulta devolve três linhas e o `name` das três é
      `Não é gasto`
- [ ] `comportamental` — RF-03
      *Dado* dois bancos SQLite em diretórios temporários distintos, `antes` e
      `depois`, os dois com as migrações aplicadas e a mesma base carregada — um
      lançamento de gasto para cada regra de `match_kind` igual a `category` de
      `tests/data/vocabulario_anterior.json` —, `antes` semeado a partir de
      `tests/data/vocabulario_anterior.json` e `depois` por
      `app.taxonomy.seed.seed_taxonomy(conn)`, os dois com `classify_all`
      executado
      *Quando* `app.queries.axes.aggregate(conn, axis=app.queries.axes.AXES[0],
      start=..., end=...)` é chamada nos dois sobre a mesma janela — `AXES[0]` é
      o primeiro eixo declarado em `app/queries/axes.json`, que é o de grupo
      *Então* as duas chamadas devolvem pelo menos uma linha cada, a soma de
      `entries` sobre todas as chaves é maior que zero, e essa soma e a soma de
      `amount_cents` sobre todas as chaves são iguais nos dois bancos — é o
      controle positivo, e sem ele a ausência seguinte passaria numa agregação
      vazia; em `depois` nenhuma chave devolvida é `Comer fora e lazer`,
      `Serviços e assinaturas`, `Dívidas e juros` ou `Transferências`, e toda
      chave devolvida é um de `Moradia`, `Transporte`, `Alimentação`, `Saúde`,
      `Educação`, `Assinaturas`, `Pessoal`, `Financeiro`, `Dependentes`,
      `Renda`, `Não é gasto`, `Outros`; e em `antes` pelo menos uma das quatro
      chaves aposentadas aparece
- [ ] `comando` — RF-03, RF-04, RF-06, RF-07
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_taxonomy_remap.py tests/test_taxonomy_seed.py
      tests/test_taxonomy_literals.py` sai com código `0`.
      `tests/test_taxonomy_remap.py` é novo e traz os testes da reconciliação de
      um banco com o vocabulário anterior, da regra do dono que perde o grupo, e
      da comparação dos quatro números entre os dois bancos.
      `tests/test_taxonomy_literals.py` traz, além do que já tem, um teste que
      planta um nome de grupo **dentro de uma expressão Jinja** num arquivo
      `.html` temporário e afirma que a varredura o acusa, e outro que planta o
      mesmo nome em texto corrido de `.html` e afirma que ela não o acusa. Quem
      executa os dois é `pytest`, que o CI já roda: **nenhum portão novo entra
      em `scripts/gates/`** e `gates_runner.sh` não é tocado

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Criar `tests/data/vocabulario_anterior.json`: cópia congelada da
      semente de hoje.**
      Cópia literal de `app/taxonomy/seed.json` como ele está antes de qualquer
      edição desta fase — dez grupos, 80 regras, naturezas, essencialidades,
      travessias e os dois escapes declarados.
      *Considerando:* nada antes — é a primeira etapa, e tem de ser, porque
      depois de 1.2 o arquivo original já não existe para ser copiado.
      *Justificativa:* RF-06. O "antes" da comparação precisa ser um arquivo, e
      não o histórico do git: o validador roda sobre a árvore de trabalho e não
      tem como voltar a um commit. `tests/data/` não é varrida por
      `tests/test_taxonomy_literals.py` (que lê só `app/`) nem por
      `tests/test_frozen_numbers.py` (idem), então a cópia do vocabulário ali
      não viola norma nenhuma.

- [ ] **1.2 — Modificar `app/taxonomy/seed.json`: os doze grupos, e o `group` de
      cada uma das 80 regras.**
      A lista `groups` passa a ter as doze entradas, com `position` de 1 a 12 na
      ordem em que o dono lê — `Moradia`, `Transporte`, `Alimentação`, `Saúde`,
      `Educação`, `Assinaturas`, `Pessoal`, `Financeiro`, `Dependentes`,
      `Renda`, `Não é gasto`, `Outros` — e `is_fallback` verdadeiro só em
      `Outros`. Em cada uma das 80 entradas de `rules`, **só** o campo `group`
      muda; `match_kind`, `match_value`, `nature` e `essentiality` ficam com o
      valor que têm, e a ordem da lista é preservada. `Não é gasto` recebe as
      categorias de transferência entre contas próprias e de estorno; `Outros`
      continua sendo onde cai o que nenhuma regra pega. A seção
      `category_labels` **não** é tocada nesta fase.
      *Considerando 1.1:* a cópia congelada já existe, e é contra ela que a fase
      se mede.
      *Justificativa:* RF-03, RF-04, RF-05, RF-06, RF-07. Mexer em `nature` ou
      `essentiality` de qualquer regra move um dos quatro números, e é
      exatamente o risco central do item; preservar a ordem da lista preserva os
      `id` que `app/taxonomy/classify.py:71` usa como precedência entre regras
      de expressão. `category_labels` sobrevive à fase porque
      `app/routers/spending.py:33` e `app/routers/rules.py:25` ainda a leem, e
      trocar a casa do rótulo é o trabalho da fase 2 — dividir o corte por aqui
      deixa cada fase com uma coisa só que pode dar errado.

- [ ] **1.3 — Modificar `app/taxonomy/seed.py`: a semente passa a reconciliar um
      banco que já tem vocabulário.**
      `seed_taxonomy` continua lendo tudo de `seed.json` e ganha, na ordem:
      (a) grupos com `ON CONFLICT (name) DO UPDATE SET position =
      excluded.position, is_fallback = excluded.is_fallback`; (b) regras com
      `ON CONFLICT (match_kind, match_value) DO UPDATE SET group_id =
      excluded.group_id` — e **só** `group_id`; (c) as regras que sobraram
      apontando para grupo que a semente não declara passam para o `id` do grupo
      com `is_fallback = 1`; (d) os lançamentos que apontam para um desses
      grupos passam a apontar para o `group_id` da regra que os pegou, ou para o
      escape quando `rule_id` é nulo; (e) `DELETE FROM category_groups` das
      linhas cujo `name` não está na semente. Nenhum nome de grupo aparece no
      código: a lista de nomes vem dos dados e entra como parâmetro.
      *Considerando 1.2:* os nomes novos e os aposentados são os da semente
      editada, e a função não precisa saber quais são.
      *Justificativa:* RF-03, RF-04, RF-07. A ordem é imposta pelas chaves
      estrangeiras: `app/db.py:27` liga `PRAGMA foreign_keys = ON`, e apagar um
      grupo antes de (c) e (d) levanta `FOREIGN KEY constraint failed`. O
      `DO UPDATE` das regras é limitado a `group_id` porque o grupo é o que este
      item redefine e a árvore é a fonte da verdade dele (RF-05), enquanto
      `nature` e `essentiality` são do dono — sobrescrevê-las desfaria em
      silêncio o que ele editou em `/regras` e moveria os números que RF-06
      congela. (d) é o mínimo que a chave estrangeira obriga, e não uma
      reclassificação: o lançamento cuja regra apenas mudou de grupo sem que o
      grupo antigo desaparecesse continua onde está até
      `python -m app.taxonomy.classify` rodar, que é o CLI seguinte na rotina e
      o único dono da reclassificação.

- [ ] **1.4 — Modificar `tests/test_taxonomy_literals.py`: doze grupos, e a
      varredura de `.html` restrita a expressão.**
      A constante `GROUPS` passa de 10 para 12. `scan` passa a considerar, em
      arquivos `.html`, só as linhas que contêm `{{` ou `{%`; `.py` e `.sql`
      seguem lidos linha a linha, inteiros. Entram dois testes: um que escreve
      um `.html` temporário com um termo do vocabulário dentro de `{{ ... }}` e
      afirma que a varredura o acusa; outro que escreve o mesmo termo como texto
      de um `<h2>` e afirma que ela não o acusa. Os quatro testes que o arquivo
      já traz seguem intactos.
      *Considerando 1.2:* é ela que põe `Assinaturas` e `Renda` no vocabulário.
      *Justificativa:* RF-03. `Assinaturas` já é título de seção em
      `app/templates/fragments/comprometido_assinaturas.html:4` e `:17` e em
      `comprometido_dispensadas.html:13`, e `Renda` em
      `app/templates/fragments/resumo_mes.html:16` — três arquivos de telas que
      este item não toca e que falam de outra coisa. O defeito que a varredura
      existe para pegar é **código decidindo por nome do vocabulário**, e é isso
      que uma expressão Jinja pode fazer e um título não pode. Instrumento sem
      prova de que reprova é instrumento que passa em verde depois de quebrado,
      e por isso o teste que planta o termo dentro da expressão entra junto;
      quem o executa é `pytest`, e nenhum portão novo entra em `scripts/gates/`.

- [ ] **1.5 — Criar `tests/test_taxonomy_remap.py`.**
      Um auxiliar que constrói a base — um lançamento de gasto por regra de
      categoria do vocabulário anterior, com valores distintos, mais
      transferência, estorno, entrada positiva e categoria sem regra —, um
      auxiliar que instala o vocabulário anterior por `INSERT` próprio a partir
      de `tests/data/vocabulario_anterior.json`, e um auxiliar que lê os quatro
      números de um banco. Os testes: a reconciliação do banco com vocabulário
      antigo, com a segunda `classify_all` devolvendo `0`; a regra do dono que
      perde o grupo e cai no escape; as 80 tuplas de regra idênticas na mesma
      ordem entre os dois arquivos; os quatro números iguais entre `antes` e
      `depois`; o mapa de `(regra, natureza, essencialidade)` por lançamento
      idêntico; as três categorias de transferência própria em `Não é gasto`; e
      o eixo de grupo sem nenhum dos quatro nomes aposentados em `depois` e com
      pelo menos um deles em `antes`.
      *Considerando 1.1, 1.2 e 1.3.*
      *Justificativa:* RF-03, RF-04, RF-06, RF-07. O "antes" é instalado por
      `INSERT` do próprio teste, e não por `seed_taxonomy`, porque uma guarda
      que compartilha código com o que ela guarda passa em verde no dia em que
      esse código quebra. A base tem um lançamento por regra de categoria para
      que qualquer alteração de natureza ou essencialidade em qualquer uma das
      76 mova pelo menos um número; a travessia `variável × supérfluo` mede
      zero nos dois lados hoje — `tests/test_taxonomy_seed.py:54` afirma que
      nenhuma regra semeada nasce com a última essencialidade —, e é justamente
      por isso que a comparação a inclui: ela reprova se o remapeamento
      distribuir `supérfluo` por engano. Toda contagem que o teste compara vem
      acompanhada da contagem que prova que ele mediu alguma coisa: comparação
      de zero com zero entre duas bases vazias é aprovação sem medição.

---

## Fase 2 — A árvore: cada categoria dentro do seu grupo (api)

**Objetivo da fase:** cada uma das 77 categorias pertence a um grupo por chave
estrangeira e tem o nome em português numa casa só, e as telas leem o rótulo
dessa casa.

**Critérios de aceite:**

- [ ] `estrutural` — RF-01
      `app/migrations/sql/012_taxonomy_tree.sql` existe, e é o único arquivo
      `.sql` acrescentado a `app/migrations/sql/` — a pasta passa de onze para
      doze arquivos, e nenhum dos onze anteriores é editado. Sobre um banco
      SQLite vazio em diretório temporário com `app.migrate.run_migrations`
      aplicada, `SELECT name, "notnull" FROM pragma_table_info('categories')`
      traz as colunas `id`, `name` e `group_id`, com `notnull` igual a `1` em
      `group_id`, e `SELECT "table", "from", "to" FROM
      pragma_foreign_key_list('categories')` traz uma linha com
      `category_groups`, `group_id` e `id`
- [ ] `comando` — RF-02
      Os dois comandos abaixo, o primeiro provando que a semente foi lida e que
      a seção que substitui a lista paralela está lá, e só o segundo concluindo
      pela ausência:
      (a) `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -c "from
      app.taxonomy.seed import load_seed; seed = load_seed();
      print(len(seed['categories']), 'category_labels' in seed)"` imprime
      exatamente `77 False`;
      (b) `rtk proxy grep -rn --exclude-dir=__pycache__
      --exclude=vocabulario_anterior.json '"category_labels"' app tests` não
      imprime nenhuma linha, e
      `rtk proxy grep -rl --exclude-dir=__pycache__ 'category_labels' app tests`
      imprime, entre outros, `app/taxonomy/seed.py`, `app/routers/spending.py` e
      `app/routers/rules.py`. A busca de (b) é pela chave **entre aspas**, que é
      a forma como a lista paralela é escrita no dado e lida no código; o
      identificador sem aspas é a função que a substitui, e a segunda busca
      existe para provar que a varredura alcançou arquivos — sem ela, caminho
      errado e arquivo apagado dariam a mesma saída vazia. As duas varrem as
      mesmas raízes, e a única exclusão da primeira é o arquivo
      `tests/data/vocabulario_anterior.json`, cópia congelada do vocabulário
      anterior que os testes instalam como estado "antes" da comparação
      numérica: não é semente, nenhum código o lê como semente, e apagar a chave
      de lá adulteraria a prova em vez de cumprir o requisito. O que a primeira
      busca cobra é a lista paralela como semente e como leitura de código:
      `app/` inteira, `app/taxonomy/seed.json` incluído, e `tests/` inteira
      menos esse único arquivo
- [ ] `estrutural` — RF-01, RF-02
      Em `app/taxonomy/seed.json`, a chave `categories` traz exatamente 77
      entradas; cada entrada tem os campos `name`, `label` e `group`; nenhum
      `name` se repete; e todo `group` é um dos `name` declarados na lista
      `groups` do mesmo arquivo. `app/taxonomy/seed.py` exporta uma função
      `category_labels`, e `app/routers/spending.py` e `app/routers/rules.py`
      montam a constante `LABELS` com o retorno dela
- [ ] `comportamental` — RF-01, RF-05
      *Dado* um banco SQLite em diretório temporário com as migrações aplicadas
      por `app.migrate.run_migrations` e `app.taxonomy.seed.seed_taxonomy(conn)`
      executada
      *Quando* são lidas `SELECT count(*) FROM categories`, `SELECT count(*)
      FROM categories WHERE group_id NOT IN (SELECT id FROM category_groups)`,
      `SELECT count(*) FROM category_rules AS r JOIN categories AS c ON
      c.name = r.match_value WHERE r.match_kind = 'category'` e
      `SELECT r.match_value FROM category_rules AS r JOIN categories AS c ON
      c.name = r.match_value WHERE r.match_kind = 'category' AND r.group_id !=
      c.group_id`
      *Então* a primeira devolve `77`, a segunda devolve `0`, a terceira devolve
      `76` — é ela o controle positivo, que prova que a comparação cruzou 76
      pares de regra e categoria antes de a quarta concluir que nenhum discorda
      —, e a quarta não devolve nenhuma linha; e o teste que a mede imprime, na
      falha, cada `match_value` em que a regra e a árvore discordam
- [ ] `comportamental` — RF-08
      *Dado* um banco SQLite em diretório temporário com as migrações aplicadas,
      `app.taxonomy.seed.seed_taxonomy(conn)` executada, e um lançamento de
      gasto carregado com `categoria` igual a `Categoria que a fonte inventou`
      *Quando* `app.taxonomy.classify.classify_all(conn)` roda
      *Então* a chamada não levanta exceção; `SELECT count(*) FROM categories`
      devolve `78`; a linha de `categories` com `name` igual a
      `Categoria que a fonte inventou` tem `group_id` igual ao `id` da linha de
      `category_groups` com `is_fallback = 1`; e o lançamento fica com `rule_id`
      nulo e com esse mesmo `group_id`
- [ ] `comportamental` — RF-01
      *Dado* um banco SQLite em diretório temporário com as migrações aplicadas,
      `app.taxonomy.seed.seed_taxonomy(conn)` executada, e em seguida
      `UPDATE categories SET group_id = (SELECT id FROM category_groups WHERE
      is_fallback = 1) WHERE name = 'Real estate financing'` aplicado à mão
      *Quando* `app.taxonomy.seed.seed_taxonomy(conn)` roda de novo
      *Então* a linha de `categories` com `name` igual a
      `Real estate financing` aponta para o `id` do grupo chamado `Moradia`, e
      não para o grupo com `is_fallback = 1` — a árvore é a fonte da verdade da
      categoria que ela conhece
- [ ] `comportamental` — RF-02
      *Dado* o painel servido a partir deste repositório, com base carregada,
      semeada e classificada, sessão autenticada, e um lançamento de gasto com
      `categoria` igual a `Real estate financing` dentro da janela padrão de
      `/gastos`
      *Quando* `GET /gastos/tabela?eixo=categoria` é buscada
      *Então* a resposta é `200`, e no recorte do HTML que vai do `<tr` que
      contém `Financiamento imobiliário` até o `</tr>` seguinte aparecem
      `<span class="cell-label">Financiamento imobiliário</span>` e
      `<span class="cell-key">Real estate financing</span>` — o rótulo vem da
      árvore, e a chave crua continua ao lado dele
- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_taxonomy_tree.py tests/test_taxonomy_integration.py
      tests/test_migrations.py tests/test_classify.py tests/test_gastos_screen.py
      tests/test_regras_screen.py` sai com código `0`.
      `tests/test_taxonomy_tree.py` é novo e traz os testes da árvore semeada, da
      discordância entre regra e árvore, da categoria desconhecida que cai no
      escape e da categoria conhecida que a semente corrige.
      `tests/test_taxonomy_integration.py` também é novo e traz os três testes da
      costura entre o vocabulário trocado e a árvore pendurada nele. Quem executa
      os dois arquivos é `pytest`, que o CI já roda: **nenhum portão novo entra
      em `scripts/gates/`** e `gates_runner.sh` não é tocado

**Critérios de integração**

Nenhum dos três se verifica com uma fase só: os dois primeiros exigem os doze
grupos da fase 1 dentro do banco em que a coluna da fase 2 existe, e o terceiro
mede o estado que um arranque deixa depois de as duas terem entrado.

- [ ] `comportamental` — RF-06, RF-07
      *Dado* dois bancos SQLite em diretórios temporários distintos, `antes` e
      `depois`, os dois com **todas** as migrações de `app/migrations/sql/`
      aplicadas em ordem por `app.migrate.run_migrations` e a **mesma** base
      carregada pelo mesmo caminho de ingestão: um lançamento de gasto para cada
      uma das 76 regras de `match_kind` igual a `category` de
      `tests/data/vocabulario_anterior.json` — arquivo que traz dez grupos,
      entre eles `Comer fora e lazer`, `Serviços e assinaturas`,
      `Dívidas e juros` e `Transferências` —, com a `categoria` do lançamento
      igual ao `match_value` da regra e valores em centavos distintos entre si;
      mais um lançamento de gasto com `categoria` igual a
      `Categoria que a fonte inventou`, e um marcado como transferência, um
      marcado como estorno e um de valor positivo, os três com `categoria` nula.
      `antes` recebe o vocabulário anterior por inserção direta a partir de
      `tests/data/vocabulario_anterior.json`; `depois` recebe
      `app.taxonomy.seed.seed_taxonomy(conn)` com a semente do repositório;
      `app.taxonomy.classify.classify_all` executado nos dois
      *Quando*, na mesma janela de datas nos dois bancos, são lidos
      `app.queries.spending.total_spending_cents(conn, start, end)`, a contagem
      de lançamentos que satisfazem `app.queries.spending.SPENDING` dentro da
      janela e `app.queries.crossings.crossing` para os dois `slug` declarados
      na semente — `corte`, rotulado `variável × supérfluo`, e `piso`, rotulado
      `fixa × essencial` —, e, em `depois`, `SELECT count(*) FROM categories`
      *Então* em `depois` a contagem de `categories` devolve `78` e a contagem
      de lançamentos da janela é maior que zero — os dois são o controle
      positivo: provam que a árvore foi realmente semeada no banco em que os
      números são medidos, e que há base medida dos dois lados —; o total em
      centavos e a contagem de lançamentos são iguais dígito a dígito nos dois
      bancos; e, para cada uma das duas travessias, `total_cents`,
      `monthly_average_cents` e a lista ordenada de
      `(key, amount_cents, entries)` são iguais elemento a elemento
- [ ] `comportamental` — RF-01, RF-04, RF-05
      *Dado* um banco SQLite em diretório temporário com **todas** as migrações
      de `app/migrations/sql/` aplicadas por `app.migrate.run_migrations`, o
      vocabulário anterior instalado por inserção direta a partir de
      `tests/data/vocabulario_anterior.json` — dez grupos, entre eles
      `Comer fora e lazer`, `Serviços e assinaturas`, `Dívidas e juros` e
      `Transferências`, e as 80 regras apontando para eles — e, também por
      inserção direta, uma linha de `categories` para cada `match_value` das
      regras de `match_kind` igual a `category`, cada uma com o `group_id` do
      grupo que a regra dela declara nesse vocabulário, de modo que pelo menos
      uma categoria aponta para cada um dos quatro grupos que a semente do
      repositório não traz
      *Quando* `app.taxonomy.seed.seed_taxonomy(conn)` roda uma vez com a
      semente do repositório
      *Então* a chamada não levanta exceção, e em particular nenhuma
      `FOREIGN KEY constraint failed`; `SELECT count(*) FROM category_groups`
      devolve `12` e `SELECT count(*) FROM categories` devolve `77` — os dois
      são o controle positivo, sem o qual a contagem de zero seguinte passaria
      numa tabela vazia —; `SELECT count(*) FROM categories AS c LEFT JOIN
      category_groups AS g ON g.id = c.group_id WHERE g.id IS NULL` devolve `0`;
      e a linha de `categories` com `name` igual a `Same person transfer`, que
      no vocabulário anterior pertencia a `Transferências`, aponta para o `id`
      do grupo chamado `Não é gasto`
- [ ] `comportamental` — RF-03
      *Dado* o painel servido a partir deste repositório sobre um banco SQLite
      em diretório temporário no estado que um arranque deixa quando **só** as
      migrações rodam: todas as migrações de `app/migrations/sql/` aplicadas por
      `app.migrate.run_migrations`; o vocabulário anterior instalado por
      inserção direta a partir de `tests/data/vocabulario_anterior.json`; uma
      base com pelo menos um lançamento de gasto em cada um dos grupos
      `Comer fora e lazer`, `Serviços e assinaturas` e `Dívidas e juros`, cada
      lançamento já com `rule_id`, `group_id`, `nature` e `essentiality`
      gravados por inserção direta, como a classificação anterior os deixou;
      `categories` vazia; sessão autenticada; e **nem**
      `app.taxonomy.seed.seed_taxonomy` **nem**
      `app.taxonomy.classify.classify_all` executadas
      *Quando* `GET /gastos/tabela?eixo=grupo&inicio=...&fim=...` é buscada
      sobre uma janela que cobre os lançamentos carregados
      *Então* a resposta é `200`; o conjunto dos valores impressos dentro de
      `<span class="cell-label">` no corpo devolvido contém
      `Comer fora e lazer`, `Serviços e assinaturas` e `Dívidas e juros` — o
      controle positivo, que prova que a tabela chegou aos dados antes de a
      ausência seguinte ser afirmada —; e nenhum desses valores é `Assinaturas`,
      `Pessoal`, `Financeiro`, `Dependentes`, `Renda` ou `Não é gasto`: com só
      as migrações aplicadas a tela mostra o vocabulário anterior inteiro, e
      nunca um grupo de cada vocabulário lado a lado

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **2.1 — Criar `app/migrations/sql/012_taxonomy_tree.sql`: `categories`
      reconstruída com o grupo a que a categoria pertence.**
      `DROP TABLE categories;` seguido de `CREATE TABLE categories (id INTEGER
      PRIMARY KEY, name TEXT NOT NULL UNIQUE, group_id INTEGER NOT NULL
      REFERENCES category_groups(id));`. DDL pura: nenhum nome de grupo, de
      categoria ou de rótulo aparece no arquivo.
      *Considerando* a fase 1 inteira: os doze grupos já existem, e é a eles que
      a chave estrangeira aponta.
      *Justificativa:* RF-01. SQLite aceita `ALTER TABLE ... ADD COLUMN` com
      `REFERENCES` apenas quando o valor padrão é nulo, e `group_id` não aceita
      nulo — a reconstrução é o único caminho para a coluna obrigatória.
      Reconstruir é seguro porque `categories` é tabela derivada: nada em `app/`
      a lê (só `app/taxonomy/classify.py:104-111` escreve nela), nenhuma outra
      tabela a referencia, e `classify_all` a repovoa a partir de
      `transactions`. O arquivo não carrega vocabulário porque
      `tests/test_taxonomy_literals.py:51` varre `app/**.sql`. O número `012` é
      obrigatório: `013`, `014` e `015` estão reservados a itens que rodam em
      worktree ao mesmo tempo que este.

- [ ] **2.2 — Modificar `app/taxonomy/seed.json`: a seção `categories`, e a
      lista paralela que sai.**
      Entra a chave `categories`, com uma entrada por categoria — `name`, a
      chave crua que a transação carrega; `label`, o nome em português; e
      `group`, um dos doze. São 77 entradas: as 77 chaves que
      `category_labels` traz hoje, cada uma com o `label` que já tinha e o
      `group` a que passa a pertencer. As 76 categorias que alguma regra casa
      recebem o mesmo grupo que a regra delas ganhou na fase 1. A chave
      `category_labels` é removida inteira.
      *Considerando 2.1* (a coluna existe) e a fase 1 (os grupos existem e as
      regras já apontam para eles).
      *Justificativa:* RF-01, RF-02, RF-05. O `group` de cada categoria segue o
      `group` da regra que a casa porque discordância entre árvore e regra é
      defeito de semente e reprova o portão — escrever os dois lados a partir da
      mesma decisão é o que torna a concordância verificável em vez de
      coincidente. Chave crua e rótulo continuam em campos separados porque a
      chave é o que casa a transação na sincronização seguinte
      (`app/routers/spending.py:31-32`) e o rótulo é o que a tela lê.

- [ ] **2.3 — Modificar `app/taxonomy/seed.py`: semear a árvore e expor o mapa
      de rótulos.**
      `seed_taxonomy` passa a gravar `categories` a partir da seção nova, com
      `INSERT INTO categories (name, group_id) ... ON CONFLICT (name) DO UPDATE
      SET group_id = excluded.group_id`, resolvendo o grupo pelo `name` como já
      faz com as regras. Essa gravação entra **antes** do
      `DELETE FROM category_groups` que fecha a reconciliação, e junto dela as
      linhas de `categories` cujo `group_id` continue apontando para grupo que a
      semente não declara passam para o `id` do grupo com `is_fallback = 1` — a
      mesma reposição de referência que a reconciliação já faz com as regras e
      com os lançamentos. Entra `category_labels() -> dict[str, str]`, que
      devolve `{entrada["name"]: entrada["label"]}` a partir da semente. A
      contagem impressa por `main()` ganha as categorias.
      *Considerando 2.2:* a seção existe e é a fonte.
      *Justificativa:* RF-01, RF-02, RF-04. A ordem é imposta pela chave
      estrangeira: `app/db.py:27` liga `PRAGMA foreign_keys = ON`, e num banco
      que já carregava o vocabulário anterior uma categoria pode estar apontando
      para um dos quatro grupos que saem — gravar a árvore depois da exclusão
      levanta `FOREIGN KEY constraint failed` exatamente na única máquina que
      tem banco antigo, que é a do dono. O `DO UPDATE` existe porque a
      classificação pode ter registrado uma categoria conhecida antes de a
      semente rodar — `app/taxonomy/classify.py:104` grava toda categoria que a
      base traz — e nesse caso ela nasce no escape; sem a atualização, a árvore
      nunca a corrigiria. `category_labels()` mora na semente, e não repetida
      nos dois routers, porque duas casas para a mesma derivação é a repetição
      que RF-02 existe para acabar.

- [ ] **2.4 — Modificar `app/taxonomy/classify.py`: a categoria que a árvore não
      conhece nasce no escape.**
      `_fallback(conn)` passa a ser resolvida antes de `_record_categories`, que
      recebe o `id` do grupo de escape e grava
      `INSERT INTO categories (name, group_id) VALUES (?, ?) ON CONFLICT (name)
      DO NOTHING`.
      *Considerando 2.1* (a coluna é obrigatória) e *2.3* (a semente já corrige
      a categoria conhecida que porventura nasça no escape).
      *Justificativa:* RF-08. A carga nunca quebra por vocabulário: uma
      categoria nova da fonte continua sendo registrada, e agora com grupo,
      porque a coluna não aceita nulo. Trocar a ordem preserva
      `tests/test_classify.py:230-234`, que exige `MissingFallbackError`
      nomeando `category_groups` quando a classificação roda antes da semente —
      é `_fallback` que a levanta, e ela passa a levantá-la mais cedo.

- [ ] **2.5 — Modificar `app/routers/spending.py` e `app/routers/rules.py`: o
      rótulo vem da árvore.**
      Nos dois arquivos, a linha que monta `LABELS`
      (`app/routers/spending.py:33` e `app/routers/rules.py:25`) passa a
      `LABELS: dict[str, str] = category_labels()`, e a linha de import que a
      alimenta passa a trazer `category_labels` de `app.taxonomy.seed` — em
      `app/routers/rules.py:12` ao lado de `message`, que continua sendo usada.
      Nenhuma outra linha dos dois arquivos é tocada.
      *Considerando 2.3:* a função existe.
      *Justificativa:* RF-02. A linha de import entra na mesma edição porque
      `load_seed` fica órfã em `app/routers/spending.py` e import não usado
      reprova `ruff check` (F401) em `scripts/lint.sh`, que a norma 35 nomeia. A
      janela padrão de `/gastos` (`app/routers/spending.py:93-105`) pertence a
      outro item que roda em worktree ao mesmo tempo e **não** é tocada; as duas
      linhas desta etapa estão a sessenta linhas dela.

- [ ] **2.6 — Modificar `tests/test_migrations.py` e
      `tests/test_gastos_screen.py`.**
      Em `tests/test_migrations.py`, `012_taxonomy_tree.sql` entra ao fim de
      `EXPECTED_MIGRATIONS` e o `max(version)` esperado em
      `test_second_run_applies_nothing` passa de `011` para `012`;
      `EXPECTED_TABLES` não muda, porque a migração reconstrói uma tabela que já
      existe. Em `tests/test_gastos_screen.py:159`, a busca da categoria cujo
      nome cru já está em português passa a ler a seção `categories`:
      `next(entrada["name"] for entrada in load_seed()["categories"] if
      entrada["name"] == entrada["label"])`.
      *Considerando 2.1* e *2.2.*
      *Justificativa:* RF-01, RF-02. As duas edições são de uma linha cada e
      existem porque a lista de migrações e a lista paralela de rótulos são
      afirmadas nominalmente nesses dois arquivos; sem elas a suíte fica
      vermelha por descrição desatualizada, não por defeito.

- [ ] **2.7 — Criar `tests/test_taxonomy_tree.py`.**
      Os testes: as 77 categorias semeadas, nenhuma sem grupo existente; a
      consulta que cruza regra e árvore, com a contagem dos 76 pares cruzados
      afirmada antes da ausência de discordância e com a falha nomeando cada
      `match_value` em desacordo; a categoria que a fonte inventou, registrada
      no escape sem quebrar a classificação; a categoria conhecida rebaixada à
      mão ao escape e corrigida pela semente seguinte; e o rótulo lido de
      `app.taxonomy.seed.category_labels()` batendo com a seção `categories`.
      *Considerando 2.2 a 2.4.*
      *Justificativa:* RF-01, RF-02, RF-05, RF-08. A concordância entre árvore e
      regra é o portão que `00-discovery.md` pede: sem ele, duas verdades sobre
      o mesmo lançamento convivem e quem decide passa a ser a ordem de execução.
      A contagem dos pares cruzados entra ao lado da ausência porque uma junção
      que não casa nada não devolve discordância nenhuma e passaria em verde. O
      teste da categoria desconhecida é o que prova que a coluna obrigatória
      não transformou vocabulário novo em falha de carga.

- [ ] **2.8 — Criar `tests/test_taxonomy_integration.py`: a costura entre as
      duas fases.**
      Três testes, todos sobre banco em diretório temporário com **todas** as
      migrações aplicadas: (a) os quatro números do vocabulário anterior contra
      os do vocabulário novo, com a árvore semeada e `classify_all` rodado nos
      dois lados, e a contagem de `categories` do lado novo como controle
      positivo; (b) um banco que carrega o vocabulário anterior **com linhas de
      `categories` apontando para os quatro grupos que saem**, sobre o qual
      `seed_taxonomy` roda uma vez sem levantar chave estrangeira e depois do
      qual nenhuma categoria aponta para grupo inexistente; (c) o estado do
      arranque — só migrações, nenhum CLI —, em que
      `GET /gastos/tabela?eixo=grupo` responde `200` com os grupos do
      vocabulário anterior e com nenhum dos seis nomes que só o vocabulário novo
      tem. O auxiliar que instala o vocabulário anterior por `INSERT` próprio e
      o que constrói a base são os mesmos de `tests/test_taxonomy_remap.py`,
      importados de lá.
      *Considerando* a fase 1 inteira e as etapas 2.1 a 2.5.
      *Justificativa:* RF-01, RF-03, RF-04, RF-06, RF-07. Cada fase é julgada
      sozinha, e o defeito que mora entre as duas não tem dono: a fase 1 apaga
      grupo, a fase 2 cria a coluna que passa a referenciá-lo, e é a ordem
      dentro de `seed_taxonomy` que decide se a exclusão levanta
      `FOREIGN KEY constraint failed` no único banco que já tem vocabulário
      antigo — o do dono, que nenhum teste de fase alcança. (a) remede RF-06 com
      a árvore dentro, porque o número que a fase 1 congelou foi medido num
      banco sem ela. (c) é o que impede que o item deixe a tela com um grupo de
      cada vocabulário lado a lado enquanto ninguém rodou os dois CLIs: a
      defasagem é pendência conhecida de roadmap, a mistura seria defeito novo.
      Quem executa os três é `pytest`, pelo comando que a fase declara: nenhum
      portão novo entra em `scripts/gates/` e `gates_runner.sh` não é tocado.

---

## Execução sugerida

1. **Fase 1, bloqueante.** Toca `app/taxonomy/seed.json`,
   `app/taxonomy/seed.py`, `tests/test_taxonomy_literals.py`,
   `tests/test_taxonomy_remap.py` (novo) e `tests/data/vocabulario_anterior.json`
   (novo).
2. **Fase 2 depois da 1.** Toca `app/migrations/sql/012_taxonomy_tree.sql`
   (novo), `app/taxonomy/seed.json`, `app/taxonomy/seed.py`,
   `app/taxonomy/classify.py`, `app/routers/spending.py`,
   `app/routers/rules.py`, `tests/test_migrations.py`,
   `tests/test_gastos_screen.py`, `tests/test_taxonomy_tree.py` (novo) e
   `tests/test_taxonomy_integration.py` (novo).

As duas **não** são paralelas, e a dependência é dupla. De dados: cada categoria
da fase 2 aponta para um grupo que só existe depois da fase 1, e a concordância
entre árvore e regra (RF-05) só é verificável quando as regras já foram
remapeadas. De arquivo: as duas editam `app/taxonomy/seed.json` e
`app/taxonomy/seed.py`, que é a interseção mais cara que este item tem.

Contra as outras cinco worktrees, a interseção declarada é
`tests/test_migrations.py` — que todo item com migração edita, numa linha de
lista — e `tests/test_gastos_screen.py`, numa linha. Nenhum arquivo de
`app/queries/`, `app/routers/reference.py`, `app/main.py`,
`app/routers/settings.py`, `app/templates/` ou dos pacotes `app/debts/`,
`app/advisor/`, `app/cards/` e `app/financings/` é tocado.

## Pendências que viram item de roadmap

- **A varredura de literais deixa de ler texto corrido de `.html`.** Depois da
  etapa 1.4, um template que escrevesse `<h2>Moradia</h2>` à mão — em vez de
  imprimir o nome que veio dos dados — passa sem ser acusado. É troca
  consciente: dois dos doze grupos do dono (`Assinaturas` e `Renda`) já são
  palavras de cópia de interface em três arquivos de tela que este item não
  toca, e a alternativa seria renomear grupo que o brief fixa. O defeito que a
  varredura existe para pegar — código decidindo por nome do vocabulário —
  continua coberto, porque em template ele mora dentro de `{{ }}` ou `{% %}`.
- **Nenhuma rotina aplica a semente sozinha.** `app/main.py:41` roda só as
  migrações; o vocabulário novo só chega ao banco do dono quando ele executa
  `python -m app.taxonomy.seed` e `python -m app.taxonomy.classify`. É como o
  produto já funciona antes deste item, e não é o item que cria a pendência —
  mas depois desta mudança a diferença entre rodar e não rodar deixa de ser
  invisível: até os dois CLIs rodarem, a tela segue mostrando os dez grupos
  antigos. O que os critérios de integração da fase 2 cobram é que essa
  defasagem seja **inteira**: com só as migrações aplicadas, a tela mostra o
  vocabulário anterior por completo, e nunca um grupo velho ao lado de um novo.
  A pendência é a defasagem, que já existia; mistura seria defeito criado por
  este item, e há critério contra ela.
- **RF-05 é medido sobre a semente, não sobre o banco do dono.** A tela
  `/regras` deixa o dono mudar o grupo de uma regra, e essa edição pode
  discordar da árvore — é o que `00-discovery.md` protege deliberadamente
  ("este beneficiário é Transporte mesmo que a fonte chame de Compras"). O
  portão afirma a concordância sobre um banco recém-semeado; a divergência que
  o dono cria à mão é escolha dele, e nada a acusa.

## Validações de campo pendentes

Nenhuma. Todo comportamento deste item se observa por consulta SQL a banco de
teste em diretório temporário, por leitura dos arquivos de dados da semente e
por requisição HTTP ao painel servido do próprio repositório; nada depende de
aparelho físico, permissão de plataforma ou rede real.
