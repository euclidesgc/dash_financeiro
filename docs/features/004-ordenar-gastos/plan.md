# PLAN 004 — ordenar gastos

Branch: `feature/004-ordenar-gastos`

Decisões registradas aqui (a SPEC deixou ao plano; escolhido o mais simples):

- `_SORT_SQL` guarda um molde por critério com os marcadores `{order}` e `{rank}`; `_page_sql(sort, order)` preenche os dois só com valores de `_ORDER_SQL` e de `_category_rank_clause()`. Nenhum valor vindo do usuário entra em string de SQL.
- Os parâmetros do `CASE` de categoria só existem quando `sort == "category"`; nos outros critérios a lista de parâmetros do `ORDER BY` é vazia. A tupla do `execute` é `(*order_params, page_size, offset)`.
- O padrão do cliente por critério (`DEFAULT_ORDER_BY_SORT`) é gravado na URL apenas quando difere do padrão global (`date`/`desc`): escolher "Categoria" grava `?sort=category&order=asc`; escolher "Valor" grava `?sort=amount`; voltar para "Data" apaga `sort` e `order`.
- A base SQLite do e2e é compartilhada com `sync.spec.ts`, que ingere "COMPRA DE SINCRONIZACAO" (−R$ 50,00, `2026-08-01`, sem categoria) e pode rodar antes. Onde esse gasto mudaria o "primeiro item", o e2e afirma posição relativa (`first()`/`last()` que não dependem dele) em vez de posição absoluta. A contagem do e2e da 003 passa a casar `/Página 1 de 1 · [23] gastos/`.
- No mock, o item de índice 3 (`id` 42) ganha `category: 'Transporte'` e o de índice 4 (`id` 41) ganha `amount_cents: -120000`; os demais itens ficam como na 003. Assim "Valor" decrescente começa em "GASTO 41" (−R$ 1.200,00), "Categoria" crescente começa em "GASTO 44" ("Alimentação") e "Categoria" decrescente começa em "GASTO 42" ("Transporte").
- `SortControls` não importa `SORTS`: mantém uma lista local `{ value: ExpenseSort; label: string }[]` com as três opções e só chama `onSortChange` com um `value` dessa lista (sem `as ExpenseSort`).
- `playwright.config.ts` já tem `workers: 1` e `fullyParallel: false`; o e2e novo entra no `expenses.spec.ts` existente, sob o `mode: 'serial'` que já está lá.

## Fase 1 — Endpoint de gastos com `sort` e `order`

Só Python. Ao final: `GET /api/transactions/expenses` aceita `sort` (`date | amount | category`, padrão `date`) e `order` (`asc | desc`, padrão `desc`), ordena em SQL antes de `LIMIT/OFFSET`, com "Sem categoria" sempre por último e a ordem de categoria seguindo o rótulo pt-BR; valor fora da lista responde 422; a suíte Python prova tudo.

