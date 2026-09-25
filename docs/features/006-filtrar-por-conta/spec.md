# SPEC 006 — filtrar por conta

Sexta fatia da SPA. Acrescenta à página "Gastos" (`/app/expenses`) um seletor "Conta" que restringe a lista a uma conta ou cartão, guardado na URL, aplicado em SQL junto com o período antes da ordenação e da paginação. Nenhum endpoint novo: a fatia estende `GET /api/transactions/expenses` com `account_id` e reaproveita `GET /api/accounts/balances` para popular o seletor.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/queries/expenses.py` · `_where(date_from, date_to) -> (sql, params)` monta `WHERE {SPENDING}` mais os predicados de data; `_page_sql(sort, order, where)`; `list_expenses(conn, *, page, page_size, sort, order, date_from, date_to) -> ExpensesPage(items, total, total_cents)`; `_SELECT` já faz `LEFT JOIN accounts AS a ON a.id = t.account_id`.
- `app/routers/transactions.py` · `Expense` e `ExpensesResponse` (Pydantic); parâmetros em `Annotated[..., Query(...)]`; 422 para intervalo invertido.
- `app/routers/accounts.py` + `app/queries/balances.py` · `GET /api/accounts/balances` devolve `{ accounts: [{ id, name, institution, type, subtype, balance_cents, updated_at }] }` ordenado por `type, name`.
- `src/features/expenses/types/expense.ts` · `Expense`, `ExpensesQuery { page, sort, order, from, to }`, `Period`.
- `src/features/expenses/api/get-expenses.ts` · `getExpenses(query)` só acrescenta ao `URLSearchParams` o que não é nulo; `queryKey: ['expenses', query]`; `keepPreviousData`.
- `src/features/expenses/components/expenses-list.tsx` · lê tudo de `useSearchParams`; `commitPeriod`/`writeSorting` partem de `new URLSearchParams(searchParams)` e apagam `page`; barra de controles (`mt-6 flex flex-wrap items-end gap-3`) com `PeriodControls` + `SortControls` fora dos ramos de estado; vazio "Nenhum gasto registrado ainda." / "Nenhum gasto nesse período."; efeito que recua `page` quando passa do fim.
- `src/features/expenses/components/sort-controls.tsx` · o `<select>` "Ordenar por" com as classes da receita "Barra de controles de lista" — a forma que o seletor de conta copia.
- `src/features/expenses/components/expense-item.tsx` · `accountLabel(expense)` junta `account_name` e `account_institution` com " · " (fallback "Conta desconhecida").
- `src/features/accounts/api/get-balances.ts` · `balancesQueryOptions` (`['accounts', 'balances']`). A feature `expenses` **não pode** importar daqui (`import/no-restricted-paths`).
- `src/testing/mocks/handlers.ts` · `fakeAccounts` (`acc-bank-1` "Conta corrente · Banco de teste" BANK; `acc-credit-1` "Cartão · Emissor de teste" CREDIT), handler de `/api/accounts/balances`, `fakeExpenses` (45 gastos, todos hoje em "Conta corrente"), handler de gastos que filtra por `from`/`to`, ordena e fatia.
- `tests/test_expenses_api.py` · fixture `client`, `_transaction(id, date, amount, **overrides)` com `conta_id="sync-acc-1"`, `_load(rows)` ingerindo com `tests/data/sync_accounts.json` (uma conta, `sync-acc-1`).
- `scripts/e2e-backend.sh` · ingere `tests/data/e2e_transactions.json` (4 lançamentos, todos em `acc-fixture-1`) com `tests/fixtures/accounts_fixture.json` (uma conta, "Conta de teste"; o arquivo é compartilhado por `test_ingest.py` e `test_accounts_api.py`). `app/ingest/loader.py` não inverte sinal de lançamento (o consolidador já o fez), então um lançamento de cartão entra no fixture com `valor` negativo direto.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `AccountSelect` (novo, na feature) renderiza na barra de controles um `<label>` "Conta" + `<select>` com a primeira opção "Todas as contas" (`value=""`) e uma `<option value={id}>` por conta devolvida por `GET /api/accounts/balances` (D4). |
| R2 | Texto da opção: `accountOptionLabel(account)` = "Nome · Instituição" (partes nulas omitidas; sem nenhuma, "Conta sem nome") + " (Cartão)" quando `type === 'CREDIT'`, senão " (Conta)". Um `<option>` nativo não renderiza selo colorido; o sufixo entre parênteses é o selo em texto (D5). |
| R3 | Sem `account` na URL, `ExpensesQuery.account` é `null`, o cliente não manda `account_id` e o servidor não filtra (`account_id=None`); o `<select>` mostra "Todas as contas". |
| R4 | `account=<id>` na URL vira `account_id=<id>` na chamada; o servidor soma `AND t.account_id = ?` ao `_where` (D1). |
| R5 | `account` entra em `ExpensesQuery` e, portanto, em toda chamada e na chave da query; "Anterior"/"Próxima" só trocam `page` (`new URLSearchParams(searchParams)`). |
| R6 | `account` mora na URL (`client-state`); recarregar ou compartilhar reproduz o filtro. Escrita usa `replace: true`, como os demais filtros. |
| R7 | `writeAccount(params, id)` chama `params.delete('page')` antes de gravar ou apagar `account` (mesma forma de `writeSorting`/`writePeriod`). |
| R8 | `writeAccount` só toca `account` e `page`; `writePeriod` e `writeSorting` não conhecem `account`. Todos partem de `new URLSearchParams(searchParams)`. |
| R9 | `total` e `total_cents` continuam vindo do mesmo `SELECT count(*), coalesce(sum(...))` com o mesmo `_where`, agora com o predicado de conta (D1). `Pagination` não muda. |
| R10 | Quando as contas já carregaram e o `account` da URL não está na lista, `expenses-list.tsx` usa `account: null` na query e um efeito apaga `account` da URL (`replace: true`) — a tela fica idêntica a "Todas as contas", sem 404 nem alerta (D6). Enquanto as contas carregam, o id da URL é enviado como está. No servidor, id desconhecido é só um filtro sem linhas: `items: []`, `total: 0`, `total_cents: 0`, status 200 (D2). |
| R11 | Com qualquer filtro ativo (`period.kind !== 'all'` ou `account !== null`) e `total === 0`, o vazio diz "Nenhum gasto para esse filtro."; sem filtro continua "Nenhum gasto registrado ainda.". O texto "Nenhum gasto nesse período." da 005 é substituído (uma mensagem para os dois filtros, e para os que vierem). |
| R12 | Os quatro estados de `ExpensesList` não mudam de forma; a chave `['expenses', { page, sort, order, from, to, account }]` faz "Tentar de novo" refazer com a conta atual e a troca de conta mostrar a lista anterior com paginação desabilitada (`keepPreviousData`). O seletor fica na barra, fora dos ramos, para o usuário sair de um filtro vazio ou com erro. |

## Decisões técnicas

### D1 — Predicado de conta somado ao `_where` existente; `account_id` no item da resposta

- Escolha: `_where(date_from, date_to, account_id: str | None) -> tuple[str, list[str]]` acrescenta `" AND t.account_id = ?"` e o parâmetro quando `account_id` não é `None`; a ordem dos `?` segue a ordem de concatenação (data, depois conta). `list_expenses(..., date_from=None, date_to=None, account_id: str | None = None)`. Contagem e soma continuam no mesmo `SELECT` do `_TOTAL` com o mesmo `where`, então `total` e `total_cents` só podem ver o mesmo filtro (invariante 25). `_SELECT` passa a projetar também `t.account_id`, e cada item devolve `"account_id": row["account_id"]`; `Expense` (Pydantic) e `Expense` (TS) ganham `account_id: str | None` / `string | null`. O campo é barato (já está na linha) e é o que permite ao mock e ao teste de componente filtrar `fakeExpenses` pela mesma chave que o servidor usa.
- Alternativa descartada: função `_where_account` separada concatenada pelo `list_expenses` — motivo: dois montadores de `WHERE` para uma consulta só; o `_where` já é o lugar do predicado e a 005 registrou que ele sobe para `spending.py` quando o terceiro consumidor aparecer.
- Alternativa descartada: não devolver `account_id` no item — motivo: o mock teria de inferir a conta pelo nome, e o teste de componente compararia por `account_name`, que não é chave.

### D2 — O router recebe `account_id` como `str` opcional; id desconhecido é 200 com lista vazia

- Escolha: `account_id: Annotated[str | None, Query(min_length=1)] = None`. Repassa direto a `list_expenses`. Não consulta `accounts` para validar: o predicado `t.account_id = ?` sem linhas já devolve `items: []`, `total: 0`, `total_cents: 0` com 200. `account_id=` (vazio) → 422 pelo `min_length`. O `/openapi.json` passa a listar `account_id` como `string` opcional (norma 3). Nome do parâmetro é `account_id` (a coluna), não `account`: na API a chave é explícita; na URL do app, `account` é o que o usuário lê.
- Alternativa descartada: 404 para id inexistente — motivo: R10 pede lista como "Todas as contas", sem erro; e um link antigo com conta apagada viraria tela de erro. Filtro é predicado, não recurso.
- Alternativa descartada: validar o id contra `accounts` e ignorá-lo quando desconhecido — motivo: o servidor passaria a mentir "sem filtro" para um pedido com filtro; quem decide cair para "Todas as contas" é o cliente, que tem a lista (D6).

### D3 — Contrato JSON

- `GET /api/transactions/expenses?page=1&page_size=20&sort=date&order=desc&from=…&to=…&account_id=<id>` · `account_id` opcional, string não vazia; combina com todos os demais por `AND`. Cada item ganha `account_id: string | null` (nulo só se a coluna for nula). Os demais campos não mudam. Não se ecoa `account_id`: o cliente já o tem na URL.

### D4 — A lista de contas vem de uma chamada própria da feature `expenses` ao endpoint de saldos

- Escolha: `src/features/expenses/api/get-accounts.ts` · `getAccounts(): Promise<ExpenseAccountsResponse>` chama `apiRequest('/api/accounts/balances')`; `accountsQueryOptions` com `queryKey: ['expenses', 'accounts']`; `useExpenseAccounts()`. `ExpenseAccount { id: string; name: string | null; institution: string | null; type: 'BANK' | 'CREDIT' | null }` em `types/expense.ts` — subconjunto estrutural da resposta; os campos de saldo são ignorados. A feature não importa nada de `features/accounts` (regra de lint) e não cria endpoint novo (o de saldos já devolve o que o seletor precisa, na ordem certa: contas, depois cartões, por nome).
- Alternativa descartada: a rota `src/app/routes/expenses.tsx` chamar `useBalances` de `features/accounts` e passar `accounts` como prop de `ExpensesList` — motivo: a rota passaria a cuidar de estados de carregamento e erro de um dado que só a lista consome, `ExpensesList` ganharia três props e o teste de componente teria de simular a rota; o "encontro na rota" da `project-structure` é para compor features, não para uma feature emprestar dados da outra.
- Alternativa descartada: mover `get-balances.ts` e o tipo para `src/lib`/`src/types` como compartilhado — motivo: o que as duas features compartilham é o endpoint, não o código; `expenses` precisa de 4 campos e nenhuma das funções de saldo. Se uma terceira feature precisar da lista, aí é hora de subir.
- Alternativa descartada: reusar a chave `['accounts', 'balances']` para aproveitar o cache do painel — motivo: acopla as duas features por uma string mágica; a chamada extra é uma leitura pequena e o cache padrão do React Query já evita repetição dentro da página.

### D5 — `AccountSelect` é componente da feature, na mesma barra, com os três estados da lista de contas dentro do próprio controle

- Escolha: `src/features/expenses/components/account-select.tsx` · `AccountSelect({ value, accounts, isPending, isError, onChange, onRetry })`, controlado pela URL. `<label htmlFor={useId()}>` "Conta" + `<select>` com as classes do `<select>` de `SortControls`. Opções: "Todas as contas" (`value=""`) e uma por conta com `accountOptionLabel(account)`. `value` do `<select>` é `value ?? ''`; se o `value` não está entre as opções (contas ainda carregando, ou id desconhecido antes do efeito de D6), o `<select>` cai naturalmente em "Todas as contas". Carregando: `<select disabled>` só com "Todas as contas" e `aria-busy="true"`. Erro: `<select>` habilitado só com "Todas as contas", seguido de `<p role="alert" className="mt-1 text-sm text-red-700">` "Não foi possível carregar as contas." e um botão secundário "Tentar de novo" (`onRetry`) — a lista de gastos continua funcionando com o filtro que estiver na URL. `onChange` recebe `string | null` (`''` vira `null`).
- Alternativa descartada: um `Alert` de página para o erro das contas — motivo: o conteúdo principal é a lista de gastos; dois alertas empilhados brigam pelo "Tentar de novo" e o erro do seletor não impede o uso da página.
- Alternativa descartada: selo colorido por conta (receita "Selo de status", como `balance-item.tsx`) — motivo: `<option>` nativo só aceita texto; um combobox customizado (lista aberta com selos) é componente compartilhado novo em `components/ui/` que a fatia não justifica. O sufixo " (Conta)"/" (Cartão)" cumpre R2 no texto.
- Alternativa descartada: `AccountSelect` chamar `useExpenseAccounts()` por conta própria — motivo: `expenses-list.tsx` precisa da lista para R10 (D6); uma chamada só, no pai, evita dois donos do mesmo estado.

### D6 — Conta mora na URL; id desconhecido é descartado pelo cliente quando a lista chega

- Escolha: `?account=<id>` na URL do app. Em `expenses-list.tsx`: `readAccount(value: string | null): string | null` (`''` e ausente → `null`; qualquer outro texto passa como está — o id é opaco). `writeAccount(params, id)` apaga `page` e grava `account` ou o apaga quando `id === null`. `const accounts = useExpenseAccounts()`; `const accountKnown = accounts.data ? accounts.data.accounts.some((a) => a.id === account) : true`; a query usa `account: accountKnown ? account : null`. Um `useEffect` que, com `account !== null && accounts.data && !accountKnown`, apaga `account` da URL com `replace: true` (mesmo padrão do efeito que recua `page`). `ExpensesQuery` ganha `account: string | null`; `getExpenses` só acrescenta `account_id` quando não nulo.
- Alternativa descartada: só enviar a query de gastos depois de as contas carregarem (`enabled`) — motivo: a lista, que é o conteúdo principal, esperaria uma chamada secundária; sem `account` na URL não há o que validar.
- Alternativa descartada: `useState` para a conta — motivo: R6 exige sobreviver a recarga e link; `client-state` manda filtro para a URL.

## Interface

Receitas do `docs/design.md` usadas: contêiner de página, título de página, texto de apoio, barra de controles de lista (o `<select>` com as classes do campo de formulário mais `min-h-10`), erro de campo (`mt-1 text-sm text-red-700`), botão secundário, lista, linha de lançamento, paginação, carregando, vazio, erro. Nenhuma receita nova.

### Tela: Gastos (`/app/expenses`)

- Título do documento, `<h1>` "Gastos" e texto de apoio "Todos os gastos das suas contas e cartões." não mudam.
- Barra de controles, sempre visível, nesta ordem, quebrando de linha em 360px:
  1. Campo "Conta": `<label>` + `<select>` com "Todas as contas" e, para cada conta, "Conta corrente · Banco de teste (Conta)" / "Cartão · Emissor de teste (Cartão)". Carregando contas: `<select>` desabilitado só com "Todas as contas". Erro nas contas: abaixo do `<select>`, "Não foi possível carregar as contas." em erro de campo com `role="alert"` e botão secundário "Tentar de novo".
  2. Grupo "Mês" e campos "De"/"Até" (inalterados, 005).
  3. "Ordenar por" + botão "Decrescente"/"Crescente" (inalterados, 004).
- Carregando (`role="status"`): "Carregando gastos…" — inalterado; troca de conta mostra a lista anterior com "Anterior"/"Próxima" desabilitados (`keepPreviousData`).
- Vazio sem filtro: "Nenhum gasto registrado ainda." — inalterado.
- Vazio com filtro (conta, período ou os dois): "Nenhum gasto para esse filtro." (mesma receita "Vazio"; substitui "Nenhum gasto nesse período.").
- Erro (`role="alert"`): "Não foi possível carregar os gastos." + "Tentar de novo" — inalterado.
- Com dados: lista da 003 na ordem da 004; resumo "Página 1 de 1 · 13 gastos · R$ … no período" reflete a conta escolhida; "Anterior"/"Próxima" mantêm `account`/`month`/`from`/`to`/`sort`/`order`.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/queries/expenses.py` | `_where(date_from, date_to, account_id)` com `AND t.account_id = ?`; `_SELECT` projeta `t.account_id`; item devolve `account_id`; `list_expenses(..., account_id=None)` (D1) | — |
| alterar | `app/routers/transactions.py` | `account_id: Annotated[str \| None, Query(min_length=1)] = None` repassado a `list_expenses`; `Expense.account_id: str \| None` (D2, D3) | `api-requests` |
| alterar | `tests/test_expenses_api.py` | `_load(rows, accounts=None)` aceita uma segunda conta (dict Pluggy inline `sync-acc-2`, `type: "CREDIT"`, `subtype: "CREDIT_CARD"`, `name: "Cartão de sincronização"`, `marketingName: "Emissor de teste"`) somada às de `sync_accounts.json`; testes: sem `account_id` vêm gastos das duas contas; `account_id=sync-acc-2` devolve só os dele com `total` e `total_cents` do filtro inteiro (`page_size=1`); `account_id` + `from`/`to` combinam por `AND`; `sort=amount` respeita a conta; transferência da conta filtrada fica fora de `total_cents`; `account_id=nao-existe` → 200, `items: []`, `total: 0`, `total_cents: 0`; `account_id=` → 422; cada item traz `account_id` igual ao `conta_id` ingerido; `test_the_response_has_the_contract_fields` ganha `"account_id"`; o `/openapi.json` lista `account_id` como `string` opcional | `api-requests`, `unit-testing` |

