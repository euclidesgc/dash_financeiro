# SPEC 003 — lista de gastos

Terceira fatia da SPA. Acrescenta a página "Gastos" (`/app/expenses`), uma lista paginada de todos os lançamentos de saída de todas as contas e cartões, e a navegação entre "Saldos" e "Gastos" no cabeçalho do app. É a fatia base das 004-007 (ordenar, filtrar por período, por conta, buscar por texto): elas acrescentam parâmetros ao mesmo endpoint e controles à mesma tela.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/queries/spending.py` · `SPENDING = "amount_cents < 0 AND is_transfer = 0 AND is_refund = 0 AND refunded_by IS NULL"` — o único predicado de "gasto" do projeto (invariante 25). Toda consulta de gasto lê essa string; a tela Jinja `/gastos` (`app/routers/spending.py` → `app/queries/axes.py`) já a usa. **A fatia não reescreve a regra: importa `SPENDING`.**
- `transactions` (migrações `001`, `003`, `011`): `date` (`YYYY-MM-DD`), `description`, `amount_cents` (centavos, negativo = saída, já normalizado na ingestão — norma 22), `category` (nome cru da Pluggy, ex.: `"Shopping"`), `payee` (descrição normalizada, preenchida na pós-carga por `app/taxonomy/classify.py::_fill_payees`), `merchant_name`, `merchant_legal_name`, `receiver_name`, `account_id → accounts(id)`. `accounts`: `name`, `institution`, `type` (`BANK` | `CREDIT`).
- Rótulo da categoria em pt-BR: **não está no banco** (`categories` tem só `name`); vem de `app/taxonomy/seed.json` por `app.taxonomy.seed.category_labels()` (`{"Shopping": "Compras", …}`), como o Jinja já faz (`LABELS` em `spending.py`).
- Nome de quem recebeu: `app.payees.names.labels(conn)` devolve `{payee: nome}` só para os recebedores que têm nome melhor que a descrição normalizada (apelido do dono > nome fantasia da Pluggy > nome consultado por CNPJ > razão social); quem não tem fica fora do mapa. É exatamente o "quando houver" do R4.
- SPA: `src/lib/api-client.ts` (`apiRequest`, `ApiError`), `src/lib/auth.tsx` (`ProtectedRoute`), `src/app/router.tsx` (`routes` exportado, `basename: '/app/'`), `src/config/paths.ts`, `src/components/ui/{button,alert}.tsx`, `src/utils/format-money.ts`, receita "Link de navegação" já no `docs/design.md`, MSW em `src/testing/mocks`, e2e com `scripts/e2e-backend.sh`.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `AppHeader` (novo, compartilhado) tem `<nav>` com `NavLink` para `paths.dashboard` ("Saldos") e `paths.expenses` ("Gastos"); o ativo recebe `aria-current="page"` (padrão do `NavLink`) e o estilo de ativo da receita nova "Navegação do cabeçalho". `dashboard.tsx` passa a usar `AppHeader`. |
| R2 | `GET /api/transactions/expenses` lê `transactions LEFT JOIN accounts` com `WHERE {SPENDING} ORDER BY t.date DESC, t.id DESC` (`app/queries/expenses.py`). Nenhum filtro por conta: todas entram. |
| R3 | `LIMIT ? OFFSET ?` com `page_size` (padrão 20) e `(page - 1) * page_size`; `total` por `SELECT count(*) FROM transactions WHERE {SPENDING}`. `Pagination` mostra "Página {page} de {pages}", "{total} gasto(s)", botões "Anterior" e "Próxima" (`disabled` na primeira e na última página). `page` vive na URL (`?page=N`). |
| R4 | Cada `ExpenseItem` mostra `formatDate(date)` (dd/mm/aaaa), `description`, `payee_name` quando não nulo, "{account_name} · {account_institution}", selo com `category` ou "Sem categoria", e `formatMoney(amount_cents)` pela receita "Valor monetário" (negativo em `text-red-700`; o sinal é o do valor em centavos, como na base). |
| R5 | O predicado é `SPENDING` importado de `app/queries/spending.py` — `amount_cents < 0` (só saídas), `is_transfer = 0` (transferência entre contas próprias), `is_refund = 0 AND refunded_by IS NULL` (o estorno e o lançamento estornado). Entradas (`amount_cents > 0`) nunca passam. Teste de API ingere os quatro casos e confere que só o gasto aparece. |
| R6 | `useExpenses(page).isPending` mostra a receita "Carregando": "Carregando gastos…" (`role="status"`). |
| R7 | `total === 0` mostra a receita "Vazio": "Nenhum gasto registrado ainda."; sem paginação. |
| R8 | `isError` mostra `Alert` "Não foi possível carregar os gastos." com ação "Tentar de novo" que chama `refetch()`. |
| R9 | A rota `/expenses` é filha de `ProtectedRoute` no `router.tsx` (401 em `/api/auth/me` → `Navigate` para `/app/login`); no servidor o guard já devolve 401 para `/api/*` sem sessão. |

## Decisões técnicas

### D1 — "Gasto" é o predicado `SPENDING`, importado, nunca copiado

- Escolha: `app/queries/expenses.py` monta `WHERE {SPENDING}` a partir de `app.queries.spending.SPENDING`, como `axes.py` e `payees/names.py` já fazem. A lista da SPA e o painel Jinja concordam por construção; se a regra mudar (fatia 015, "marcar não-gasto"), muda num lugar.
- Alternativa descartada: escrever `amount_cents < 0 AND is_transfer = 0 …` na nova consulta — motivo: a segunda cópia é a que se esquece; o comentário em `spending.py` diz isso com todas as letras.

### D2 — Paginação, junção e ordem em SQL; rótulos de categoria e recebedor resolvidos no módulo de consulta

- Escolha: `list_expenses(conn, *, page, page_size) -> ExpensesPage` (dataclass com `items: list[dict[str, Any]]`, `total: int`). SQL:
  ```sql
  SELECT t.id, t.date, t.description, t.payee, t.category, t.amount_cents,
         a.name AS account_name, a.institution AS account_institution, a.type AS account_type
  FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id
  WHERE {SPENDING} ORDER BY t.date DESC, t.id DESC LIMIT ? OFFSET ?
  ```
  e `SELECT count(*) FROM transactions WHERE {SPENDING}`. O `LEFT JOIN` segue `axes.py`: uma conta ausente não some com o gasto. Depois do `fetchall`, o módulo troca `category` pelo rótulo de `category_labels()` (nome cru desconhecido fica como está; `NULL`/`''` vira `None`) e acrescenta `payee_name = labels(conn).get(payee)`. Ambos são mapas em memória — o rótulo de categoria não existe no banco (só no seed) e a precedência de nome de recebedor é Python já testado; reescrevê-los em SQL seria duplicar lógica. O router não toca em SQL nem em mapa (norma 30).
- Alternativa descartada: devolver `category` cru e mapear no cliente — motivo: o cliente teria de baixar o seed inteiro; o rótulo é dado do servidor.
- Alternativa descartada: `OFFSET` por cursor (`date, id`) — motivo: a tela pede "Página X de Y" e pular direto; cursor não dá número de página. A base tem poucos milhares de linhas; `OFFSET` é barato aqui.

### D3 — Contrato JSON

- `GET /api/transactions/expenses?page=1&page_size=20` · 200 `{"items": [{"id": int, "date": "YYYY-MM-DD", "description": str|null, "payee_name": str|null, "account_name": str|null, "account_institution": str|null, "account_type": "BANK"|"CREDIT"|null, "category": str|null, "amount_cents": int}], "page": int, "page_size": int, "total": int}`. Ordem: `date DESC, id DESC`. Página além da última devolve `items: []` com o `total` certo (não é erro: a tela corrige o `page` para o último válido).
- Validação na dependência (norma 32): `page: Annotated[int, Query(ge=1)] = 1`, `page_size: Annotated[int, Query(ge=1, le=100)] = 20`; fora disso o FastAPI responde 422. 401 sem sessão (guard).
- Router `app/routers/transactions.py`, prefixo `/api/transactions`, rota `def` (SQLite é bloqueante — norma 31, mesma forma dos routers 001/002). Modelos Pydantic `Expense`, `ExpensesResponse`; o `/openapi.json` gerado é o contrato (norma 3). Domínio `transactions` porque a fatia 016 ("entradas") entra no mesmo router.
- Alternativa descartada: 404 para página além da última — motivo: o total muda a cada sincronização; uma URL guardada com `?page=9` não pode virar erro.

### D4 — A página atual mora na URL (`?page=N`), não em estado local

- Escolha: `ExpensesList` lê `page` com `useSearchParams`; valor ausente, não numérico ou `< 1` vale 1; ao trocar de página escreve `?page=N` (sem `replace`, para "voltar" do navegador funcionar). Se a resposta vier com `page > pages` (e `total > 0`), o componente navega para a última página com `replace`. `expensesQueryOptions(page)` usa `queryKey: ['expenses', { page }]` e `placeholderData: keepPreviousData` para a lista não piscar "Carregando" a cada troca; `isPlaceholderData` desabilita os botões durante a busca.
- Alternativa descartada: `useState(page)` — motivo: recarregar ou compartilhar a página perderia a posição; e as fatias 005-007 vão pôr período, conta e texto na mesma URL.

### D5 — Cabeçalho do app vira componente compartilhado com fatia de ação

- Escolha: `src/components/layouts/app-header.tsx` exporta `AppHeader({ userLogin, action }: { userLogin?: string; action?: ReactNode })`: nome do painel, `<nav aria-label="Principal">` com os dois `NavLink`, e à direita `userLogin` + `action`. O `LogoutButton` é da feature `auth`, e compartilhado não importa de feature (`project-structure`): a rota passa `action={<LogoutButton />}`. Vai para o compartilhado porque duas rotas o usam. Nome da pasta segue `project-structure` (`components/layouts/`).
- Alternativa descartada: repetir o `<header>` em `expenses.tsx` — motivo: dois cabeçalhos divergem no primeiro ajuste; o `NavLink` ativo precisa existir nos dois.

### D6 — Data só de dia formatada sem `Date`

- Escolha: `src/utils/format-date.ts` · `formatDate(iso: string): string` divide `YYYY-MM-DD` e monta `dd/mm/aaaa`; entrada que não casa com o padrão volta como veio. `new Date('2026-08-01')` é UTC e vira 31/07 em fuso negativo — o bug clássico.
- Alternativa descartada: reusar `formatDateTime` — motivo: mostra hora e sofre o deslocamento de fuso.

### D7 — Lista responsiva em vez de `<table>`

- Escolha: `<ul>` com a receita "Lista" e uma receita nova "Linha de lançamento" (duas colunas: identificação à esquerda, número à direita). Seis campos numa `<table>` não cabem em 360px sem rolagem horizontal (piso da `interface-design`). A fatia 004 (ordenar) põe os controles acima da lista, não em cabeçalho de coluna.
- Alternativa descartada: `<table>` com `overflow-x-auto` — motivo: rolagem horizontal no celular é o que o piso proíbe.

### D8 — Feature `expenses` separada; `Pagination` nasce nela

- Escolha: `src/features/expenses/{api,types,components}`; zona nova no `eslint.config.js`. `Pagination` fica em `features/expenses/components/` até a segunda lista paginada (016 "entradas") — aí sobe para `components/ui/` na mesma tarefa.
- Alternativa descartada: pôr `Pagination` já em `components/ui/` — motivo: um consumidor só; `project-structure` manda esperar o segundo.

### D9 — O e2e nasce com lançamentos no banco

- Escolha: `scripts/e2e-backend.sh` passa a ingerir `tests/data/e2e_transactions.json` (três linhas na conta `acc-fixture-1`: um gasto "MERCADO DO BAIRRO" de −R$ 84,90 em 2026-09-02, uma transferência entre contas próprias "TED PARA POUPANCA" de −R$ 500,00 com `eh_transferencia: true`, uma entrada "SALARIO" de +R$ 6.000,00). `sync_runs` continua apagada depois do bootstrap (o `sync.spec.ts` ainda começa em "Nunca atualizado"). A jornada: login → link "Gastos" → `<h1>` "Gastos" → "MERCADO DO BAIRRO" visível, "TED PARA POUPANCA" e "SALARIO" ausentes → "Página 1 de 1" e "1 gasto".
- Alternativa descartada: depender do `sync.spec.ts` ter rodado antes — motivo: a ordem entre arquivos de spec não é garantida.

## Interface

Receitas do `docs/design.md` usadas: contêiner de página, título de página, texto de apoio, lista, selo de status (`bg-gray-100 text-gray-700`), botão secundário, link de navegação, carregando, vazio, erro (via `Alert`), valor monetário, cabeçalho de app.

Receitas novas a acrescentar em "Padrões acrescentados pelas entregas":

| Padrão | Classes | Fatia |
|---|---|---|
| Navegação do cabeçalho | `<nav aria-label="Principal" className="flex items-center gap-4">`; `NavLink` com `text-sm font-medium underline-offset-4 hover:underline`; ativo (`aria-current="page"`) `text-gray-900 underline`; inativo `text-gray-600` | 003 |
| Linha de lançamento | item da receita "Lista" com `items-start`; esquerda `min-w-0 flex-1` empilhando `font-medium truncate` (descrição), `text-sm text-gray-600 truncate` (recebedor, conta); direita `flex shrink-0 flex-col items-end gap-1` com `text-sm text-gray-600 tabular-nums` (data), selo, valor monetário | 003 |
| Paginação | `<nav aria-label="Paginação" className="mt-6 flex flex-wrap items-center justify-between gap-4">`; texto `text-sm text-gray-600`; dois botões secundários | 003 |

### Cabeçalho de app (todas as rotas protegidas)

- Esquerda: "dash_financeiro" (`font-medium text-gray-900`) e, ao lado, a navegação do cabeçalho: "Saldos" (→ `/app/`) e "Gastos" (→ `/app/expenses`); o link da rota atual marcado.
- Direita: login do usuário em `text-gray-600` e o botão "Sair" (passado pela rota).
- Em 360px a linha quebra (`flex-wrap`, `gap-4`); nada sai da tela.

### Tela: Gastos (`/app/expenses`)

- Título do documento: "Gastos · dash_financeiro".
- Contêiner de página:
  - `<h1>` "Gastos"
  - Texto de apoio: "Todos os gastos das suas contas e cartões, do mais recente ao mais antigo."
  - Carregando (`role="status"`, só na primeira busca; nas trocas de página a lista anterior fica visível com os botões desabilitados): "Carregando gastos…"
  - Vazio: "Nenhum gasto registrado ainda."
  - Erro (`Alert`, `role="alert"`): "Não foi possível carregar os gastos." + "Tentar de novo".
  - Com dados: lista (receita "Lista" + "Linha de lançamento"); cada linha:
    - esquerda: descrição (`font-medium truncate`; sem descrição mostra "Sem descrição"); abaixo, nome de quem recebeu (`text-sm text-gray-600 truncate`), só quando `payee_name` não é nulo; abaixo, "{account_name} · {account_institution}" (`text-sm text-gray-600 truncate`; parte nula omitida; ambas nulas mostra "Conta desconhecida").
    - direita: data "dd/mm/aaaa"; selo com o rótulo da categoria ou "Sem categoria"; valor pela receita "Valor monetário" (negativo em vermelho, ex.: "-R$ 84,90").
  - Paginação (receita nova), só quando `total > 0`:
    - esquerda: "Página {page} de {pages} · {total} gasto" / "{total} gastos" (ex.: "Página 1 de 3 · 45 gastos").
    - direita: botão secundário "Anterior" (`disabled` em `page === 1` ou enquanto busca) e "Próxima" (`disabled` em `page === pages` ou enquanto busca).

### Tela: Saldos (`/app/`)

- Só o cabeçalho muda: passa a ser o `AppHeader` com a navegação; "Saldos" marcado como ativo. Nada mais se altera.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `app/queries/expenses.py` | `ExpensesPage` (dataclass `items`, `total`), `list_expenses(conn, *, page, page_size)`: SQL de D2 com `SPENDING` importado, `count(*)`, rótulo de categoria via `category_labels()`, `payee_name` via `app.payees.names.labels(conn)` | — |
| criar | `app/routers/transactions.py` | `router = APIRouter(prefix="/api/transactions")`; `GET /expenses` com `page`/`page_size` em `Annotated[int, Query(...)]`; modelos `Expense`, `ExpensesResponse`; só traduz HTTP | `api-requests` |
| alterar | `app/main.py` | inclui `transactions.router` | — |
| criar | `tests/data/e2e_transactions.json` | três lançamentos de D9 no formato consolidado (`id`, `data`, `conta_id`, `descricao`, `valor`, `eh_transferencia`, `eh_estorno`, `estornada_por`, …) | `e2e-testing` |
| alterar | `scripts/e2e-backend.sh` | `ingest(..., transactions=load_transactions("tests/data/e2e_transactions.json"), ...)` | `e2e-testing` |
| criar | `tests/test_expenses_api.py` | sem sessão 401; base vazia `{"items": [], "page": 1, "page_size": 20, "total": 0}`; ingere gasto, transferência, estorno (+ lançamento estornado via `estornada_por`) e entrada → só o gasto sai e `total == 1`; ordem `date DESC, id DESC` com três gastos; 25 gastos → página 1 com 20, página 2 com 5, `total 25`; página 3 → `items: []`, `total 25`; `page=0` e `page_size=101` → 422; `merchant_name` preenchido vira `payee_name` (após `_fill_payees`/pós-carga) e sem nome vira `null`; `category "Shopping"` vira o rótulo do seed e `category ""` vira `null`; conta com `name` e `institution` do fixture | `api-requests`, `unit-testing` |

### Ferramental (raiz)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `eslint.config.js` | zona `{ target: './src/features/expenses', from: './src/features', except: ['./expenses'] }` | `project-structure` |
| alterar | `docs/design.md` | três receitas novas (seção Interface) | `interface-design` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/config/paths.ts` | `expenses: '/expenses'` | `routing` |
| alterar | `src/app/router.tsx` | rota `paths.expenses` → `<ProtectedRoute><ExpensesRoute /></ProtectedRoute>` | `routing` |
| criar | `src/app/routes/expenses.tsx` | `ExpensesRoute`: título do documento, `AppHeader` com `userLogin` e `action={<LogoutButton />}`, `<h1>` "Gastos", texto de apoio, `<ExpensesList />` | `routing`, `interface-design` |
| alterar | `src/app/routes/dashboard.tsx` | troca o `<header>` inline por `<AppHeader userLogin={data?.login} action={<LogoutButton />} />` | `routing` |
| criar | `src/components/layouts/app-header.tsx` | `AppHeader` (D5): nome, `<nav>` com `NavLink` "Saldos" e "Gastos", login e ação | `ui-components`, `routing`, `interface-design` |
| criar | `src/components/layouts/__tests__/app-header.test.tsx` | em `/` "Saldos" tem `aria-current="page"` e "Gastos" não; em `/expenses` o inverso; `action` renderiza | `component-testing` |
| criar | `src/utils/format-date.ts` | `formatDate(iso: string): string` (D6) | `unit-testing` |
| criar | `src/utils/__tests__/format-date.test.ts` | `'2026-08-01' → '01/08/2026'`; entrada fora do padrão volta como veio | `unit-testing` |
| criar | `src/features/expenses/types/expense.ts` | `Expense { id: number; date: string; description: string \| null; payee_name: string \| null; account_name: string \| null; account_institution: string \| null; account_type: 'BANK' \| 'CREDIT' \| null; category: string \| null; amount_cents: number }`, `ExpensesResponse { items: Expense[]; page: number; page_size: number; total: number }` | — |
| criar | `src/features/expenses/api/get-expenses.ts` | `getExpenses(page)` (`/api/transactions/expenses?page=N&page_size=20`, `page_size` constante `PAGE_SIZE = 20`), `expensesQueryOptions(page)` (`['expenses', { page }]`, `placeholderData: keepPreviousData`), `useExpenses(page)` | `api-requests` |
| criar | `src/features/expenses/components/expenses-list.tsx` | lê/escreve `?page` (D4), quatro estados, lista de `ExpenseItem`, `Pagination`, correção de página além da última | `interface-design`, `error-handling`, `client-state`, `component-robustness` |
| criar | `src/features/expenses/components/expense-item.tsx` | uma linha (receita "Linha de lançamento"): descrição, recebedor, conta, data, selo de categoria, valor | `interface-design`, `component-robustness` |
| criar | `src/features/expenses/components/pagination.tsx` | `Pagination({ page, pages, total, isFetching, onChange })`: texto e dois `Button variant="secondary"` | `ui-components`, `interface-design` |
| criar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | carregando; vazio; erro + "Tentar de novo" refaz a busca; com dados mostra descrição, recebedor, conta, "01/08/2026", selo "Compras", "Sem categoria", valor negativo em `text-red-700`; "Página 1 de 3 · 45 gastos"; "Anterior" desabilitado na 1; "Próxima" leva a `?page=2` e chama a API com `page=2`; `?page=9` com 3 páginas cai na 3 (MSW) | `component-testing`, `api-mocking` |
| alterar | `src/testing/mocks/handlers.ts` | `fakeExpenses` (gerador determinístico: 45 gastos, com um sem `payee_name`, um sem `category`), handler `GET /api/transactions/expenses` que lê `page` e `page_size` da URL e fatia a lista | `api-mocking` |
| criar | `src/app/__tests__/expenses.test.tsx` | integração: sem sessão em `/expenses` vai para "Entrar"; depois do login, clicar em "Gastos" chega em `<h1>` "Gastos" com "Gastos" marcado `aria-current`; clicar em "Saldos" volta a "Saldos de hoje" | `integration-testing`, `api-mocking` |
| criar | `e2e/expenses.spec.ts` | jornada de D9 contra o FastAPI | `e2e-testing` |

## Estimativa de tamanho

Jornadas: 1 (abrir "Gastos" e folhear a lista) · Telas novas: 1 (Gastos) · Linhas alteradas (sem testes): ~115 Python (`queries/expenses.py` ~55, `routers/transactions.py` ~45, `main.py` 2, script + fixture ~15) + ~330 em `src/` (header ~40, rota ~30, paths/router ~10, tipos ~20, api ~20, lista ~85, item ~50, paginação ~45, `format-date` ~10, mocks ~20) + ~15 de config/doc · Fases previstas: 3 (endpoint + testes de API; cabeçalho compartilhado + rota + lista com estados; paginação + integração + e2e).

O sinal 4 (>400 linhas sem testes) dispara por pouco (~460). Mantida inteira por decisão do dono: é a fatia base das 004-007, e cortar paginação ou cabeçalho deixaria uma lista que não serve sozinha (20 gastos sem sair da primeira página) ou uma tela sem como chegar nela.

## Dívida encontrada

- `app/routers/spending.py` (Jinja) monta SQL direto (`_CROSSINGS`, `_CANDIDATES`, `_TARGET`, …) e chama `correct_payee`, que dá `commit` — viola a norma 30, como já registrado na SPEC 001 para os demais routers Jinja. Fora do escopo; item de roadmap existente.
- O rótulo em pt-BR da categoria mora só em `app/taxonomy/seed.json`, não na tabela `categories`; toda consulta que precisa do rótulo o resolve em Python (`category_labels()`), o que impede ordenar ou filtrar por rótulo em SQL. A fatia 004 (ordenar por categoria) vai esbarrar nisso: ou ordena pelo nome cru, ou a migração passa a guardar o rótulo. Registrar como item antes da 004.
- A pós-carga (`_fill_payees`, classificação) roda em `synchronise`, não em `ingest`: uma base carregada só por `ingest` (testes, bootstrap do e2e) fica com `payee` nulo e sem `group_id`. Não afeta esta fatia (`payee_name` nulo é caso previsto), mas todo teste que precisar de nome de recebedor precisa chamar a pós-carga à mão.
