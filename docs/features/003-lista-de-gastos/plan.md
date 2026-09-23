# PLAN 003 — lista de gastos

Branch: `feature/003-lista-de-gastos`

Decisões registradas aqui (a SPEC deixou ao plano; escolhido o mais simples):

- No formato consolidado, o campo que o `ingest` grava em `transactions.category` é `categoria` (`app/ingest/loader.py::_transaction_row`), não `categoria_pluggy`. Fixtures e testes que querem o rótulo "Compras" escrevem `"categoria": "Shopping"`.
- `app.payees.names.labels(conn)` só enxerga linhas com `payee` preenchido, e o `ingest` não preenche (`_fill_payees` roda em `synchronise`). O teste de `payee_name` chama `app.taxonomy.classify._fill_payees(conn)` e `conn.commit()` depois do `ingest`; o backend do e2e não chama (lá `payee_name` nulo é o caso previsto).
- `account_type` no Pydantic é `Literal["BANK", "CREDIT"] | None`, igual ao contrato de D3; o tipo TS repete a união.
- `pages = Math.max(1, Math.ceil(total / page_size))`; texto "{total} gasto" quando `total === 1`, senão "{total} gastos".
- `?page` é lido com `Number.parseInt(value, 10)`; `NaN` ou `< 1` vale 1. A correção de página além da última é um `useEffect` que, com `data.total > 0 && page > pages`, faz `setSearchParams({ page: String(pages) }, { replace: true })`.
- O `NavLink` "Saldos" leva `end` (rota `/` casaria com `/expenses` sem ele).
- `ExpensesRoute` lê o login com `useUser()` (`@/lib/auth`), como `dashboard.tsx`.
- O `sync.spec.ts` ingere `tests/data/sync_transactions.json` ("COMPRA DE SINCRONIZACAO", −R$ 50,00, também um gasto) na mesma base SQLite, e a ordem entre arquivos de spec não é garantida. `e2e/expenses.spec.ts` prova presença de "MERCADO DO BAIRRO", ausência de "TED PARA POUPANCA" e "SALARIO" e "Página 1 de 1", mas a contagem casa com `/Página 1 de 1 · [12] gastos?/`; a contagem exata ("1 gasto") é provada em `tests/test_expenses_api.py` e em `expenses-list.test.tsx`.
- Fase 2 entrega a lista funcional com `?page` na URL e os quatro estados; a fase 3 acrescenta `Pagination`, a correção de página além da última, o teste de integração e o e2e. `expenses-list.tsx` e seu teste são alterados na fase 3.

## Fase 1 — Endpoint de gastos paginado

Só Python. Ao final: `GET /api/transactions/expenses?page=N&page_size=M` responde a página de gastos (predicado `SPENDING`, ordem `date DESC, id DESC`, rótulo de categoria em pt-BR, nome do recebedor quando houver) com `total`; o backend do e2e nasce com três lançamentos; a suíte Python prova tudo.

- [ ] T1.1 — Consulta paginada de gastos com rótulos resolvidos
  - Arquivos: `app/queries/expenses.py` (criar)
  - O que fazer:
    - `from app.queries.spending import SPENDING`; `from app.taxonomy.seed import category_labels`; `from app.payees.names import labels`.
    - `@dataclass(frozen=True) class ExpensesPage: items: list[dict[str, Any]]; total: int`.
    - `_PAGE = f"""SELECT t.id, t.date, t.description, t.payee, t.category, t.amount_cents, a.name AS account_name, a.institution AS account_institution, a.type AS account_type FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id WHERE {SPENDING} ORDER BY t.date DESC, t.id DESC LIMIT ? OFFSET ?"""` e `_TOTAL = f"SELECT count(*) FROM transactions WHERE {SPENDING}"`. A string `amount_cents < 0` não aparece neste arquivo: só via `SPENDING` (D1).
    - `def list_expenses(conn: sqlite3.Connection, *, page: int, page_size: int) -> ExpensesPage`: `offset = (page - 1) * page_size`; `rows = conn.execute(_PAGE, (page_size, offset)).fetchall()`; `total = conn.execute(_TOTAL).fetchone()[0]`; `names = labels(conn)`; `categories = category_labels()`. Para cada linha, monta dict com `id`, `date`, `description`, `payee_name = names.get(row["payee"])` (nulo quando `payee` é nulo ou não está no mapa), `account_name`, `account_institution`, `account_type`, `category = categories.get(raw, raw) if raw else None` (raw desconhecido fica como está; `NULL`/`''` vira `None`), `amount_cents`. Não devolve `payee`.
    - Comentário de porquê só nos dois mapas resolvidos em Python (rótulo não existe no banco; precedência de nome já é código testado — D2). Nenhum `commit`.
  - Skills: —
  - Complexidade: média

