# Plano — 015-configuracao-e-nome-do-beneficiario

**Trilha:** rápida · **Brief:** `01-brief.md` · Três fases, em sequência.

> **Método de planejamento em acúmulo.** Cada etapa foi escrita considerando o
> que as anteriores deixam no código, e diz isso na linha **Considerando**. A
> etapa 3.4 não inventa onde o nome mora se a 3.2 já criou o lugar. O objetivo é
> consistência: um padrão por decisão, escolhido uma vez e reusado.
>
> **Todo número deste plano foi medido antes de ser escrito**, contra a base de
> 05/09/2026 e contra o JSON bruto da Pluggy. Nenhum veio de estimativa.

## Por que esta ordem

1. **Fase 1 é bloqueante.** As fases 2 e 3 escrevem no armazém. Unificá-lo depois
   obrigaria a refazer as duas.
2. **Fase 2 depois da 1** — a tela renderiza o catálogo e lê o armazém; sem eles
   o contrato de retorno seria inventado no template e refeito ao encontrar o
   real, que foi o erro do item `003`.
3. **Fase 3 depois da 2** — o bloco de beneficiários mora dentro da tela que a
   fase 2 cria, e reusa o mesmo `_answer` e o mesmo padrão de recusa.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | Padrão que decidiu | Decisão |
|---|---|---|
| Catálogo novo ou o `PARAMETERS` que já existe? | `app/routers/debts.py:50` já valida nome contra dicionário antes de gravar | O catálogo **promove** o `PARAMETERS`, não nasce ao lado |
| Qual dos três leitores de valor digitado sobrevive? | `app/plan/whatif.py::_cents` é o único corrigido pelo item `008` | Ele é a origem; os outros passam a importar |
| Vocabulário de `kind` e `unit`: código ou dado? | `app/taxonomy/seed.json` do item `002` | Dado, no catálogo |
| Beneficiário com dois nomes candidatos: quem ganha? | Medido: **zero** beneficiários têm dois valores distintos em qualquer nível, e zero têm dois CNPJs | `MIN()` no agrupamento — determinístico, hoje sem efeito |
| Limite da lista de beneficiários | `CANDIDATES = 12` em `app/routers/rules.py:22` | Constante de módulo `PAYEES = 30`, medida: cobre 55,8% do gasto |
| `merchant.cnae` entra? | Norma 12 — pendência não vira coluna especulativa | **Fora**: é código nu (`7490104`), inútil sem tabela, e a consulta de CNPJ já traz a atividade |
| Chave de junção em `/comprometido` | `commitments.series_key` é o `payee` normalizado, medido | Junta por `series_key`, sem chave nova |

---

## Fase 1 — Um armazém só para o que só o humano sabe

**Objetivo:** uma tabela, um catálogo, um leitor e um escritor. Nenhuma tela
muda de endereço; o que muda é onde elas gravam — e um valor digitado passa a
ser lido do mesmo jeito nas duas.

### Etapas

- [ ] **1.1 — Migração `010_settings.sql`.**
      `plan_facts` ganha a coluna `kind` (`fato` ou `meta`), com `fato` nas
      linhas existentes. As linhas de `plan_parameters` são **convertidas** para
      `plan_facts` — `label` igual ao nome, `unit` `centavos`, `source`
      `plan_parameters`, `captured_at` igual ao `updated_at` de origem —, e
      `plan_parameters` é removida.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-01 a RF-03. `plan_facts` tem `label`, `unit`, `source`
      e `captured_at` como `NOT NULL`; a conversão precisa preencher os quatro,
      ou a migração falha na primeira base que já tenha um parâmetro gravado — e
      a base do dono tem.

- [ ] **1.2 — `app/settings/catalog.py`: o catálogo como dado.**
      Uma tupla de dicionários, um por valor aceito, com `name`, `label`,
      `help`, `unit`, `kind`, `screen` e `moves` — este dizendo, em uma frase,
      qual número aquele valor muda. `app/routers/debts.py` deixa de declarar
      `PARAMETERS` e passa a perguntar ao catálogo.
      *Considerando 1.1:* `kind` e `unit` só assumem os valores que a coluna
      aceita, e o catálogo é a fonte deles.
      *Justificativa:* RF-06, RF-08. O dicionário `PARAMETERS` já é um catálogo
      com dois itens e sem `unit`; o certo é promovê-lo, não criar um segundo.
      Vocabulário fechado é dado, como `app/taxonomy/seed.json` (item `002`).

