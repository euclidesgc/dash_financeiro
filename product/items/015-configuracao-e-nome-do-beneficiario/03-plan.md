# Plano — 015-configuracao-e-nome-do-beneficiario

**Trilha:** rápida · **Brief:** `01-brief.md` · **Revisão pré-código:**
`02-revisao-pre-codigo.md` · Três fases, em sequência.

> **Método de planejamento em acúmulo.** Cada etapa foi escrita considerando o
> que as anteriores deixam no código, e diz isso na linha **Considerando**.
> Terminado o plano inteiro, quatro revisores de modelo forte o leram contra o
> código real **sem escrever implementação**: 36 problemas, três deles defeitos
> vivos que não são deste item. Esta é a versão corrigida por eles.
>
> **Todo número foi medido**, contra a base de 05/09/2026, o JSON bruto da
> Pluggy e o predicado de gasto único do projeto (`app/queries/spending.py:8`).

## Por que esta ordem

1. **Fase 1 é bloqueante.** As fases 2 e 3 escrevem no armazém.
2. **Fase 2 depois da 1** — a tela renderiza o catálogo e lê o armazém.
3. **Fase 3 depois da 2** — o bloco de beneficiários mora dentro da tela que a
   fase 2 cria, e depende do `_text` que a 2.1 traz: sem ele `Consórcio Coimex`
   chega mojibake e o critério da fase 3 reprova por um defeito da fase 2.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | Padrão que decidiu | Decisão |
|---|---|---|
| Catálogo novo, ou um dos três que já existem? | `app/advisor/gaps.py:13` já tem `name`, `label`, `moves`, `where` — os campos que eu ia criar | O catálogo **promove o `WANTED`**, e os nomes dele são os canônicos |
| Qual leitor de valor digitado sobrevive? | `app/plan/whatif.py::_cents` é o único corrigido pelo item `008` | Ele é a origem da gramática de dinheiro; a de taxa vem de `parse_rate` |
| Uma gramática ou uma por unidade? | Medido: taxa usa ponto decimal e faixa 0–100%; dinheiro recusa ponto | **Uma por unidade**, um módulo, uma exceção |
| Qual exceção o leitor único levanta? | Cinco `except` hoje esperam três classes diferentes | **Uma**, `InvalidValueError`; as cinco sedes entram no escopo |
| Vocabulário de `kind` e `unit`: código ou dado? | `app/taxonomy/seed.json` do item `002` | Dado, no catálogo |
| Beneficiário com dois candidatos: quem ganha? | Medido: **zero** beneficiários têm dois valores distintos em qualquer nível | `MIN()` no agrupamento — determinístico, hoje sem efeito |
| Chave de `payee_names` | `commitments` usa `UNIQUE (kind, series_key, …)` para guardar variantes | `PRIMARY KEY (payee, source)` — a chave só em `payee` comportaria 4 níveis de uma precedência de 5 |
| Limite da lista de beneficiários | `CANDIDATES = 12` em `app/routers/rules.py:22` | Constante de módulo `PAYEES = 30`, medida: cobre 55,53% do gasto |
| Predicado de gasto | `app/queries/spending.py:8` diz que toda consulta lê aquela string | Adotado, e os números do brief são os dele |
| Período da lista | Nome não é do período: um beneficiário fora da janela ainda precisa de nome | **Todo o histórico**, declarado na tela |
| `merchant.cnae` entra? | Norma 12 — pendência não vira coluna especulativa | **Fora**: código nu (`7490104`), inútil sem tabela |
| Fonte de CNPJ e como não quebrar a promessa "local" | `app/advisor/gemini.py` só existe se o dono puser a chave: egresso opt-in por construção | BrasilAPI nomeada, **opt-in explícito**, 14 dígitos validados, e `payee_names` é o cache |
| Chave de junção em `/comprometido` | Medido: as 115 linhas de `commitments.series_key` são `payee` existentes | Junta por `series_key`, sem chave nova |
| Padrão de campo na tela nova | Medido: 10 controles usam `field-input`, 15 usam o quebrado | `div.field > label.field-label > input.field-input` |

---

## Fase 1 — Um armazém só para o que só o humano sabe

**Objetivo:** uma tabela, um catálogo, um leitor e um escritor — e o fim de o
painel perguntar o que o dono já respondeu.

### Etapas