- [ ] T1.1 — Ordenação na consulta paginada, com lista branca e `CASE` por rótulo de categoria
  - Arquivos: `app/queries/expenses.py` (alterar)
  - O que fazer:
    - `import unicodedata`; `from typing import Any, Literal`.
    - `Sort = Literal["date", "amount", "category"]` e `Order = Literal["asc", "desc"]` exportados (sem `_`) para o router importar.
    - `_ORDER_SQL: dict[Order, str] = {"asc": "ASC", "desc": "DESC"}`.
    - `_SORT_SQL: dict[Sort, str] = {"date": "t.date {order}", "amount": "abs(t.amount_cents) {order}", "category": "CASE WHEN t.category IS NULL OR t.category = '' THEN 1 ELSE 0 END, {rank} {order}, t.category"}`. O prefixo de nulos não recebe `{order}`: "Sem categoria" fica por último nas duas direções.
    - `def _category_rank_clause() -> tuple[str, list[str | int]]`: `labels = category_labels()`; ordena as chaves por `unicodedata.normalize("NFKD", labels[key]).encode("ascii", "ignore").casefold()`; devolve `("CASE t.category " + "WHEN ? THEN ? " * len(keys) + "ELSE ? END", params)` com `params = [chave, posição, chave, posição, …, len(keys)]` (posição a partir de 0; chave fora do seed cai no `ELSE`, última entre as rotuladas, e desempata por `t.category`). Comentário de porquê: o rótulo não está no banco (dívida 023) e `BINARY` do SQLite poria "Água" depois de "Z".
    - `def _page_sql(sort: Sort, order: Order) -> tuple[str, list[str | int]]`: `rank_sql, params = _category_rank_clause() if sort == "category" else ("", [])`; `expression = _SORT_SQL[sort].format(order=_ORDER_SQL[order], rank=rank_sql)`; devolve a SQL `SELECT … FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id WHERE {SPENDING} ORDER BY {expression}, t.id DESC LIMIT ? OFFSET ?` (mesmas colunas da 003) e `params`. A constante `_PAGE` some; `_SELECT` (ou nome equivalente) guarda o `SELECT … WHERE {SPENDING}` e `_TOTAL` fica como está.
    - `def list_expenses(conn: sqlite3.Connection, *, page: int, page_size: int, sort: Sort = "date", order: Order = "desc") -> ExpensesPage`: `sql, order_params = _page_sql(sort, order)`; `rows = conn.execute(sql, (*order_params, page_size, offset)).fetchall()`; o resto (total, `labels`, `category_labels`, montagem dos dicts) não muda. Nenhum `commit`. A string `amount_cents < 0` continua ausente (só via `SPENDING`).
  - Skills: —
  - Complexidade: média

- [ ] T1.2 — Router aceita `sort` e `order` validados por `Literal`
  - Arquivos: `app/routers/transactions.py` (alterar)
  - O que fazer:
    - `from app.queries.expenses import Order, Sort, list_expenses`.
    - Assinatura de `expenses` passa a `def expenses(page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20, sort: Annotated[Sort, Query()] = "date", order: Annotated[Order, Query()] = "desc") -> ExpensesResponse`; chama `list_expenses(conn, page=page, page_size=page_size, sort=sort, order=order)`. Resposta inalterada (`items`, `page`, `page_size`, `total`; sem eco de `sort`/`order`). Rota continua `def`; `SELECT`, `INSERT` e `commit(` continuam ausentes do arquivo.
  - Skills: api-requests
  - Complexidade: baixa

