# PLAN 005 — filtrar por período

Branch: `feature/005-filtrar-por-periodo`

Decisões registradas aqui (a SPEC deixou ao plano; escolhido o mais simples):

- `onRangeChange` de `PeriodControls` recebe **qual campo mudou** e o valor novo: `onRangeChange(field: 'from' | 'to', value: string)`. O pai (`expenses-list.tsx`) parte dos limites atuais (`toDateBounds(period)`), substitui o campo alterado e aplica "campo recém-alterado vence": se `from` e `to` ficarem invertidos, apaga o **outro**. Valor `''` (campo limpo) vira `null`; com os dois nulos o período volta a `{ kind: 'all' }`.
- `readPeriod` também nunca devolve intervalo invertido lido da URL: com `from` e `to` válidos e `to < from`, ignora `to`. Assim a API não recebe 422 por link montado à mão.
- O resumo usa `formatMoney(Math.abs(totalCents))`, não `formatMoney(-totalCents)`: `-0` em `Intl.NumberFormat` sai "-R$ 0,00". `total_cents` é sempre ≤ 0 (predicado `SPENDING`), logo o valor absoluto é o total que saiu.
- O texto do mês é um `<span aria-live="polite">` sem `role`: `role="status"` já é do "Carregando gastos…". Nos testes, o texto do grupo se localiza com `getByText('Todo o período', { selector: 'span' })` e o botão com `getByRole('button', { name: 'Todo o período' })`.
- No e2e a base SQLite é compartilhada com `sync.spec.ts`, que pode ingerir "COMPRA DE SINCRONIZACAO" (−R$ 50,00, `2026-08-01`) antes. Por isso o mês vazio da jornada é `2026-10` (posterior a todo dado) e o caminho para setembro é "Mês anterior", não "Próximo mês" a partir de agosto; o resumo sem filtro casa `/Página 1 de 1 · (2 gastos · R\$ 234,90|3 gastos · R\$ 284,90) no período/`.
- No OpenAPI, `date | None` sai como `anyOf: [{type: "string", format: "date"}, {type: "null"}]`; o teste procura `format == "date"` dentro do `anyOf`.
- `playwright.config.ts` já tem `workers: 1` e `fullyParallel: false`; o e2e novo entra no `expenses.spec.ts` existente, sob o `mode: 'serial'` que já está lá.

## Fase 1 — Endpoint de gastos com `from`/`to` e `total_cents`

Só Python. Ao final: `GET /api/transactions/expenses` aceita `from` e `to` (ISO `YYYY-MM-DD`, opcionais, inclusivos), filtra em SQL antes do `ORDER BY` e do `LIMIT/OFFSET`, responde `total_cents` (soma do filtro inteiro no mesmo `SELECT` da contagem), devolve 422 para data inválida ou `to < from`, e a suíte Python prova tudo.

- [x] T1.1 — Predicado de data e soma do filtro na consulta paginada
  - Arquivos: `app/queries/expenses.py` (alterar)
  - O que fazer:
    - `_SELECT` perde o `WHERE {SPENDING}` (fica só `SELECT … FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id`). `_TOTAL` vira `f"SELECT count(*), coalesce(sum(t.amount_cents), 0) FROM transactions AS t"` (sem `WHERE`).
    - `def _where(date_from: str | None, date_to: str | None) -> tuple[str, list[str]]`: começa em `f"WHERE {SPENDING}"` e `params: list[str] = []`; se `date_from is not None`, concatena `" AND t.date >= ?"` e acrescenta `date_from`; se `date_to is not None`, `" AND t.date <= ?"` e `date_to`. Devolve `(sql, params)`.
    - `def _page_sql(sort: Sort, order: Order, where: str) -> tuple[str, list[str | int]]`: mesma montagem de hoje, mas `sql = f"{_SELECT} {where} ORDER BY {expression}, t.id DESC LIMIT ? OFFSET ?"`.
    - `ExpensesPage` ganha `total_cents: int` (depois de `total`).
    - `def list_expenses(conn: sqlite3.Connection, *, page: int, page_size: int, sort: Sort = "date", order: Order = "desc", date_from: str | None = None, date_to: str | None = None) -> ExpensesPage`: `where, where_params = _where(date_from, date_to)`; `sql, order_params = _page_sql(sort, order, where)`; `rows = conn.execute(sql, (*where_params, *order_params, page_size, offset)).fetchall()`; `total, total_cents = conn.execute(f"{_TOTAL} {where}", where_params).fetchone()`; devolve `ExpensesPage(items=items, total=total, total_cents=int(total_cents))`. Montagem dos dicts, `labels` e `category_labels` não mudam. Nenhum `commit`; `amount_cents < 0` continua só via `SPENDING`.
  - Skills: —
  - Complexidade: média