- [ ] T1.2 — Router `transactions` e registro no app
  - Arquivos: `app/routers/transactions.py` (criar); `app/main.py` (alterar)
  - O que fazer:
    - `app/routers/transactions.py`: `router = APIRouter(prefix="/api/transactions")`; `class Expense(BaseModel): id: int; date: str; description: str | None; payee_name: str | None; account_name: str | None; account_institution: str | None; account_type: Literal["BANK", "CREDIT"] | None; category: str | None; amount_cents: int`; `class ExpensesResponse(BaseModel): items: list[Expense]; page: int; page_size: int; total: int`. `@router.get("/expenses")` `def expenses(page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20) -> ExpensesResponse`: `conn = connect()`; `try: found = list_expenses(conn, page=page, page_size=page_size)` `finally: conn.close()`; devolve `ExpensesResponse(items=[Expense(**item) for item in found.items], page=page, page_size=page_size, total=found.total)`. Rota `def` (norma 31). As strings `SELECT`, `INSERT` e `commit(` não aparecem no arquivo (norma 30). Sem sessão o guard existente já devolve 401.
    - `app/main.py`: importar `transactions` de `app.routers` e `app.include_router(transactions.router)` logo após `sync.router`.
  - Skills: api-requests
  - Complexidade: baixa

- [ ] T1.3 — Backend do e2e com lançamentos
  - Arquivos: `tests/data/e2e_transactions.json` (criar); `scripts/e2e-backend.sh` (alterar)
  - O que fazer:
    - `tests/data/e2e_transactions.json`: lista com três objetos no formato de `tests/data/sync_transactions.json` (mesmas chaves), todos com `"conta_id": "acc-fixture-1"`: `{"id": "e2e-t-1", "data": "2026-09-02", "descricao": "MERCADO DO BAIRRO", "valor": -84.9, "tipo": "DEBIT", "categoria_pluggy": "Groceries", "categoria": "Groceries", "eh_transferencia": false, "eh_estorno": false, "estornada_por": "", …}`; `{"id": "e2e-t-2", "data": "2026-09-03", "descricao": "TED PARA POUPANCA", "valor": -500.0, "eh_transferencia": true, "motivo_transferencia": "conta propria", …}`; `{"id": "e2e-t-3", "data": "2026-09-05", "descricao": "SALARIO", "valor": 6000.0, "tipo": "CREDIT", …}`. Demais campos: `parcela_atual`/`parcela_total` `null`, strings vazias.
    - `scripts/e2e-backend.sh`: importar `load_transactions` de `app.ingest.source`; trocar `transactions=[]` por `transactions=load_transactions("tests/data/e2e_transactions.json")`. O `DELETE FROM sync_runs` e as variáveis exportadas ficam como estão.
  - Skills: e2e-testing
  - Complexidade: baixa

- [ ] T1.4 — Testes da fase 1
  - Arquivos: `tests/test_expenses_api.py` (criar)
  - O que fazer:
    - Fixture `client(tmp_path, monkeypatch)` igual à de `tests/test_sync_api.py` (env `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH`, `SESSION_SECRET`, `DASH_TRANSACTIONS_PATH`/`DASH_ACCOUNTS_GLOB` apontando para `tests/data/sync_*.json`, `create_app()`, `seed_user`, `seed_taxonomy`, `TestClient(app, follow_redirects=False)`); `_sign_in(client)`; helper `_transaction(id: str, date: str, amount: float, **overrides) -> dict[str, Any]` que devolve o dict consolidado com as chaves de `tests/data/sync_transactions.json` (`conta_id` `"sync-acc-1"`, `descricao` `f"GASTO {id}"`, `categoria` `""`, `eh_transferencia` `False`, `eh_estorno` `False`, `estornada_por` `""`, `nome_fantasia` `""`, …) sobrescrito por `overrides`; helper `_load(rows)` que abre `connect()`, chama `ingest(conn, transactions=rows, accounts=load_accounts(str(DATA / "sync_accounts.json")), source="teste")` e fecha.
    - Casos (api-requests, unit-testing):
      - `test_expenses_without_session_answers_401` → 401 `{"detail": "nao autenticado"}`.
      - `test_an_empty_base_answers_an_empty_first_page` → `{"items": [], "page": 1, "page_size": 20, "total": 0}`.
      - `test_only_spending_rows_come_back` — ingere quatro linhas: gasto `-50.0`; transferência `-500.0` com `eh_transferencia=True`; estorno `+30.0` com `eh_estorno=True` e o lançamento estornado `-30.0` com `estornada_por="<id do estorno>"`; entrada `+6000.0` → `total == 1` e a única `description` é a do gasto.
      - `test_rows_come_newest_first_and_ties_break_by_id_desc` — três gastos (`2026-08-01`, `2026-08-03`, `2026-08-03`) → `[d for d in dates] == ["2026-08-03", "2026-08-03", "2026-08-01"]` e, entre os dois de `08-03`, o de `id` maior vem primeiro.
      - `test_pages_hold_twenty_rows_and_the_last_page_the_rest` — 25 gastos → `page=1` tem 20 itens, `page=2` tem 5, ambos com `total == 25`, `page_size == 20`.
      - `test_a_page_past_the_end_is_empty_with_the_right_total` — mesmos 25 → `page=3` responde 200 `items == []`, `total == 25`, `page == 3`.
      - `test_page_size_is_honoured` — 25 gastos, `page_size=10` → 10 itens e `page_size == 10`.
      - `test_page_zero_and_page_size_over_100_answer_422` — `page=0` → 422; `page_size=101` → 422; `page_size=0` → 422.
      - `test_the_merchant_name_becomes_the_payee_name` — gasto com `nome_fantasia="Mercado do Bairro"` e outro sem; depois do `ingest`, `_fill_payees(conn)` + `commit` → o primeiro tem `payee_name == "Mercado do Bairro"` e o segundo `payee_name is None`.
      - `test_the_category_comes_back_as_the_seed_label` — `categoria="Shopping"` → `category == "Compras"`; `categoria=""` → `category is None`; `categoria="Desconhecida"` → `category == "Desconhecida"`.
      - `test_the_account_name_and_institution_come_from_the_account` — `account_name == "Conta de sincronização"`, `account_institution == "Banco de teste"`, `account_type == "BANK"`.
      - `test_the_response_has_the_contract_fields` — o item tem exatamente as chaves `{"id", "date", "description", "payee_name", "account_name", "account_institution", "account_type", "category", "amount_cents"}` e `amount_cents == -5000` (int).
  - Skills: api-requests, unit-testing
  - Complexidade: média