- [ ] **1.1 — Migração `010_settings.sql`.**
      `plan_facts` ganha `kind TEXT NOT NULL DEFAULT 'fato'` e a coluna
      `value_cents` é renomeada para `value`. As linhas de `plan_parameters` são
      convertidas para `plan_facts` **com o nome canônico** — `quitacao` vira
      `quitacao-cdc`, `transporte` vira `transporte-sem-carro` —, com `label` do
      catálogo, `unit` `centavos`, `source` `plan_parameters` e `captured_at`
      igual ao `updated_at` de origem. Onde o nome canônico já existir em
      `plan_facts`, a linha de lá **prevalece** e a de `plan_parameters` é
      descartada: ela é mais pobre, sem rótulo nem validade. `plan_parameters` é
      removida.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-01 a RF-03, RF-08a. `DEFAULT` não é enfeite: medido,
      `ALTER TABLE ADD COLUMN NOT NULL` sem default **funciona em tabela vazia e
      falha em tabela com linha** — passaria em todo teste e quebraria só na base
      do dono, que tem fatos gravados desde o item `008`. E o rename de
      `value_cents` existe porque a coluna passa a guardar meses: `brl(6)` é
      "R$ 0,06".

- [ ] **1.2 — `app/settings/catalog.py`: o catálogo como dado.**
      Uma tupla de dicionários com `name`, `label`, `help`, `unit`, `kind`,
      `screen` e `moves`. `app/advisor/gaps.py::WANTED` passa a derivar dele, e
      `app/routers/debts.py:50` deixa de declarar `PARAMETERS`.
      *Considerando 1.1:* `kind` e `unit` só assumem os valores que a coluna
      aceita, e os nomes são os canônicos que a migração gravou.
      *Justificativa:* RF-06, RF-08, RF-08a. São **três** catálogos hoje —
      `PARAMETERS` com dois itens e só rótulo, `WANTED` com três e
      `label`/`moves`/`where`, e o nome livre de `/simulador`. Criar um quarto
      seria o oposto do item; o `WANTED` é o mais rico e vira o único.

- [ ] **1.3 — `app/settings/typed.py`: a leitura de valor digitado, num lugar só.**
      `parse_money`, `parse_rate` e `parse_months`, uma gramática por unidade,
      todas levantando `InvalidValueError`. O corpo de `parse_money` vem de
      `app/plan/whatif.py::_cents`; o de `parse_rate` vem de
      `app/debts/ladder.py::parse_rate`, **corrigido** para recusar `nan`.
      `app/debts/simulate.py::parse_amount` é apagado.
      `app/debts/ladder.py::_cents(value: float)` **não é tocado** — apesar do
      nome, converte float já validado.
      *Considerando 1.2:* a unidade vem do catálogo e escolhe a gramática.
      *Justificativa:* RF-04, RF-04a. Uma gramática só seria regressão medida:
      taxa aceita `3.52` com ponto e se limita a 100% ao mês; sob a gramática
      estrita de dinheiro, `3.52` passaria a ser recusado e `200`% ao mês
      passaria a ser aceito. E é aqui que a fase paga sozinha: hoje `/dividas` lê
      `5000.00` como **R$ 500.000,00** no campo do saldo de quitação, e `inf`,
      `nan` e `1e308` ali — e `nan` no campo de taxa — são HTTP 500.

- [ ] **1.4 — A exceção única, nas cinco sedes.**
      `InvalidAmountError`, `InvalidRateError` e `InvalidScenarioError` dão lugar
      a `InvalidValueError` em: `app/routers/debts.py:77`, `:97` e `:117`, e
      `app/routers/whatif.py:57` e `:82`. `app/debts/simulate.py:19` (aporte não
      positivo) e `app/plan/whatif.py::parse_validity` passam a levantar a nova.
      *Considerando 1.3:* sem esta etapa, três rotas trocam `400` por `500` — o
      `except` de `debts.py:117` fica **inteiramente** órfão.
      *Justificativa:* RF-04a.

- [ ] **1.5 — `app/settings/store.py`: ler e gravar.**
      `read(conn)` devolve o catálogo com valor, unidade e marca de vencido;
      `write(conn, name, typed)` valida contra o catálogo, converte pela unidade
      e grava; `value(conn, name)` devolve o inteiro ou `None`.
      *Considerando 1.1, 1.2 e 1.3.* O `unit` e o `source` deixam de ser literais
      no `INSERT` de `app/routers/whatif.py:89`.
      *Justificativa:* RF-05, RF-07. A recusa por nome fora do catálogo copia a
      de `app/taxonomy/rules.py`.

