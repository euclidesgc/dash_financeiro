# Plano — Gastos em três eixos

**Item:** `002-gastos-tres-eixos` · **Trilha:** rápida · **Brief:** `01-brief.md`
(aprovado em 2026-09-06)

## Objetivo

Ao fim das quatro fases o dono lê os próprios gastos por grupo, categoria,
beneficiário, natureza e essencialidade, em qualquer período, desce de qualquer
linha até a transação, vê os dois cruzamentos que decidem — variável × supérfluo
e fixa × essencial — e corrige a classificação numa tela, sem deploy e sem
reingestão.

A quebra é por **contrato**, não por camada. A fase 1 fixa a forma do dado — as
tabelas da taxonomia, as colunas de classificação em `transactions` e a ordem
determinística das regras — porque premissa errada de contrato se espalha de uma
vez para os cinco eixos, os dois cruzamentos e as duas telas. A fase 2 consome
esse contrato em consultas puras, sem tela, e é onde todo número congelado é
cobrado. As fases 3 e 4 vestem as duas telas sobre consultas já provadas: erro de
agregação descoberto dentro de um template custa a tela inteira de novo.

Convenções que atravessam o plano e que os comandos dos critérios assumem:

- Identificadores de código em inglês; texto de interface, mensagem de erro e
  parâmetro de URL em pt-BR (norma 16, seguindo o `senha` do formulário de login).
- O caminho do banco vem de `DASH_DB_PATH`; o arquivo de ambiente vem de
  `DASH_ENV_FILE`. **Nenhum comando deste plano lê o `.env` do dono**: todo
  comando que carrega configuração declara `DASH_ENV_FILE=/dev/null` e, quando
  precisa de credencial, declara a própria na linha.
- Banco de verificação sempre em `/tmp`, nunca em `data/`. O ambiente é `.venv/`
  na raiz.
- `python -m app.query "<select …>"` é o instrumento de evidência de banco;
  `python -m app.migrate` aplica migrações; `python -m app.ingest` carrega a
  fonte de 05/09/2026.
- Os cinco eixos se nomeiam `grupo`, `categoria`, `beneficiario`, `natureza` e
  `essencialidade`.
- Valor em centavos inteiros, negativo = dinheiro saindo (invariante 22).
  Formatação em reais é da apresentação.

## Fase 1 — Taxonomia e motor de classificação (python)

**Objetivo da fase:** a classificação passa a morar em tabela editável, e todo
lançamento do banco ganha grupo, natureza, essencialidade e beneficiário por
regra aplicada em ordem determinística.

**Critérios de aceite:**

- [ ] `comando` — RF-01
      Depois de `rm -f /tmp/dash-002-f1.sqlite && rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f1.sqlite
      .venv/bin/python -m app.migrate`, o comando `rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f1.sqlite
      .venv/bin/python -m app.query "select (select count(*) from sqlite_master
      where type='table' and name in
      ('category_groups','categories','category_rules','natures','essentialities','crossings')),
      (select count(*) from pragma_table_info('transactions') where name in
      ('payee','group_id','nature','essentiality','rule_id')), (select count(*)
      from sqlite_master where type='index' and name='idx_transactions_payee')"`
      imprime `6 5 1`
- [ ] `comando` — RF-01
      `rtk proxy grep -Ec "payee|category_groups|category_rules|natures|essentialities|crossings"
      app/migrations/sql/001_schema.sql app/migrations/sql/002_session_epoch.sql`
      imprime exatamente as duas linhas `app/migrations/sql/001_schema.sql:0` e
      `app/migrations/sql/002_session_epoch.sql:0`
- [ ] `comando` — RF-02, RF-03
      Com `/tmp/dash-002-f1.sqlite` carregado por `rm -f /tmp/dash-002-f1.sqlite
      && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.ingest`, o
      comando `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.query "select
      'grupos=' || (select group_concat(name, ',') from (select name from
      category_groups order by position)) || ' naturezas=' || (select
      group_concat(value, ',') from (select value from natures order by
      position)) || ' essencialidades=' || (select group_concat(value, ',') from
      (select value from essentialities order by position))"` imprime
      `grupos=Moradia,Educação,Transporte,Alimentação,Comer fora e lazer,Saúde,Serviços e assinaturas,Dívidas e juros,Transferências,Outros naturezas=fixa,variável,eventual essencialidades=essencial,importante,supérfluo`
- [ ] `comando` — RF-04, RF-05
      Com `/tmp/dash-002-f1.sqlite` carregado por `rm -f /tmp/dash-002-f1.sqlite
      && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.ingest`, o
      comando `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.query "select
      (select count(distinct category) from transactions), (select count(*) from
      categories c where not exists (select 1 from category_rules r where
      r.match_kind = 'category' and r.match_value = c.name)), (select count(*)
      from category_rules where essentiality = 'supérfluo'), (select count(*) >
      0 from category_rules where match_kind = 'category'), (select count(*) > 0
      from category_rules where match_kind = 'description'), (select count(*)
      from category_rules where group_id is null or nature is null or
      essentiality is null), (select count(*) from categories c where c.name =
      'Não classificado' and not exists (select 1 from category_rules r where
      r.match_kind = 'category' and r.match_value = c.name))"` imprime
      `77 1 0 1 1 0 1` — a única categoria sem regra de categoria é
      `Não classificado`
- [ ] `comportamental` — RF-06
      *Dado* o banco `/tmp/dash-002-f1.sqlite` carregado por `rm -f
      /tmp/dash-002-f1.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.ingest`
      *Quando* `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.taxonomy.seed`
      é executado mais duas vezes seguidas
      *Então* as duas execuções saem com código 0, e o comando `rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f1.sqlite
      .venv/bin/python -m app.query "select (select count(*) from
      category_groups), (select count(*) from natures), (select count(*) from
      essentialities), (select count(*) from crossings), (select count(*) from
      category_rules)"` imprime a mesma linha antes e depois delas, começando por
      `10 3 3 2 `
- [ ] `comportamental` — RF-07
      *Dado* o banco `/tmp/dash-002-f1.sqlite` carregado por `rm -f
      /tmp/dash-002-f1.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.ingest`, e o
      `id` do grupo `Outros` lido de `category_groups`
      *Quando* `app.taxonomy.rules.create_rule` é chamada três vezes contra esse
      banco, sempre com `match_kind='category'` e `match_value='Zzz'` — a
      primeira com `group_id=9999`, `nature='fixa'`, `essentiality='essencial'`;
      a segunda com o `id` do grupo `Outros`, `nature='fixo'`,
      `essentiality='essencial'`; a terceira com o `id` do grupo `Outros`,
      `nature='fixa'`, `essentiality='dispensável'`
      *Então* as três chamadas levantam `app.taxonomy.rules.InvalidTermError`
      com as mensagens `grupo inválido: 9999`, `natureza inválida: fixo` e
      `essencialidade inválida: dispensável`, e `rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f1.sqlite
      .venv/bin/python -m app.query "select count(*) from category_rules where
      match_value = 'Zzz'"` imprime `0`
- [ ] `comando` — RF-08
      `rtk proxy .venv/bin/python -c "import json, pathlib, sys; seed =
      json.loads(pathlib.Path('app/taxonomy/seed.json').read_text());
      termos = {g['name'] for g in seed['groups']} | set(seed['natures']) |
      set(seed['essentialities']) | {r['match_value'] for r in seed['rules'] if
      r['match_kind'] == 'category'}; alvos = [p for ext in ('py','sql','html')
      for p in pathlib.Path('app').rglob('*.' + ext)]; achados = [f'{p}:{t}' for
      p in alvos for t in termos if t in p.read_text()]; print(len(achados),
      achados[:5]); sys.exit(1 if achados else 0)"` imprime `0 []` e sai com
      código 0 — nenhum nome de grupo, natureza, essencialidade ou categoria do
      seed aparece como literal em arquivo de código de `app/`