### Ferramental (raiz)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `tests/data/e2e_accounts.json` | cópia de `tests/fixtures/accounts_fixture.json` mais `acc-fixture-2` (`type: "CREDIT"`, `subtype: "CREDIT_CARD"`, `name: "Cartão de teste"`, `marketingName: "Emissor de teste"`, `balance: -45.0`, `currencyCode: "BRL"`, `updatedAt` igual ao da primeira); o fixture de `tests/fixtures/` não muda porque `test_ingest.py` e `test_accounts_api.py` dependem dele | `e2e-testing` |
| alterar | `tests/data/e2e_transactions.json` | quinto objeto `e2e-t-5`: `"data": "2026-08-15"`, `"conta_id": "acc-fixture-2"`, `"descricao": "FARMACIA CENTRAL"`, `"valor": -45.0`, `"tipo": "DEBIT"`, `"categoria_pluggy": "Health"`, `"categoria": "Health"`, demais campos como em `e2e-t-1` (em agosto, para não mexer nas contagens de setembro do e2e da 005) | `e2e-testing` |
| alterar | `scripts/e2e-backend.sh` | `accounts=load_accounts("tests/data/e2e_accounts.json")` | `e2e-testing` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/features/expenses/types/expense.ts` | `Expense.account_id: string \| null`; `ExpensesQuery.account: string \| null`; `ExpenseAccount` e `ExpenseAccountsResponse { accounts: ExpenseAccount[] }` (D1, D4, D6) | — |
| criar | `src/features/expenses/api/get-accounts.ts` | `getAccounts()`, `accountsQueryOptions` (`['expenses', 'accounts']`), `useExpenseAccounts()` (D4) | `api-requests` |
| alterar | `src/features/expenses/api/get-expenses.ts` | acrescenta `account_id` ao `URLSearchParams` só quando `query.account` não é nulo | `api-requests` |
| criar | `src/features/expenses/components/account-select.tsx` | `AccountSelect` e `accountOptionLabel` (D5): label "Conta", opções, estados carregando e erro com "Tentar de novo" | `interface-design`, `error-handling`, `component-robustness` |
| criar | `src/features/expenses/components/__tests__/account-select.test.tsx` | carregando: `<select>` desabilitado só com "Todas as contas"; com `fakeAccounts`: opções "Todas as contas", "Conta corrente · Banco de teste (Conta)", "Cartão · Emissor de teste (Cartão)"; conta com `name` e `institution` nulos → "Conta sem nome (Conta)"; `value` desconhecido cai em "Todas as contas"; escolher opção chama `onChange('acc-credit-1')`; escolher "Todas as contas" chama `onChange(null)`; erro: "Não foi possível carregar as contas." com `role="alert"` e "Tentar de novo" chama `onRetry` | `component-testing` |
| alterar | `src/features/expenses/components/expenses-list.tsx` | `readAccount`/`writeAccount`; `useExpenseAccounts()`; `accountKnown` e efeito que apaga `account` desconhecido da URL (D6); `AccountSelect` como primeiro controle da barra; `handleAccountChange`; vazio "Nenhum gasto para esse filtro." quando `period.kind !== 'all' \|\| account !== null` | `client-state`, `interface-design`, `component-robustness` |
| alterar | `src/testing/mocks/handlers.ts` | `fakeExpenses` ganha `account_id`: os cinco casos especiais (`id` 45–41) ficam em `acc-bank-1`; dos demais, `id % 3 === 0` (13 gastos: 39, 36, …, 3) vai para `acc-credit-1` com `account_name: 'Cartão'`, `account_institution: 'Emissor de teste'`, `account_type: 'CREDIT'`; os outros seguem em `acc-bank-1` (32 no total); handler lê `account_id` e filtra junto com `from`/`to` antes de ordenar e fatiar; handler de saldos inalterado | `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | `filterForSpy` ganha `accountId`; padrão: `<select>` "Conta" em "Todas as contas", API sem `account_id`, "45 gastos"; `?account=acc-credit-1` → API com `account_id=acc-credit-1`, `<select>` na opção do cartão, "13 gastos", só itens com "Cartão · Emissor de teste"; escolher "Cartão · Emissor de teste (Cartão)" a partir de `?page=2&sort=amount&month=2026-07` → URL sem `page`, com `account=acc-credit-1`, `sort=amount` e `month=2026-07`, API com `account_id` e `from`/`to`; escolher "Todas as contas" apaga `account`; "Próxima" com `?account=acc-bank-1` (32 gastos, 2 páginas) → `?account=acc-bank-1&page=2`; `?account=acc-credit-1&month=2026-09` → "Nenhum gasto para esse filtro." com os controles visíveis; `?account=nao-existe` → após as contas carregarem, URL sem `account`, API chamada sem `account_id` e "45 gastos"; handler de saldos com 500 → seletor só com "Todas as contas", "Não foi possível carregar as contas.", lista de gastos normal; os textos "Nenhum gasto nesse período." dos testes da 005 trocam para "Nenhum gasto para esse filtro." | `component-testing`, `api-mocking` |
| alterar | `e2e/expenses.spec.ts` | ajustes nos testes existentes: regex `[23] gastos` → `[34] gastos`; alternativas do resumo sem filtro → "3 gastos · R$ 279,90 no período" / "4 gastos · R$ 329,90 no período"; "Nenhum gasto nesse período." → "Nenhum gasto para esse filtro.". Teste novo: login → "Gastos" → `getByLabel('Conta')` em "Todas as contas" → `selectOption({ label: 'Cartão de teste · Emissor de teste (Cartão)' })` → URL contém `account=acc-fixture-2`, 1 item "FARMACIA CENTRAL" com "-R$ 45,00", resumo "1 gasto · R$ 45,00 no período" → `page.reload()` mantém o item e a opção → `page.goto('/app/expenses?account=acc-fixture-2&month=2026-09')` → "Nenhum gasto para esse filtro." → "Todo o período" → 1 item e URL ainda com `account=acc-fixture-2` → `selectOption({ label: 'Todas as contas' })` → URL sem `account`, ≥ 3 itens → `page.goto('/app/expenses?account=nao-existe')` → URL termina sem `account` e a lista aparece com ≥ 3 itens | `e2e-testing` |

## Estimativa de tamanho

Jornadas: 1 (restringir a lista de gastos a uma conta) · Telas novas: 0 · Linhas alteradas (sem testes): ~15 Python (`queries/expenses.py` ~8, `routers/transactions.py` ~5) + ~165 em `src/` (tipos ~12, `api/get-accounts.ts` ~20, `api/get-expenses.ts` ~3, `account-select.tsx` ~70, `expenses-list.tsx` ~35, mocks ~25) + ~10 de fixtures e script · Fases previstas: 2 (endpoint com `account_id` e `account_id` no item + testes de API; chamada de contas, `AccountSelect`, URL, mocks, testes de componente e e2e).

Nenhum sinal de "grande demais" dispara.

## Dívida encontrada

- nenhuma nova. A da 005 continua valendo (o predicado de `_where` duplicado com `app/queries/spending.py`, a subir para lá antes da fatia 008) e esta fatia só o estende.