### Critérios de aceite da fase 1

- [ ] CA1.1 — `bash scripts/lint.sh` sai com código 0. (comando)
- [ ] CA1.2 — `uv run pytest tests/test_expenses_api.py tests/test_sync_api.py tests/test_accounts_api.py tests/test_auth_api.py` passa, e cada nome de teste listado em T1.4 existe em `tests/test_expenses_api.py`. (comando)
- [ ] CA1.3 — `bash scripts/gates/gates_runner.sh` sai com código 0. (comando)
- [ ] CA1.4 — Existe `app/queries/expenses.py` com `ExpensesPage` (dataclass com `items: list[dict[str, Any]]` e `total: int`) e `list_expenses(conn: sqlite3.Connection, *, page: int, page_size: int) -> ExpensesPage`; o arquivo importa `SPENDING` de `app.queries.spending`, `category_labels` de `app.taxonomy.seed` e `labels` de `app.payees.names`; a string `amount_cents < 0` não aparece nele; contém `LEFT JOIN accounts`, `ORDER BY t.date DESC, t.id DESC` e `LIMIT ? OFFSET ?`; não contém `commit(`. (estrutural)
- [ ] CA1.5 — `app/routers/transactions.py` define `router = APIRouter(prefix="/api/transactions")`, `Expense` e `ExpensesResponse` com os campos de T1.2, e `def expenses(page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20) -> ExpensesResponse` em `@router.get("/expenses")`; a rota é `def`, não `async def`; as strings `SELECT`, `INSERT` e `commit(` não aparecem no arquivo; `app/main.py` inclui `transactions.router`. (estrutural)
- [ ] CA1.6 — `GET /api/transactions/expenses` sem sessão responde 401 (`test_expenses_without_session_answers_401`); com transferência, estorno, lançamento estornado e entrada na base, só o gasto volta e `total == 1` (`test_only_spending_rows_come_back`); `page=3` de 25 gastos responde 200 com `items: []` e `total: 25` (`test_a_page_past_the_end_is_empty_with_the_right_total`). (comportamental)
- [ ] CA1.7 — `tests/data/e2e_transactions.json` tem três objetos com `conta_id` `"acc-fixture-1"`, descrições `"MERCADO DO BAIRRO"` (`valor` `-84.9`), `"TED PARA POUPANCA"` (`valor` `-500.0`, `eh_transferencia` `true`) e `"SALARIO"` (`valor` `6000.0`); `scripts/e2e-backend.sh` chama `load_transactions("tests/data/e2e_transactions.json")` dentro do `ingest(...)` e mantém `DELETE FROM sync_runs`. (estrutural)
- [ ] CA1.8 — `uv run pytest --cov=app.queries.expenses --cov=app.routers.transactions --cov-report=term tests/test_expenses_api.py` reporta ≥ 80% em `app/queries/expenses.py` e `app/routers/transactions.py`. (comando)