- [ ] `comando` — RF-09
      Com `/tmp/dash-002-f1.sqlite` carregado por `rm -f /tmp/dash-002-f1.sqlite
      && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.ingest`, o
      comando `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.query "select
      (select count(*) from transactions where group_id is null or nature is
      null or essentiality is null), (select count(*) from transactions where
      payee is null or payee = ''), (select count(*) from transactions)"` imprime
      `0 0 1942`
- [ ] `comando` — RF-10
      `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -c "import json; from
      app.db import connect; from app.ingest.normalize import
      normalize_description; fonte =
      json.load(open('data/processed/transacoes.json')); banco =
      dict(connect().execute('select pluggy_id, payee from transactions'));
      print(sum(1 for l in fonte if normalize_description(l['descricao']) !=
      l['chave']), sum(1 for l in fonte if banco.get(l['id']) != l['chave']),
      len(fonte))"` imprime `0 0 1942`
- [ ] `comportamental` — RF-11
      *Dado* o banco `/tmp/dash-002-f1.sqlite` carregado por `rm -f
      /tmp/dash-002-f1.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.ingest`, e a
      assinatura da classificação gravada por `rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f1.sqlite
      .venv/bin/python -m app.query "select count(*), sum(rule_id), sum(group_id),
      sum(length(nature) + length(essentiality)) from transactions" >
      /tmp/dash-002-antes.txt`
      *Quando* `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m
      app.taxonomy.classify` é executado mais duas vezes seguidas e a mesma
      consulta é gravada em `/tmp/dash-002-depois.txt`
      *Então* `rtk proxy diff /tmp/dash-002-antes.txt /tmp/dash-002-depois.txt`
      não imprime nenhuma linha, e a primeira coluna dos dois arquivos é `1942`
- [ ] `comportamental` — RF-11
      *Dado* o banco `/tmp/dash-002-ordem.sqlite` carregado por `rm -f
      /tmp/dash-002-ordem.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-ordem.sqlite .venv/bin/python -m app.ingest`, e
      uma regra de expressão gravada por `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-ordem.sqlite .venv/bin/python -c "from app.db
      import connect; from app.taxonomy.rules import create_rule; c = connect();
      g = c.execute(\"select id from category_groups where name = 'Saúde'\").fetchone()[0];
      print(create_rule(c, match_kind='description', match_value='ifood',
      group_id=g, nature='variável', essentiality='importante'))"` — uma
      expressão que alcança lançamentos cuja categoria já tem regra própria
      *Quando* `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-ordem.sqlite .venv/bin/python -m
      app.query "select count(*) from transactions t join category_rules r on
      r.id = t.rule_id where r.match_kind = 'description' and r.match_value =
      'ifood'"` é executado
      *Então* o número impresso é maior que zero e igual ao de
      `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-ordem.sqlite .venv/bin/python -m app.query
      "select count(*) from transactions where lower(description) like
      '%ifood%'"` — a regra de expressão venceu a regra de categoria em todos os
      lançamentos que as duas alcançavam
- [ ] `comportamental` — RF-12
      *Dado* o banco `/tmp/dash-002-f1.sqlite` carregado por `rm -f
      /tmp/dash-002-f1.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.ingest` e
      copiado por `cp /tmp/dash-002-f1.sqlite /tmp/dash-002-residuo.sqlite`
      *Quando* a regra de `category_rules` com `match_kind = 'category'` e
      `match_value = 'Eating out'` é removida de `/tmp/dash-002-residuo.sqlite` e
      `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-residuo.sqlite .venv/bin/python -m
      app.taxonomy.classify` é executado
      *Então* `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-residuo.sqlite .venv/bin/python -m app.query
      "select count(*) from transactions t join category_groups g on g.id =
      t.group_id where t.category = 'Eating out' and t.rule_id is null and
      g.is_fallback = 1 and t.nature = (select value from natures where
      is_fallback = 1) and t.essentiality = (select value from essentialities
      where is_fallback = 1)"` imprime `128`, e `rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-residuo.sqlite
      .venv/bin/python -c "from app.db import connect; from
      app.taxonomy.classify import residue; linha = residue(connect(),
      start='2026-03-01', end='2026-08-31'); print(linha['entries'],
      linha['amount_cents'])"` imprime `60 -436013`
- [ ] `comportamental` — RF-13
      *Dado* o banco `/tmp/dash-002-f1.sqlite` carregado por `rm -f
      /tmp/dash-002-f1.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f1.sqlite .venv/bin/python -m app.ingest` e
      copiado por `cp /tmp/dash-002-f1.sqlite /tmp/dash-002-corte.sqlite`
      *Quando* a essencialidade da regra com `match_kind = 'category'` e
      `match_value = 'Eating out'` passa de `importante` para `supérfluo` por uma
      chamada a `app.taxonomy.rules.update_rule` contra
      `/tmp/dash-002-corte.sqlite`, sem reingestão e sem reiniciar o processo
      *Então* a chamada devolve `128` como número de lançamentos reclassificados,
      e a chamada seguinte a `app.queries.crossings.crossing(conn, slug='corte',
      start='2026-03-01', end='2026-08-31')`, no mesmo processo, traz entre suas
      linhas uma com chave `Eating out`, `amount_cents` igual a `-436013` e
      `entries` igual a `60`