- [ ] T1.3 — Testes da fase 1
  - Arquivos: `tests/test_expenses_api.py` (alterar)
  - O que fazer: reaproveitar `client`, `_sign_in`, `_transaction` e `_load`. Helper local `_descriptions(client, query: str) -> list[str]` que faz `GET /api/transactions/expenses?{query}` e devolve `[item["description"] for item in items]`. Casos (api-requests, unit-testing):
    - `test_the_default_order_is_date_desc_then_id_desc` — gastos em `2026-08-01`, `2026-08-03`, `2026-08-03`; sem `sort`/`order`, as datas vêm `["2026-08-03", "2026-08-03", "2026-08-01"]` e, entre os dois de `08-03`, o de `id` maior primeiro; `?sort=date&order=desc` devolve a mesma lista.
    - `test_sort_date_asc_puts_the_oldest_first` — mesmos três; `?sort=date&order=asc` → `["2026-08-01", "2026-08-03", "2026-08-03"]`, e entre os dois de `08-03` o de `id` maior continua primeiro.
    - `test_sort_amount_desc_puts_the_biggest_spending_first` — gastos `-50.0`, `-300.0`, `-120.0`; `?sort=amount&order=desc` → `amount_cents` `[-30000, -12000, -5000]`.
    - `test_sort_amount_asc_puts_the_smallest_spending_first` — mesmos; `?sort=amount&order=asc` → `[-5000, -12000, -30000]`.
    - `test_sort_category_asc_follows_the_label_with_uncategorised_last` — `categoria="Groceries"` (rótulo "Supermercado"), `categoria="Housing"` ("Casa"), `categoria=""`; `?sort=category&order=asc` → `category` `["Casa", "Supermercado", None]`.
    - `test_sort_category_desc_reverses_the_labels_and_keeps_uncategorised_last` — mesmos; `?sort=category&order=desc` → `["Supermercado", "Casa", None]`.
    - `test_accented_labels_sort_by_their_base_letter` — `categoria="Water"` ("Água") e `categoria="Housing"` ("Casa"); `asc` → `["Água", "Casa"]`; `desc` → `["Casa", "Água"]`.
    - `test_a_category_outside_the_seed_comes_after_the_labelled_ones` — `categoria="Groceries"`, `categoria="Zzz-desconhecida"`, `categoria=""`; `asc` → `["Supermercado", "Zzz-desconhecida", None]`.
    - `test_equal_amounts_break_ties_by_id_desc` — dois gastos `-50.0`; `?sort=amount&order=asc` e `order=desc` devolvem os dois com o `id` maior primeiro.
    - `test_sorting_applies_before_pagination` — 25 gastos com `amount = -(i * 10.0)` para `i` de 1 a 25; `?sort=amount&order=desc&page=2` → 5 itens com `amount_cents` `[-5000, -4000, -3000, -2000, -1000]` e `total == 25`.
    - `test_unknown_sort_and_order_answer_422` — `?sort=payee` → 422; `?order=up` → 422.
    - `test_the_openapi_lists_the_sort_and_order_enums` — com sessão, `GET /openapi.json`; entre os `parameters` de `paths["/api/transactions/expenses"]["get"]`, o de nome `sort` tem `schema.enum == ["date", "amount", "category"]` e `default == "date"`, e o de nome `order` tem `enum == ["asc", "desc"]` e `default == "desc"`.
  - Skills: api-requests, unit-testing
  - Complexidade: média

### Critérios de aceite da fase 1

- [ ] CA1.1 — `bash scripts/lint.sh` sai com código 0. (comando)
- [ ] CA1.2 — `uv run pytest tests/test_expenses_api.py tests/test_sync_api.py tests/test_accounts_api.py tests/test_auth_api.py` passa, e cada nome de teste listado em T1.3 existe em `tests/test_expenses_api.py`, junto com os doze da fatia 003 (`test_expenses_without_session_answers_401` … `test_the_response_has_the_contract_fields`). (comando)
- [ ] CA1.3 — `bash scripts/gates/gates_runner.sh` sai com código 0. (comando)
- [ ] CA1.4 — `app/queries/expenses.py` define `Sort = Literal["date", "amount", "category"]`, `Order = Literal["asc", "desc"]`, `_ORDER_SQL`, `_SORT_SQL` (com as chaves `"date"`, `"amount"`, `"category"` e a substring `CASE WHEN t.category IS NULL OR t.category = '' THEN 1 ELSE 0 END`), `def _category_rank_clause() -> tuple[str, list[str | int]]`, `def _page_sql(sort: Sort, order: Order) -> tuple[str, list[str | int]]` e `def list_expenses(conn: sqlite3.Connection, *, page: int, page_size: int, sort: Sort = "date", order: Order = "desc") -> ExpensesPage`; importa `unicodedata`; contém `, t.id DESC` e `LIMIT ? OFFSET ?`; não contém a string `ORDER BY t.date DESC`, nem `amount_cents < 0`, nem `commit(`; o único `.format(` do arquivo recebe apenas `_ORDER_SQL[order]` e o resultado de `_category_rank_clause()`. (estrutural)
- [ ] CA1.5 — `app/routers/transactions.py` importa `Order` e `Sort` de `app.queries.expenses`, e `def expenses(` declara `sort: Annotated[Sort, Query()] = "date"` e `order: Annotated[Order, Query()] = "desc"` e chama `list_expenses(conn, page=page, page_size=page_size, sort=sort, order=order)`; a rota é `def`, não `async def`; `SELECT`, `INSERT` e `commit(` não aparecem no arquivo; `ExpensesResponse` continua com exatamente `items`, `page`, `page_size`, `total`. (estrutural)
- [ ] CA1.6 — Sem `sort`/`order`, as datas vêm `["2026-08-03", "2026-08-03", "2026-08-01"]` (`test_the_default_order_is_date_desc_then_id_desc`); `?sort=amount&order=desc` devolve `[-30000, -12000, -5000]` (`test_sort_amount_desc_puts_the_biggest_spending_first`); `?sort=category&order=desc` devolve `["Supermercado", "Casa", None]` (`test_sort_category_desc_reverses_the_labels_and_keeps_uncategorised_last`); `?sort=amount&order=desc&page=2` de 25 gastos devolve `[-5000, -4000, -3000, -2000, -1000]` (`test_sorting_applies_before_pagination`); `?sort=payee` e `?order=up` respondem 422 (`test_unknown_sort_and_order_answer_422`). (comportamental)
- [ ] CA1.7 — `uv run pytest --cov=app.queries.expenses --cov=app.routers.transactions --cov-report=term tests/test_expenses_api.py` reporta ≥ 80% em `app/queries/expenses.py` e `app/routers/transactions.py`. (comando)