- [ ] **1.6 — Os quatro pontos de contato, e a tela que renderiza a tabela.**
      `app/debts/simulate.py::parameter` e `POST /dividas/parametro`
      (`app/routers/debts.py:120`); `app/plan/whatif.py::facts` e
      `POST /simulador/fato` (`app/routers/whatif.py:89`). E
      `app/templates/simulador.html:120,122`, que hoje renderiza **toda** linha
      de `plan_facts` com `|brl`: passa a formatar pela `unit`.
      *Considerando 1.5:* os cinco leem o `store`, e nenhum monta SQL próprio.
      *Justificativa:* RF-04, RF-05, RF-17. Sem o template, gravar
      `reserva-meses` na fase 2 faria `/simulador` exibir "R$ 0,06".

- [ ] **1.7 — Os testes que a fase quebra, no escopo declarado.**
      `tests/test_debts.py:6,14` importa `parse_rate` e `parse_amount` no topo —
      erro de coleta leva **17 testes** de uma vez. `tests/test_migrations.py:23`
      lista `plan_parameters` em `EXPECTED_TABLES` e `:70` trava a contagem em
      `("009")`. `tests/test_plan.py:54` compara com `RESERVE_MONTHS`.
      *Considerando 1.3, 1.4 e 1.5.*
      *Justificativa:* norma 10 — "pronto" é build verde. Uma etapa que não
      nomeia o teste que ela quebra empurra a quebra para o portão.

- [ ] **1.8 — `tests/test_settings.py`.**
      A migração sobre base **com linha preexistente** em `plan_facts`; a
      conversão de nome antigo para canônico; a colisão resolvida a favor do
      `plan_facts`; nome fora do catálogo recusado; a unidade respeitada; ausente
      devolvendo `None` e não zero; o vencido marcado; o mesmo valor visível
      pelas duas telas; `5000.00` recusado; `inf`, `nan` e `1e308` recusados nas
      duas gramáticas; `3,52` aceito como taxa e `200` recusado.
      *Considerando 1.1 a 1.7.*
      *Justificativa:* RF-01 a RF-08a. Nenhum destes erros quebra tela; todos
      produzem número plausível e errado.

**Critérios de aceite da fase 1:**

`Q` abrevia `rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-015.sqlite .venv/bin/python -m app.query`, sobre base
preparada por `rm -f /tmp/dash-015.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-015.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest`.

- [ ] `comando` — RF-01, RF-03, RF-04
      `Q "select count(*) from sqlite_master where type='table' and name in
      ('plan_facts','plan_parameters')"` imprime `1`; `Q "select count(*) from
      pragma_table_info('plan_facts') where name='kind'"` imprime `1`; e
      `Q "select count(*) from pragma_table_info('plan_facts') where
      name='value_cents'"` imprime `0`
- [ ] `comando` — RF-02, RF-08a · a migração sobre base que **não** está vazia
      Um trecho que copia os nove `.sql` até `009` para uma pasta temporária,
      cria a base com eles, insere **uma linha em `plan_facts`** e a linha
      `('quitacao', 3500000, '2026-09-01T10:00:00')` em `plan_parameters`, roda a
      migração `010` e lê de volta: termina com código `0`, a linha preexistente
      de `plan_facts` continua lá com `kind` valendo `fato`, e
      `Q "select name, value, kind, unit, source from plan_facts where name like
      'quitacao%'"` imprime uma linha só, com `quitacao-cdc`, `3500000`, `fato`,
      `centavos`, `plan_parameters` — separados por espaço, que é como
      `app/query.py:22` imprime
- [ ] `comando` — RF-04a · os defeitos medidos
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -c "$(cat
      product/items/015-configuracao-e-nome-do-beneficiario/06-evidencias/typed.py)"`
      imprime `recusado` para `5000.00`, `inf`, `nan` e `1e308` em `parse_money`,
      `recusado` para `nan` e `200` em `parse_rate`, `352` para `3,52`, e
      `250000` para `2.500,00` — e sai com código `0`, sem traceback