- [ ] `comando` — RF-14
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_rules_atomicity.py` sai com código 0, e o teste
      `tests/test_rules_atomicity.py::test_a_failed_reclassification_leaves_no_row_changed`
      grava uma regra num banco temporário com
      `app.taxonomy.classify.classify_all` substituída por uma função que levanta
      `RuntimeError` depois de escrever parte das linhas, e afirma que a contagem
      de `category_rules` e a lista de `(id, rule_id, group_id, nature,
      essentiality)` de todos os lançamentos são idênticas às lidas antes da
      chamada

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Criar `app/migrations/sql/003_taxonomy.sql` com
      `category_groups(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
      position INTEGER NOT NULL, is_fallback INTEGER NOT NULL DEFAULT 0)`,
      `natures(value TEXT PRIMARY KEY, position INTEGER NOT NULL, is_fallback
      INTEGER NOT NULL DEFAULT 0)`, `essentialities` com a mesma forma de
      `natures`, `categories(id INTEGER PRIMARY KEY, name TEXT NOT NULL
      UNIQUE)`, `category_rules(id INTEGER PRIMARY KEY, match_kind TEXT NOT NULL,
      match_value TEXT NOT NULL, group_id INTEGER NOT NULL REFERENCES
      category_groups(id), nature TEXT NOT NULL REFERENCES natures(value),
      essentiality TEXT NOT NULL REFERENCES essentialities(value), UNIQUE
      (match_kind, match_value))`, `crossings(id INTEGER PRIMARY KEY, slug TEXT
      NOT NULL UNIQUE, label TEXT NOT NULL, nature TEXT NOT NULL REFERENCES
      natures(value), essentiality TEXT NOT NULL REFERENCES
      essentialities(value), position INTEGER NOT NULL)`, mais
      `ALTER TABLE transactions ADD COLUMN` para `payee TEXT`, `group_id INTEGER
      REFERENCES category_groups(id)`, `nature TEXT REFERENCES natures(value)`,
      `essentiality TEXT REFERENCES essentialities(value)` e `rule_id INTEGER
      REFERENCES category_rules(id)`, e os índices `idx_transactions_payee`,
      `idx_transactions_group_id` e `idx_transactions_date`.
      Justificativa: RF-01, RF-03 e RF-08 — o vocabulário fechado vira tabela
      referenciada por chave estrangeira em vez de `CHECK` com literal, porque
      `app/db.py` já liga `PRAGMA foreign_keys = ON` e a recusa de RF-07 passa a
      vir do banco, não de um `if` com o nome da natureza dentro. `is_fallback`
      existe porque RF-12 precisa do balde de resíduo sem que `Outros`,
      `eventual` e `importante` apareçam escritos em `app/`. `crossings` é tabela
      pela mesma razão: sem ela, "variável × supérfluo" seria literal dentro da
      condição da consulta de RF-25.
- [ ] 1.2 Criar `app/ingest/normalize.py` com `normalize_description(text: str |
      None) -> str`, reproduzindo a normalização de
      `ingestao/pluggy_consolidate.py` (NFKD sem combinantes, minúsculas, data e
      parcela removidas, o que não é letra vira espaço, espaços colapsados).
      Justificativa: D1 — o beneficiário é a descrição normalizada, e `ingestao/`
      é script de fora do pacote, não importável por `app/` (norma 15). O
      beneficiário precisa ser derivável de `transactions.description` para os
      lançamentos já carregados, não só do campo `chave` do arquivo de origem.
- [ ] 1.3 Modificar `app/ingest/loader.py` para gravar
      `payee = normalize_description(raw["descricao"])` na linha da transação.
      Justificativa: D1 — coluna com índice é o que torna o agrupamento por
      beneficiário barato; o SQLite não tem regex para fazer isso em tempo de
      consulta.
- [ ] 1.4 Criar `app/taxonomy/seed.json` com os dez grupos (com `position` e o
      `is_fallback` de `Outros`), as três naturezas, as três essencialidades, os
      dois cruzamentos (`corte` = variável × supérfluo, `piso` = fixa ×
      essencial) e as regras iniciais: uma regra `category` para **cada uma das
      76 categorias nomeadas da base**, deixando `Não classificado` de fora, e
      regras `description` **apenas** para padrões que aparecem em lançamentos
      cuja categoria é `Não classificado` ou vazia.
      Justificativa: RF-05 e RF-13 — regra de expressão vence regra de categoria
      (RF-11), então uma expressão que alcance lançamento de categoria já coberta
      roubaria linhas dela e quebraria a contagem de 128 de `Eating out`.
      `Não classificado` fica sem regra de propósito: é o nome que a consolidação
      deu ao que ninguém classificou, e cobri-lo esvaziaria o balde de resíduo no
      primeiro dia, escondendo o que precisa de olho. O
      arquivo é JSON, e não `.py`, porque o vocabulário não pode aparecer em
      arquivo de código de `app/` (RF-08). D2 manda: nenhuma regra do seed nasce
      `supérfluo`.
- [ ] 1.5 Criar `app/taxonomy/seed.py` com `seed_taxonomy(conn) -> None`,
      idempotente por `INSERT … ON CONFLICT DO NOTHING` sobre as chaves únicas, e
      CLI `python -m app.taxonomy.seed`.
      Justificativa: RF-06 — o seed roda em toda carga, e uma segunda execução
      que duplicasse regra mudaria a ordem de precedência de RF-11 sem ninguém
      pedir.
- [ ] 1.6 Criar `app/taxonomy/classify.py` com `classify_all(conn) -> int`,
      `residue(conn, *, start, end) -> sqlite3.Row` (colunas `entries` e
      `amount_cents`, contando só `rule_id IS NULL`) e CLI
      `python -m app.taxonomy.classify`. `classify_all` preenche `payee` onde
      estiver vazio, atualiza `categories` com as categorias distintas
      observadas, avalia as regras em ordem — `description` antes de `category`,
      `id` crescente dentro do tipo, primeira que casa vence — e grava tudo numa
      única transação SQL.
      Justificativa: RF-09, RF-11 e RF-12 — a ordem explícita é o que torna o
      total explicável na tela de Regras, e materializar o resultado na linha do
      lançamento é o que mantém a agregação lendo coluna indexada. Resíduo é
      `rule_id IS NULL`, **não** grupo `Outros`: outras regras do seed
      também apontam para `Outros`, e confundir os dois faria a tela dizer que há
      resíduo onde há classificação declarada.
- [ ] 1.7 Criar `app/taxonomy/rules.py` com `create_rule`, `update_rule` e
      `delete_rule` — cada uma devolvendo o número de lançamentos reclassificados
      —, `InvalidTermError` (mensagens `grupo inválido: <valor>`,
      `natureza inválida: <valor>`, `essencialidade inválida: <valor>`) e
      `InvalidExpressionError` (mensagem `expressão inválida: <valor>`). A
      gravação e a reclassificação que ela dispara acontecem na **mesma**
      transação SQL, com `rollback` em qualquer falha.
      Justificativa: RF-07, RF-13, RF-14 e RF-42 — uma base meio reclassificada é
      pior que uma não reclassificada, porque o total continua somando e passa a
      mentir; e a mensagem que nomeia o valor recusado é o que transforma o erro
      mudo em erro corrigível na tela.
- [ ] 1.8 Modificar `app/ingest/__main__.py` para chamar `seed_taxonomy` e
      `classify_all` depois de uma carga bem-sucedida.
      Justificativa: RF-09 fala de *todo* lançamento; base carregada e não
      classificada deixaria a afirmação falsa no intervalo entre dois comandos, e
      o seed é idempotente (RF-06), então rodar sempre não custa nada.
- [ ] 1.9 Criar `tests/test_normalize.py`, que percorre os 1.942 registros de
      `data/processed/transacoes.json` e afirma
      `normalize_description(l["descricao"]) == l["chave"]`.
      Justificativa: a normalização foi reescrita dentro de `app/` a partir de um
      script que não é importável; sem o teste que a casa registro a registro com
      a origem, a divergência só apareceria como beneficiário errado numa tela,
      meses depois. Quem executa é o `pytest`, rodado pelo job `testes` de
      `.github/workflows/harness.yml`.
- [ ] 1.10 Criar `tests/test_taxonomy_literals.py`, que varre `app/**/*.py`,
      `app/**/*.sql` e `app/**/*.html` procurando os dez nomes de grupo, as três
      naturezas, as três essencialidades e os nomes de categoria da Pluggy, e
      falha citando arquivo e linha; mais um caso que planta um desses literais
      num arquivo temporário e afirma que o varredor o encontra.
      Justificativa: RF-08 é a regra que mais barato se quebra — basta um
      `WHERE nature = 'fixa'` escrito com pressa — e um varredor que nunca reprova
      é indistinguível de um que não roda. Quem executa é o `pytest`, rodado pelo
      job `testes` de `.github/workflows/harness.yml`.
- [ ] 1.11 Criar `tests/test_taxonomy_seed.py` (idempotência e vocabulário),
      `tests/test_classify.py` (ordem de precedência, resíduo e reclassificação
      sem reingestão), `tests/test_rules.py` (recusa de termo fora do vocabulário
      e de expressão que não compila) e `tests/test_rules_atomicity.py` (a
      reclassificação que falha no meio não deixa linha alterada).
      Justificativa: RF-11, RF-12 e RF-14 são os modos de falha caros de
      descobrir tarde, porque nenhum deles quebra a tela — todos produzem um
      total plausível e errado. Quem executa é o `pytest`, rodado pelo job
      `testes` de `.github/workflows/harness.yml`.

## Fase 2 — Agregação pelos cinco eixos (python)

**Objetivo da fase:** existem as consultas que reparticionam o mesmo total pelos
cinco eixos, os dois cruzamentos, a série de treze meses e o drill-down até a
transação — sem nenhuma tela.

**Critérios de aceite:**

Todos os comandos desta fase correm contra o banco preparado por
`rm -f /tmp/dash-002-f2.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-002-f2.sqlite .venv/bin/python -m app.ingest`, e todos
levam o prefixo `rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-002-f2.sqlite`.

- [ ] `comando` — RF-15, RF-16
      `.venv/bin/python -c "from app.db import connect; from app.queries.axes
      import aggregate; linhas = aggregate(connect(), axis='grupo',
      start='2026-03-01', end='2026-08-31'); print(len(linhas) > 0,
      sum(l['amount_cents'] for l in linhas), sum(l['entries'] for l in
      linhas))"` imprime `True -10377233 732`