## Fase 2 — Controles de ordenação na tela, mocks, testes de componente e e2e

Ao final: a página "Gastos" tem, abaixo do texto de apoio e antes dos estados da lista, o `<select>` "Ordenar por" (Data / Valor / Categoria) e o botão de direção ("Decrescente"/"Crescente"); a escolha mora na URL (`?sort=…&order=…`, padrões apagados), sobrevive a recarga, zera a página e é preservada por "Anterior"/"Próxima"; o mock ordena; a jornada é provada com API mockada e, contra o FastAPI real, pelo Playwright.

- [ ] T2.1 — Tipos, chamada de API com `URLSearchParams` e mock que ordena
  - Arquivos: `src/features/expenses/types/expense.ts` (alterar); `src/features/expenses/api/get-expenses.ts` (alterar); `src/testing/mocks/handlers.ts` (alterar)
  - O que fazer:
    - `expense.ts`: acrescentar `export type ExpenseSort = 'date' | 'amount' | 'category'`, `export type ExpenseOrder = 'asc' | 'desc'` e `export interface ExpensesQuery { page: number; sort: ExpenseSort; order: ExpenseOrder }`.
    - `get-expenses.ts`: `export function getExpenses(query: ExpensesQuery): Promise<ExpensesResponse>` monta `const params = new URLSearchParams({ page: String(query.page), page_size: String(PAGE_SIZE), sort: query.sort, order: query.order })` e chama `apiRequest<ExpensesResponse>(`/api/transactions/expenses?${params.toString()}`)`; `export function expensesQueryOptions(query: ExpensesQuery)` com `queryKey: ['expenses', query]`, `queryFn: () => getExpenses(query)`, `placeholderData: keepPreviousData`; `export function useExpenses(query: ExpensesQuery)`. `PAGE_SIZE` fica.
    - `handlers.ts`: em `generateFakeExpenses`, o item de `index === 3` fica igual ao ramo padrão mas com `category: 'Transporte'`; o de `index === 4` igual ao padrão mas com `amount_cents: -120000`. O handler de `/api/transactions/expenses` lê `sort` (padrão `'date'`) e `order` (padrão `'desc'`) de `searchParams`, ordena uma cópia de `fakeExpenses` com `sortExpenses(items, sort, order)` (função local do mock): `date` compara `a.date` com `b.date` (string); `amount` compara `Math.abs(a.amount_cents)` com `Math.abs(b.amount_cents)`; `category` põe `category === null` sempre por último e compara os demais com `a.category.localeCompare(b.category, 'pt-BR')`; `order === 'desc'` inverte o sinal da comparação (exceto o de nulos); empate desempata por `b.id - a.id`. Só depois fatia por página, como hoje.
  - Skills: api-requests, api-mocking
  - Complexidade: baixa