- [ ] `comando` — RF-04a, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_settings.py` sai com código `0`
- [ ] `comando` — RF-01, RF-04a, DRY
      `rtk proxy grep -REn --exclude-dir=__pycache__ "plan_parameters" app`
      imprime linhas **apenas** de `app/migrations/sql/`;
      `rtk proxy grep -REn "InvalidAmountError|InvalidRateError|InvalidScenarioError" app`
      não imprime nenhuma linha; e `rtk proxy grep -c "def parse_money" app/settings/typed.py`
      imprime `1` — o critério prova que o leitor **existe**, não só que os
      antigos sumiram
- [ ] `comportamental` — RF-05, RF-08a
      *Dado* o servidor rodando contra `/tmp/dash-015.sqlite` e um cookie válido
      *Quando* `POST /dividas/parametro` grava `valor=35.000,00` no saldo de
      quitação, e em seguida `GET /simulador` e `GET /consultor` são buscadas
      *Então* `/simulador` traz `35.000,00` no bloco `id="fatos"`, e `/consultor`
      **não** traz mais a pergunta "o saldo de quitação antecipada do CDC do
      carro" — hoje traz as duas coisas ao contrário

**Critérios de integração da fase 1:**

- [ ] `comando` — portão local e de lint
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz e `rtk proxy bash scripts/lint.sh` saem ambos com código `0`, e a
      contagem de testes é de **pelo menos** `433` — a fase não pode encolher a
      suíte

---

## Fase 2 — A tela de configuração

**Objetivo:** um lugar que lista tudo o que alimenta cálculo, diz o que cada
valor muda, e grava — sem que a tela passe a dizer um número e calcular outro.

### Etapas

- [ ] **2.1 — `app/routers/settings.py`: `GET /configuracao` e `POST /configuracao`.**
      `_answer(request, conn, *, notice, status_code)` na forma de
      `app/routers/whatif.py:104`, **com o `_text` de `app/routers/rules.py:264`**
      aplicado a todo campo de formulário. O router é registrado em
      `app/main.py`, no import e no `include_router`.
      *Considerando 1.5:* o contexto vem de `store.read(conn)` inteiro.
      *Justificativa:* RF-12, RF-16. O `_text` não é zelo: Starlette lê campo
      urlencoded como latin-1 antes de percent-decode, e sem ele
      `Consórcio Coimex` — que a fase 3 grava — chega mojibake. A forma de
      `plan.py` foi descartada: ele não tem `_answer`, e o `bool` do
      `_reference` dele só serve junto de `record()`.

- [ ] **2.2 — `app/templates/configuracao.html`.**
      Dois blocos, `id="fatos"` e `id="metas"`, cada linha com
      `data-config="<nome>"` e `data-valor`, o que ele muda, e o link para a tela
      de contexto. Estrutura de campo `div.field > label.field-label >
      input.field-input`, `.cifra` em toda cifra, recusa em
      `p.notice#recusa[role=alert]`.
      *Considerando 2.1* e *1.2* (o texto de "o que muda" vem do `moves`).
      *Justificativa:* RF-13 a RF-15, RF-30. O padrão de campo é medido, não
      escolhido: `input.field` — usado em 15 controles do projeto — não tem
      borda, raio nem `font-size`, e cai abaixo dos 16px que a linguagem visual
      exige para o celular não dar zoom ao focar.

- [ ] **2.3 — O Resumo leva à configuração.**
      Uma linha em `app/templates/resumo.html`. *Considerando 2.1.*
      *Justificativa:* RF-12.

- [ ] **2.4 — Meta informada substitui a constante, inclusive no texto.**
      `app/plan/objective.py::reserve_target_cents` e
      `app/projection/monthly.py::complete_months` passam a ler o armazém, com a
      constante como padrão. E o número segue até onde ele é **escrito**:
      `app/routers/plan.py:75` e `app/templates/objetivo.html:12` e `:96`.
      `complete_months` recusa meta maior que os meses fechados da base.
      *Considerando 1.5* (o leitor) e *1.2* (os nomes vêm do catálogo).
      *Justificativa:* RF-09, RF-10a, invariante 26. Sem as três últimas
      referências, gravar `reserva-meses = 3` faz `/objetivo` imprimir **"6 meses
      de reserva"** acima de uma cifra que vale 3 — e o critério que só compara a
      cifra **aprova em verde**. E `seen[-N:]` trunca calado: pedir 12 numa base
      com 6 diria 12 e calcularia 6.

- [ ] **2.5 — `scripts/capturas.mjs`, versionado.**
      Um script parametrizado por item, tela e larguras, que escreve em
      `product/items/<item>/06-capturas/`.
      *Considerando:* nada do plano — é dívida de processo.
      *Justificativa:* norma 20. Quatro vezes nesta corrida uma captura foi
      escrita em diretório inexistente porque o script era recriado por `sed` a
      cada item. A causa raiz é ele não existir no repositório.