## Fase 2 — Cabeçalho com navegação, rota `/expenses` e lista de gastos com estados

Ao final: o cabeçalho de `/app/` e `/app/expenses` é o mesmo `AppHeader`, com "Saldos" e "Gastos" e o ativo marcado; `/app/expenses` mostra `<h1>` "Gastos", o texto de apoio e a lista da página lida de `?page` (carregando, vazio, erro e com dados), cada linha com data, descrição, recebedor, conta, selo de categoria e valor. Ainda sem botões de paginação.

- [ ] T2.1 — `AppHeader` compartilhado, caminho `expenses` e rota protegida
  - Arquivos: `src/components/layouts/app-header.tsx` (criar); `src/config/paths.ts` (alterar); `src/app/router.tsx` (alterar); `src/app/routes/expenses.tsx` (criar); `src/app/routes/dashboard.tsx` (alterar); `docs/design.md` (alterar)
  - O que fazer:
    - `paths.ts`: acrescentar `expenses: '/expenses'`.
    - `app-header.tsx`: `export function AppHeader({ userLogin, action }: { userLogin?: string; action?: ReactNode }): React.JSX.Element`. Estrutura (receita "Cabeçalho de app" + receita nova "Navegação do cabeçalho"): à esquerda, o nome "dash_financeiro" e um `<nav aria-label="Principal">` com `NavLink` para `paths.dashboard` (texto "Saldos", com `end`) e `NavLink` para `paths.expenses` (texto "Gastos"); `className` do `NavLink` é função de `{ isActive }` que aplica o estilo de ativo ou inativo da receita. À direita, `userLogin` em texto secundário e `action`. A linha quebra em 360px (`flex-wrap`). Importa só de `react`, `react-router` e `@/config/paths` (compartilhado não importa de feature).
    - `expenses.tsx`: `export function ExpensesRoute(): React.JSX.Element`; `useUser()`; `useEffect` com `document.title = 'Gastos · dash_financeiro'`; renderiza `<AppHeader userLogin={data?.login} action={<LogoutButton />} />` e, no contêiner de página, `<h1>` "Gastos", texto de apoio "Todos os gastos das suas contas e cartões, do mais recente ao mais antigo." e `<ExpensesList />` (de T2.3; a tarefa cria o arquivo já com o import — a fase é executada em ordem e compila ao fim de T2.3).
    - `dashboard.tsx`: substituir o `<header>` inline por `<AppHeader userLogin={data?.login} action={<LogoutButton />} />`; nada mais muda.
    - `router.tsx`: acrescentar `{ path: paths.expenses, element: <ProtectedRoute><ExpensesRoute /></ProtectedRoute> }`.
    - `docs/design.md`, "Padrões acrescentados pelas entregas": as três linhas da tabela "Receitas novas" da SPEC 003 — "Navegação do cabeçalho", "Linha de lançamento", "Paginação" — com fatia `003`.
    - Aparência pelo `docs/design.md` e pelo piso de `interface-design`; sem JSX copiado deste plano.
  - Skills: ui-components, routing, interface-design
  - Complexidade: média

- [ ] T2.2 — Feature `expenses`: tipos, consulta, `formatDate`, mocks e zona de lint
  - Arquivos: `src/features/expenses/types/expense.ts` (criar); `src/features/expenses/api/get-expenses.ts` (criar); `src/utils/format-date.ts` (criar); `src/testing/mocks/handlers.ts` (alterar); `eslint.config.js` (alterar)
  - O que fazer:
    - `expense.ts`: `export type Expense = { id: number; date: string; description: string | null; payee_name: string | null; account_name: string | null; account_institution: string | null; account_type: 'BANK' | 'CREDIT' | null; category: string | null; amount_cents: number }`; `export type ExpensesResponse = { items: Expense[]; page: number; page_size: number; total: number }`.
    - `get-expenses.ts`: `export const PAGE_SIZE = 20`; `export function getExpenses(page: number): Promise<ExpensesResponse>` → `apiRequest<ExpensesResponse>(`/api/transactions/expenses?page=${page}&page_size=${PAGE_SIZE}`)`; `export function expensesQueryOptions(page: number)` → `queryOptions({ queryKey: ['expenses', { page }], queryFn: () => getExpenses(page), placeholderData: keepPreviousData })`; `export function useExpenses(page: number)` → `useQuery(expensesQueryOptions(page))`.
    - `format-date.ts`: `export function formatDate(iso: string): string`: casa `/^(\d{4})-(\d{2})-(\d{2})$/`; devolve `dd/mm/aaaa`; sem casar, devolve `iso` como veio. Não usa `Date` (comentário de porquê: `new Date('YYYY-MM-DD')` é UTC e vira o dia anterior em fuso negativo).
    - `handlers.ts`: `export const fakeExpenses: Expense[]` gerado por função determinística com 45 itens, `id` de 45 a 1 e datas decrescentes a partir de `'2026-08-01'` (um dia a menos por item; montar a data por aritmética de `Date.UTC` + `toISOString().slice(0, 10)` só aqui, no mock). Item 1 (o mais recente): `description 'MERCADO DO BAIRRO'`, `payee_name 'Mercado do Bairro'`, `account_name 'Conta corrente'`, `account_institution 'Banco de teste'`, `account_type 'BANK'`, `category 'Compras'`, `amount_cents -8490`, `date '2026-08-01'`. Item 2: `payee_name null`, `category 'Alimentação'`. Item 3: `category null`, `description null`. Demais: `description `GASTO ${id}``, `payee_name null`, `category 'Compras'`, `amount_cents -1000 * n`. Handler `http.get('/api/transactions/expenses', ({ request }) => …)` que lê `page` e `page_size` de `new URL(request.url).searchParams` (padrões 1 e 20) e responde `{ items: fakeExpenses.slice((page - 1) * size, page * size), page, page_size: size, total: fakeExpenses.length }`.
    - `eslint.config.js`: zona `{ target: './src/features/expenses', from: './src/features', except: ['./expenses'] }` ao lado das de `auth`, `accounts` e `sync`.
  - Skills: api-requests, unit-testing, api-mocking, project-structure
  - Complexidade: baixa