- [ ] `comando` — RF-17
      `.venv/bin/python -c "from app.db import connect; from app.queries.axes
      import aggregate; linhas = aggregate(connect(), axis='categoria',
      start='2026-03-01', end='2026-08-31'); print(len(linhas)); [print(l['key'],
      l['amount_cents'], l['entries']) for l in linhas[:10]]"` imprime `52` e, em
      seguida, exatamente estas dez linhas nesta ordem: `School -1299218 20`,
      `Real estate financing -1235881 5`, `Services -877412 48`, `Loans and
      financing -787050 7`, `Transfers -622071 21`, `Transfer - Bank Slip -523959
      1`, `Groceries -501764 84`, `Transfer - PIX -468515 58`, `Eating out -436013
      60`, `Shopping -417870 84`
- [ ] `comando` — RF-10, RF-18
      `.venv/bin/python -c "from app.db import connect; from app.queries.axes
      import aggregate; linhas = aggregate(connect(), axis='beneficiario',
      start='2026-03-01', end='2026-08-31'); print(len(linhas)); [print(l['key'],
      l['amount_cents'], l['entries']) for l in linhas[:3]]"` imprime `317` e, em
      seguida, exatamente estas três linhas nesta ordem: `debito prestacao hab
      -1235881 5`, `pagamento de boleto sociedade de assistencia e cultura sagra
      -1088005 7`, `pagamento de boleto safra cfi s a -749738 6`
- [ ] `comando` — RF-19
      `.venv/bin/python -c "from app.db import connect; from app.queries.axes
      import aggregate; m = {l['key']: l for l in aggregate(connect(),
      axis='categoria', start='2026-03-01', end='2026-08-31')}; print(m['Transfer
      - PIX']['amount_cents'], m['Transfer - PIX']['entries'], m['Transfer - Bank
      Slip']['amount_cents'], m['Transfer - Bank Slip']['entries'])"` imprime
      `-468515 58 -523959 1`
- [ ] `comando` — RF-20, RF-21
      `.venv/bin/python -c "from app.db import connect; from app.queries.axes
      import AXES, aggregate; c = connect(); somas = [sum(l['amount_cents'] for l
      in aggregate(c, axis=e, start='2026-03-01', end='2026-08-31')) for e in
      AXES]; positivas = sum(1 for e in AXES for l in aggregate(c, axis=e,
      start='2026-03-01', end='2026-08-31') if l['amount_cents'] >= 0);
      print(len(AXES), set(somas), positivas)"` imprime `5 {-10377233} 0`
- [ ] `comportamental` — RF-23
      *Dado* o banco `/tmp/dash-002-f2.sqlite` carregado
      *Quando* `app.queries.axes.aggregate` é chamada com `axis='grupo'`,
      `start='2026-03-01'`, `end='2026-01-31'`, e depois com `axis='grupo'`,
      `start='2026-13-01'`, `end='2026-08-31'`
      *Então* a primeira chamada levanta
      `app.queries.axes.InvalidPeriodError` com a mensagem
      `período inválido: fim (2026-01-31) anterior a inicio (2026-03-01)`, a
      segunda levanta a mesma exceção com a mensagem
      `data inválida: inicio (2026-13-01)`, e nenhuma das duas devolve linha
- [ ] `comportamental` — RF-24
      *Dado* o banco `/tmp/dash-002-f2.sqlite` carregado
      *Quando* `app.queries.axes.aggregate` é chamada com `axis='cor'`,
      `start='2026-03-01'`, `end='2026-08-31'`
      *Então* a chamada levanta `app.queries.axes.UnknownAxisError` com a
      mensagem `eixo inválido: cor. Eixos aceitos: grupo, categoria,
      beneficiario, natureza, essencialidade`
- [ ] `comando` — RF-25
      `.venv/bin/python -c "from app.db import connect; from
      app.queries.crossings import crossing; c = crossing(connect(),
      slug='corte', start='2026-03-01', end='2026-08-31'); ordenado =
      all(c.rows[i]['amount_cents'] <= c.rows[i+1]['amount_cents'] for i in
      range(len(c.rows) - 1)); soma = sum(l['amount_cents'] for l in c.rows);
      print(c.label, c.total_cents, len(c.rows), soma); raise SystemExit(0 if
      c.label == 'variável × supérfluo' and ordenado and soma == c.total_cents
      else 1)"` imprime uma linha começando por `variável × supérfluo ` e sai
      com código 0
- [ ] `comando` — RF-26
      `.venv/bin/python -c "from app.db import connect; from
      app.queries.crossings import crossing; c = crossing(connect(), slug='piso',
      start='2026-03-01', end='2026-08-31'); print(c.label, c.total_cents,
      c.monthly_average_cents); raise SystemExit(0 if c.label == 'fixa ×
      essencial' and c.monthly_average_cents == round(c.total_cents / 6) else
      1)"` imprime uma linha começando por `fixa × essencial ` e sai com código 0
- [ ] `comando` — RF-27
      `.venv/bin/python -c "from app.db import connect; from app.queries.series
      import monthly_series; s = monthly_series(connect(), end_month='2026-08');
      print(len(s), s[0]['month'], s[-1]['month'], s[-1]['amount_cents'])"`
      imprime `13 2025-08 2026-08 -1921711`
- [ ] `comando` — RF-28
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_series.py` sai com código 0, e o teste
      `tests/test_series.py::test_a_month_without_spending_stays_in_the_series`
      monta um banco temporário com gasto em `2026-01` e em `2026-03` e nenhum em
      `2026-02`, chama `monthly_series(conn, end_month='2026-03')` e afirma que a
      série tem 13 pontos, que o ponto `2026-02` está presente e que o
      `amount_cents` dele é `0`
- [ ] `comando` — RF-29, RF-30
      `.venv/bin/python -c "from app.db import connect; from app.queries.axes
      import transactions_of; linhas = transactions_of(connect(),
      axis='categoria', key='School', start='2026-03-01', end='2026-08-31');
      print(len(linhas), sum(l['amount_cents'] for l in linhas), all(l['date'] and
      l['description'] and l['account'] and l['amount_cents'] for l in linhas))"`
      imprime `20 -1299218 True`
- [ ] `comando` — RF-22
      `rtk proxy grep -REn "10377233|103772|1921711|19217|\b732\b|\b317\b|\b52\b"
      app "--include=*.py" "--include=*.sql" "--include=*.html"` não imprime
      nenhuma linha

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 2.1 Criar `app/queries/axes.py` com `AXES = ("grupo", "categoria",
      "beneficiario", "natureza", "essencialidade")`, `aggregate(conn, *, axis,
      start, end) -> list[sqlite3.Row]` (colunas `key`, `amount_cents`,
      `entries`, ordenadas do maior gasto para o menor),
      `transactions_of(conn, *, axis, key, start, end) -> list[sqlite3.Row]`
      (colunas `date`, `description`, `account`, `amount_cents`),
      `UnknownAxisError` e `InvalidPeriodError`.
      Justificativa: RF-15, RF-20 e RF-24 — os cinco eixos precisam sair da mesma
      função para que trocar o eixo não possa mudar o total; cinco consultas
      escritas em cinco lugares divergem na primeira correção de filtro. O eixo
      chega por parâmetro nomeado e é validado contra `AXES` antes de tocar SQL,
      porque eixo interpolado direto em `GROUP BY` é injeção.