- [ ] **1.3 — `app/settings/typed.py`: a leitura de valor digitado, num lugar só.**
      Move para cá o corpo de `app/plan/whatif.py::_cents` — forma brasileira
      estrita, teto de doze algarismos, centavos de inteiro para inteiro — e o de
      `app/debts/ladder.py::parse_rate`, e acrescenta a leitura de meses.
      `app/debts/simulate.py::parse_amount` é **apagado**: quem chamava passa a
      chamar o leitor único. `app/debts/ladder.py::_cents(value: float)` **não é
      tocado** — apesar do nome, converte float já validado, não texto digitado.
      *Considerando 1.2:* a função recebe a `unit` do catálogo e devolve inteiro
      naquela unidade; não há um leitor por chamador.
      *Justificativa:* RF-04, e é aqui que a fase paga sozinha. Medido: hoje
      `/dividas` lê `5000.00` como **R$ 500.000,00**, em silêncio, no campo do
      saldo de quitação — a mesma falha que o item `008` corrigiu em
      `/simulador`, viva no outro leitor. E `inf`, `nan` ou `1e308` no mesmo
      campo levantam `OverflowError` fora do `try`, que é HTTP 500. Três
      leitores, três comportamentos; um deles decide se vale quitar uma dívida.

- [ ] **1.4 — `app/settings/store.py`: ler e gravar.**
      `read(conn)` devolve o catálogo com o valor de cada linha e a marca de
      vencido; `write(conn, name, typed)` valida contra o catálogo, converte pela
      unidade e grava; `value(conn, name)` devolve o inteiro ou `None`.
      *Considerando 1.1* (a tabela), *1.2* (o catálogo autoriza o nome) e *1.3*
      (a conversão vem de um lugar só). O `unit` e o `source` deixam de ser
      literais no `INSERT` de `app/routers/whatif.py:89`.
      *Justificativa:* RF-05, RF-07. A recusa por nome fora do catálogo copia a
      de `app/taxonomy/rules.py`, que já recusa grupo, natureza e essencialidade
      fora do vocabulário: mesma forma de erro, mensagem que nomeia o inválido.

- [ ] **1.5 — Os quatro pontos de contato passam a usar o armazém.**
      `app/debts/simulate.py::parameter` e `POST /dividas/parametro`
      (`app/routers/debts.py:120`); `app/plan/whatif.py::facts` e
      `POST /simulador/fato` (`app/routers/whatif.py:89`).
      *Considerando 1.4:* os quatro chamam `store`, e nenhum monta SQL próprio.
      *Justificativa:* RF-05. É aqui que o saldo de quitação informado em
      `/dividas` passa a aparecer em `/simulador` — o sintoma que o dono viu.

- [ ] **1.6 — `tests/test_settings.py`.**
      A conversão da migração com uma linha preexistente; o nome fora do
      catálogo recusado; a unidade respeitada; o valor ausente devolvendo `None`
      e não zero; o vencido marcado; o mesmo valor visível pelas duas telas; e
      os dois defeitos da 1.3 — `5000.00` recusado e `inf` sem 500.
      *Considerando 1.1 a 1.5.*
      *Justificativa:* RF-01 a RF-07. Nenhum destes erros quebra tela; todos
      produzem número plausível e errado.

**Critérios de aceite da fase 1:**

A base é preparada por `rm -f /tmp/dash-015.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-015.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest`, e `Q` abrevia `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-015.sqlite .venv/bin/python -m
app.query`.

- [ ] `comando` — RF-01, RF-03
      `Q "select count(*) from sqlite_master where type='table' and name in
      ('plan_facts','plan_parameters')"` imprime `1`, e `Q "select count(*) from
      pragma_table_info('plan_facts') where name='kind'"` imprime `1`
- [ ] `comando` — RF-02
      Um trecho que cria base só com as migrações até `009`, insere em
      `plan_parameters` a linha `('quitacao', 3500000, '2026-09-01T10:00:00')`,
      roda `app.migrate` até o fim e lê `plan_facts` de volta imprime
      `quitacao|3500000|fato|centavos|plan_parameters`
- [ ] `comando` — RF-04 · o defeito medido em `/dividas`
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -c "from
      app.settings.typed import parse; print(parse('5000.00','centavos','x'))"`
      termina em recusa, **não** em `500000000`; e o mesmo com `inf` e `1e308`
      termina em recusa, **não** em `OverflowError`