- [ ] T2.3 — `ExpenseItem` e `ExpensesList` com os quatro estados e página na URL
  - Arquivos: `src/features/expenses/components/expense-item.tsx` (criar); `src/features/expenses/components/expenses-list.tsx` (criar)
  - O que fazer:
    - `expense-item.tsx`: `export function ExpenseItem({ expense }: { expense: Expense }): React.JSX.Element` — um `<li>` pela receita "Linha de lançamento". Esquerda, empilhado: descrição (ou "Sem descrição" quando nula); nome de quem recebeu, só quando `payee_name` não é nulo; linha da conta com `account_name` e `account_institution` unidos por " · ", parte nula omitida, ambas nulas mostra "Conta desconhecida". Direita, empilhado e alinhado à direita: `formatDate(date)`; selo (receita "Selo de status", par cinza) com `category` ou "Sem categoria"; valor `formatMoney(amount_cents)` pela receita "Valor monetário" (`text-red-700` quando `amount_cents < 0`, senão `text-gray-900`).
    - `expenses-list.tsx`: `export function ExpensesList(): React.JSX.Element`. `const [searchParams] = useSearchParams()`; `page` = `Number.parseInt(searchParams.get('page') ?? '', 10)`, `NaN` ou `< 1` vira 1. `const { data, isPending, isError, refetch } = useExpenses(page)`. Estados, no lugar do conteúdo: `isPending` → receita "Carregando" (`role="status"`) "Carregando gastos…"; `isError` → `<Alert message="Não foi possível carregar os gastos." action={{ label: 'Tentar de novo', onClick: () => void refetch() }} />`; `data.total === 0` → receita "Vazio" "Nenhum gasto registrado ainda."; senão `<ul>` (receita "Lista") com um `<ExpenseItem key={expense.id} expense={expense} />` por item. Nesta fase não há botões de página: `?page=2` na URL já busca a página 2 (o teste de fase cobre).
  - Skills: interface-design, error-handling, client-state, component-robustness
  - Complexidade: média

- [ ] T2.4 — Testes da fase 2
  - Arquivos: `src/components/layouts/__tests__/app-header.test.tsx` (criar); `src/utils/__tests__/format-date.test.ts` (criar); `src/features/expenses/components/__tests__/expenses-list.test.tsx` (criar)
  - O que fazer:
    - `app-header.test.tsx` (component-testing, `renderWithProviders` com `route`): `marks "Saldos" as current on the dashboard` (`route: '/'` → link "Saldos" tem `aria-current="page"` e "Gastos" não tem); `marks "Gastos" as current on the expenses page` (`route: '/expenses'` → o inverso); `renders the login and the action` (`userLogin="teste"` e `action={<button type="button">Sair</button>}` → texto "teste" e botão "Sair" presentes); `links point to the routes` ("Saldos" tem `href="/"` e "Gastos" `href="/expenses"`).
    - `format-date.test.ts` (unit-testing): `formats a day-only ISO date as dd/mm/yyyy` (`'2026-08-01'` → `'01/08/2026'`); `keeps the last day of the month regardless of timezone` (`'2026-07-31'` → `'31/07/2026'`); `returns unknown formats untouched` (`'2026-08-01T10:00:00Z'` volta igual; `''` volta `''`).
    - `expenses-list.test.tsx` (component-testing, MSW, `renderWithProviders`): `shows the loading state` (`role="status"` "Carregando gastos…"); `shows the empty state` (`server.use` com `{ items: [], page: 1, page_size: 20, total: 0 }` → texto "Nenhum gasto registrado ainda." e nenhum `list`); `shows the error and retries` (`GET` 500 na primeira vez → `role="alert"` "Não foi possível carregar os gastos." com botão "Tentar de novo"; clique → `list` aparece); `renders the fields of a row` (`route: '/expenses'` → "MERCADO DO BAIRRO", "Mercado do Bairro", "Conta corrente · Banco de teste", "01/08/2026", selo "Compras" e valor "-R$ 84,90" com classe `text-red-700`); `hides the payee when it is null` (item 2: texto "Mercado do Bairro" aparece uma vez só); `shows "Sem categoria" and "Sem descrição" fallbacks` (item 3); `shows twenty rows on the first page` (`getAllByRole('listitem')` tem 20); `reads the page from the URL` (`route: '/expenses?page=3'` → 5 `listitem`, o primeiro com "GASTO 5"); `treats an invalid page as the first` (`route: '/expenses?page=abc'` → 20 `listitem` e "MERCADO DO BAIRRO" presente).
  - Skills: component-testing, unit-testing, api-mocking
  - Complexidade: média