- [ ] T2.2 — `SortControls` e a receita "Barra de controles de lista"
  - Arquivos: `src/features/expenses/components/sort-controls.tsx` (criar); `docs/design.md` (alterar)
  - O que fazer:
    - `sort-controls.tsx`: `export function SortControls({ sort, order, onSortChange, onOrderToggle }: { sort: ExpenseSort; order: ExpenseOrder; onSortChange: (sort: ExpenseSort) => void; onOrderToggle: () => void }): React.JSX.Element`. Componente controlado. Estrutura pela receita nova "Barra de controles de lista": um bloco com `<label htmlFor={id}>` de texto "Ordenar por" (`id` de `useId()`) e um `<select id={id} value={sort}>` nativo com três `<option>`: "Data" (`date`), "Valor" (`amount`), "Categoria" (`category`); as opções vêm de uma lista local `{ value: ExpenseSort; label: string }[]`, e o `onChange` procura o `value` do evento nessa lista e só chama `onSortChange` quando encontra. Ao lado, `<Button type="button" variant="secondary" aria-label="Inverter direção da ordenação" onClick={onOrderToggle}>` cujo texto é "Decrescente" quando `order === 'desc'` e "Crescente" quando `order === 'asc'`. Em 360px os dois controles quebram de linha, nada sai da tela. O `<select>` usa as classes do `<input>` da receita "Campo de formulário" mais `min-h-10`, sem `w-full`; o `<label>` usa as classes de `<label>` dessa receita. Aparência pelo `docs/design.md` e pelo piso de `interface-design`; sem JSX copiado deste plano.
    - `docs/design.md`, "Padrões acrescentados pelas entregas": linha `| Barra de controles de lista | <div className="mt-6 flex flex-wrap items-end gap-3">; cada controle em flex flex-col gap-1; <select> com as classes do <input> da receita "Campo de formulário" mais min-h-10 (sem w-full); botão secundário alinhado pela base | 004 |`.
  - Skills: interface-design, client-state, ui-components
  - Complexidade: baixa

- [ ] T2.3 — Ordenação na URL em `ExpensesList` e texto de apoio da rota
  - Arquivos: `src/features/expenses/components/expenses-list.tsx` (alterar); `src/app/routes/expenses.tsx` (alterar)
  - O que fazer:
    - `expenses-list.tsx`: constantes `const SORTS = ['date', 'amount', 'category'] as const`, `const ORDERS = ['asc', 'desc'] as const`, `const DEFAULT_SORT: ExpenseSort = 'date'`, `const DEFAULT_ORDER: ExpenseOrder = 'desc'`, `const DEFAULT_ORDER_BY_SORT: Record<ExpenseSort, ExpenseOrder> = { date: 'desc', amount: 'desc', category: 'asc' }`. `function readSort(value: string | null): ExpenseSort` devolve `value` se estiver em `SORTS`, senão `'date'`; `function readOrder(value: string | null): ExpenseOrder` idem com `ORDERS` e `'desc'` (mesma forma de `readPage`). `sort = readSort(searchParams.get('sort'))`, `order = readOrder(searchParams.get('order'))`, `useExpenses({ page, sort, order })`. Helper `function writeSorting(params: URLSearchParams, sort: ExpenseSort, order: ExpenseOrder): void` que apaga `page`, grava `sort` (ou apaga quando `sort === DEFAULT_SORT`) e grava `order` (ou apaga quando `order === DEFAULT_ORDER`). `handleSortChange(next)`: `params = new URLSearchParams(searchParams)`; `writeSorting(params, next, DEFAULT_ORDER_BY_SORT[next])`; `setSearchParams(params, { replace: true })`. `handleOrderToggle()`: mesmo caminho com `sort` atual e `order === 'asc' ? 'desc' : 'asc'`. A paginação preserva os demais parâmetros: `onChange` monta `new URLSearchParams(searchParams)`, faz `params.set('page', String(next))` e chama `setSearchParams(params)` sem `replace`; o `useEffect` de correção de página além da última também parte de `new URLSearchParams(searchParams)`, faz `set('page', String(pages))` e usa `{ replace: true }`. Estrutura de renderização: `<SortControls sort={sort} order={order} onSortChange={handleSortChange} onOrderToggle={handleOrderToggle} />` vem **antes** e **fora** dos ramos de estado (aparece em carregando, erro, vazio e com dados); os quatro estados e seus textos ("Carregando gastos…", "Nenhum gasto registrado ainda.", "Não foi possível carregar os gastos.", "Tentar de novo") não mudam, e a lista continua sendo mantida visível na troca de ordenação (`keepPreviousData`, botões de paginação desabilitados por `isPlaceholderData`). Ordenação e página nunca vêm de `useState`.
    - `expenses.tsx`: o texto de apoio passa a "Todos os gastos das suas contas e cartões."; nada mais muda.
  - Skills: client-state, interface-design, component-robustness
  - Complexidade: média