- [ ] **2.6 — `tests/test_configuracao_screen.py` e as capturas.**
      A tela lista o catálogo; gravar move o número na mesma resposta; ausente
      diz o que o painel usa no lugar; meta informada muda a reserva alvo **e o
      texto**; meta maior que a base é recusada; acento sobrevive ao formulário.
      Capturas em 375, 768, 1440 e 1440 escuro.
      *Considerando 2.1 a 2.5.* *Justificativa:* RF-09 a RF-16, RF-30.

**Critérios de aceite da fase 2:**

- [ ] `comportamental` — RF-12, RF-13
      *Dado* o servidor rodando e um cookie válido
      *Quando* `GET /configuracao` é salva em `/tmp/config.html`
      *Então* `grep -o 'id="fatos"' /tmp/config.html | wc -l` e o mesmo para
      `id="metas"` imprimem `1` cada, e `grep -o 'data-config="[^"]*"'
      /tmp/config.html | sort -u | wc -l` imprime o mesmo número que
      `len(CATALOG)` — a classe `[^"]*` casa nome com dígito, que `[a-z-]*` não
      casa
- [ ] `comportamental` — RF-09, RF-14, RF-16 · a cifra **e** o texto
      *Dado* o servidor rodando, um cookie válido e nenhuma meta gravada
      *Quando* a configuração é lida, `POST /configuracao` grava `reserva-meses`
      com valor `3`, e `GET /objetivo?data=2026-09-05` é buscada antes e depois
      *Então* a primeira leitura da configuração diz que o painel usa `6`
      enquanto não houver valor; a reserva alvo extraída da manchete por
      `grep -o 'data-alvo="[-0-9]*"' | head -1` é exatamente **metade**; e
      `grep -c "3 meses de reserva"` na segunda leitura de `/objetivo` imprime
      pelo menos `1`, enquanto `grep -c "6 meses de reserva"` imprime `0`
- [ ] `comportamental` — RF-07, RF-10a
      *Dado* o servidor rodando e um cookie válido
      *Quando* `POST /configuracao` é feito com `nome=inexistente`, depois com
      `nome=reserva-meses` e `valor=abc`, e depois com `nome=mediana-meses` e
      `valor=12`
      *Então* as três respostas têm código `400`, a primeira nomeia
      `inexistente`, a segunda nomeia o campo, a terceira diz quantos meses a
      base tem, e nada é gravado
- [ ] `comando` — RF-12, RF-16
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_configuracao_screen.py` sai com código `0`
- [ ] `estrutural` — RF-30
      Existem, em `06-capturas/`, `configuracao-375.png`, `configuracao-768.png`,
      `configuracao-1440.png` e `configuracao-dark-1440.png`, cada um com mais de
      `1024` bytes, e existe `scripts/capturas.mjs` rastreado pelo git
- [ ] `comportamental` — RF-30
      *Dado* o Chromium com sessão válida e `/configuracao` carregada
      *Quando* a janela é ajustada para `375`, `768` e `1440` px por `800`, uma
      vez carregando já naquela largura e uma vez redimensionando
      *Então* nas seis medições `document.documentElement.scrollWidth <=
      window.innerWidth` avalia `true`, e todo `input` da tela tem
      `getComputedStyle(el).fontSize` de pelo menos `16px` — a medida que o
      padrão de campo errado reprova

**Critérios de integração da fase 2:**

- [ ] `comando` — portão local e de lint
      `pytest -q` na raiz e `bash scripts/lint.sh` saem ambos com código `0`
- [ ] `comando` — RF-10, RF-11
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -c "from
      app.settings.catalog import CATALOG; print(sorted(v['name'] for v in
      CATALOG))"` imprime uma lista que **não** contém `janela-dias` nem nome
      algum ligado a `WINDOW_DAYS`, `DUE_TOLERANCE_DAYS`,
      `SAME_PURCHASE_DEVIATION` ou `MIN_BALANCE_CENTS` — o critério lê o
      catálogo, e não `grep` por nome de constante Python, que nunca casaria com
      um catálogo em kebab-case
- [ ] `comportamental` — RF-12, invariante 24
      *Dado* um cookie válido e, em seguida, nenhuma sessão
      *Quando* `GET /configuracao` e `POST /configuracao` são chamadas nas duas
      condições
      *Então* com sessão nenhuma delas responde `404` — isto é, as rotas
      existem — e sem sessão as duas respondem `302`. As duas metades são
      necessárias: a guarda é middleware e responde antes do roteamento, então
      `302` sem sessão sozinho é o que qualquer URL inventada também devolve.
      `tests/test_route_guard.py` cobre a segunda metade para toda rota
      registrada. A rota `POST /configuracao/cnpj` é cobrada pela fase 3, que é
      quem a cria — ver `04-divergencias/D-002.md`