- [ ] `comando` — RF-04, RF-06, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_settings.py` sai com código `0`, e o arquivo contém: um teste
      que grava nome fora do catálogo e afirma que a recusa nomeia o inválido;
      um que afirma que `2.500,00` em `centavos` vira `250000` e que `2500.00` é
      recusado; um que afirma que `6` em `meses` vira `6`; um que afirma que
      valor ausente devolve `None` e não `0`; e um que afirma que o catálogo traz
      os seis valores de RF-08
- [ ] `comando` — RF-03, RF-04, DRY
      `rtk proxy grep -REn --exclude-dir=__pycache__ "plan_parameters" app`
      imprime linhas **apenas** de `app/migrations/sql/`; e `rtk proxy grep -REn
      "def parse_amount|def parse_rate|def _cents\(typed" app` não imprime
      nenhuma linha fora de `app/settings/typed.py`
- [ ] `comportamental` — RF-05
      *Dado* o servidor rodando contra `/tmp/dash-015.sqlite` e um cookie válido
      *Quando* `POST /dividas/parametro` grava `nome=quitacao` e
      `valor=35.000,00`, e em seguida `GET /simulador` é buscada
      *Então* `rtk proxy curl -s -b "dash_session=$C"
      http://127.0.0.1:8000/simulador | grep -c "35.000,00"` imprime pelo menos
      `1` — hoje imprime `0`

**Critérios de integração da fase 1:**

- [ ] `comando` — portão local e de lint
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz e `rtk proxy bash scripts/lint.sh` saem ambos com código `0`

---

## Fase 2 — A tela de configuração

**Objetivo:** um lugar que lista tudo o que alimenta cálculo, diz o que cada
valor muda, e grava.

### Etapas

- [ ] **2.1 — `app/routers/settings.py`: `GET /configuracao` e `POST /configuracao`.**
      *Considerando 1.4:* o contexto vem de `store.read(conn)` inteiro; o router
      não sabe quais valores existem, só os renderiza.
      *Considerando o padrão de rota:* `_reference` com faixa de datas como em
      `app/routers/plan.py`, `_answer` com `notice` e `status_code` como em
      `app/routers/debts.py`, recusa em `400`, e a sessão exigida como em toda
      rota que devolve dado (invariante 24).
      *Justificativa:* RF-12, RF-16.

- [ ] **2.2 — `app/templates/configuracao.html`.**
      Dois blocos, `id="fatos"` e `id="metas"`, cada linha com
      `data-config="<nome>"` e `data-valor`, o que ele muda, e o link para a tela
      de contexto.
      *Considerando 2.1:* os nomes de atributo seguem o padrão já usado —
      `data-degrau`, `data-fato`, `data-cenario` —, para o critério se medir do
      mesmo jeito. Os `id` `fatos` e `metas` não colidem: `id="fatos"` existe em
      `simulador.html`, e são telas distintas.
      *Considerando 1.2:* o texto de "o que muda" vem do campo `moves` do
      catálogo, não do template. Vocabulário é dado.
      *Justificativa:* RF-13, RF-14, RF-15, RF-30.

- [ ] **2.3 — O Resumo leva à configuração.**
      Uma linha em `app/templates/resumo.html`, ao lado das que já existem.
      *Considerando 2.1.* *Justificativa:* RF-12.

- [ ] **2.4 — Meta informada substitui a constante.**
      `app/plan/objective.py::reserve_target_cents` — hoje
      `survival_floor_cents(...) * RESERVE_MONTHS` — e
      `app/projection/monthly.py::complete_months` — hoje `seen[-MONTHS:]` —
      passam a ler o armazém, com a constante atual como **padrão** quando não
      há meta.
      *Considerando 1.4* (o leitor) e *1.2* (os nomes `reserva-meses` e
      `mediana-meses` vêm do catálogo).
      *Justificativa:* RF-09, invariante 26. `WINDOW_DAYS` fica de fora por
      RF-10 — é contrato entre `/resumo` e `/comprometido`, não meta do dono — e
      a etapa não a toca.

- [ ] **2.5 — `tests/test_configuracao_screen.py`.**
      A tela lista os seis valores; gravar move o número na mesma resposta; valor
      ausente diz o que o painel usa no lugar; meta informada muda a reserva
      alvo; a rota exige sessão.
      *Considerando 2.1 a 2.4.* *Justificativa:* RF-09, RF-12 a RF-16.

- [ ] **2.6 — As três capturas.**
      *Considerando o erro repetido quatro vezes nesta corrida:* o `const OUT` do
      script de captura é conferido **antes** de rodar.
      *Justificativa:* RF-30.