- [ ] T2.4 — Backend do e2e com dois gastos distinguíveis e jornada Playwright de ordenação
  - Arquivos: `tests/data/e2e_transactions.json` (alterar); `e2e/expenses.spec.ts` (alterar)
  - O que fazer:
    - `e2e_transactions.json`: acrescentar um quarto objeto com as mesmas chaves dos três existentes: `"id": "e2e-t-4"`, `"data": "2026-09-01"`, `"conta_id": "acc-fixture-1"`, `"descricao": "POSTO CENTRAL"`, `"valor": -150.0`, `"tipo": "DEBIT"`, `"categoria_pluggy": "Housing"`, `"categoria": "Housing"`, demais campos como em `e2e-t-1` (`null`, `false`, `""`).
    - `expenses.spec.ts`: no teste `opens the expenses page and lists only the spending`, a regex da contagem passa a `/Página 1 de 1 · [23] gastos/`. Teste novo `reorders the expenses by amount and by category and keeps the order on reload`: login com `e2e`/`senha-e2e-9k2` (mesmos passos dos testes existentes); clica `link` "Gastos"; `toHaveURL(/\/app\/expenses$/)`; `page.getByRole('listitem').first()` contém "MERCADO DO BAIRRO"; o `combobox` "Ordenar por" (`getByLabel('Ordenar por')`) tem valor `date` e o `button` "Decrescente" está visível. `selectOption('amount')` → `toHaveURL(/sort=amount/)`; `first()` contém "POSTO CENTRAL" e "-R$ 150,00". Clica `button` "Decrescente" → `toHaveURL(/order=asc/)`; `button` "Crescente" visível; `first()` não contém "POSTO CENTRAL" e `last()` contém "POSTO CENTRAL". `page.reload()` → `combobox` com valor `amount`, `button` "Crescente" visível, `last()` contém "POSTO CENTRAL" e `toHaveURL(/sort=amount/)`. `selectOption('category')` → `toHaveURL(/sort=category/)`; `first()` contém "POSTO CENTRAL" e "Casa". Selecionar `date` → URL sem `sort=` (`not.toHaveURL(/sort=/)`) e `first()` contém "MERCADO DO BAIRRO".
  - Skills: e2e-testing
  - Complexidade: baixa