---

## Fase 3 — O nome real do beneficiário

**Objetivo:** os lançamentos que a Pluggy já nomeia ganham nome de verdade sem o
dono digitar nada, e o resto ele batiza uma vez, começando pelo dinheiro.

### Etapas

- [ ] **3.1 — `httpx` vira dependência de produção.**
      Sai de `[dependency-groups] dev` e entra em `[project] dependencies`.
      *Considerando:* nada do plano.
      *Justificativa:* norma 15. `app/advisor/gemini.py:4` já o importa em
      produção e `app/main.py` registra o router no boot: instalação sem o grupo
      dev não sobe o app. A etapa 3.7 seria o segundo consumidor.

- [ ] **3.2 — O consolidador carrega os campos adiante.**
      `ingestao/pluggy_consolidate.py` escreve `nome_fantasia` (de
      `merchant.name`), `razao_social` (de `merchant.businessName`), `cnpj` e
      `recebedor` (de `paymentData.receiver.name`). String vazia é ausência. A
      leitura é `(t.get("merchant") or {}).get(...)`.
      *Considerando o formato do consolidado:* as chaves são em português.
      *Justificativa:* RF-18, e a decisão `D7` do item `001`. Medido: `merchant`
      vem como **`None`, não ausente**, em 1556 dos 1942 lançamentos —
      `t.get("merchant", {})` levantaria `AttributeError` em 80% da base. E
      `businessName` vem como `""` em 48 lançamentos que **têm** nome fantasia:
      gravar a string vazia faria `is not null` contar `386` onde a resposta é
      `338`.

- [ ] **3.3 — Migração `011_payee_names.sql`.**
      `transactions` ganha `merchant_name`, `merchant_legal_name`,
      `merchant_cnpj` e `receiver_name`. Nasce `payee_names` com
      `PRIMARY KEY (payee, source)`, `name` e `updated_at`.
      *Considerando 3.2:* uma coluna por campo, sem coluna órfã — e por isso não
      há CNAE.
      *Justificativa:* RF-19, RF-20, RF-27. A chave composta é o conserto do
      furo que a revisão achou: com a chave só em `payee`, batizar por cima
      **destruiria** o nome consultado e apagar o apelido cairia dois níveis, o
      que contradiz RF-24.

- [ ] **3.4 — A carga grava, e recusa consolidado velho.**
      `app/ingest/loader.py` acrescenta as quatro colunas a
      `_TRANSACTION_COLUMNS` e as quatro chaves a `_transaction_row`. Se o
      consolidado não trouxer as chaves novas, a carga **recusa** dizendo para
      rodar o consolidador.
      *Considerando 3.2* e *3.3*.
      *Justificativa:* RF-19. Medido: `_upsert` faz `ON CONFLICT DO UPDATE SET`
      em **todas** as colunas, então apertar Sincronizar com um consolidado
      gerado antes da 3.2 zera as quatro colunas em 1942 linhas e o painel perde
      todo nome, com `sync_runs` registrando `ok`.

- [ ] **3.5 — `app/payees/names.py`: a precedência, num lugar só.**
      `display_name(conn)` devolve, por beneficiário, nome e origem, nesta
      ordem: apelido do dono (`source='dono'`); nome fantasia da Pluggy
      (`merchant_name`); nome fantasia consultado (`source='cnpj'`); razão social
      (`merchant_legal_name`, senão `receiver_name`); descrição normalizada.
      *Considerando 3.3* (a chave composta é o que permite os níveis 1 e 3
      coexistirem) e *o padrão do `014`* (a origem viaja junto com o valor).
      *Justificativa:* RF-21, RF-22, RF-24, RF-27. A ordem é por **qualidade do
      nome**: medido, `merchant.name` traz `Apple`, `Shopee`, `outback`, e
      `receiver.name` traz `IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A.` — os
      dois vêm da Pluggy, e um é resposta e o outro é razão social. `MIN()` no
      agrupamento é determinístico e hoje não muda nada: nenhum dos 720
      beneficiários tem dois valores distintos em nível algum.