### Critérios de aceite da fase 2

- [ ] CA2.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0. (comando)
- [ ] CA2.2 — `src/config/paths.ts` exporta `expenses: '/expenses'`; `src/app/router.tsx` tem uma rota `path: paths.expenses` cujo `element` é `<ExpensesRoute />` dentro de `<ProtectedRoute>`; `src/app/routes/expenses.tsx` exporta `ExpensesRoute(): React.JSX.Element`, define `document.title = 'Gastos · dash_financeiro'` e renderiza `<AppHeader`, um `<h1>` com "Gastos", o texto "Todos os gastos das suas contas e cartões, do mais recente ao mais antigo." e `<ExpensesList />`. (estrutural)
- [ ] CA2.3 — `src/components/layouts/app-header.tsx` exporta `AppHeader({ userLogin, action }: { userLogin?: string; action?: ReactNode })`, contém `<nav aria-label="Principal"`, dois `NavLink` com os textos "Saldos" (com `end`) e "Gastos" apontando para `paths.dashboard` e `paths.expenses`, e não importa de `@/features` nem de `@/app`; `src/app/routes/dashboard.tsx` não contém `<header` e renderiza `<AppHeader userLogin={data?.login} action={<LogoutButton />} />`. (estrutural)
- [ ] CA2.4 — `src/features/expenses/types/expense.ts` exporta `Expense` e `ExpensesResponse` com os campos de T2.2; `src/features/expenses/api/get-expenses.ts` exporta `PAGE_SIZE = 20`, `getExpenses(page: number): Promise<ExpensesResponse>` chamando `/api/transactions/expenses?page=${page}&page_size=${PAGE_SIZE}`, `expensesQueryOptions(page)` com `queryKey: ['expenses', { page }]` e `placeholderData: keepPreviousData`, e `useExpenses(page)`; `src/utils/format-date.ts` exporta `formatDate(iso: string): string` e não contém `new Date`. (estrutural)
- [ ] CA2.5 — `expenses-list.tsx` contém os textos literais "Carregando gastos…", "Nenhum gasto registrado ainda.", "Não foi possível carregar os gastos." e "Tentar de novo"; o carregando tem `role="status"`; o erro é renderizado por `<Alert>` com `action` que chama `refetch`; a página vem de `useSearchParams` e nunca de `useState`. `expense-item.tsx` contém "Sem descrição", "Sem categoria" e "Conta desconhecida", renderiza `formatDate(` e `formatMoney(` e aplica `text-red-700` quando `amount_cents < 0`. (estrutural)
- [ ] CA2.6 — Piso visual, lido no código: `expenses.tsx` usa o contêiner de página e o `<h1>` usa as classes de "Título de página" do `docs/design.md`; a lista usa as classes de "Lista"; cada `<li>` de `expense-item.tsx` usa as classes de "Linha de lançamento" (bloco da esquerda com `min-w-0 flex-1` e `truncate`, bloco da direita com `shrink-0` e `items-end`); o selo usa as classes de "Selo de status" com `bg-gray-100 text-gray-700`; o `<nav>` de `app-header.tsx` usa as classes de "Navegação do cabeçalho" e aplica `underline` ao ativo; nenhum arquivo em `src/` contém `style={{`, `<a href` ou `!important`. (estrutural)
- [ ] CA2.7 — `docs/design.md` tem, em "Padrões acrescentados pelas entregas", as linhas "Navegação do cabeçalho", "Linha de lançamento" e "Paginação" com fatia `003`. (estrutural)
- [ ] CA2.8 — `src/testing/mocks/handlers.ts` exporta `fakeExpenses` com 45 itens, o primeiro com `description: 'MERCADO DO BAIRRO'` e `amount_cents: -8490`, e registra `GET /api/transactions/expenses` lendo `page` e `page_size` da URL; `eslint.config.js` tem a zona `target: './src/features/expenses'` com `except: ['./expenses']`; `src/features/expenses/**` não importa de `@/features/auth`, `@/features/accounts`, `@/features/sync` nem de `@/app` (basta `pnpm lint` passar). (estrutural)
- [ ] CA2.9 — Os testes nomeados em T2.4 existem nos arquivos indicados; `npx vitest run --coverage` reporta ≥ 80% de linhas em `src/components/layouts/app-header.tsx`, `src/utils/format-date.ts`, `src/features/expenses/api/get-expenses.ts`, `src/features/expenses/components/expense-item.tsx` e `src/features/expenses/components/expenses-list.tsx`. (comando)