- [ ] T2.5 — Testes da fase 2
  - Arquivos: `src/features/expenses/components/__tests__/expenses-list.test.tsx` (alterar)
  - O que fazer: reaproveitar `renderWithProviders`, `LocationProbe` (`data-testid="search"`) e o `server` MSW. Helper local `spyOnExpensesRequests()` que, via `server.use`, registra um handler de `GET /api/transactions/expenses` que guarda `new URL(request.url).searchParams` numa lista e devolve `passthrough()`-equivalente (ou repete a lógica do handler padrão), para afirmar os parâmetros enviados. Casos novos (component-testing, api-mocking):
    - `shows the default sorting controls` — `route: '/expenses'` → `combobox` "Ordenar por" com valor `date` (opção selecionada "Data"), `button` "Decrescente" com `aria-label` "Inverter direção da ordenação"; `search` é `''`; a primeira chamada à API leva `sort=date` e `order=desc`.
    - `sorting by amount puts the biggest spending first` — seleciona "Valor" → `search` vira `?sort=amount`, `button` continua "Decrescente", a API é chamada com `sort=amount&order=desc` e o primeiro `listitem` contém "-R$ 1.200,00".
    - `sorting by category starts ascending` — seleciona "Categoria" → `search` vira `?sort=category&order=asc`, `button` mostra "Crescente" e o selo do primeiro `listitem` é "Alimentação".
    - `toggling the direction inverts the order` — em `?sort=category&order=asc`, clica "Crescente" → `search` vira `?sort=category`, `button` mostra "Decrescente" e o selo do primeiro `listitem` é "Transporte".
    - `toggling the direction on the default sort writes only the order` — em `/expenses`, clica "Decrescente" → `search` vira `?order=asc`, `button` mostra "Crescente" e o primeiro `listitem` contém "GASTO 1".
    - `changing the sorting drops the page` — `route: '/expenses?page=2'`, seleciona "Valor" → `search` vira `?sort=amount` e "Página 1 de 3 · 45 gastos" aparece.
    - `pagination keeps the sorting` — `route: '/expenses?sort=amount'`, clica "Próxima" → `search` vira `?sort=amount&page=2` e a API é chamada com `sort=amount&order=desc&page=2` (ordem dos parâmetros irrelevante: afirmar cada `get`).
    - `falls back to the defaults on unknown sort and order` — `route: '/expenses?sort=foo&order=bar'` → `combobox` com valor `date`, `button` "Decrescente", API chamada com `sort=date&order=desc` e o primeiro `listitem` contém "MERCADO DO BAIRRO".
    - `keeps the controls visible in the error state` — `GET` 500 → `role="alert"` "Não foi possível carregar os gastos." e o `combobox` "Ordenar por" continua presente.
    - `keeps the controls visible in the empty state` — resposta `total: 0` → "Nenhum gasto registrado ainda." e o `combobox` "Ordenar por" presente.
    - Os casos da 003 continuam passando sem alteração de nome.
  - Skills: component-testing, api-mocking
  - Complexidade: média

### Critérios de aceite da fase 2