- [ ] 2.2 Extrair para uma constante única em `app/queries/spending.py` o filtro
      de gasto — `amount_cents < 0`, `is_transfer = 0`, `is_refund = 0`,
      `refunded_by IS NULL` — e reusá-lo em `aggregate`, `transactions_of`,
      `crossing`, `monthly_series` e `residue`.
      Justificativa: invariante 25 e RF-16/RF-21 — o filtro que tira os
      R$ 20.272,00 de transferência precisa morar em um lugar só; repetido em
      cinco consultas, será esquecido em uma, e o painel passa a mentir só num
      eixo, que é o jeito mais caro de errar.
- [ ] 2.3 Criar `app/queries/crossings.py` com `crossing(conn, *, slug, start,
      end) -> Crossing`, lendo `nature` e `essentiality` da tabela `crossings`
      pelo `slug` e devolvendo `label`, `rows` (agrupadas por categoria, do maior
      gasto para o menor), `total_cents` e `monthly_average_cents`.
      Justificativa: RF-25, RF-26 e RF-08 — o par que define cada cruzamento vem
      da tabela, não de literal na condição; e a média mensal é o número que
      dimensiona a reserva do item `007`, então ela nasce aqui, ao lado do total,
      e não na tela.
- [ ] 2.4 Criar `app/queries/series.py` com `monthly_series(conn, *, end_month,
      months=13) -> list[sqlite3.Row]`, gerando os meses em Python e casando com
      o agregado por `strftime('%Y-%m', date)`, com zero onde não há gasto.
      Justificativa: RF-28 — um `GROUP BY` mês devolve só os meses que existem, e
      buraco invisível numa série temporal mente sobre a tendência; a série
      completa se produz gerando os pontos e preenchendo, nunca lendo.
- [ ] 2.5 Criar `app/queries/period.py` com `default_period(today: date) ->
      tuple[str, str]`, devolvendo os seis meses fechados mais recentes.
      Justificativa: D5 — o mês corrente abriria a tela com cinco dias de dado; e
      `today` entra por parâmetro para que a primeira carga da tela seja
      verificável sem relógio falso.
- [ ] 2.6 Criar `tests/test_axes.py`, `tests/test_crossings.py`,
      `tests/test_series.py` e `tests/test_period.py`, todos sobre bancos
      montados no próprio teste, e `tests/test_frozen_numbers.py`, que varre
      `app/**/*.py`, `app/**/*.sql` e `app/**/*.html` procurando `10377233`,
      `103772`, `1921711`, `19217`, `732`, `317` e `52` como número isolado e
      falha citando arquivo e linha — mais um caso que planta um desses números
      num arquivo temporário e afirma que o varredor o encontra.
      Justificativa: RF-22 e invariante 28 — a base cresce no item `006`, e um
      total congelado dentro do código faria a consulta do mês seguinte falhar
      por estar certa; sem o caso que reprova, um varredor quebrado passaria
      despercebido. Quem executa é o `pytest`, rodado pelo job `testes` de
      `.github/workflows/harness.yml`.

## Fase 3 — Tela de Gastos (tela)

**Objetivo da fase:** existe `/gastos`, com seletor de eixo e de período, tabela
ordenada por valor, evolução de treze meses, drill-down até a transação, os dois
cruzamentos e o resíduo visível.

**Critérios de aceite:**

O banco desta fase é preparado por `rm -f /tmp/dash-002-f3.sqlite && rtk proxy
env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f3.sqlite
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-002-f3.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f3.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=chave-do-servidor .venv/bin/python -m
app`. A sessão se obtém com **um único** `POST /login` com a senha correta, e o
cookie se reusa em todas as chamadas: cinco senhas erradas do mesmo IP em quinze
minutos fecham a porta.

- [ ] `comportamental` — RF-31
      *Dado* o servidor rodando em `http://127.0.0.1:8000` contra
      `/tmp/dash-002-f3.sqlite`, um cookie `dash_session` obtido por um único
      `POST /login` com `login=teste&senha=senha-teste-9k2`, e a data corrente do
      sistema em setembro de 2026
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      http://127.0.0.1:8000/gastos` é executado
      *Então* a resposta é `200`, o HTML traz cinco elementos `<option>` com os
      valores `grupo`, `categoria`, `beneficiario`, `natureza` e
      `essencialidade`, traz `value="2026-03-01"` e `value="2026-08-31"` nos
      campos de data, e traz as strings `−R$ 103.772,33` e `732`
- [ ] `comportamental` — RF-32
      *Dado*
      `http://127.0.0.1:8000/gastos?eixo=grupo&inicio=2026-03-01&fim=2026-08-31`
      aberta no Chromium com sessão válida, a página rolada até
      `window.scrollY === 400`, e
      `document.querySelector("#cruzamentos").dataset.marca = "x"` executado no
      console
      *Quando* o seletor de eixo passa de `grupo` para `categoria`
      *Então* a tabela de agregação passa a ter 52 linhas de dados,
      `document.querySelector("#cruzamentos").dataset.marca` continua valendo
      `"x"`, `window.scrollY` continua valendo `400` e o campo de data final
      continua valendo `2026-08-31`
- [ ] `comportamental` — RF-33
      *Dado*
      `http://127.0.0.1:8000/gastos?eixo=beneficiario&inicio=2026-03-01&fim=2026-08-31`
      aberta no Chromium com sessão válida
      *Quando* o campo de data final passa de `2026-08-31` para `2026-07-31` e o
      período é aplicado
      *Então* o seletor de eixo continua em `beneficiario`, a última linha da
      tabela da evolução passa a ser o mês `2026-07`, os totais exibidos nos
      dois cruzamentos mudam de valor em relação aos exibidos antes da troca, e
      o total da tabela de agregação deixa de ser `−R$ 103.772,33`
- [ ] `comportamental` — RF-34, RF-35
      *Dado* o servidor rodando contra `/tmp/dash-002-f3.sqlite` e um cookie
      `dash_session` válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/gastos?eixo=grupo&inicio=2026-03-01&fim=2026-08-31"`
      é executado
      *Então* o HTML traz um bloco com as strings `Sem regra`, `0 lançamentos` e
      `R$ 0,00` e um `<a>` com `href="/regras"`, e traz os dois rótulos
      `variável × supérfluo` e `fixa × essencial`, cada um seguido de uma cifra
      que casa com `−?R\$ [\d.]+,\d{2}`
- [ ] `comportamental` — RF-36
      *Dado*
      `http://127.0.0.1:8000/gastos?eixo=categoria&inicio=2026-03-01&fim=2026-08-31`
      aberta no Chromium com sessão válida e `document.body.dataset.marca = "y"`
      executado no console
      *Quando* a linha `School` da tabela de agregação é acionada
      *Então* aparece uma lista com 20 transações, cada uma com data, descrição,
      conta e valor, `document.body.dataset.marca` continua valendo `"y"`,
      `window.location.pathname` continua valendo `/gastos`, o seletor de eixo
      continua em `categoria` e os dois cruzamentos continuam exibidos com os
      mesmos totais
- [ ] `comportamental` — RF-37
      *Dado* o servidor rodando contra `/tmp/dash-002-f3.sqlite` e um cookie
      `dash_session` válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/gastos?eixo=grupo&inicio=2020-01-01&fim=2020-01-31"`
      é executado
      *Então* a resposta é `200`, o HTML não traz nenhuma linha `<tr>` de dados
      na tabela de agregação, e traz uma mensagem contendo as palavras
      `Nenhum gasto` e `período`, com um `<button>` ou um `<a>` que devolve ao
      período de seis meses
- [ ] `comportamental` — RF-38
      *Dado*
      `http://127.0.0.1:8000/gastos?eixo=grupo&inicio=2026-03-01&fim=2026-08-31`
      aberta no Chromium com sessão válida e **JavaScript desabilitado**
      *Quando* a página termina de carregar
      *Então* existe uma `<table>` da evolução com 13 linhas de dados, a primeira
      com o texto `2025-08` e a última com o texto `2026-08` seguido de
      `−R$ 19.217,11`