## Fase 3 — Paginação, integração e e2e

Ao final: a lista tem "Página X de Y · N gastos" com "Anterior" e "Próxima" que trocam `?page` sem perder a lista anterior; URL com página além da última cai na última; o fluxo login → "Gastos" → lista → "Saldos" é provado com API mockada e, contra o FastAPI real, pelo Playwright.

- [ ] T3.1 — `Pagination` e lista folheável com correção de página
  - Arquivos: `src/features/expenses/components/pagination.tsx` (criar); `src/features/expenses/components/expenses-list.tsx` (alterar)
  - O que fazer:
    - `pagination.tsx`: `export function Pagination({ page, pages, total, isFetching, onChange }: { page: number; pages: number; total: number; isFetching: boolean; onChange: (page: number) => void }): React.JSX.Element` — `<nav aria-label="Paginação">` pela receita "Paginação". À esquerda, texto "Página {page} de {pages} · {total} gasto" quando `total === 1`, senão "… · {total} gastos". À direita, dois `<Button variant="secondary" type="button">`: "Anterior" (`disabled` quando `page <= 1 || isFetching`, `onClick` → `onChange(page - 1)`) e "Próxima" (`disabled` quando `page >= pages || isFetching`, `onClick` → `onChange(page + 1)`).
    - `expenses-list.tsx`: passa a usar `const [searchParams, setSearchParams] = useSearchParams()` e `isPlaceholderData` de `useExpenses`; `pages = Math.max(1, Math.ceil(data.total / data.page_size))`; `useEffect` que, com `data && data.total > 0 && page > pages`, chama `setSearchParams({ page: String(pages) }, { replace: true })`; abaixo da lista, só quando `data.total > 0`, `<Pagination page={page} pages={pages} total={data.total} isFetching={isPlaceholderData} onChange={(next) => setSearchParams({ page: String(next) })} />` (sem `replace`, para "voltar" funcionar). O estado "Carregando" só aparece em `isPending` (primeira busca); na troca de página a lista anterior fica visível, com os botões desabilitados por `isPlaceholderData`.
  - Skills: ui-components, interface-design, client-state, component-robustness
  - Complexidade: média

- [ ] T3.2 — Jornada Playwright de gastos
  - Arquivos: `e2e/expenses.spec.ts` (criar)
  - O que fazer: `test.describe.configure({ mode: 'serial' })` com comentário de porquê (mesma base SQLite que o `sync.spec.ts` escreve). Teste `opens the expenses page and lists only the spending`: login com `e2e`/`senha-e2e-9k2` (mesmos passos de `sync.spec.ts`); `expect(page).toHaveURL(/\/app\/?$/)`; clica `getByRole('link', { name: 'Gastos' })`; `toHaveURL(/\/app\/expenses$/)`; `heading level 1` "Gastos" visível; link "Gastos" tem `aria-current="page"` (`toHaveAttribute('aria-current', 'page')`); `listitem` contendo "MERCADO DO BAIRRO" visível, com "02/09/2026" e "-R$ 84,90"; `getByText('TED PARA POUPANCA')` e `getByText('SALARIO')` com `toHaveCount(0)`; texto casando `/Página 1 de 1 · [12] gastos?/` visível; botões "Anterior" e "Próxima" desabilitados. Teste `goes back to the balances page`: depois dos passos acima, clica `link` "Saldos" → `heading level 1` "Saldos de hoje" visível e `toHaveURL(/\/app\/?$/)`.
  - Skills: e2e-testing
  - Complexidade: baixa