**Critérios de aceite da fase 2:**

- [ ] `comportamental` — RF-12, RF-13
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -b "dash_session=$C"
      http://127.0.0.1:8000/configuracao > /tmp/config.html` é executado
      *Então* `grep -c 'id="fatos"' /tmp/config.html` e `grep -c 'id="metas"'`
      imprimem `1` cada, e `grep -o 'data-config="[a-z-]*"' /tmp/config.html |
      sort -u | wc -l` imprime `6`
- [ ] `comportamental` — RF-09, RF-14, RF-16
      *Dado* o servidor rodando, um cookie válido e nenhuma meta gravada
      *Quando* a tela é lida, `POST /configuracao` grava `reserva-meses` com
      valor `3`, e `GET /objetivo?data=2026-09-05` é buscada antes e depois
      *Então* a primeira leitura da configuração diz, na linha de
      `reserva-meses`, que o painel usa `6` enquanto não houver valor; e a
      reserva alvo de `/objetivo` depois é exatamente **metade** da de antes
- [ ] `comportamental` — RF-07
      *Dado* o servidor rodando e um cookie válido
      *Quando* `POST /configuracao` é feito com `nome=inexistente`, e depois com
      `nome=reserva-meses` e `valor=abc`
      *Então* as duas respostas têm código `400`, a primeira traz `inexistente`
      na recusa, a segunda traz o rótulo do campo, e nada é gravado
- [ ] `comando` — RF-12
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_configuracao_screen.py` sai com código `0`
- [ ] `estrutural` — RF-30
      Existem, no diretório `06-capturas/` do item, `configuracao-375.png`,
      `configuracao-1440.png` e `configuracao-dark-1440.png`, cada um com mais de
      `1024` bytes
- [ ] `comportamental` — RF-30
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado, sessão
      válida e `/configuracao` carregada
      *Quando* a janela é ajustada para `375`, `768` e `1440` px de largura por
      `800` de altura, uma vez carregando já naquela largura e uma vez
      redimensionando
      *Então* nas seis medições `document.documentElement.scrollWidth <=
      window.innerWidth` avalia `true`, e todo elemento de
      `document.querySelectorAll("#fatos *")` tem `animationDuration` e
      `transitionDuration` iguais a `0s`

**Critérios de integração da fase 2:**

- [ ] `comando` — portão local e de lint
      `pytest -q` na raiz e `bash scripts/lint.sh` saem ambos com código `0`
- [ ] `comando` — RF-10, RF-11
      `rtk proxy grep -cE "WINDOW_DAYS|DUE_TOLERANCE_DAYS|SAME_PURCHASE_DEVIATION|MIN_BALANCE_CENTS"
      app/settings/catalog.py` imprime `0`
- [ ] `comportamental` — RF-12, invariante 24
      *Dado* nenhuma sessão
      *Quando* `rtk proxy curl -s -o /dev/null -w "%{http_code}"
      http://127.0.0.1:8000/configuracao` é executado
      *Então* a saída é `302`

---

## Fase 3 — O nome real do beneficiário

**Objetivo:** os lançamentos que a Pluggy já nomeia ganham nome de verdade sem o
dono digitar nada, e o resto ele batiza uma vez, começando pelos que representam
dinheiro.

### Etapas

- [ ] **3.1 — O consolidador carrega os campos adiante.**
      `ingestao/pluggy_consolidate.py` passa a escrever, em cada lançamento,
      `nome_fantasia` (de `merchant.name`), `razao_social` (de
      `merchant.businessName`), `cnpj` (de `merchant.cnpj`) e `recebedor` (de
      `paymentData.receiver.name`). **String vazia é ausência**: o campo sai como
      nulo, não como `""`.
      *Considerando o formato do consolidado:* as chaves do arquivo são em
      português — `descricao`, `valor`, `conta_id` —, e as novas seguem a mesma
      língua, não a do JSON da Pluggy.
      *Justificativa:* RF-18, e a decisão `D7` do item `001`: o consolidador
      produz, o painel lê o consolidado. Medido: `merchant.businessName` vem como
      `""` em lançamentos que **têm** `merchant.name` — gravar a string vazia
      faria `is not null` contar `391` onde a resposta certa é `338`, e o
      critério passaria medindo a coisa errada. Registro que `ingestao/` está
      fora do alcance de `scripts/lint.sh`, que varre `app tests`.