- [ ] `comando` — RF-44
      `rtk proxy grep -REn "#[0-9a-fA-F]{3,8}|rgb\(|hsl\(" app/templates
      app/static/css "--include=*.html" "--include=*.css" --exclude=tokens.css`
      não imprime nenhuma linha
- [ ] `comportamental` — RF-44
      *Dado*
      `http://127.0.0.1:8000/gastos?eixo=categoria&inicio=2026-03-01&fim=2026-08-31`
      aberta no Chromium com sessão válida
      *Quando* `document.querySelectorAll(".cifra")` é percorrido
      *Então* o conjunto tem mais de 50 elementos, para cada um
      `getComputedStyle(el).fontVariantNumeric` contém `tabular-nums`, e o texto
      de cada elemento casa com a expressão `^−?R\$ [\d.]+,\d{2}$`, com o sinal
      `−` (U+2212) colado ao `R$` em todo valor negativo
- [ ] `comportamental` — RF-45
      *Dado*
      `http://127.0.0.1:8000/gastos?eixo=categoria&inicio=2026-03-01&fim=2026-08-31`
      aberta no Chromium com sessão válida
      *Quando* a janela é ajustada para as larguras de viewport 375, 768 e 1440
      px, com altura de 800 px
      *Então* em cada uma das três larguras
      `document.documentElement.scrollWidth <= window.innerWidth` avalia como
      `true`
- [ ] `estrutural` — RF-45
      Existem os arquivos
      `product/items/002-gastos-tres-eixos/06-capturas/gastos-categoria-375.png`,
      `gastos-categoria-768.png`, `gastos-categoria-1440.png`,
      `gastos-detalhe-1440.png`, `gastos-vazio-375.png` e `gastos-dark-1440.png`,
      todos no mesmo diretório e cada um com mais de 1024 bytes
- [ ] `comportamental` — RF-46
      *Dado*
      `http://127.0.0.1:8000/gastos?eixo=categoria&inicio=2026-03-01&fim=2026-08-31`
      aberta no Chromium com sessão válida
      *Quando* a tecla `Tab` move o foco, em sequência, para o seletor de eixo,
      para o campo de data inicial e para o primeiro controle de linha da tabela
      de agregação
      *Então* em cada um deles `getComputedStyle(el).outlineStyle` é diferente de
      `none` e `parseFloat(getComputedStyle(el).outlineWidth)` é maior ou igual a
      2
- [ ] `comportamental` — RF-47
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado e sessão
      válida
      *Quando*
      `http://127.0.0.1:8000/gastos?eixo=categoria&inicio=2026-03-01&fim=2026-08-31`
      é carregada
      *Então* para todo elemento devolvido por `document.querySelectorAll("*")`,
      `getComputedStyle(el).animationDuration` e
      `getComputedStyle(el).transitionDuration` valem `0s`, e a tabela de
      agregação continua com 52 linhas de dados

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 3.1 Carregar a skill `frontend-design` antes de escrever qualquer marcação
      ou folha de estilo, e reler `product/00-linguagem-visual.md`.
      Justificativa: invariante 27 — a linguagem visual é canônica e já existe
      desde o item `001`; escolher cor, escala ou raio nesta fase seria abrir uma
      segunda opinião ao lado do documento.
- [ ] 3.2 Criar `app/format.py` com `brl(cents: int) -> str`, devolvendo
      `−R$ 12.992,18` com o sinal U+2212 colado ao `R$`, e registrá-la como
      filtro Jinja em `app/main.py`.
      Justificativa: RF-44 e `product/00-linguagem-visual.md` — cor nunca é o
      único sinal, então o `−` é obrigatório em todo valor negativo; formatar em
      cada template é o jeito de esquecer em um deles.
- [ ] 3.3 Criar `app/routers/spending.py` com `GET /gastos` (página inteira),
      `GET /gastos/tabela` (fragmento da tabela de agregação),
      `GET /gastos/painel` (fragmento com os dois cruzamentos, a evolução e o
      resíduo) e `GET /gastos/detalhe` (fragmento com as transações de uma
      linha), todos lendo `eixo`, `inicio`, `fim` e, no detalhe, `chave`.
      Justificativa: RF-32 e RF-33 — trocar o eixo repinta só a tabela e trocar o
      período repinta tabela e painel; um fragmento só forçaria a troca de eixo a
      recalcular cruzamento e série sem necessidade, e a rolagem saltaria.
- [ ] 3.4 Registrar o router em `app/main.py` e acrescentar em
      `app/templates/home.html` um `<a href="/gastos">`.
      Justificativa: sem o link a tela só se alcança digitando a URL; e a
      varredura de `tests/test_route_guard.py`, escrita no item `001`, passa a
      cobrir as quatro rotas novas sozinha — nenhuma delas pode nascer aberta
      (invariante 24).
- [ ] 3.5 Criar `app/templates/gastos.html` e os fragmentos
      `app/templates/fragments/gastos_tabela.html`,
      `app/templates/fragments/gastos_painel.html` e
      `app/templates/fragments/gastos_detalhe.html`, com o seletor de eixo e o de
      período dentro de um `<form method="get" action="/gastos">` que funciona
      sem JavaScript.
      Justificativa: RF-38 e a régua de `product/00-linguagem-visual.md` — a tela
      precisa ser legível sem rede; o formulário nativo é o piso, e a troca de
      fragmento é o acréscimo por cima dele.
- [ ] 3.6 Acrescentar em `app/templates/base.html` um bloco
      `{% block head_scripts %}{% endblock %}`, preenchido só pelas telas deste
      item, e carregar nele HTMX e Chart.js por CDN com `integrity` e
      `crossorigin="anonymous"`.
      Justificativa: `docs/plano.md` fixa FastAPI + Jinja2 + HTMX sem etapa de
      build e Chart.js por CDN; o bloco separado mantém a tela de login sem
      requisição externa, que é o que `tests/test_stylesheet.py` já cobra. O
      `integrity` existe porque script de terceiro sem hash é dependência que
      muda sozinha (norma 15).
- [ ] 3.7 Renderizar sempre a `<table>` dos treze pontos da evolução, e desenhar
      o gráfico por cima dela quando o Chart.js carregar.
      Justificativa: RF-38 — o gráfico vem de CDN, e uma tela que fica com um
      retângulo vazio quando a rede falha é uma tela que não se lê. A tabela é o
      dado; o gráfico é a leitura rápida dele.
- [ ] 3.8 Acrescentar em `app/static/css/app.css` as classes de tabela de dados,
      de cifra (`font-variant-numeric: tabular-nums`), de painel de cruzamento e
      de estado vazio, com o embrulho da tabela rolando em `overflow-x: auto` em
      vez do corpo da página.
      Justificativa: RF-45 — em 375 px uma tabela de cinco colunas empurra o
      corpo inteiro; o que rola tem de ser a tabela, e nenhum valor de cor ou de
      espaço nasce fora de `app/static/css/tokens.css` (RF-44).
- [ ] 3.9 Criar `tests/test_gastos_screen.py` com `fastapi.testclient`: a
      resposta 200 com sessão, os quatro fragmentos, o estado vazio do período
      sem gasto, o bloco de resíduo e os dois cruzamentos.
      Justificativa: os critérios de navegador provam a tela uma vez, na sessão
      em que ela foi feita; o teste é o que impede a fase seguinte de quebrá-la
      em silêncio. Quem executa é o `pytest`, rodado pelo job `testes` de
      `.github/workflows/harness.yml`.