- [ ] T3.3 — Testes da fase 3
  - Arquivos: `src/features/expenses/components/__tests__/expenses-list.test.tsx` (alterar); `src/features/expenses/components/__tests__/pagination.test.tsx` (criar); `src/app/__tests__/expenses.test.tsx` (criar)
  - O que fazer:
    - `pagination.test.tsx` (component-testing): `shows page, pages and the plural total` (`page=1 pages=3 total=45` → "Página 1 de 3 · 45 gastos"); `uses the singular for one expense` (`total=1` → "Página 1 de 1 · 1 gasto"); `disables "Anterior" on the first page` e `disables "Próxima" on the last page`; `disables both while fetching` (`isFetching` → ambos `disabled`); `calls onChange with the neighbour page` (clique em "Próxima" → `onChange(2)`; em "Anterior" com `page=2` → `onChange(1)`).
    - `expenses-list.test.tsx` (component-testing, MSW): acrescentar um componente auxiliar `LocationProbe` no teste que renderiza `useLocation().search` em `data-testid="search"`; casos novos: `shows the pagination summary` (`route: '/expenses'` → "Página 1 de 3 · 45 gastos"); `hides the pagination when empty` (resposta com `total: 0` → nenhum `navigation` com nome "Paginação"); `"Próxima" moves to page 2 in the URL and in the API` (clique → `search` vira `?page=2`, "Página 2 de 3 · 45 gastos" aparece e o primeiro `listitem` é "GASTO 25"); `keeps the previous rows while the next page loads` (handler com atraso de ~50 ms; logo após o clique não há `role="status"` e "Próxima" está `disabled`; depois, a página 2 aparece); `falls back to the last page when the URL is past the end` (`route: '/expenses?page=9'` → `search` vira `?page=3` e "Página 3 de 3 · 45 gastos" aparece).
    - `expenses.test.tsx` (integration-testing, `routes` de `@/app/router` com `createMemoryRouter`, como `login-to-balances.test.tsx`): `redirects to the login page without a session` (`['/expenses']` → `heading` "Entrar"); `navigates from the balances page to the expenses page` (login em `/login` → `heading` "Saldos de hoje" → clique em `link` "Gastos" → `heading` "Gastos", link "Gastos" com `aria-current="page"`, "MERCADO DO BAIRRO" presente, `document.title === 'Gastos · dash_financeiro'`); `navigates back to the balances page` (a partir de "Gastos", clique em `link` "Saldos" → `heading` "Saldos de hoje" e link "Saldos" com `aria-current="page"`).
  - Skills: component-testing, integration-testing, api-mocking
  - Complexidade: média

### Critérios de aceite da fase 3

- [ ] CA3.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0; `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` também. (comando)
- [ ] CA3.2 — `pnpm test:e2e` sai com código 0 com os testes `opens the expenses page and lists only the spending` e `goes back to the balances page` em `e2e/expenses.spec.ts`, além dos de `e2e/sync.spec.ts` e `e2e/login-and-balances.spec.ts`; `e2e/expenses.spec.ts` contém `test.describe.configure({ mode: 'serial' })`. (comando, estrutural)
- [ ] CA3.3 — `src/features/expenses/components/pagination.tsx` exporta `Pagination({ page, pages, total, isFetching, onChange }: { page: number; pages: number; total: number; isFetching: boolean; onChange: (page: number) => void })`, contém `<nav aria-label="Paginação"`, os textos "Página ", " de ", " gasto", " gastos", "Anterior" e "Próxima", e os dois botões são `<Button variant="secondary"` com `disabled` ligado a `isFetching`. (estrutural)
- [ ] CA3.4 — `expenses-list.tsx` usa `setSearchParams` de `useSearchParams`, chama `setSearchParams({ page: String(pages) }, { replace: true })` dentro de um `useEffect` e passa `isPlaceholderData` como `isFetching` para `<Pagination`; a chamada de `onChange` não usa `replace`; `<Pagination` só é renderizado com `total > 0`. (estrutural)
- [ ] CA3.5 — Piso visual, lido no código: o `<nav>` de `pagination.tsx` usa as classes de "Paginação" do `docs/design.md` (`flex-wrap`, `justify-between`, `gap-4`) e o texto usa `text-sm text-gray-600`; nenhum arquivo em `src/features/expenses/` contém `style={{`, `<a href` ou `!important`. (estrutural)
- [ ] CA3.6 — Em `?page=9` com 45 gastos, a URL vira `?page=3` e a lista mostra "Página 3 de 3 · 45 gastos" (`falls back to the last page when the URL is past the end`); ao clicar em "Próxima" a URL vira `?page=2` e a API é chamada com `page=2` (`"Próxima" moves to page 2 in the URL and in the API`); sem sessão, `/expenses` cai em "Entrar" (`redirects to the login page without a session`). (comportamental)
- [ ] CA3.7 — Os testes nomeados em T3.3 existem nos arquivos indicados; `npx vitest run --coverage` reporta ≥ 80% de linhas em `src/features/expenses/components/pagination.tsx` e `src/features/expenses/components/expenses-list.tsx`. (comando)

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