- [ ] **3.2 — Migração `011_payee_names.sql`.**
      `transactions` ganha `merchant_name` (fantasia), `merchant_legal_name`
      (razão social), `merchant_cnpj` e `receiver_name`. Nasce `payee_names` com
      `payee` como chave primária, `name`, `source` e `updated_at`.
      *Considerando 3.1:* uma coluna por campo que o consolidador passou a
      escrever, sem coluna órfã — e por isso **não** há coluna de CNAE.
      *Considerando o padrão do `003`:* a chave é o beneficiário, que é como as
      séries de compromisso já se agrupam, não a descrição.
      *Justificativa:* RF-19, RF-20.

- [ ] **3.3 — A carga grava os campos novos.**
      `app/ingest/loader.py` acrescenta as quatro colunas a
      `_TRANSACTION_COLUMNS` e as lê do consolidado.
      *Considerando 3.1* (as chaves) e *3.2* (as colunas).
      *Considerando a semântica do item `006`:* a carga continua contando
      inserções; acrescentar coluna não muda o que `transactions_count` significa.
      *Justificativa:* RF-19.

- [ ] **3.4 — `app/payees/names.py`: a precedência, num lugar só.**
      `display_name(conn)` devolve, por beneficiário, o nome e a origem, nesta
      ordem: **apelido do dono** (`payee_names.source = 'dono'`); **nome fantasia
      da Pluggy** (`merchant_name`); **nome fantasia consultado**
      (`payee_names.source = 'cnpj'`); **razão social** (`merchant_legal_name`,
      senão `receiver_name`); **descrição normalizada** (`payee`).
      *Considerando 3.2* (onde cada candidato mora) e *3.3* (que existem).
      *Considerando o padrão do `014`:* a origem viaja junto com o valor, como
      `observed_rates` faz com a faixa, para a tela declará-la.
      *Justificativa:* RF-21, RF-22, RF-24. A ordem é por **qualidade do nome**,
      não por fonte: medido, `merchant.name` traz `Apple`, `Shopee`, `outback`, e
      `receiver.name` traz `IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A.` — os
      dois são "da Pluggy", e um é resposta e o outro é razão social. O
      agrupamento usa `MIN()` sobre os candidatos, o que hoje não muda nada:
      medido, **nenhum** dos 721 beneficiários tem dois valores distintos em
      nível algum, nem dois CNPJs. Resolver na leitura é o que permite apagar o
      apelido e recuperar o nome anterior sem reescrever lançamento.

- [ ] **3.5 — O bloco de beneficiários dentro da configuração.**
      `id="beneficiarios"`, os `PAYEES = 30` maiores por gasto absoluto, cada
      linha com `data-beneficiario`, `data-origem`, `data-gasto` e um campo para
      batizar. O bloco declara quantos beneficiários existem ao todo e que
      fração do gasto os 30 cobrem.
      *Considerando 2.1 e 2.2:* mesma rota, mesmo `_answer`, mesmo padrão de
      recusa e de atributo `data-`.
      *Considerando 3.4:* a linha exibe o que a precedência devolveu.
      *Justificativa:* RF-23, e o limite segue `CANDIDATES = 12` de
      `app/routers/rules.py:22`. A ordem por dinheiro é o que torna a tarefa
      finita: medido, 30 de 721 beneficiários cobrem 55,8% do gasto, e o maior
      de todos — `debito prestacao hab`, R$ 24.667,33 — é justamente um que a
      Pluggy **não** nomeia.

- [ ] **3.6 — A consulta de CNPJ, sob demanda.**
      `app/payees/lookup.py`, chamado por `POST /configuracao/cnpj`.
      *Considerando 3.4:* o nome consultado grava com `source = 'cnpj'`, abaixo
      do apelido do dono na precedência, e só vira apelido quando ele salvar.
      *Considerando o padrão do `009`:* `httpx` direto, sem SDK; degradação com
      `200` e mensagem em português distinguindo recusa da fonte, tempo esgotado
      e formato inesperado.
      *Justificativa:* RF-25, RF-26, RF-27. Medido: `110` dos 721 beneficiários
      têm CNPJ, e é para eles que o botão aparece.

- [ ] **3.7 — As telas de leitura exibem o nome resolvido.**
      `/comprometido` e `/gastos` mostram o nome de `display_name` onde hoje
      mostram a descrição.
      *Considerando 3.4* e *RF-28:* nenhuma consulta de agregação muda; o nome
      entra só na renderização, e o agrupamento continua por `payee`. Em
      `/comprometido` a junção é por `commitments.series_key`, que é medidamente
      o `payee` normalizado — sem chave nova.
      *Justificativa:* RF-21, RF-28.