- [ ] 3.10 Gerar as capturas em
      `product/items/002-gastos-tres-eixos/06-capturas/`:
      `gastos-categoria-375.png`, `gastos-categoria-768.png`,
      `gastos-categoria-1440.png`, `gastos-detalhe-1440.png`,
      `gastos-vazio-375.png` e `gastos-dark-1440.png`.
      Justificativa: RF-45 — a captura é a evidência que sobrevive à sessão, e o
      estado vazio é o que mais some de revisão visual por não estar no caminho
      feliz.

## Fase 4 — Tela de Regras (tela)

**Objetivo da fase:** existe `/regras`, onde o dono lista, cria, edita e remove
regra, vê quantos lançamentos cada mudança reclassificou e recebe recusa nomeada
quando o valor está fora do vocabulário.

**Critérios de aceite:**

O banco desta fase é preparado por `rm -f /tmp/dash-002-f4.sqlite && rtk proxy
env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f4.sqlite
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-002-f4.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f4.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=chave-do-servidor .venv/bin/python -m
app`. A sessão se obtém com **um único** `POST /login` com a senha correta.

- [ ] `comportamental` — RF-39
      *Dado* o servidor rodando em `http://127.0.0.1:8000` contra
      `/tmp/dash-002-f4.sqlite` e um cookie `dash_session` obtido por um único
      `POST /login` com `login=teste&senha=senha-teste-9k2`
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      http://127.0.0.1:8000/regras` é executado
      *Então* a resposta é `200`, a contagem de `<tr>` de dados da lista de
      regras é igual ao número impresso por `rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f4.sqlite
      .venv/bin/python -m app.query "select count(*) from category_rules"`, e a
      linha de `Eating out` traz o casamento `Eating out`, um nome de grupo, uma
      natureza, uma essencialidade e o número `128`
- [ ] `comportamental` — RF-40
      *Dado* o servidor rodando contra `/tmp/dash-002-f4.sqlite`, um cookie
      `dash_session` válido, o `id` do grupo `Transporte` lido de
      `category_groups`, e o valor do grupo `Transporte` lido em
      `http://127.0.0.1:8000/gastos?eixo=grupo&inicio=2026-03-01&fim=2026-08-31`
      antes da gravação
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/regras -d
      "match_kind=description&match_value=uber&group_id=<id de
      Transporte>&nature=variável&essentiality=importante"` é executado
      *Então* a resposta traz a string `lançamentos reclassificados`, `rtk proxy
      env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f4.sqlite
      .venv/bin/python -m app.query "select count(*) from category_rules where
      match_kind='description' and match_value='uber'"` imprime `1`, e o valor do
      grupo `Transporte` em
      `http://127.0.0.1:8000/gastos?eixo=grupo&inicio=2026-03-01&fim=2026-08-31`
      passa a ser diferente do lido antes da gravação
- [ ] `comportamental` — RF-40
      *Dado* o servidor rodando contra `/tmp/dash-002-f4.sqlite`, um cookie
      `dash_session` válido, e o `id` da regra com `match_kind = 'category'` e
      `match_value = 'Eating out'`
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/regras/<id da regra>/editar -d
      "match_kind=category&match_value=Eating out&group_id=<id do grupo atual da
      regra>&nature=variável&essentiality=supérfluo"` é executado
      *Então* a resposta traz a string `128 lançamentos reclassificados`, e
      `http://127.0.0.1:8000/gastos?eixo=categoria&inicio=2026-03-01&fim=2026-08-31`,
      buscada em seguida com o mesmo cookie, traz no bloco rotulado
      `variável × supérfluo` uma linha `Eating out` com a cifra `−R$ 4.360,13` e
      o número `60`
- [ ] `comportamental` — RF-07
      *Dado* o servidor rodando contra `/tmp/dash-002-f4.sqlite` e um cookie
      `dash_session` válido
      *Quando* `rtk proxy curl -i -s -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/regras -d
      "match_kind=category&match_value=Zzz&group_id=9999&nature=fixo&essentiality=dispensável"`
      é executado
      *Então* a resposta é `400`, o HTML traz a mensagem
      `natureza inválida: fixo`, e `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f4.sqlite .venv/bin/python -m app.query "select
      count(*) from category_rules where match_value = 'Zzz'"` imprime `0`
- [ ] `comportamental` — RF-42
      *Dado* o servidor rodando contra `/tmp/dash-002-f4.sqlite`, um cookie
      `dash_session` válido, o `id` do grupo `Outros` lido de `category_groups`,
      e a contagem de `category_rules` lida antes da chamada
      *Quando* `rtk proxy curl -i -s -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/regras -d
      "match_kind=description&match_value=[a-&group_id=<id de
      Outros>&nature=eventual&essentiality=importante"` é executado
      *Então* a resposta é `400`, o HTML traz a mensagem `expressão inválida:
      [a-`, e `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f4.sqlite .venv/bin/python -m app.query "select
      count(*) from category_rules"` imprime o mesmo número lido antes da chamada
- [ ] `comportamental` — RF-43
      *Dado* o servidor rodando contra `/tmp/dash-002-f4.sqlite`, um cookie
      `dash_session` válido, e o `id` da regra com `match_kind = 'category'` e
      `match_value = 'Eating out'`
      *Quando* `rtk proxy curl -i -s -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/regras/<id da regra>/remover` é executado
      *Então* a resposta traz a string `128 lançamentos reclassificados`, `rtk
      proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-f4.sqlite
      .venv/bin/python -m app.query "select count(*) from transactions where
      category = 'Eating out' and rule_id is null"` imprime `128`, e
      `http://127.0.0.1:8000/gastos?eixo=grupo&inicio=2026-03-01&fim=2026-08-31`,
      buscada em seguida, traz no bloco de resíduo as strings `60 lançamentos` e
      `−R$ 4.360,13`
- [ ] `comportamental` — RF-41
      *Dado* o servidor rodando contra `/tmp/dash-002-f4.sqlite`, um cookie
      `dash_session` válido, e a regra de `match_value = 'Eating out'` removida
      por `rtk proxy curl -s -o /dev/null -b "dash_session=<cookie>" -X POST
      http://127.0.0.1:8000/regras/$(rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-f4.sqlite .venv/bin/python -m app.query "select
      id from category_rules where match_kind = 'category' and match_value =
      'Eating out'")/remover`
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      http://127.0.0.1:8000/regras` é executado
      *Então* o HTML traz, **antes** da lista de regras, um bloco com o texto
      `Sem regra` contendo a string `Eating out` seguida de uma cifra que casa
      com `−?R\$ [\d.]+,\d{2}`, e o primeiro item desse bloco é o de maior valor
      absoluto entre os listados nele
- [ ] `comando` — RF-44
      `rtk proxy grep -REn "#[0-9a-fA-F]{3,8}|rgb\(|hsl\(" app/templates
      app/static/css "--include=*.html" "--include=*.css" --exclude=tokens.css`
      não imprime nenhuma linha
- [ ] `comportamental` — RF-44
      *Dado* `http://127.0.0.1:8000/regras` aberta no Chromium com sessão válida
      *Quando* `document.querySelectorAll(".cifra")` é percorrido
      *Então* para cada elemento `getComputedStyle(el).fontVariantNumeric` contém
      `tabular-nums` e o texto casa com a expressão `^−?R\$ [\d.]+,\d{2}$`, com o
      sinal `−` (U+2212) colado ao `R$` em todo valor negativo
- [ ] `comportamental` — RF-45
      *Dado* `http://127.0.0.1:8000/regras` aberta no Chromium com sessão válida
      *Quando* a janela é ajustada para as larguras de viewport 375, 768 e 1440
      px, com altura de 800 px
      *Então* em cada uma das três larguras
      `document.documentElement.scrollWidth <= window.innerWidth` avalia como
      `true`
- [ ] `estrutural` — RF-45
      Existem os arquivos
      `product/items/002-gastos-tres-eixos/06-capturas/regras-lista-375.png`,
      `regras-lista-768.png`, `regras-lista-1440.png`, `regras-erro-1440.png` e
      `regras-dark-1440.png`, todos no mesmo diretório e cada um com mais de 1024
      bytes
