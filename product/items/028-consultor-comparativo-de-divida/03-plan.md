# Plano — 028-consultor-comparativo-de-divida

**Item:** `028-consultor-comparativo-de-divida` · **Trilha:** rápida ·
**Fonte aprovada:** `01-brief.md` · **Terreno:** `00-discovery.md` · Duas fases,
em sequência.

> **Os valores em centavos deste plano não foram medidos por execução: são
> derivados à mão da fórmula declarada abaixo**, e é isso que os torna
> conferíveis por **oráculo independente**. O validador refaz a mesma aritmética
> por fora — sem ler a implementação — e tem de chegar ao mesmo centavo. Uma
> função e um teste saídos da mesma cabeça, sem oráculo, não provam nada.

## Objetivo

Ao fim das duas fases o painel responde à pergunta que decide dinheiro: **fico no
cheque especial ou pego um empréstimo, e qual proposta quita tudo mais barato**.
O dono informa as propostas em `/configuracao`, na mesma forma das duas entidades
editáveis que acabaram de nascer; `/consultor` mostra, por proposta, quanto custa
continuar como está e quanto custa a proposta, com a diferença nomeada; e a IA lê
o resultado e explica — sem nunca compor um número.

A quebra é por **contrato**: a fase 1 fixa a forma do dado (a tabela de propostas
e a função de custo) e a fase 2 a consome em três lugares de uma vez (a tela, o
contexto do modelo e a guarda de citação). Premissa errada sobre o que "custo
total até zerar" significa se espalharia para os três consumidores juntos.

**A restrição que desenha o item é a norma 23.** Nenhum número da comparação sai
do modelo: quem calcula é `total_cost`, testada contra oráculo; o modelo recebe o
resultado pronto, e o painel **não exibe** leitura que cite cifra ausente do
contexto.

## O terreno, lido

| Sítio | Hoje | O que falta |
|---|---|---|
| `app/debts/ladder.py:134-141` | `ladder(conn)` devolve os degraus com taxa, `ORDER BY monthly_rate_bp DESC, balance_cents` | nada: o degrau mais caro é `ladder(conn)[0]`, e é ele o "continuar como está" |
| `app/financings/store.py`, `app/financings/typed.py`, `app/routers/financings.py`, `app/templates/fragments/configuracao_financiamentos.html` | entidade editável completa, nascida no item `025` | é o molde de forma que a fase 1 copia |
| `app/cards/store.py:21-44`, `app/templates/fragments/configuracao_cartoes.html` | seção própria em `/configuracao`, com `data-cartao` e não `data-config` | é o molde de fragmento que a fase 1 copia |
| `app/routers/settings.py:189-225` | `answer()` e `_context()` montam `configuracao.html`; `cards.py` e `financings.py` importam `answer` | `_context` precisa entregar as propostas |
| `app/advisor/context.py:30-53` | `lines()` é a lista única que a tela renderiza **e** o modelo recebe | as linhas da comparação |
| `app/advisor/gemini.py:54-62` | `ask()` manda `systemInstruction` + `f"{context}\n\nPergunta: {question}"` por `httpx.post(..., json=body)` | nada: o contexto enviado é observável pelo corpo da requisição |
| `app/routers/advisor.py:62-68` | a leitura do modelo vai direto para a tela | a conferência de cifra antes de exibir |
| `app/templates/consultor.html:54-64` | `id="leitura"`, `id="indisponivel"` e a frase de falta de chave | a seção da comparação e o aviso de leitura não conferida |

**Duas armadilhas medidas na leitura, e não descobertas na implementação:**

1. `tests/test_configuracao_screen.py:64` casa **todo** `data-config` da página
   com o catálogo, por igualdade de conjunto: um fragmento novo que use esse
   atributo derruba a suíte. O atributo do fragmento novo é `data-proposta`.
2. `tests/test_migrations.py:9-51` fixa `EXPECTED_TABLES` e `EXPECTED_MIGRATIONS`
   por igualdade de lista: uma migração nova sem as duas entradas correspondentes
   derruba a suíte.

E uma terceira, de escrita: os portões arquiteturais medem o diff nesta corrida,
então **todo comentário novo começa por marca de justificativa** — `Motivo:`,
`Decisão:`, `Contorno:`, `Invariante:`, `Limitação:`
(`scripts/gates/gate3_no_comments.sh:29`). `tests/test_frozen_numbers.py:11-37`
varre `app/**` atrás dos números congelados do relatório: nenhum literal novo em
`app/` pode ser um deles.

## A aritmética, declarada antes de ser implementada

Esta é a definição que a fase 1 implementa e que o validador refaz por fora.

Com `taxa = monthly_rate_bp / 10000` (a escala de `app/financings/money.py:1`),
`valor` o valor liberado em centavos, `prazo` em meses e `contratacao` em
centavos:

```
parcela = round(valor * taxa / (1 - (1 + taxa) ** -prazo))
custo   = parcela * prazo - valor + contratacao
```

e, quando `taxa == 0`, `custo = contratacao` — sem juros não há fator de anuidade
para dividir, e a divisão por zero não é o caso de borda, é o caso zero.

Os três valores que os critérios cobram, derivados à mão desta fórmula:

| Entrada | Conta | Resultado |
|---|---|---|
| `valor=100000`, `taxa=1000`, `prazo=2`, `contratacao=5000` | `1,1² = 1,21`; `1 − 1,21⁻¹ = 0,1735537…`; `10000 / 0,1735537… = 57619,0476…` → `57619`; `57619 × 2 − 100000 = 15238`; `+ 5000` | **20238** |
| `valor=100000`, `taxa=2000`, `prazo=2`, `contratacao=0` | `1,2² = 1,44`; `1 − 1,44⁻¹ = 0,3055555…`; `20000 / 0,3055555… = 65454,5454…` → `65455`; `65455 × 2 − 100000` | **30910** |
| `valor=100000`, `taxa=0`, `prazo=2`, `contratacao=5000` | sem juros | **5000** |