- [ ] **3.8 — `tests/test_payee_names.py` e as capturas.**
      A precedência nos cinco níveis; apagar o apelido devolve o anterior; a
      string vazia tratada como ausência; a ordem por dinheiro; a degradação da
      consulta; e que nenhum total muda.
      *Considerando 3.1 a 3.7.* *Justificativa:* RF-21 a RF-28.

**Critérios de aceite da fase 3:**

A base é preparada pelos mesmos comandos, depois de o consolidador ter rodado, e
`Q` tem o mesmo significado da fase 1.

- [ ] `comando` — RF-18, RF-19
      `Q "select count(*) from transactions where merchant_name is not null"`
      imprime `53`; `... where merchant_legal_name is not null` imprime `338`;
      `... where receiver_name is not null` imprime `169`; `... where cnpj is
      not null` imprime `338`; e `... where merchant_name is not null or
      merchant_legal_name is not null or receiver_name is not null` imprime `404`
- [ ] `comando` — RF-19
      `Q "select count(distinct payee) from transactions where merchant_name is
      not null or merchant_legal_name is not null or receiver_name is not null"`
      imprime `148`, e `Q "select count(*) from transactions where
      merchant_legal_name = ''"` imprime `0`
- [ ] `comando` — RF-21, RF-24
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_payee_names.py` sai com código `0`, e o arquivo contém um teste
      por nível da precedência — apelido, fantasia da Pluggy, fantasia
      consultada, razão social, descrição — e um que afirma que apagar o apelido
      devolve o nível seguinte
- [ ] `comportamental` — RF-22, RF-23
      *Dado* o servidor rodando e um cookie válido
      *Quando* `GET /configuracao` é salva em `/tmp/config.html`
      *Então* `grep -c 'data-beneficiario' /tmp/config.html` imprime `30`; o
      primeiro `data-beneficiario` é `debito prestacao hab`; toda linha tem
      `data-origem`; e os `data-gasto` saem em ordem não crescente de valor
      absoluto, o que `grep -o 'data-gasto="[0-9]*"'` seguido de `sort -c -k2 -t
      '"' -nr` confirma sem erro
- [ ] `comportamental` — RF-20, RF-24, RF-28
      *Dado* o servidor rodando, um cookie válido, e `/comprometido` salva antes
      *Quando* `POST /configuracao/beneficiario` grava `Consórcio Coimex` para
      `pagamento de boleto mycon`, `/comprometido` é buscada, o apelido é
      apagado, e `/comprometido` é buscada de novo
      *Então* `grep -c "Consórcio Coimex"` imprime `1` na leitura do meio e `0`
      nas outras duas, e o total comprometido extraído por `grep -o
      'data-total="[-0-9]*"' | head -1` é **idêntico** nas três
- [ ] `comportamental` — RF-26
      *Dado* o servidor rodando sem rede alcançável e um cookie válido
      *Quando* `POST /configuracao/cnpj` é executado para um beneficiário com
      CNPJ
      *Então* a resposta tem código `200`, não `500`; traz uma mensagem em
      português que diz o que aconteceu; e o nome que já existia permanece
- [ ] `estrutural` — RF-30
      Existem, no diretório `06-capturas/` do item, `beneficiarios-375.png`,
      `beneficiarios-1440.png` e `beneficiarios-dark-1440.png`, cada um com mais
      de `1024` bytes

**Critérios de integração da fase 3:**

- [ ] `comando` — portão local e de lint
      `pytest -q` na raiz e `bash scripts/lint.sh` saem ambos com código `0`
- [ ] `comando` — RF-29
      `rtk proxy grep -REn --exclude-dir=__pycache__ "\b(404|338|169|148|721|137|110|53)\b"
      app --include=*.py` não imprime nenhuma linha fora de `app/settings/catalog.py`
- [ ] `comando` — RF-28
      `rtk proxy grep -REn --exclude-dir=__pycache__ "display_name" app/queries
      app/commitments app/plan app/projection app/debts app/taxonomy` não imprime
      nenhuma linha — o nome resolvido não entra em motor de cálculo nenhum

> A DoD global é do CI e não se repete aqui.

## Validações de campo pendentes

- A consulta pública de CNPJ só se prova com rede e com um CNPJ real. Como
  verificar: consultar o CNPJ que a base traz para `pagamento de boleto mycon` e
  conferir que o nome devolvido é reconhecível ao lado da razão social medida,
  `COIMEX ADMINISTRADORA DE CONSORCIOS S.A`.