- [x] T1.2 — Router aceita `from`/`to` como `date`, rejeita intervalo invertido e responde `total_cents`
  - Arquivos: `app/routers/transactions.py` (alterar)
  - O que fazer:
    - `from datetime import date`; `from fastapi import APIRouter, HTTPException, Query`.
    - `ExpensesResponse` ganha `total_cents: int` (depois de `total`).
    - Assinatura: `def expenses(page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20, sort: Annotated[Sort, Query()] = "date", order: Annotated[Order, Query()] = "desc", from_: Annotated[date | None, Query(alias="from")] = None, to: Annotated[date | None, Query()] = None) -> ExpensesResponse`.
    - Antes de abrir a conexão: `if from_ is not None and to is not None and to < from_: raise HTTPException(status_code=422, detail="A data final precisa ser igual ou posterior à inicial.")`.
    - Chama `list_expenses(conn, page=page, page_size=page_size, sort=sort, order=order, date_from=from_.isoformat() if from_ else None, date_to=to.isoformat() if to else None)` e devolve `total_cents=found.total_cents`. Não ecoa `from`/`to`. Rota continua `def`; `SELECT`, `INSERT` e `commit(` continuam ausentes.
  - Skills: api-requests
  - Complexidade: baixa

- [x] T1.3 — Testes da fase 1
  - Arquivos: `tests/test_expenses_api.py` (alterar)
  - O que fazer: reaproveitar `client`, `_sign_in`, `_transaction`, `_load` e `_descriptions`. Atualizar `test_an_empty_base_answers_an_empty_first_page` (json passa a incluir `"total_cents": 0`) e `test_the_response_has_the_contract_fields` (chave `total_cents` presente e `int`). Casos novos (api-requests, unit-testing):
    - `test_total_cents_sums_every_spending_without_a_filter` — gastos `-50.0`, `-84.9`, `-150.0`; sem `from`/`to`, `total == 3` e `total_cents == -28490`.
    - `test_from_and_to_keep_only_the_month` — gastos em `2026-08-31`, `2026-09-01`, `2026-09-15`, `2026-09-30`, `2026-10-01`, todos `-10.0`; `?from=2026-09-01&to=2026-09-30` devolve exatamente as datas `["2026-09-30", "2026-09-15", "2026-09-01"]`, `total == 3` e `total_cents == -3000` (limites inclusivos: `09-30` entra, `10-01` e `08-31` não).
    - `test_total_and_total_cents_cover_the_whole_filter_not_the_page` — mesmos cinco gastos; `?from=2026-09-01&to=2026-09-30&page_size=1` devolve 1 item, `total == 3` e `total_cents == -3000`.
    - `test_only_from_is_an_open_ended_interval` — mesmos cinco; `?from=2026-09-15` devolve as datas `["2026-10-01", "2026-09-30", "2026-09-15"]`.
    - `test_only_to_is_an_open_ended_interval` — mesmos cinco; `?to=2026-09-01` devolve `["2026-09-01", "2026-08-31"]`.
    - `test_a_transfer_inside_the_period_stays_out_of_total_cents` — gasto `-50.0` em `2026-09-02` e `_transaction("transfer-1", "2026-09-02", -500.0, eh_transferencia=True)`; `?from=2026-09-01&to=2026-09-30` devolve `total == 1` e `total_cents == -5000`.
    - `test_sorting_respects_the_period` — gastos `-300.0` em `2026-08-01`, `-50.0` em `2026-09-01`, `-120.0` em `2026-09-02`; `?from=2026-09-01&to=2026-09-30&sort=amount&order=desc` devolve `amount_cents` `[-12000, -5000]`.
    - `test_invalid_dates_answer_422` — `?from=2026-13-01`, `?from=01/09/2026`, `?from=2026-02-31` e `?to=hoje` respondem 422 cada.
    - `test_an_inverted_interval_answers_422` — `?from=2026-09-10&to=2026-09-01` responde 422 e `response.json()["detail"] == "A data final precisa ser igual ou posterior à inicial."`.
    - `test_the_openapi_lists_from_and_to_as_dates` — com sessão, `GET /openapi.json`; entre os `parameters` de `paths["/api/transactions/expenses"]["get"]` existem `from` e `to`, e em cada um há um item de `schema["anyOf"]` com `type == "string"` e `format == "date"`.
  - Skills: api-requests, unit-testing
  - Complexidade: média

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh` sai com código 0. (comando)
- [x] CA1.2 — `uv run pytest tests/test_expenses_api.py tests/test_sync_api.py tests/test_accounts_api.py tests/test_auth_api.py` passa, e cada nome de teste listado em T1.3 existe em `tests/test_expenses_api.py`, junto com os 24 já existentes (`test_expenses_without_session_answers_401` … `test_the_openapi_lists_the_sort_and_order_enums`), sem renomear. (comando)
- [x] CA1.3 — `bash scripts/gates/gates_runner.sh` sai com código 0. (comando)
- [x] CA1.4 — `app/queries/expenses.py` define `def _where(date_from: str | None, date_to: str | None) -> tuple[str, list[str]]`, `def _page_sql(sort: Sort, order: Order, where: str) -> tuple[str, list[str | int]]` e `def list_expenses(conn: sqlite3.Connection, *, page: int, page_size: int, sort: Sort = "date", order: Order = "desc", date_from: str | None = None, date_to: str | None = None) -> ExpensesPage`; `ExpensesPage` tem os campos `items`, `total` e `total_cents: int`; o arquivo contém as substrings `" AND t.date >= ?"`, `" AND t.date <= ?"`, `count(*), coalesce(sum(t.amount_cents), 0)` e `(*where_params, *order_params, page_size, offset)`; `_SELECT` e `_TOTAL` não contêm `WHERE`; não contém `amount_cents < 0` nem `commit(`. (estrutural)
- [x] CA1.5 — `app/routers/transactions.py` importa `date` de `datetime` e `HTTPException` de `fastapi`; `def expenses(` declara `from_: Annotated[date | None, Query(alias="from")] = None` e `to: Annotated[date | None, Query()] = None`; contém `HTTPException(status_code=422, detail="A data final precisa ser igual ou posterior à inicial.")` e a chamada `list_expenses(` com `date_from=` e `date_to=`; `ExpensesResponse` tem exatamente `items`, `page`, `page_size`, `total`, `total_cents`; a rota é `def`, não `async def`; `SELECT`, `INSERT` e `commit(` não aparecem. (estrutural)
- [x] CA1.6 — Sem filtro, `total_cents == -28490` para três gastos de `-50.0`, `-84.9` e `-150.0` (`test_total_cents_sums_every_spending_without_a_filter`); `?from=2026-09-01&to=2026-09-30` devolve só `["2026-09-30", "2026-09-15", "2026-09-01"]` (`test_from_and_to_keep_only_the_month`); com `page_size=1` o `total_cents` continua `-3000` (`test_total_and_total_cents_cover_the_whole_filter_not_the_page`); transferência no período não entra na soma (`test_a_transfer_inside_the_period_stays_out_of_total_cents`); `?from=2026-02-31` e `?from=01/09/2026` respondem 422 (`test_invalid_dates_answer_422`); `?from=2026-09-10&to=2026-09-01` responde 422 com o `detail` literal (`test_an_inverted_interval_answers_422`). (comportamental)
- [x] CA1.7 — `uv run pytest --cov=app.queries.expenses --cov=app.routers.transactions --cov-report=term tests/test_expenses_api.py` reporta ≥ 80% em `app/queries/expenses.py` e `app/routers/transactions.py`. (comando)

## Fase 2 — Controles de período na tela, total do período, mocks, testes de componente e e2e

Ao final: a página "Gastos" tem, na mesma barra de controles da ordenação, o grupo "Mês" ("Mês anterior" · texto do mês · "Próximo mês" · "Todo o período") e os campos "De"/"Até"; o período mora na URL (`?month=YYYY-MM` ou `?from=…&to=…`), sobrevive a recarga, zera a página, preserva a ordenação e é preservado por "Anterior"/"Próxima"; o resumo mostra o total do período; o vazio filtrado diz "Nenhum gasto nesse período."; o mock filtra; a jornada é provada com API mockada e, contra o FastAPI real, pelo Playwright.

- [x] T2.1 — Tipos, utilitário puro de período, chamada de API com `from`/`to` e mock que filtra
  - Arquivos: `src/features/expenses/types/expense.ts` (alterar); `src/features/expenses/utils/period.ts` (criar); `src/features/expenses/api/get-expenses.ts` (alterar); `src/testing/mocks/handlers.ts` (alterar)
  - O que fazer:
    - `expense.ts`: `ExpensesResponse` ganha `total_cents: number`; `ExpensesQuery` ganha `from: string | null` e `to: string | null`; `export type Period = { kind: 'all' } | { kind: 'month'; month: string } | { kind: 'range'; from: string | null; to: string | null }`.
    - `period.ts` (só funções puras, sem React; o único acesso ao relógio é `currentMonth`):
      - `export function readMonth(value: string | null): string | null` — devolve `value` se casa `^\d{4}-(0[1-9]|1[0-2])$`, senão `null`.
      - `export function daysInMonth(year: number, month: number): number` — `new Date(Date.UTC(year, month, 0)).getUTCDate()` (`month` de 1 a 12).
      - `export function readIsoDate(value: string | null): string | null` — casa `^\d{4}-\d{2}-\d{2}$`, mês entre 1 e 12 e dia entre 1 e `daysInMonth`; senão `null`.
      - `export function monthRange(month: string): { from: string; to: string }` — `{ from: 'YYYY-MM-01', to: 'YYYY-MM-<daysInMonth>' }` com o dia em dois dígitos.
      - `export function shiftMonth(month: string, delta: number): string` — aritmética inteira de ano/mês; `'2026-01', -1` → `'2025-12'`; `'2026-12', 1` → `'2027-01'`; mês com dois dígitos.
      - `export function currentMonth(): string` — `new Date()` local, `getFullYear()`/`getMonth() + 1`.
      - `export function formatMonth(month: string): string` — `"<nome> de <ano>"` a partir de um array local com os doze nomes em pt-BR minúsculos (`janeiro` … `dezembro`); `'2026-09'` → `'setembro de 2026'`.
      - `export function readPeriod(searchParams: URLSearchParams): Period` — `month = readMonth(get('month'))`; se houver, `{ kind: 'month', month }`; senão `from = readIsoDate(get('from'))`, `to = readIsoDate(get('to'))`; se `from` e `to` e `to < from`, `to = null`; se algum dos dois, `{ kind: 'range', from, to }`; senão `{ kind: 'all' }`.
      - `export function toDateBounds(period: Period): { from: string | null; to: string | null }` — `all` → nulos; `month` → `monthRange`; `range` → os próprios.
      - `export function writePeriod(params: URLSearchParams, period: Period): void` — `params.delete('page')`, `delete('month')`, `delete('from')`, `delete('to')`; depois `set('month', …)` para `month`, e `set('from'/'to', …)` só para os não nulos em `range`; nada para `all`. Não toca `sort`/`order`.
    - `get-expenses.ts`: `getExpenses` continua montando `new URLSearchParams({ page, page_size, sort, order })` e, em seguida, `if (query.from !== null) params.set('from', query.from)` e `if (query.to !== null) params.set('to', query.to)`. `expensesQueryOptions`/`useExpenses` inalterados (a chave `['expenses', query]` passa a incluir `from`/`to` por construção).
    - `handlers.ts`: o handler de `/api/transactions/expenses` lê `from` e `to` de `searchParams`; `const filtered = fakeExpenses.filter((item) => (from === null || item.date >= from) && (to === null || item.date <= to))` antes de `sortExpenses(filtered, sort, order)`; responde `total: filtered.length` e `total_cents: filtered.reduce((sum, item) => sum + item.amount_cents, 0)`. `fakeExpenses` não muda (45 itens: 1 em `2026-08`, 31 em `2026-07`, 13 em `2026-06`).
  - Skills: client-state, api-requests, api-mocking
  - Complexidade: média

- [x] T2.2 — `PeriodControls`, `SortControls` sem a barra e a receita "Grupo de período"
  - Arquivos: `src/features/expenses/components/period-controls.tsx` (criar); `src/features/expenses/components/sort-controls.tsx` (alterar); `docs/design.md` (alterar)
  - O que fazer:
    - `period-controls.tsx`: `export function PeriodControls({ period, onMonthChange, onRangeChange, onClear }: { period: Period; onMonthChange: (delta: -1 | 1) => void; onRangeChange: (field: 'from' | 'to', value: string) => void; onClear: () => void }): React.JSX.Element`. Componente controlado pela URL, sem `useState`. Estrutura (receita nova "Grupo de período" + "Campo de formulário" + botão secundário; aparência pelo `docs/design.md` e pelo piso de `interface-design`, sem JSX copiado deste plano):
      1. `<fieldset>` com `<legend>` "Mês" e uma linha com: `Button variant="secondary" type="button"` "Mês anterior" (`onClick={() => onMonthChange(-1)}`); `<span aria-live="polite">` com `formatMonth(period.month)` quando `kind === 'month'`, "Todo o período" quando `all`, "Período personalizado" quando `range`; `Button` "Próximo mês" (`onMonthChange(1)`); `Button` "Todo o período" (`onClick={onClear}`, `disabled={period.kind === 'all'}`). O texto visível é o nome acessível dos botões (sem `aria-label`).
      2. Dois campos "De" e "Até": `<label htmlFor>` + `<input type="date" id>` com `id`s de `useId()`; `value` = `toDateBounds(period).from ?? ''` / `.to ?? ''` (com mês selecionado mostram os limites do mês); `onChange` chama `onRangeChange('from', event.target.value)` / `onRangeChange('to', …)`.
      Em 360px os grupos quebram de linha, nada sai da tela.
    - `sort-controls.tsx`: remove a `<div className="mt-6 flex flex-wrap items-end gap-3">` externa; devolve os dois controles num fragmento (`<>…</>`), sem mais mudanças (rótulo "Ordenar por", opções, `aria-label="Inverter direção da ordenação"`, textos "Decrescente"/"Crescente").
    - `docs/design.md`, "Padrões acrescentados pelas entregas": linha `| Grupo de período | <fieldset className="flex flex-col gap-1"> com <legend className="text-sm font-medium text-gray-900">; linha flex flex-wrap items-center gap-2; texto do mês min-w-40 text-center text-sm text-gray-900 tabular-nums; <input type="date"> com as classes do <input> da receita "Campo de formulário" mais min-h-10 (sem w-full) | 005 |`.
  - Skills: interface-design, client-state, component-robustness
  - Complexidade: média

- [x] T2.3 — Período na URL em `ExpensesList`, barra única de controles, vazio filtrado e total no resumo
  - Arquivos: `src/features/expenses/components/expenses-list.tsx` (alterar); `src/features/expenses/components/pagination.tsx` (alterar)
  - O que fazer:
    - `pagination.tsx`: prop nova `totalCents: number`; o resumo passa a `Página {page} de {pages} · {total}{unit} · {formatMoney(Math.abs(totalCents))} no período` (importa `formatMoney` de `@/utils/format-money`). Ex.: "Página 1 de 3 · 42 gastos · R$ 3.210,00 no período"; "Página 1 de 1 · 1 gasto · R$ 84,90 no período"; `0` → "R$ 0,00 no período". Botões inalterados.
    - `expenses-list.tsx`:
      - Importa `readPeriod`, `toDateBounds`, `writePeriod`, `shiftMonth`, `currentMonth` de `@/features/expenses/utils/period` e `PeriodControls`.
      - `const period = readPeriod(searchParams)`; `const { from, to } = toDateBounds(period)`; `useExpenses({ page, sort, order, from, to })`.
      - `function commitPeriod(next: Period): void` — `params = new URLSearchParams(searchParams)`; `writePeriod(params, next)`; `setSearchParams(params, { replace: true })`.
      - `handleMonthChange(delta)`: `base = period.kind === 'month' ? period.month : currentMonth()`; `commitPeriod({ kind: 'month', month: shiftMonth(base, delta) })`.
      - `handleRangeChange(field, value)`: parte de `toDateBounds(period)`; `nextFrom = field === 'from' ? (value || null) : bounds.from`; `nextTo = field === 'to' ? (value || null) : bounds.to`; se os dois existem e `nextTo < nextFrom`, apaga o não alterado (`field === 'from'` → `nextTo = null`; senão `nextFrom = null`); `commitPeriod(nextFrom || nextTo ? { kind: 'range', from: nextFrom, to: nextTo } : { kind: 'all' })`.
      - `handleClear()`: `commitPeriod({ kind: 'all' })`.
      - A barra de controles é montada aqui: `<div className="mt-6 flex flex-wrap items-end gap-3">` (receita "Barra de controles de lista") contendo `<PeriodControls period={period} onMonthChange={handleMonthChange} onRangeChange={handleRangeChange} onClear={handleClear} />` e depois `<SortControls … />`; a variável `controls` substitui `sortControls` e continua **antes** e **fora** dos quatro ramos de estado.
      - Vazio: `data.total === 0` mostra "Nenhum gasto nesse período." quando `period.kind !== 'all'` e "Nenhum gasto registrado ainda." quando `all` (mesma receita "Vazio").
      - `<Pagination … totalCents={data.total_cents} />`; `onChange` da paginação e o `useEffect` de correção de página não mudam (partem de `new URLSearchParams(searchParams)` e só tocam `page`). `writeSorting` não muda (só `sort`, `order`, `page`). Nada vem de `useState`. Textos "Carregando gastos…", "Não foi possível carregar os gastos." e "Tentar de novo" inalterados.
  - Skills: client-state, interface-design, component-robustness
  - Complexidade: média

- [x] T2.4 — Jornada Playwright de período contra o FastAPI real
  - Arquivos: `e2e/expenses.spec.ts` (alterar)
  - O que fazer: teste novo `filters the expenses by month and by date range and keeps the period on reload`, dentro do `mode: 'serial'` existente. Login com `e2e`/`senha-e2e-9k2` (mesmos passos dos testes existentes); clica `link` "Gastos"; `toHaveURL(/\/app\/expenses$/)`; `getByText(/Página 1 de 1 · (2 gastos · R\$ 234,90|3 gastos · R\$ 284,90) no período/)` visível; `getByRole('button', { name: 'Todo o período' })` desabilitado. `page.goto('/app/expenses?month=2026-10')` → `getByText('Nenhum gasto nesse período.')` visível e `getByText('outubro de 2026')` visível. Clica `button` "Mês anterior" → `toHaveURL(/month=2026-09/)`, `getByText('setembro de 2026')` visível, `getByRole('listitem')` com `toHaveCount(2)`, `getByLabel('De', { exact: true })` com valor `2026-09-01` e `getByLabel('Até', { exact: true })` com valor `2026-09-30`. `getByLabel('De', { exact: true }).fill('2026-09-02')` → `toHaveURL(/from=2026-09-02/)` e `not.toHaveURL(/month=/)`; `getByLabel('Até', { exact: true }).fill('2026-09-02')` → `toHaveURL(/to=2026-09-02/)`, `listitem` com `toHaveCount(1)` contendo "MERCADO DO BAIRRO", `getByText('Período personalizado')` visível e `getByText('Página 1 de 1 · 1 gasto · R$ 84,90 no período')` visível. `page.reload()` → `listitem` continua 1 com "MERCADO DO BAIRRO", `getByLabel('De', { exact: true })` e `getByLabel('Até', { exact: true })` com valor `2026-09-02`. Clica `button` "Todo o período" → `not.toHaveURL(/from=/)`, `listitem` com contagem 2 ou 3 (`expect(await page.getByRole('listitem').count()).toBeGreaterThanOrEqual(2)`) e o botão "Todo o período" desabilitado.
  - Skills: e2e-testing
  - Complexidade: baixa

- [x] T2.5 — Testes da fase 2
  - Arquivos: `src/features/expenses/utils/__tests__/period.test.ts` (criar); `src/features/expenses/components/__tests__/pagination.test.tsx` (alterar); `src/features/expenses/components/__tests__/expenses-list.test.tsx` (alterar)
  - O que fazer:
    - `period.test.ts` (unit-testing):
      - `monthRange gives the first and last day of the month` — `'2026-02'` → `{ from: '2026-02-01', to: '2026-02-28' }`; `'2028-02'` → `to: '2028-02-29'`; `'2026-09'` → `to: '2026-09-30'`.
      - `shiftMonth crosses the year in both directions` — `('2026-01', -1)` → `'2025-12'`; `('2026-12', 1)` → `'2027-01'`; `('2026-07', -1)` → `'2026-06'`.
      - `formatMonth spells the month in pt-BR` — `'2026-09'` → `'setembro de 2026'`; `'2026-01'` → `'janeiro de 2026'`.
      - `readMonth rejects what is not YYYY-MM` — `'2026-13'`, `'13'`, `'2026-9'`, `null` → `null`; `'2026-09'` → `'2026-09'`.
      - `readIsoDate rejects impossible days` — `'2026-02-31'`, `'2026-13-01'`, `'01/09/2026'`, `null` → `null`; `'2026-02-28'` → `'2026-02-28'`.
      - `readPeriod prefers the month over a range` — `new URLSearchParams('month=2026-07&from=2026-01-01')` → `{ kind: 'month', month: '2026-07' }`.
      - `readPeriod drops an inverted "to"` — `'from=2026-09-10&to=2026-09-01'` → `{ kind: 'range', from: '2026-09-10', to: null }`.
      - `readPeriod falls back to all on invalid values` — `'month=13'` → `{ kind: 'all' }`; `''` → `{ kind: 'all' }`.
      - `toDateBounds expands a month and passes a range through` — mês `'2026-07'` → `{ from: '2026-07-01', to: '2026-07-31' }`; `all` → nulos.
      - `writePeriod drops the page and the competing format` — de `'page=2&month=2026-07&sort=amount'` escrever `{ kind: 'range', from: '2026-07-10', to: null }` → `'sort=amount&from=2026-07-10'` (sem `page`, `month`, `to`); de `'from=2026-07-10&to=2026-07-20'` escrever `{ kind: 'month', month: '2026-08' }` → só `month=2026-08`; escrever `{ kind: 'all' }` apaga os três.
    - `pagination.test.tsx` (component-testing): os seis casos existentes passam a receber `totalCents` (`-321000` nos de 45 gastos, `-8490` no singular); os textos esperados viram `'Página 1 de 3 · 45 gastos · R$ 3.210,00 no período'` e `'Página 1 de 1 · 1 gasto · R$ 84,90 no período'`. Caso novo `shows R$ 0,00 when the total is zero` — `total={0} totalCents={0}` → texto contém `'R$ 0,00 no período'` e não contém `'-R$'`.
    - `expenses-list.test.tsx` (component-testing, api-mocking): `spyOnExpensesRequests` e `sortForSpy` passam a filtrar por `from`/`to` (comparação de string, como o handler) e a devolver `total`/`total_cents` do filtro. Os 24 casos existentes continuam com o mesmo nome; os que afirmam `'Página 1 de 3 · 45 gastos'` passam a usar o texto com ` · R$ … no período` (ou regex `/Página 1 de 3 · 45 gastos/`). Casos novos:
      - `shows the whole period by default` — `route: '/expenses'` → `getByText('Todo o período', { selector: 'span' })`, `getByRole('button', { name: 'Todo o período' })` desabilitado, `getByLabelText('De')` e `getByLabelText('Até')` com valor `''`, a primeira chamada à API não tem `from` nem `to`, e o resumo casa `/45 gastos · R\$ .* no período/`.
      - `reads the month from the URL` — `route: '/expenses?month=2026-07'` → API chamada com `from=2026-07-01` e `to=2026-07-31`; texto `'julho de 2026'`; resumo casa `/31 gastos/`; `getByLabelText('De')` com valor `2026-07-01` e `'Até'` com `2026-07-31`; botão "Todo o período" habilitado.
      - `"Mês anterior" moves one month back` — `?month=2026-07`, clica "Mês anterior" → `search` vira `?month=2026-06` e o resumo casa `/13 gastos/`.
      - `"Próximo mês" moves one month forward` — `?month=2026-07`, clica "Próximo mês" → `search` vira `?month=2026-08`, resumo casa `/1 gasto ·/` e o único `listitem` contém "MERCADO DO BAIRRO".
      - `"Mês anterior" without a month starts from the current month` — `vi.useFakeTimers({ toFake: ['Date'] })` + `vi.setSystemTime(new Date(2026, 8, 15))`, `route: '/expenses'`, clica "Mês anterior" → `search` vira `?month=2026-08`; `vi.useRealTimers()` no fim.
      - `shows the filtered empty state with the controls` — `?month=2026-09` → `'Nenhum gasto nesse período.'` visível, `queryByText('Nenhum gasto registrado ainda.')` ausente, botões "Mês anterior" e "Todo o período" presentes.
      - `"Todo o período" clears the month` — `?month=2026-07`, clica o `button` "Todo o período" → `search` vira `''` e o resumo casa `/45 gastos/`.
      - `editing a date switches from month to range` — `?month=2026-07`; `userEvent.clear` + `type` em "De" com `2026-07-10` → `search` vira `?from=2026-07-10&to=2026-07-31`; depois "Até" com `2026-07-20` → `?from=2026-07-10&to=2026-07-20`, sem `month`; texto `'Período personalizado'`; API chamada com `from=2026-07-10` e `to=2026-07-20`.
      - `the field just edited wins over an inverted range` — `?from=2026-07-10&to=2026-07-20`; "De" recebe `2026-07-25` → `search` vira `?from=2026-07-25` (sem `to`).
      - `the month wins when the URL has both formats` — `?month=2026-07&from=2026-01-01` → API com `from=2026-07-01` e `to=2026-07-31`; texto `'julho de 2026'`.
      - `changing the period drops the page and keeps the sorting` — `?month=2026-07&page=2&sort=amount`, clica "Mês anterior" → `search` vira `?month=2026-06&sort=amount` (sem `page`; ordem dos parâmetros irrelevante: afirmar cada `get`).
      - `pagination keeps the period` — `?month=2026-07`, clica "Próxima" → `search` contém `month=2026-07` e `page=2`; API chamada com `from=2026-07-01`, `to=2026-07-31` e `page=2`.
      - `falls back to the whole period on an invalid month` — `?month=13` → texto `'Todo o período'` (span), API sem `from`/`to`.
      - `keeps the period controls visible in the error state` — `GET` 500 → `role="alert"` "Não foi possível carregar os gastos." e o `button` "Mês anterior" presente.
  - Skills: unit-testing, component-testing, api-mocking
  - Complexidade: média

### Critérios de aceite da fase 2

- [x] CA2.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0; `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` também. (comando)
- [x] CA2.2 — `pnpm test:e2e` sai com código 0 com o teste `filters the expenses by month and by date range and keeps the period on reload` em `e2e/expenses.spec.ts`, além de `opens the expenses page and lists only the spending`, `reorders the expenses by amount and by category and keeps the order on reload`, `goes back to the balances page` e os de `e2e/sync.spec.ts` e `e2e/login-and-balances.spec.ts`; `playwright.config.ts` contém `workers: 1`; `e2e/expenses.spec.ts` contém `test.describe.configure({ mode: 'serial' })`, `month=2026-10`, `getByLabel('De', { exact: true })`, `getByLabel('Até', { exact: true })`, `page.reload()` e `getByRole('button', { name: 'Inverter direção da ordenação' })`. (comando, estrutural)
- [x] CA2.3 — `src/features/expenses/types/expense.ts` tem `total_cents: number` em `ExpensesResponse`, `from: string | null` e `to: string | null` em `ExpensesQuery`, e exporta `Period` com as três variantes `kind: 'all'`, `kind: 'month'` e `kind: 'range'`; `src/features/expenses/utils/period.ts` exporta `readMonth(value: string | null): string | null`, `daysInMonth(year: number, month: number): number`, `readIsoDate(value: string | null): string | null`, `monthRange(month: string): { from: string; to: string }`, `shiftMonth(month: string, delta: number): string`, `currentMonth(): string`, `formatMonth(month: string): string`, `readPeriod(searchParams: URLSearchParams): Period`, `toDateBounds(period: Period): { from: string | null; to: string | null }` e `writePeriod(params: URLSearchParams, period: Period): void`; `new Date()` sem argumento aparece só dentro de `currentMonth`; o arquivo não importa `react` nem `Intl`, e contém `'setembro'` e `'dezembro'`; `src/features/expenses/api/get-expenses.ts` contém `params.set('from', query.from)` e `params.set('to', query.to)` guardados por `!== null`, e mantém `queryKey: ['expenses', query]` e `placeholderData: keepPreviousData`. (estrutural)
- [x] CA2.4 — `src/features/expenses/components/period-controls.tsx` exporta `PeriodControls({ period, onMonthChange, onRangeChange, onClear }: { period: Period; onMonthChange: (delta: -1 | 1) => void; onRangeChange: (field: 'from' | 'to', value: string) => void; onClear: () => void })`; contém `<fieldset`, `<legend` com o texto "Mês", `aria-live="polite"`, os textos "Mês anterior", "Próximo mês", "Todo o período" e "Período personalizado", `useId()`, dois `<label` com `htmlFor` e os textos "De" e "Até", dois `<input` com `type="date"`, `disabled={period.kind === 'all'}`, e usa `Button` de `@/components/ui/button` com `variant="secondary"` e `type="button"`; não contém `useState`, `aria-label` nem `as Period`. `src/features/expenses/components/sort-controls.tsx` não contém `mt-6` nem `items-end`. (estrutural)
- [x] CA2.5 — `src/features/expenses/components/expenses-list.tsx` importa `readPeriod`, `toDateBounds`, `writePeriod`, `shiftMonth` e `currentMonth` de `@/features/expenses/utils/period` e `PeriodControls`; chama `useExpenses({ page, sort, order, from, to })`; renderiza `<PeriodControls` antes de `<SortControls` dentro de uma `<div className="mt-6 flex flex-wrap items-end gap-3">`, e essa barra aparece antes do primeiro `if (isPending)`; contém `currentMonth()`, `shiftMonth(`, `{ kind: 'all' }`, os textos "Nenhum gasto nesse período." e "Nenhum gasto registrado ainda.", e `totalCents={data.total_cents}`; toda escrita na URL parte de `new URLSearchParams(searchParams)`; as escritas de período e de ordenação usam `{ replace: true }` e a de `onChange` da `<Pagination` não; não contém `useState`; mantém "Carregando gastos…", "Não foi possível carregar os gastos." e "Tentar de novo". `src/features/expenses/components/pagination.tsx` declara a prop `totalCents: number`, importa `formatMoney` de `@/utils/format-money` e contém `formatMoney(Math.abs(totalCents))` e o texto "no período". (estrutural)
- [x] CA2.6 — Piso visual, lido no código: o `<fieldset>` de `period-controls.tsx` usa as classes de "Grupo de período" do `docs/design.md` (`flex flex-col gap-1`, `<legend>` com `text-sm font-medium text-gray-900`, linha `flex flex-wrap items-center gap-2`, texto do mês `min-w-40 text-center text-sm text-gray-900 tabular-nums`); os `<label>` de "De"/"Até" usam as classes de `<label>` de "Campo de formulário"; os `<input type="date">` usam as classes do `<input>` de "Campo de formulário" mais `min-h-10` e sem `w-full`; `docs/design.md` tem, em "Padrões acrescentados pelas entregas", a linha "Grupo de período" com fatia `005`; nenhum arquivo em `src/features/expenses/` contém `style={{`, `<a href` ou `!important`. (estrutural)
- [x] CA2.7 — `src/testing/mocks/handlers.ts` lê `from` e `to` de `searchParams` no handler de `/api/transactions/expenses`, contém `.filter(` antes de `sortExpenses(`, `item.date >= from`, `item.date <= to`, e responde `total_cents` calculado por `reduce(`; `fakeExpenses` continua com 45 itens. (estrutural)
- [x] CA2.8 — `?month=2026-07` chama a API com `from=2026-07-01&to=2026-07-31`, mostra "julho de 2026" e "31 gastos" (`reads the month from the URL`); "Mês anterior" leva a `?month=2026-06` com 13 gastos (`"Mês anterior" moves one month back`); sem mês e com relógio em 15/09/2026, "Mês anterior" leva a `?month=2026-08` (`"Mês anterior" without a month starts from the current month`); `?month=2026-09` mostra "Nenhum gasto nesse período." (`shows the filtered empty state with the controls`); editar "De" e "Até" leva a `?from=2026-07-10&to=2026-07-20` sem `month` e ao texto "Período personalizado" (`editing a date switches from month to range`); "De" `2026-07-25` sobre `to=2026-07-20` apaga `to` (`the field just edited wins over an inverted range`); `?month=2026-07&page=2&sort=amount` + "Mês anterior" apaga `page` e mantém `sort=amount` (`changing the period drops the page and keeps the sorting`); "Próxima" em `?month=2026-07` mantém `month` e grava `page=2` (`pagination keeps the period`); `?month=13` cai em "Todo o período" (`falls back to the whole period on an invalid month`). (comportamental)
- [x] CA2.9 — Os testes nomeados em T2.5 existem em `src/features/expenses/utils/__tests__/period.test.ts`, `src/features/expenses/components/__tests__/pagination.test.tsx` e `src/features/expenses/components/__tests__/expenses-list.test.tsx`; `npx vitest run --coverage` reporta ≥ 80% de linhas em `src/features/expenses/utils/period.ts`, `src/features/expenses/api/get-expenses.ts`, `src/features/expenses/components/period-controls.tsx`, `src/features/expenses/components/sort-controls.tsx`, `src/features/expenses/components/pagination.tsx` e `src/features/expenses/components/expenses-list.tsx`. (comando)

## DoD da entrega

- [x] DoD1 — Todas as tarefas e critérios do plano marcados
- [x] DoD2 — Suíte de testes inteira passa
- [x] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [x] DoD4 — Tipos de todos os `tsconfig` sem erros
- [x] DoD5 — Console dos testes sem erro nem aviso
- [x] DoD6 — `build` passa
- [x] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [x] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [x] DoD9 — Nenhuma worktree ou branch temporária sobrando