A diferença entre os dois primeiros caminhos é `30910 − 20238 = 10672`, e em
`brl` os três saem `R$ 202,38`, `R$ 309,10` e `R$ 106,72`. Nenhum dos três está
perto de um empate de arredondamento: as frações são `,0476` e `,5454`, então a
conta é reprodutível em qualquer linguagem com ponto flutuante de dupla precisão.

## Decisões resolvidas pelo terreno, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| Contra que dinheiro e que prazo se compara "continuar como está"? | Um cheque especial **não tem cronograma próprio**: não existe "custo até zerar" dele sem alguém fixar quanto se paga por mês. A única base definida para os dois lados é a que a proposta já traz | mesmo **valor liberado** e mesmo **prazo** da proposta, à taxa do degrau atual. Registrado no retorno como lacuna do brief |
| Qual é o "degrau atual"? | O exemplo do discovery é o cheque especial a 4,22%, e `app/debts/ladder.py:138-140` já ordena por taxa decrescente | `ladder(conn)[0]` — o degrau mais caro da escada |
| Custo é positivo ou negativo? | `app/debts/simulate.py:73` devolve `interest_saved_cents` positivo e `cards.limit_cents` guarda o limite positivo: parâmetro e magnitude não são movimento de dinheiro | positivo, rotulado como custo na tela. A invariante 22 vale para movimento, e nenhuma linha nova é movimento |
| Fórmula fechada ou amortização mês a mês? | Medido à mão: para `valor=100000, taxa=2000, prazo=2` a fórmula fechada dá 30910 e o laço com resíduo na última parcela dá 30909 — **um centavo de diferença**, e um critério ambíguo entre os dois não é conferível por oráculo | **fórmula fechada**, declarada acima |
| Proposta sem taxa é gravável? | RF-04 exige que ela exista e fique de fora | sim: `monthly_rate_bp` é anulável. `prazo` e `valor liberado` são obrigatórios — sem eles não há proposta nenhuma —, e `custo de contratação` em branco vale zero |
| Como uma proposta se identifica? | RF-01 lista quatro campos, nenhum deles identidade, e uma lista de propostas precisa de uma para ser editada e removida | campo `nome`, com `UNIQUE`: regravar o mesmo nome atualiza, como `app/financings/store.py:28-31` já faz por `kind`. Registrado no retorno |
| Onde mora o POST? | Os itens `024` e `025` deram router próprio a cada entidade nova (`app/routers/cards.py`, `app/routers/financings.py`), e concentrar a quarta em `settings.py` transforma o arquivo em gaveta | **router próprio, `app/routers/offers.py`**, registrado por uma linha em `app/main.py`, que o dono abriu no escopo. A norma 29 vale, e o precedente dos dois itens vizinhos é o desempate |
| O que impede o modelo de citar cifra que ele compôs? | `app/advisor/gemini.py:13-20` **pede** ao modelo que não invente; pedido não é garantia, e RF-05 diz "apenas" | o painel confere a leitura contra o contexto e **não a exibe** se achar cifra ausente. Registrado no retorno |
| O que conta como "cifra" na conferência? | Uma gramática larga acusaria `2026` e `quatro`; o risco nomeado no brief é `R$ 3.400` | só `R$` seguido de valor e número seguido de `%`. Limitação declarada |
| Que número da migração? | O runner ordena por nome e tolera lacuna (`app/migrations/runner.py:36`), e os itens `019` e `026` estão em curso | `018_offers.sql`, deixando `016` e `017` livres para quem colidir antes do merge |
| A escada, o objetivo e o comprometido mudam? | RF-08 | **nenhuma** fase toca `app/queries/`, `app/commitments/`, `app/taxonomy/`, `app/routers/spending.py` nem `app/routers/commitments.py` |

---

## Fase 1 — A proposta como entidade, e o custo até zerar (api)

**Objetivo da fase:** o dono informa propostas de empréstimo em `/configuracao`,
e existe uma função testada que diz quanto um caminho de dívida custa até zerar.

**Critérios de aceite:**