- [ ] `comportamental` — RF-46
      *Dado* `http://127.0.0.1:8000/regras` aberta no Chromium com sessão válida
      *Quando* a tecla `Tab` move o foco, em sequência, para o campo de
      casamento, para o seletor de grupo e para o botão que grava a regra
      *Então* em cada um deles `getComputedStyle(el).outlineStyle` é diferente de
      `none` e `parseFloat(getComputedStyle(el).outlineWidth)` é maior ou igual a
      2
- [ ] `comportamental` — RF-47
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado e sessão
      válida
      *Quando* `http://127.0.0.1:8000/regras` é carregada
      *Então* para todo elemento devolvido por `document.querySelectorAll("*")`,
      `getComputedStyle(el).animationDuration` e
      `getComputedStyle(el).transitionDuration` valem `0s`, e a lista de regras
      continua com o mesmo número de linhas de dados

**Critérios de integração:**

- [ ] `comando` — portão local, no lugar do CI que este repositório não tem
      `rtk proxy .venv/bin/python -m pytest -q` executado na raiz sai com código 0
- [ ] `comportamental` — RF-13, RF-33
      *Dado* o banco preparado por `rm -f /tmp/dash-002-e2e.sqlite && rtk proxy
      env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-e2e.sqlite
      .venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-e2e.sqlite LOGIN=teste PASSORD=senha-teste-9k2
      .venv/bin/python -m app.auth.seed && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-e2e.sqlite .venv/bin/python -m
      app.taxonomy.seed && rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-002-e2e.sqlite .venv/bin/python -m
      app.taxonomy.classify`, o servidor subido por `rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-002-e2e.sqlite
      DASH_KEY_PATH=/tmp/dash-002-e2e.key LOGIN=teste PASSORD=senha-teste-9k2
      SESSION_SECRET=segredo-de-teste-7h4 .venv/bin/python -m app`, e o cookie
      `dash_session` obtido de `rtk proxy curl -i -s -X POST
      http://127.0.0.1:8000/login -d "login=teste&senha=senha-teste-9k2"`, com o
      período de 01/03/2026 a 31/08/2026 no eixo essencialidade
      *Quando* a essencialidade da regra de categoria `Eating out` é mudada para
      `supérfluo` em `http://127.0.0.1:8000/regras` e a tela
      `http://127.0.0.1:8000/gastos` é recarregada com o mesmo período e eixo
      *Então* a linha `supérfluo` cresce em exatamente R$ 4.360,13 e a linha de
      onde `Eating out` saiu diminui no mesmo valor, sem que nenhum processo
      tenha sido reiniciado e sem que a ingestão tenha rodado de novo
- [ ] `comportamental` — RF-16, RF-20
      *Dado* o servidor rodando contra `/tmp/dash-002-e2e.sqlite` com o mesmo
      cookie `dash_session` obtido por `rtk proxy curl -i -s -X POST
      http://127.0.0.1:8000/login -d "login=teste&senha=senha-teste-9k2"`, e o
      período de 01/03/2026 a 31/08/2026
      *Quando*
      `http://127.0.0.1:8000/gastos?eixo=<eixo>&inicio=2026-03-01&fim=2026-08-31`
      é buscada com esse cookie uma vez para cada um dos cinco eixos — `grupo`,
      `categoria`, `beneficiario`, `natureza` e `essencialidade`
      *Então* o total exibido é `−R$ 103.772,33` nas cinco vezes

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 4.1 Criar `app/routers/rules.py` com `GET /regras`, `POST /regras`,
      `POST /regras/{rule_id}` e `POST /regras/{rule_id}/remover`, todos
      chamando `app.taxonomy.rules` e devolvendo `400` com o formulário
      reexibido quando a gravação é recusada.
      Justificativa: RF-07 e RF-42 — a recusa precisa chegar à tela com o valor
      recusado dentro dela; e o `POST` puro, sem JavaScript, é o que mantém a
      tela funcional quando o CDN não responde.
- [ ] 4.2 Criar `app/templates/regras.html` e
      `app/templates/fragments/regras_lista.html`, com os `<select>` de grupo, de
      natureza e de essencialidade preenchidos a partir de `category_groups`,
      `natures` e `essentialities`.
      Justificativa: RF-08 e invariante 26 — o vocabulário é do banco; escrever
      as opções no template criaria uma segunda fonte de verdade, que diverge do
      banco no primeiro grupo novo.
- [ ] 4.3 Exibir no topo de `/regras`, enquanto o resíduo for maior que zero, as
      categorias e os beneficiários sem regra, ordenados pelo valor absoluto do
      dinheiro que carregam.
      Justificativa: RF-41 — resíduo silencioso é resíduo que ninguém corrige, e
      ordenar pelo dinheiro é o que faz a primeira correção ser a que mais muda a
      conta.
- [ ] 4.4 Mostrar na resposta de toda gravação o número de lançamentos
      reclassificados, no formato `<n> lançamentos reclassificados`, e registrar
      o router em `app/main.py`.
      Justificativa: RF-40 — sem o número, quem edita não sabe se a regra pegou
      alguma coisa, e a única forma de descobrir seria voltar à tela de Gastos e
      comparar de cabeça.
- [ ] 4.5 Criar `tests/test_regras_screen.py` com `fastapi.testclient`: a lista
      com a contagem de alcance, a criação, a edição, a remoção com queda no
      resíduo, a recusa de termo fora do vocabulário e a recusa de expressão que
      não compila.
      Justificativa: as quatro rotas mexem na classificação de toda a base, e um
      erro aqui não aparece como tela quebrada — aparece como total plausível e
      errado na tela de Gastos. Quem executa é o `pytest`, rodado pelo job
      `testes` de `.github/workflows/harness.yml`.
- [ ] 4.6 Gerar as capturas em
      `product/items/002-gastos-tres-eixos/06-capturas/`:
      `regras-lista-375.png`, `regras-lista-768.png`, `regras-lista-1440.png`,
      `regras-erro-1440.png` (o formulário reexibido com a mensagem de recusa) e
      `regras-dark-1440.png`.
      Justificativa: RF-45 — o estado de erro é o que mais some da revisão
      visual, e é o único desta tela que o dono vai ver com pressa.

## Execução sugerida

As quatro fases correm **em sequência**, sem paralelismo. A verificação foi feita
por interseção dos conjuntos de arquivos de cada fase, e ela é grande demais em
todos os pares:

1. **Fase 1** — bloqueante. Fixa o contrato que as outras três consomem: as
   colunas de classificação em `transactions`, o vocabulário em tabela e a ordem
   de precedência das regras. Uma premissa errada aqui se espalha de uma vez para
   os cinco eixos, os dois cruzamentos e as duas telas.
2. **Fase 2** depois da fase 1 — toda consulta lê `transactions.group_id`,
   `nature`, `essentiality`, `payee` e `rule_id`, e a tabela `crossings`, que só
   existem depois da migração `003`.
3. **Fase 3** depois da fase 2 — a tela renderiza o que `app/queries/axes.py`,
   `crossings.py`, `series.py` e `period.py` devolvem. Em paralelo com a fase 2,
   a tela não teria o que exibir, e um contrato de retorno inventado no template
   seria refeito ao encontrar o real.
4. **Fase 4** depois da fase 3 — as duas telas escrevem em `app/main.py`,
   `app/templates/base.html` e `app/static/css/app.css`, e a fase 4 verifica o
   próprio efeito lendo a tela de Gastos (RF-40 e RF-43). Em worktrees paralelos
   isso seria conflito de merge em três arquivos e dois critérios impossíveis de
   medir.

## Validações de campo pendentes

Nenhuma.