- [ ] CA2.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0; `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` também. (comando)
- [ ] CA2.2 — `pnpm test:e2e` sai com código 0 com o teste `reorders the expenses by amount and by category and keeps the order on reload` em `e2e/expenses.spec.ts`, além de `opens the expenses page and lists only the spending`, `goes back to the balances page` e os de `e2e/sync.spec.ts` e `e2e/login-and-balances.spec.ts`; `playwright.config.ts` contém `workers: 1`; `e2e/expenses.spec.ts` contém `test.describe.configure({ mode: 'serial' })`, `selectOption('amount')`, `selectOption('category')` e `page.reload()`. (comando, estrutural)
- [ ] CA2.3 — `src/features/expenses/types/expense.ts` exporta `ExpenseSort = 'date' | 'amount' | 'category'`, `ExpenseOrder = 'asc' | 'desc'` e `ExpensesQuery { page: number; sort: ExpenseSort; order: ExpenseOrder }`; `src/features/expenses/api/get-expenses.ts` exporta `getExpenses(query: ExpensesQuery): Promise<ExpensesResponse>`, contém `new URLSearchParams(` com as chaves `page`, `page_size`, `sort` e `order`, não contém `?page=${`, e exporta `expensesQueryOptions(query: ExpensesQuery)` com `queryKey: ['expenses', query]` e `placeholderData: keepPreviousData`, e `useExpenses(query: ExpensesQuery)`. (estrutural)
- [ ] CA2.4 — `src/features/expenses/components/sort-controls.tsx` exporta `SortControls({ sort, order, onSortChange, onOrderToggle }: { sort: ExpenseSort; order: ExpenseOrder; onSortChange: (sort: ExpenseSort) => void; onOrderToggle: () => void })`; contém `useId()`, um `<label` com `htmlFor` e o texto "Ordenar por", um `<select` com `value={sort}` e `id`, `<option`s com os textos "Data", "Valor" e "Categoria" e os valores `date`, `amount`, `category`, e um `<Button` com `variant="secondary"`, `type="button"` e `aria-label="Inverter direção da ordenação"` cujo texto é "Decrescente" ou "Crescente" conforme `order`; não contém `as ExpenseSort`. (estrutural)
- [ ] CA2.5 — `src/features/expenses/components/expenses-list.tsx` define `SORTS`, `ORDERS`, `DEFAULT_ORDER_BY_SORT` (com `category: 'asc'`), `readSort` e `readOrder`; chama `useExpenses({ page, sort, order })`; renderiza `<SortControls` antes do primeiro `if (isPending)`; contém `params.delete('page')`; as chamadas de troca de ordenação usam `{ replace: true }` e a chamada de `onChange` da `<Pagination` não usa `replace`; toda escrita na URL parte de `new URLSearchParams(searchParams)`; não contém `useState`; mantém os textos "Carregando gastos…", "Nenhum gasto registrado ainda.", "Não foi possível carregar os gastos." e "Tentar de novo". `src/app/routes/expenses.tsx` contém o texto "Todos os gastos das suas contas e cartões." e não contém "do mais recente ao mais antigo". (estrutural)
- [ ] CA2.6 — Piso visual, lido no código: o contêiner de `sort-controls.tsx` usa as classes de "Barra de controles de lista" do `docs/design.md` (`flex flex-wrap items-end gap-3`); o `<label>` usa as classes de `<label>` de "Campo de formulário"; o `<select>` usa as classes do `<input>` de "Campo de formulário" mais `min-h-10` e sem `w-full`; o botão é o `Button` de `@/components/ui/button`; `docs/design.md` tem, em "Padrões acrescentados pelas entregas", a linha "Barra de controles de lista" com fatia `004`; nenhum arquivo em `src/features/expenses/` contém `style={{`, `<a href` ou `!important`. (estrutural)
- [ ] CA2.7 — `src/testing/mocks/handlers.ts` lê `sort` e `order` de `searchParams` no handler de `/api/transactions/expenses`, ordena antes de `slice(`, contém `Math.abs(` e `localeCompare(` com `'pt-BR'`, e `fakeExpenses` tem 45 itens, um com `category: 'Transporte'` e um com `amount_cents: -120000`. (estrutural)
- [ ] CA2.8 — Selecionar "Valor" leva a URL a `?sort=amount` e o primeiro item a "-R$ 1.200,00" (`sorting by amount puts the biggest spending first`); selecionar "Categoria" leva a `?sort=category&order=asc` com botão "Crescente" e primeiro selo "Alimentação" (`sorting by category starts ascending`); em `?page=2`, trocar a ordenação apaga `page` (`changing the sorting drops the page`); "Próxima" em `?sort=amount` leva a `?sort=amount&page=2` (`pagination keeps the sorting`); `?sort=foo&order=bar` cai em `date`/`desc` (`falls back to the defaults on unknown sort and order`); com erro 500 o `combobox` "Ordenar por" continua na tela (`keeps the controls visible in the error state`). (comportamental)
- [ ] CA2.9 — Os testes nomeados em T2.5 existem em `src/features/expenses/components/__tests__/expenses-list.test.tsx`; `npx vitest run --coverage` reporta ≥ 80% de linhas em `src/features/expenses/api/get-expenses.ts`, `src/features/expenses/components/sort-controls.tsx` e `src/features/expenses/components/expenses-list.tsx`. (comando)
- [ ] CA2.10 — `tests/data/e2e_transactions.json` tem quatro objetos; o quarto tem `"id": "e2e-t-4"`, `"descricao": "POSTO CENTRAL"`, `"valor": -150.0`, `"data": "2026-09-01"`, `"categoria": "Housing"` e `"conta_id": "acc-fixture-1"`. (estrutural)

## DoD da entrega

- [ ] DoD1 — Todas as tarefas e critérios do plano marcados
- [ ] DoD2 — Suíte de testes inteira passa
- [ ] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [ ] DoD4 — Tipos de todos os `tsconfig` sem erros
- [ ] DoD5 — Console dos testes sem erro nem aviso
- [ ] DoD6 — `build` passa
- [ ] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [ ] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [ ] DoD9 — Nenhuma worktree ou branch temporária sobrando