- [ ] `comando` — RF-01
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -c "import
      tempfile, pathlib; from app.migrate import SQL_FOLDER; from
      app.migrations.runner import apply_migrations; from app.db import connect;
      d=tempfile.mkdtemp(); c=connect(str(pathlib.Path(d)/'x.sqlite'));
      apply_migrations(c, SQL_FOLDER); cols={r[1]: (r[2], r[3]) for r in
      c.execute(\"pragma table_info('offers')\")};
      assert set(cols) >= {'name','monthly_rate_bp','term_months',
      'released_cents','fee_cents','captured_at'}, cols;
      assert cols['monthly_rate_bp'][1] == 0, cols;
      assert cols['term_months'][1] == 1 and cols['released_cents'][1] == 1,
      cols"` sai com código `0`. A asserção é de **pertinência**, não de
      igualdade: a tabela pode ganhar coluna em outro item. `notnull == 0` na
      taxa é o que RF-04 exige — proposta sem taxa precisa caber na tabela antes
      de ficar de fora da comparação
- [ ] `estrutural` — RF-02
      Existe `app/offers/cost.py`, e ele exporta `total_cost` com os parâmetros
      `released_cents`, `monthly_rate_bp`, `term_months` e `fee_cents`. O arquivo
      **não** contém as cadeias `httpx`, `ask(` nem `gemini`: nenhum número da
      comparação passa pelo modelo
- [ ] `comportamental` — RF-02
      *Dado* o interpretador do repositório com `DASH_ENV_FILE=/dev/null`
      *Quando* `app.offers.cost.total_cost` é chamada três vezes, com
      `(released_cents=100000, monthly_rate_bp=1000, term_months=2,
      fee_cents=5000)`, com `(100000, 2000, 2, 0)` e com `(100000, 0, 2, 5000)`
      *Então* as três devolvem, na ordem, os inteiros `20238`, `30910` e `5000`.
      **A conferência é por oráculo independente**, refeita fora da
      implementação: com `i = monthly_rate_bp / 10000`, a parcela é
      `round(released_cents * i / (1 - (1 + i) ** -term_months))` e o custo é
      `parcela * term_months - released_cents + fee_cents`; com `i == 0` o custo
      é `fee_cents`. À mão: `1,1² = 1,21`, parcela `57619`, juros `15238`, mais
      `5000` de contratação dá `20238`; `1,2² = 1,44`, parcela `65455`, juros
      `30910`; sem juros, só a contratação, `5000`
- [ ] `comportamental` — RF-01
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-09-05` e `DASH_ENV_FILE=/dev/null` no ambiente do
      processo, base carregada e sessão autenticada
      *Quando* `POST /configuracao/proposta` é enviada com `nome=Banco Teste`,
      `taxa=10`, `prazo=2`, `liberado=1.000,00` e `contratacao=50,00`, e em
      seguida `GET /configuracao` é buscada
      *Então* a resposta do POST é `200`, e no recorte do HTML que vai de
      `data-proposta="Banco Teste"` até o primeiro `</article>` depois dele
      aparecem `data-prazo="2"`, `10,00%`, `1.000,00`, `50,00` e `05/09/2026` —
      a data em que a proposta foi informada, que é o que impede o painel de
      comparar contra um número que já não existe. O recorte é declarado porque
      `1.000,00` e `05/09/2026` aparecem em outras seções da mesma página
- [ ] `comportamental` — RF-07
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` e
      `DASH_ENV_FILE=/dev/null` no ambiente do processo, sessão autenticada, e
      uma cópia de trabalho da base em que `SELECT COUNT(*) FROM offers` vale `0`
      *Quando* `POST /configuracao/proposta` é enviada com `nome=Banco Ruim`,
      `taxa=1`, `prazo=2`, `liberado=5.000.00` (ponto no lugar da vírgula
      decimal) e, **na mesma execução**, uma segunda com `nome=Banco Bom`,
      `taxa=1`, `prazo=2`, `liberado=5.000,00`
      *Então* a primeira responde `400`, **não** `500`, o HTML contém
      `id="recusa"`, a palavra `Valor liberado` e a cadeia `id="propostas"`; a
      segunda responde `200`; e ao fim `SELECT name FROM offers` traz `Banco Bom`
      e **não** traz `Banco Ruim`. A segunda requisição é o controle positivo:
      sem ela, "nada foi gravado" passaria numa rota que não grava nunca
- [ ] `comportamental` — RF-04
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` no ambiente do
      processo e sessão autenticada
      *Quando* `POST /configuracao/proposta` é enviada com `nome=Banco Sem Taxa`,
      `taxa=` (vazio), `prazo=24` e `liberado=1.000,00`, e `GET /configuracao` é
      buscada
      *Então* a resposta do POST é `200`;
      `SELECT monthly_rate_bp FROM offers WHERE name = 'Banco Sem Taxa'` devolve
      `NULL`; e no recorte do HTML que vai de `data-proposta="Banco Sem Taxa"`
      até o primeiro `</article>` depois dele aparece a palavra `Ausente`
- [ ] `comportamental` — RF-01
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` no ambiente do
      processo e sessão autenticada, com duas propostas já gravadas por
      `POST /configuracao/proposta` — `nome=Banco Teste`, `taxa=10`, `prazo=2`,
      `liberado=1.000,00`; e `nome=Banco Sem Taxa`, `taxa=` vazio, `prazo=24`,
      `liberado=1.000,00`
      *Quando* `POST /configuracao/proposta/remover` é enviada com
      `nome=Banco Sem Taxa`
      *Então* a resposta é `200`, o HTML **não** contém
      `data-proposta="Banco Sem Taxa"` e **contém** `data-proposta="Banco Teste"`
      — a segunda metade é o controle positivo, sem o qual a remoção passaria
      numa página que perdeu a seção inteira
- [ ] `estrutural` — RF-01
      Existe `app/templates/fragments/configuracao_propostas.html`;
      `app/templates/configuracao.html` contém exatamente **uma** linha
      `{% include "fragments/configuracao_propostas.html" %}`; e o fragmento
      **não** contém a cadeia `data-config` — o atributo dele é `data-proposta`
- [ ] `comando` — RF-01, RF-02, RF-04, RF-07
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_offers_cost.py tests/test_configuracao_propostas.py
      tests/test_migrations.py tests/test_configuracao_screen.py` sai com código
      `0`, e `tests/test_offers_cost.py` exercita a fórmula com taxa maior que
      zero, com taxa igual a zero e com custo de contratação igual a zero

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Criar `app/migrations/sql/018_offers.sql`: a tabela de propostas.**
      Método:
      ```sql
      CREATE TABLE offers (
          id INTEGER PRIMARY KEY,
          name TEXT NOT NULL UNIQUE,
          monthly_rate_bp INTEGER,
          term_months INTEGER NOT NULL,
          released_cents INTEGER NOT NULL,
          fee_cents INTEGER NOT NULL DEFAULT 0,
          captured_at TEXT NOT NULL
      );
      ```
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-01, RF-04. `monthly_rate_bp` é a **única** anulável
      porque RF-04 manda a proposta sem taxa existir e ficar de fora; sem prazo
      ou sem valor liberado não há caminho a custear, e deixá-los anuláveis
      empurraria a decisão para dentro da função de custo. `name UNIQUE` dá à
      linha a identidade que os quatro campos do brief não dão, e faz da
      regravação uma edição, como `app/financings/store.py:28-31` já resolve por
      `kind`. `captured_at` desarma o risco que o brief nomeia — proposta de
      banco vale por dias — sem pedir campo novo ao dono. Comentário no arquivo,
      se houver, começa por `Decisão:` ou `Invariante:`
      (`scripts/gates/gate3_no_comments.sh:29`).

- [ ] **1.2 — Criar `app/offers/__init__.py` e `app/offers/typed.py`: a gramática
      de digitação.**
      `read_form(typed: dict[str, str], *, today: date) -> dict` devolve a linha
      pronta. `nome` é obrigatório e limitado a 60 caracteres; `taxa` passa por
      `parse_rate(..., "Taxa mensal")` e **pode** voltar `None`; `prazo` por
      `parse_months(..., "Prazo em meses")` e `None` vira
      `InvalidValueError("Prazo em meses é obrigatório.")`; `liberado` por
      `parse_money(..., "Valor liberado")`; `contratacao` por
      `parse_money(..., "Custo de contratação", allow_zero=True)`.
      `captured_at` é `today.isoformat()`.
      *Considerando 1.1:* os nomes de campo são os da tabela.
      *Justificativa:* RF-01, RF-04, RF-07. É a forma de
      `app/financings/typed.py:15-45`, com a única inversão que o item exige: lá
      a taxa ausente é recusada, aqui ela é guardada. Os três leitores de
      `app/settings/typed.py` já recusam em pt-BR e já não estouram —
      `parse_rate` trata `nan` e a faixa, `parse_money` trata o ponto decimal e o
      teto de algarismos —, e reescrever a gramática aqui seria a segunda casa de
      uma regra que já tem dono. O teto de 60 caracteres existe porque o nome
      volta para a tela e para o contexto do modelo, e um nome de cinco mil
      caracteres é o que `app/advisor/gaps.py` já recusa no irmão.

- [ ] **1.3 — Criar `app/offers/store.py`: leitura, escrita, remoção e a seção da
      tela.**
      `read_all(conn) -> list[dict]` com `ORDER BY id`; `write(conn, typed, *,
      today)` fazendo `INSERT ... ON CONFLICT (name) DO UPDATE SET`;
      `remove(conn, name) -> None`; e
      `section(conn) -> {"action", "remove_action", "offers"}`.
      *Considerando 1.2:* `write` chama `read_form` antes de tocar o banco.
      *Justificativa:* RF-01. Espelha `app/financings/store.py:99-121` e
      `app/cards/store.py:21-22`: a tela recebe um dicionário pronto e o template
      não sabe SQL. `ON CONFLICT DO UPDATE`, e não `INSERT OR REPLACE`, pelo
      mesmo motivo escrito em `app/financings/store.py:25-27` — substituir apaga
      e reinsere, e a ordem de exibição passa a depender de ordem física de
      linha.

- [ ] **1.4 — Criar `app/offers/cost.py`: o custo total até zerar.**
      Método:
      ```python
      def total_cost(
          released_cents: int,
          monthly_rate_bp: int,
          term_months: int,
          fee_cents: int = 0,
      ) -> int
      ```
      Com `monthly_rate_bp == 0` devolve `fee_cents`. Caso contrário
      `rate = monthly_rate_bp / RATE_SCALE`,
      `payment = round(released_cents * rate / (1 - (1 + rate) ** -term_months))`
      e o resultado é `payment * term_months - released_cents + fee_cents`.
      `RATE_SCALE` vem de `app.financings.money`.
      *Considerando 1.1 e 1.2:* as unidades são as da tabela — centavos inteiros
      e centésimos de ponto percentual.
      *Justificativa:* RF-02, norma 23. A escala vem de
      `app/financings/money.py:1` e não de um literal local porque
      `app/debts/ladder.py:11` já a importa de lá, e uma segunda casa para a
      mesma constante é como duas telas passam a dividir por números diferentes.
      A fórmula fechada é escolha de **conferibilidade**: medida à mão, ela
      diverge do laço de amortização com resíduo em um centavo para
      `(100000, 2000, 2)`, e um critério que aceitasse os dois não seria oráculo
      de coisa nenhuma. O ramo de taxa zero é o mesmo de
      `app/financings/math.py:36-40`, pelo mesmo motivo: sem juros não há fator
      de anuidade, e não é borda, é o caso zero.

- [ ] **1.5 — Criar `app/routers/offers.py` com as duas rotas, registrá-lo em
      `app/main.py`, e acrescentar as propostas ao contexto de `app/routers/settings.py`
      no contexto.**
      Acrescentar `OFFER = f"{SCREEN}/proposta"` e
      `OFFER_REMOVE = f"{OFFER}/remover"`; dois handlers `POST` que leem os
      campos por `Form()`, passam cada valor por `text(...)`, chamam
      `app.offers.store.write(conn, typed, today=reference_date())` ou
      `remove(conn, nome)`, devolvem `answer(request, conn, notice=str(refusal),
      status_code=400)` em `InvalidValueError` e `answer(request, conn,
      done=SAVED)` no sucesso. `_context` ganha
      `"offers": offers_store.section(conn)`.
      *Considerando 1.3:* o router só traduz HTTP; quem grava é o store.
      *Justificativa:* RF-01, RF-07, normas 29 e 30. As rotas moram aqui, e não
      num `app/routers/offers.py`, porque router novo exige uma linha em
      `app/main.py` que o escopo declarado deste item não abre — divergência
      registrada no retorno. `text(...)` em cada campo porque
      `app/routers/settings.py:178-186` documenta que Starlette entrega o corpo
      urlencoded em latin-1, e sem ele "Nubank Ultravioleta" com acento entra
      torto no banco. Nenhuma das duas rotas monta consulta nem dá commit
      (norma 30), e as duas herdam a guarda de sessão de `install_guard`
      (`app/main.py:59`), varrida por `tests/test_route_guard.py`.

- [ ] **1.6 — Criar `app/templates/fragments/configuracao_propostas.html` e
      incluí-lo em `app/templates/configuracao.html`.**
      Uma `<section id="propostas" class="panel panel-wide">` com um
      `<article class="setting" data-proposta="{{ offer['name'] }}"
      data-prazo="{{ offer['term_months'] }}">` por proposta — os cinco campos
      pré-preenchidos por `|digitado`, a data de captação por `|dia`, o botão de
      salvar e o de remover — e um formulário vazio para informar a próxima. Uma
      linha de `include` em `configuracao.html`, ao lado da de financiamentos
      (linha 86).
      *Considerando 1.5:* os dados vêm de `offers`.
      *Justificativa:* RF-01, RF-04. O atributo é `data-proposta` porque
      `tests/test_configuracao_screen.py:64` casa **todo** `data-config` da
      página com o catálogo, por igualdade de conjunto: um `data-config` novo
      derruba a suíte inteira por um fragmento que não é item de catálogo. A
      forma é a de `app/templates/fragments/configuracao_cartoes.html`, que já
      resolveu o mesmo problema com `data-cartao`. `data-prazo` existe porque o
      prazo é o único dos cinco campos cujo valor é um inteiro pequeno, que
      aparece por acaso em qualquer lugar do HTML: sem atributo próprio não há
      como afirmar que a tela o mostrou. O campo da taxa em branco mostra
      `Ausente`, como o cartão sem taxa, porque é a linguagem que a tela já usa
      para "o painel não sabe e não vai inventar". Antes de escrever a seção,
      carregue a skill **`frontend-design`** (norma 27).

- [ ] **1.7 — Criar `tests/test_offers_cost.py` e
      `tests/test_configuracao_propostas.py`, e ampliar
      `tests/test_migrations.py`.**
      `test_offers_cost.py`: os três casos da fórmula, com pelo menos um deles
      afirmando o inteiro literal `20238` — comparar a saída de `total_cost` com
      uma expressão que a reproduz por dentro seria escrever a implementação duas
      vezes e chamar isso de teste.
      `test_configuracao_propostas.py`: a gravação e a leitura na tela, a recusa
      de `5.000.00` com o par de controle positivo, a taxa em branco gravada como
      `NULL` e a remoção com a proposta vizinha intacta.
      `test_migrations.py`: `018_offers.sql` entra em `EXPECTED_MIGRATIONS` e
      `offers` em `EXPECTED_TABLES`, na ordem alfabética que a consulta de
      `:53-55` devolve — entre `natures` e `payee_names`.
      Quem executa os três arquivos é o `pytest` que o CI já roda; **nenhum
      portão novo entra em `scripts/gates/`** e o `gates_runner.sh` não é tocado.
      *Considerando 1.1 a 1.6.*
      *Justificativa:* RF-01, RF-02, RF-04, RF-07. As duas listas de
      `tests/test_migrations.py:9-51` são igualdade exata, não pertinência: sem
      as duas entradas a suíte reprova por uma migração correta, e o implementer
      descobre isso depois de escrever a fase inteira. O par recusa/aceite da
      gravação existe porque "não gravou" é conclusão por ausência, e sozinha ela
      passa numa rota que perdeu a capacidade de gravar.

---

## Fase 2 — A comparação na tela, e a leitura que só copia (api)

**Objetivo da fase:** `/consultor` mostra quanto custa continuar como está e
quanto custa cada proposta, e a IA explica o resultado sem exibir número que ela
mesma tenha composto.

**Critérios de aceite:**

- [ ] `estrutural` — RF-03, RF-05
      `app/offers/cost.py` exporta `compare` e `comparison`;
      `app/advisor/cited.py` existe e exporta `figures` e `uncited`;
      `app/advisor/context.py` importa `comparison` de `app.offers.cost`; e
      `app/routers/advisor.py` importa `uncited` de `app.advisor.cited`
- [ ] `comportamental` — RF-02, RF-03
      *Dado* o interpretador do repositório com `DASH_ENV_FILE=/dev/null`
      *Quando* `app.offers.cost.compare` é chamada com o degrau
      `{"name": "Conta corrente", "monthly_rate_bp": 2000}` e com a lista de uma
      proposta `{"name": "Banco Teste", "monthly_rate_bp": 1000,
      "term_months": 2, "released_cents": 100000, "fee_cents": 5000}`
      *Então* o resultado traz uma linha para `Banco Teste` com `stay_cents`
      igual a `30910`, `offer_cents` igual a `20238` e `difference_cents` igual a
      `10672`, e a linha nomeia a proposta como o caminho mais barato.
      **Conferência por oráculo independente:** com `i = taxa / 10000`, a parcela
      é `round(100000 * i / (1 - (1 + i) ** -2))` — `65455` a 20,00% ao mês e
      `57619` a 10,00% ao mês —, o custo de cada caminho é `parcela * 2 - 100000`
      mais o custo de contratação daquele caminho, e a diferença é a subtração
      dos dois. Os dois caminhos usam **o mesmo valor liberado e o mesmo prazo**:
      é a única base em que um cheque especial, que não tem cronograma próprio,
      tem custo até zerar
- [ ] `comportamental` — RF-03, RF-04
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-09-05` e `DASH_ENV_FILE=/dev/null` no ambiente do
      processo, sessão autenticada, uma cópia de trabalho da base em que
      `INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source)
      VALUES ('overdraft', 'Conta corrente', -500000, 2000, 'accounts')` já foi
      executado, e duas propostas gravadas por `POST /configuracao/proposta` —
      `nome=Banco Teste`, `taxa=10`, `prazo=2`, `liberado=1.000,00`,
      `contratacao=50,00`; e `nome=Banco Sem Taxa`, `taxa=` vazio, `prazo=24`,
      `liberado=1.000,00`
      *Quando* `GET /consultor` é buscada
      *Então* a resposta é `200`; no recorte do HTML que vai de
      `id="comparativo"` até o primeiro `</section>` depois dele aparecem
      `R$ 309,10`, `R$ 202,38` e `R$ 106,72`, a palavra `diferença` e o nome
      `Conta corrente`; e o mesmo recorte contém `1 proposta ficou de fora` e o
      nome `Banco Sem Taxa`. A proposta com taxa é o controle positivo da que
      ficou de fora: sem ela, a frase de exclusão apareceria igual numa tela sem
      comparação nenhuma
- [ ] `comportamental` — RF-05
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` e
      `DASH_ENV_FILE=/dev/null` no ambiente do processo, sessão autenticada,
      chave de IA configurada, e `httpx.post` substituído por um dublê que
      **guarda o corpo enviado** e responde
      `{"candidates": [{"content": {"parts": [{"text": "O caminho da proposta
      custa R$ 202,38 e continuar como está custa R$ 309,10."}]}}]}`, sobre uma
      base com o degrau `Conta corrente` a `2000` centésimos de ponto ao mês e a
      proposta `Banco Teste` com taxa `10`, prazo `2`, valor liberado
      `1.000,00` e contratação `50,00`
      *Quando* `POST /consultor` é enviada com `pergunta=qual sai mais barato?`
      *Então* a resposta é `200` e contém `id="leitura"` com a frase do dublê; e,
      lendo do corpo guardado o texto de
      `body["contents"][0]["parts"][0]["text"]`, **toda ocorrência** do padrão
      `R\$ [\d.]+,\d{2}` presente na frase respondida ocorre literalmente nesse
      texto. É a verificação que o brief prescreve: não se lê a resposta, se
      confere que cada cifra dela está no contexto
- [ ] `comportamental` — RF-05
      *Dado* o mesmo painel, a mesma base e a mesma chave, com `httpx.post`
      substituído por um dublê que responde
      `{"candidates": [{"content": {"parts": [{"text": "Essa proposta te
      economiza R$ 987.654,32 no total."}]}}]}`
      *Quando* `POST /consultor` é enviada com `pergunta=qual sai mais barato?`
      *Então* a resposta é `200`, o HTML **não** contém `id="leitura"`, **não**
      contém a cadeia `987.654,32`, e **contém** `id="nao-conferido"` com uma
      frase em português dizendo que a leitura citou número fora do contexto e
      que os números da tela são os mesmos. É o controle positivo da conferência:
      sem ele, uma conferência quebrada aprovaria toda leitura para sempre, e o
      critério anterior passaria em verde exatamente igual
- [ ] `comportamental` — RF-03, RF-05
      *Dado* uma base com o degrau
      `{"kind": "overdraft", "name": "Conta corrente",
      "balance_cents": -500000, "monthly_rate_bp": 2000, "source": "accounts"}`
      na tabela `debts` e a proposta `Banco Teste` na tabela `offers`, com
      `monthly_rate_bp` `1000`, `term_months` `2`, `released_cents` `100000` e
      `fee_cents` `5000`
      *Quando* `app.advisor.context.lines(app.advisor.context.snapshot(conn,
      today=date(2026, 9, 5)))` e `app.advisor.context.as_text` do mesmo
      instantâneo são lidas
      *Então* **entre** as linhas devolvidas há três cujo rótulo começa por
      `Banco Teste`, com os valores `R$ 309,10`, `R$ 202,38` e `R$ 106,72`; e o
      texto traz as três, cada uma na forma `{rótulo}: {valor}.`. A asserção é de
      pertinência, não de igualdade de conjunto: a lista de linhas cresce em
      outros itens, e uma igualdade aqui reprovaria o item seguinte por estar
      certo
- [ ] `comportamental` — RF-06
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` e
      `DASH_ENV_FILE=/dev/null` no ambiente do processo, sessão autenticada,
      **sem** `GEMINI_API_KEY` no ambiente e sem chave gravada, sobre uma base em
      que `debts` traz o degrau `Conta corrente` com `monthly_rate_bp` `2000` e
      `offers` traz `Banco Teste` com taxa `10`, prazo `2`, valor liberado
      `1.000,00` e contratação `50,00`
      *Quando* `GET /consultor` é buscada
      *Então* a resposta é `200`, o recorte entre `id="comparativo"` e o
      `</section>` seguinte traz `R$ 309,10`, `R$ 202,38` e `R$ 106,72`, e a
      página diz que a leitura em prosa não roda sem a chave, apontando
      `/configuracao`. Nenhuma cifra da comparação depende da chave, por
      construção

**Critérios de integração:**

- [ ] `comportamental` — RF-08
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` e
      `DASH_ENV_FILE=/dev/null` no ambiente do processo, sessão autenticada, e
      uma cópia de trabalho da base carregada em que a tabela `offers` está vazia
      *Quando* `GET /dividas`, `GET /objetivo` e `GET /comprometido` são buscadas
      e os seus totais anotados; depois duas propostas são gravadas por
      `POST /configuracao/proposta` (`nome=Banco Teste`, `taxa=10`, `prazo=2`,
      `liberado=1.000,00`, `contratacao=50,00`; e `nome=Banco Sem Taxa`, `taxa=`
      vazio, `prazo=24`, `liberado=1.000,00`); e as três telas são buscadas de
      novo
      *Então* o total da escada em `/dividas`, o alvo de reserva em `/objetivo` e
      o comprometido por mês em `/comprometido` são **os mesmos** antes e depois,
      e o validador escreve os três valores observados no veredicto. A escada
      precisa trazer **pelo menos um degrau** e o comprometido precisa ser
      diferente de zero nas duas leituras: dois conjuntos vazios são iguais entre
      si e não provam nada
- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_offers_cost.py tests/test_offers_comparison.py
      tests/test_configuracao_propostas.py tests/test_consultor_screen.py
      tests/test_advisor.py tests/test_debts.py tests/test_plan.py
      tests/test_comprometido_screen.py tests/test_migrations.py` sai com código
      `0`, e `tests/test_consultor_screen.py` define um teste que substitui
      `httpx.post` por um dublê que responde citando `R$ 987.654,32` e afirma que
      a página não traz `id="leitura"` nem essa cadeia

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **2.1 — Ampliar `app/offers/cost.py`: a comparação.**
      Método:
      ```python
      def compare(step: dict | None, offers: list[dict]) -> dict
      def comparison(conn: sqlite3.Connection) -> dict
      ```
      `compare` devolve `{"step", "rows", "without_rate"}`. Cada linha de `rows`
      traz `name`, `monthly_rate_bp`, `term_months`, `released_cents`,
      `fee_cents`, `offer_cents`, `stay_cents`, `difference_cents` e `cheaper`.
      Proposta com `monthly_rate_bp` nulo não vira linha: o nome dela entra em
      `without_rate`. Com `step` nulo, `stay_cents` e `difference_cents` ficam
      nulos e `cheaper` também. `comparison` lê `app.debts.ladder.ladder(conn)` e
      `app.offers.store.read_all(conn)` e chama
      `compare(steps[0] if steps else None, offers)`.
      *Considerando 1.4:* os dois lados chamam a mesma `total_cost`, com o mesmo
      valor liberado e o mesmo prazo.
      *Justificativa:* RF-03, RF-04. `compare` é pura sobre dicionários — a forma
      que `tests/test_debts.py:21-32` já usa para exercitar degrau sem levantar a
      aplicação —, e `comparison` é a única que toca o banco: sem essa quebra o
      oráculo do custo teria de subir o painel para medir uma conta de duas
      linhas. `ladder(conn)[0]` é o degrau mais caro porque
      `app/debts/ladder.py:138-140` já ordena por taxa decrescente, e é o degrau
      caro que a pergunta do dono é sobre. Degrau sem taxa nem chega aqui: a
      consulta de `ladder` já filtra `monthly_rate_bp IS NOT NULL`.

- [ ] **2.2 — Modificar `app/advisor/context.py`: a comparação vira linha.**
      `snapshot` ganha `"comparison": comparison(conn)`. `lines` ganha, por linha
      de `rows`, três entradas: o custo de continuar no degrau atual, o custo da
      proposta e a diferença — cada rótulo começando pelo nome da proposta e
      trazendo a taxa em `%` e o prazo em meses, e cada valor em `brl`. Com
      `stay_cents` nulo, só a entrada da proposta é emitida.
      *Considerando 2.1.*
      *Justificativa:* RF-03, RF-05, norma 23. As linhas entram em `lines()`, e
      não numa lista paralela, porque `app/advisor/context.py:31-35` registra a
      razão: a tela renderiza e o modelo recebe **a mesma** lista, e é essa
      identidade que sustenta a frase "você acha na tela todo número que ele
      citar" — `tests/test_advisor.py:146-156` a cobra por construção. A taxa
      viaja **dentro do rótulo** porque a tela mostra `10,00%` na comparação: uma
      cifra visível fora do contexto é uma cifra que a conferência da etapa 2.3
      recusaria se o modelo a copiasse da tela.

- [ ] **2.3 — Criar `app/advisor/cited.py`: a conferência de cifra.**
      Método:
      ```python
      def figures(text: str) -> list[str]
      def uncited(reading: str, context: str) -> list[str]
      ```
      `figures` recolhe as ocorrências de `R$` seguido de valor e de número
      seguido de `%`. `uncited` devolve as cifras da leitura que **não** ocorrem
      literalmente no contexto.
      *Considerando 2.2:* o contexto conferido é o mesmo `as_text(...)` que foi
      enviado.
      *Justificativa:* RF-05, norma 23. `app/advisor/gemini.py:13-20` **pede** ao
      modelo que não invente, e pedido não é garantia: RF-05 diz "apenas", e a
      única forma de "apenas" ser propriedade e não esperança é o painel
      conferir. A gramática é deliberadamente estreita — só dinheiro e
      porcentagem —, e a limitação vai escrita no módulo, começando por
      `Limitação:`: um inteiro solto como `24` não é acusado, porque uma
      gramática larga acusaria `2026` e transformaria a guarda em ruído que
      alguém desliga na primeira semana. Comparação literal, sem normalizar:
      `R$ 3.400` onde o contexto traz `R$ 3.400,00` é citação truncada, e a
      instrução que o modelo recebe diz "copiado dígito a dígito".

- [ ] **2.4 — Modificar `app/routers/advisor.py`: a leitura passa pela
      conferência antes da tela.**
      No `POST /consultor`, depois de `ask(...)`, o texto do contexto já montado
      é comparado com a leitura por `uncited(...)`. Havendo cifra ausente, a rota
      responde com a chave nova `unchecked` no contexto e **sem** `reading`; caso
      contrário responde como hoje. `_answer` ganha o parâmetro
      `unchecked: str | None = None` e o repassa.
      *Considerando 2.3.*
      *Justificativa:* RF-05. A leitura inteira é descartada, e não apenas
      marcada, porque exibir a frase com a cifra inventada dentro é exatamente o
      dano que a norma 23 existe para impedir — um número errado na unidade
      central do produto. A mensagem **não repete** a cifra recusada, pelo mesmo
      motivo. A chave é nova, e não o `unavailable` que já existe, porque
      `unavailable` é a resposta do provedor que não respondeu, e as duas causas
      pedem frases diferentes ao dono.

- [ ] **2.5 — Modificar `app/templates/consultor.html`: a comparação e o aviso.**
      Uma `<section id="comparativo" class="panel panel-wide">` entre a conversa
      e a seção `numeros`, com uma linha por proposta — nome, taxa, prazo, custo
      de continuar como está, custo da proposta, diferença e qual é o mais
      barato —, a frase de quantas propostas ficaram de fora e por quê, e a frase
      de que não há dívida medida quando `step` é nulo. E um bloco
      `id="nao-conferido"` ao lado de `id="indisponivel"`.
      *Considerando 2.1 e 2.4.*
      *Justificativa:* RF-03, RF-04, RF-06. A seção fica **antes** de `numeros`
      porque `numeros` é a prova de que o modelo só copia, e a comparação é o
      assunto. A frase de exclusão é a mesma régua que
      `app/debts/ladder.py:144-147` já aplica a degrau sem taxa: mostrar apartado
      dizendo o que falta, nunca estimar. A tela diz que mostra custo e não
      recomendação de contratar — o brief nomeia esse risco, e a frase não pode
      depender da IA para ser dita. Antes de escrever a seção, carregue a skill
      **`frontend-design`** (norma 27).

- [ ] **2.6 — Criar `tests/test_offers_comparison.py` e ampliar
      `tests/test_consultor_screen.py`.**
      `test_offers_comparison.py`: `compare` sobre dicionários, com o degrau a
      20,00% e a proposta a 10,00% em dois meses, afirmando os três inteiros; a
      proposta sem taxa em `without_rate` e fora de `rows`; o degrau nulo
      deixando `stay_cents` nulo; e as três linhas dentro de `lines(...)` e de
      `as_text(...)`, por pertinência.
      `test_consultor_screen.py`: a seção da comparação com as duas propostas; o
      dublê de `httpx.post` que guarda o corpo enviado e responde citando só
      cifras do contexto, afirmando que toda cifra da resposta ocorre no corpo
      guardado; o dublê que responde citando `R$ 987.654,32`, afirmando que a
      página não traz `id="leitura"` nem a cadeia; e a tela sem chave com as três
      cifras de pé.
      Quem executa os dois arquivos é o `pytest` que o CI já roda; **nenhum
      portão novo entra em `scripts/gates/`** e o `gates_runner.sh` não é tocado.
      *Considerando 2.1 a 2.5.*
      *Justificativa:* RF-03, RF-04, RF-05, RF-06. O dublê é a única forma de
      observar o contexto **enviado**: `app/advisor/gemini.py:60-70` o entrega em
      `json=body`, e `tests/conftest.py:76-87` já derruba qualquer teste que
      tente sair para a rede — substituir `httpx.post` no teste é a via que
      `tests/test_advisor.py:119-133` já usa. O segundo dublê é o controle
      positivo da conferência: sem ele, `uncited` podendo devolver lista vazia
      sempre passaria em verde para sempre, e o teste da leitura bem-comportada
      não notaria.

---

## Execução sugerida

1. **Fase 1, bloqueante.** A fase 2 consome a tabela, a função de custo e a forma
   da linha de proposta nos três consumidores de uma vez — a tela de
   `/consultor`, o contexto do modelo e a conferência de citação.
2. **Fase 2 depois da 1.** Toca `app/offers/cost.py`, `app/advisor/context.py`,
   `app/advisor/cited.py`, `app/routers/advisor.py`,
   `app/templates/consultor.html`, `tests/test_offers_comparison.py` e
   `tests/test_consultor_screen.py`.

As duas **não** são paralelas, e a razão não é a interseção de arquivos: os
critérios da fase 2 medem números que só existem depois que a tabela e a função
de custo existem. Num par de worktrees a fase 2 reprovaria inteira por trabalho
que a outra frente ainda não entregou.

## Pendências que viram item de roadmap

- **A proposta envelhece e ninguém avisa.** `captured_at` é guardado e mostrado,
  mas nada acontece quando a data ficou velha: não há validade, nem marca de
  vencido como a de `app/settings/store.py`. O brief nomeia o risco e não pede o
  remédio, e escolher o prazo de validade de uma proposta de banco é decisão do
  dono, não do plano.
- **A comparação usa um degrau só, o mais caro.** Um empréstimo que quita **duas**
  dívidas ao mesmo tempo — o cheque especial e o cartão — custa outra coisa, e o
  painel não responde isso. O brief pede comparar os caminhos que existem; somar
  degraus é simulação de consolidação, e está no não-escopo por vizinhança.
- **`mypy --strict` não roda** sobre o pacote novo, como não roda sobre nenhum
  outro: é o item `018-tipagem-estrita-em-python`, já na fila.

## Validações de campo pendentes

- **Que o modelo real obedeça à instrução.** O dublê prova que o painel recusa
  leitura com cifra fora do contexto; ele não prova que o Gemini, com chave real
  e rede real, respeita "copiado dígito a dígito". A suíte não sai para a rede
  (`tests/conftest.py:76-87`) e nenhum agent tem chave: o que fica sem
  verificação é a taxa de acerto do provedor, e o que a substitui é a guarda —
  se o modelo desobedecer, o dono vê `id="nao-conferido"` em vez de um número
  inventado. Item de origem: `028-consultor-comparativo-de-divida`, RF-05.

Todo o resto se observa por requisição HTTP, leitura do HTML devolvido, consulta
SQL à base de trabalho e chamada direta de função pura; nada depende de aparelho
físico nem de permissão de plataforma.