- [ ] **3.6 — O bloco de beneficiários dentro da configuração.**
      `id="beneficiarios"`, os `PAYEES = 30` maiores por gasto absoluto sobre
      **todo o histórico**, usando `app/queries/spending.py::SPENDING`, cada
      linha com `data-beneficiario`, `data-origem`, `data-gasto` **com sinal** e
      um campo para batizar. O bloco declara quantos existem ao todo e que fração
      os 30 cobrem.
      *Considerando 2.1 e 2.2* (mesma rota, mesmo `_answer`, mesmo `_text`) e
      *3.5*.
      *Justificativa:* RF-23. Medido com o predicado do projeto: 30 de **720**
      beneficiários cobrem **55,53%** do gasto, e o maior — `debito prestacao
      hab`, R$ 22.204,77 — é justamente um que a Pluggy não nomeia.

- [ ] **3.7 — A consulta de CNPJ, opt-in e sob demanda.**
      `app/payees/lookup.py`, chamado por `POST /configuracao/cnpj`, contra
      `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`, com o CNPJ validado como 14
      dígitos, tempo limite próprio e os quatro `except` do `009`. Desligada
      enquanto o dono não a habilitar; a tela declara que está desligada. O nome
      grava com `source='cnpj'`, que é o cache.
      *Considerando 3.5:* o nome consultado fica abaixo do apelido do dono.
      *Justificativa:* RF-25 a RF-27. O produto é local por definição, e hoje o
      único egresso — o consultor — só existe se o dono puser a chave. Um botão
      sem opt-in diria a um terceiro, numa lista ordenada por dinheiro, com quem
      ele tem relação comercial.

- [ ] **3.8 — As telas de leitura exibem o nome resolvido, só como rótulo.**
      `/comprometido` e o eixo **beneficiário** de `/gastos` recebem o mapa de
      `display_name` como `labels`, que a macro `cell_name` já sabe usar. O
      `row['key']` do drill-down **não muda**. `/regras` fica de fora, e
      `gastos_detalhe.html` também.
      *Considerando 3.5* e *RF-28.* Em `/comprometido` a junção é por
      `commitments.series_key`, medido igual ao `payee` nas 115 linhas.
      *Justificativa:* RF-21, RF-28. `row['key']` é rótulo **e** parâmetro de
      drill-down: trocar o valor renderizado mataria a abertura da lista em
      silêncio. E `/regras` exibindo apelido faria o dono escrever regra contra
      um texto que nunca casa.

- [ ] **3.9 — `tests/test_payee_names.py`, a guarda de rede e os números
      congelados.**
      A precedência nos cinco níveis, **com `dono` e `cnpj` no mesmo
      beneficiário**; apagar o apelido devolve o consultado; string vazia é
      ausência; a ordem por dinheiro; a recusa de consolidado velho; a degradação
      da consulta por `monkeypatch`; e que nenhum total muda. Uma fixture de
      `conftest.py` faz qualquer chamada real de `httpx` falhar. Os números novos
      entram em `tests/test_frozen_numbers.py`.
      *Considerando 3.1 a 3.8.* *Justificativa:* RF-21 a RF-29.

**Critérios de aceite da fase 3:**

- [ ] `comando` — RF-18, RF-19
      Com `Q` como na fase 1: `Q "select count(*) from transactions where
      merchant_name is not null"` imprime `53`; `... merchant_legal_name ...`
      imprime `338`; `... receiver_name ...` imprime `169`; `... merchant_cnpj
      ...` imprime `338`; a união dos três nomes imprime `404`;
      `Q "select count(*) from transactions where merchant_legal_name = ''"`
      imprime `0`; e `Q "select count(distinct payee) from transactions where
      merchant_name is not null or merchant_legal_name is not null or
      receiver_name is not null"` imprime `148`
- [ ] `comando` — RF-21, RF-24, RF-27
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_payee_names.py` sai com código `0`, e o arquivo contém um teste
      que grava `cnpj` **e** `dono` para o mesmo beneficiário, afirma que o
      exibido é o do dono, apaga o do dono e afirma que o exibido volta a ser o
      consultado — não a razão social
- [ ] `comportamental` — RF-22, RF-23
      *Dado* o servidor rodando e um cookie válido
      *Quando* `GET /configuracao` é salva em `/tmp/config.html`
      *Então* `grep -o 'data-beneficiario="[^"]*"' /tmp/config.html | wc -l`
      imprime `30`; o primeiro é `debito prestacao hab`; toda linha tem
      `data-origem`; e `grep -o 'data-gasto="[-0-9]*"' /tmp/config.html | cut -d
      '"' -f2 | sort -c -n` sai com código `0` — ordem não decrescente de valor
      **com sinal**, que é ordem não crescente de valor absoluto
- [ ] `comportamental` — RF-20, RF-24, RF-28
      *Dado* o servidor rodando, um cookie válido, e `/comprometido?data=2026-09-05`
      salva antes
      *Quando* `POST /configuracao/beneficiario` grava `Consórcio Coimex` para
      `pagamento de boleto mycon`, `/comprometido?data=2026-09-05` é buscada, o
      apelido é apagado, e ela é buscada de novo
      *Então* `grep -c "Consórcio Coimex"` imprime `0` na primeira, **pelo menos
      `1`** na segunda e `0` na terceira; e o total comprometido, extraído do
      `data-comprometido` do cabeçalho que a etapa 3.8 acrescenta, é **idêntico**
      nas três
- [ ] `comportamental` — RF-26, RF-25b
      *Dado* o servidor rodando, um cookie válido, a consulta habilitada, e
      `httpx.get` trocado por um que levanta `httpx.TimeoutException`
      *Quando* `POST /configuracao/cnpj` é executado para um beneficiário com
      CNPJ, e depois para um cujo CNPJ foi adulterado para `../etc`
      *Então* as duas respostas têm código `200`, não `500`; a primeira diz em
      português que o tempo esgotou e o nome que já existia permanece; a segunda
      recusa sem sair para a rede
- [ ] `estrutural` — RF-30
      Existem, em `06-capturas/`, `beneficiarios-375.png`,
      `beneficiarios-768.png`, `beneficiarios-1440.png` e
      `beneficiarios-dark-1440.png`, cada um com mais de `1024` bytes

**Critérios de integração da fase 3:**

- [ ] `comando` — portão local e de lint
      `pytest -q` na raiz e `bash scripts/lint.sh` saem ambos com código `0`
- [ ] `comando` — RF-29
      `rtk proxy grep -REn --exclude-dir=__pycache__ "\b(338|169|148|720|137|110|53)\b"
      app --include='*.py'` não imprime nenhuma linha — com o `*.py` **entre
      aspas**, sem o que o zsh aborta a linha e o critério passa sem rodar. E
      `tests/test_frozen_numbers.py` traz os números novos
- [ ] `comando` — RF-28
      `rtk proxy grep -REn --exclude-dir=__pycache__ "display_name|payee_names"
      app/queries app/commitments app/plan app/projection app/debts app/taxonomy`
      não imprime nenhuma linha — proibir o identificador não basta, um
      `LEFT JOIN payee_names` escrito à mão passaria limpo e mudaria o `GROUP BY`
- [ ] `comportamental` — RF-12, RF-25a, invariante 24
      *Dado* um cookie válido e, em seguida, nenhuma sessão
      *Quando* `POST /configuracao/cnpj` e `POST /configuracao/beneficiario` são
      chamadas nas duas condições
      *Então* com sessão nenhuma delas responde `404` — isto é, as rotas que a
      fase 3 cria existem — e sem sessão as duas respondem `302`
      — ver `04-divergencias/D-002.md`
- [ ] `comando` — norma 15
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -c "import
      tomllib,pathlib; d=tomllib.loads(pathlib.Path('pyproject.toml').read_text());
      assert 'httpx' in d['project']['dependencies']"` sai com código `0` — e
      levanta `AssertionError` com código `1` se a dependência voltar para o
      grupo `dev`. Um comando que apenas imprimisse o resultado da comparação
      sairia com código zero nos dois casos, e certificaria a si mesmo

> A DoD global é do CI e não se repete aqui.

## Pendências que viram item de roadmap

- `data/manual/financiamento_caixa.json` e `cdc_safra_veiculo.json` carregam
  saldo devedor, juros e prazo informados pelo humano, em arquivo cujo nome está
  no código (`app/debts/ladder.py:22`). É invariante 26 e não cabe nesta fase.
- `tests/` não tem guarda global de rede fora do que a fase 3 acrescenta.

## Validações de campo pendentes

- A consulta de CNPJ só se prova com rede. Como verificar: habilitar a consulta,
  consultar o CNPJ que a base traz para `pagamento de boleto mycon` e conferir
  que o nome devolvido é reconhecível ao lado da razão social medida,
  `COIMEX ADMINISTRADORA DE CONSORCIOS S.A`.
