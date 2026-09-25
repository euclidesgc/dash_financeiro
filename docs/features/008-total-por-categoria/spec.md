# SPEC 008 — total por categoria

Oitava fatia da SPA. Acrescenta à página "Gastos" (`/app/expenses`), entre a barra de controles e a lista, um bloco "Por categoria" com uma linha por categoria (rótulo, quantidade, total), ordenado do maior total para o menor, obedecendo ao mesmo período, conta e busca da lista. Um endpoint novo, `GET /api/transactions/expenses/by-category`, agrupa em SQL reaproveitando `_FROM` e `_where` de `app/queries/expenses.py`, então o total do bloco e o do resumo da lista saem do mesmo predicado por construção.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/queries/expenses.py` · `_FROM` (junções com `accounts` e as duas de `payee_names`), `_where(date_from, date_to, account_id, search) -> (sql, params)` sobre `SPENDING`, `_TOTAL` (`count(*)`, `coalesce(sum(t.amount_cents), 0)`), `list_expenses(...)`; o rótulo pt-BR vem de `category_labels()` em Python; a ordenação por categoria já trata `t.category = ''` como nulo.
- `app/queries/spending.py` · `SPENDING` e `total_spending_cents(conn, start, end)` com predicado de data próprio (dívida 025).
- `app/routers/transactions.py` · `router = APIRouter(prefix="/api/transactions")`; `GET /expenses` valida `to < from` (422 com "A data final precisa ser igual ou posterior à inicial."), normaliza `q` (`strip`, menos de 2 caracteres → `None`), abre `connect()` em `try/finally`.
- `app/taxonomy/seed.py` · `category_labels() -> dict[str, str]` (chave → rótulo). O seed tem a chave "Não classificado" com rótulo "Sem categoria".
- Ingestão grava `categoria=""` como `''` em `t.category` (teste `test_the_category_comes_back_as_the_seed_label`), e a lista devolve `None` nesse caso.
- `src/features/expenses/types/expense.ts` · `ExpensesQuery { page, sort, order, from, to, account, search }`.
- `src/features/expenses/api/get-expenses.ts` · `URLSearchParams` só com o não nulo; `queryOptions` + `useQuery`; `placeholderData: keepPreviousData`; chave `['expenses', query]`.
- `src/features/expenses/components/expenses-list.tsx` · lê `page/sort/order/period/account/search` da URL; `accountKnown` zera a conta desconhecida antes de chamar a API; `controls` (barra) é renderizado fora dos ramos de estado; os quatro estados devolvem `{controls}` seguido do conteúdo.
- `src/components/ui/alert.tsx` · `Alert({ message, action })` com `role="alert"` e `Button variant="danger"`. `src/components/ui/button.tsx` · `Button` com `variant`, `min-h-10`, `type="button"`.
- `src/utils/format-money.ts` · `formatMoney(cents)`; `Pagination` mostra `formatMoney(Math.abs(totalCents))` no resumo "N gastos · R$ X no período".
- `src/testing/mocks/handlers.ts` · `fakeExpenses` (45 gastos: 42 "Compras" somando -948490, 1 "Alimentação" -44000 (id 44), 1 sem categoria -43000 (id 43), 1 "Transporte" -42000 (id 42)); `foldText`; handler de `/api/transactions/expenses` com filtro por `from/to/account_id/q`.
- Testes de componente e e2e contam `getAllByRole('listitem')` / `getByRole('listitem')` na página inteira: qualquer `<li>` novo fora da lista de gastos quebra essas contagens.
- `tests/data/e2e_transactions.json` · em 2026-08: "FARMACIA CENTRAL" -45,00 (`Health`, `acc-fixture-2`) e "AÇOUGUE SÃO JORGE" -60,00 (`Groceries`, `acc-fixture-1`); em 2026-09: "MERCADO DO BAIRRO" -84,90 (`Groceries`) e "POSTO CENTRAL" -150,00 (`Housing`). Rótulos no seed: `Groceries` → "Supermercado", `Housing` → "Casa", `Health` → "Saúde".

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `CategoryTotals` (novo, na feature `expenses`) é montado em `ExpensesList` logo depois de `controls`, antes de qualquer ramo de estado da lista; renderiza `<section>` com `<h2>` "Por categoria" e uma `<table>` com uma linha por grupo devolvido por `GET /api/transactions/expenses/by-category` (D1, D4, D5). |
| R2 | Cada `<tr>` mostra `label`, "`count` gasto(s)" e `formatMoney(Math.abs(total_cents))`. O endpoint recebe `from, to, account_id, q` com a mesma normalização do `GET /expenses` e passa por `_where(...)`, o mesmo predicado da lista (D1, D3). |
| R3 | `ORDER BY abs(total) DESC, category IS NULL, category` no SQL; "Sem categoria" é só mais um grupo (`NULLIF(t.category, '')` nulo), sem posição fixa (D1, D2). |
| R4 | O agrupamento usa `_FROM` + `_where` — o mesmo `FROM/WHERE` de `_TOTAL` — então `sum(total_cents dos grupos) == total_cents da lista` por construção; a resposta ainda devolve `total_cents` (soma dos grupos) para o teste de API afirmar a igualdade contra `GET /expenses` (D1, D3). |
| R5 | A chave da query é `['expenses', 'by-category', { from, to, account, search }]` com exatamente os valores que `ExpensesList` já passa a `useExpenses` (inclusive `account` zerado quando desconhecido); mudar qualquer filtro na URL troca a chave e refaz a chamada sem ação do usuário (D4). |
| R6 | `CategoryTotals` guarda `expanded` em `useState(false)`; mostra `groups.slice(0, 8)` quando não expandido e há mais de 8; abaixo da tabela, botão secundário "Mostrar todas (N)" (N = `groups.length`) que vira "Mostrar menos" depois de aberto. Com 8 ou menos, sem botão (D5). |
| R7 | `isPending` → `<p role="status">` "Carregando totais por categoria…" no lugar do bloco (D5). |
| R8 | `isError` → `Alert` "Não foi possível carregar os totais por categoria." com "Tentar de novo" (`refetch`). É uma query separada da lista, com estado próprio: a lista segue nos seus quatro estados independentemente (D4, D5). |
| R9 | `groups.length === 0` → o componente devolve `null` (nem título nem tabela). Como o predicado é o mesmo, a lista vazia e o bloco ausente coincidem (D5). |
| R10 | As linhas são `<td>` com texto; nenhum `<button>`, `<Link>` ou `onClick` nas linhas (D5). |

## Decisões técnicas

### D1 — `sum_by_category` em `app/queries/expenses.py`, sobre `_FROM` e `_where`

- Escolha: `@dataclass(frozen=True) class CategoryTotal: category: str | None; label: str; count: int; total_cents: int` e `sum_by_category(conn, *, date_from, date_to, account_id, search) -> list[CategoryTotal]` no mesmo módulo de `list_expenses`. SQL: `SELECT NULLIF(t.category, '') AS category, count(*) AS count, coalesce(sum(t.amount_cents), 0) AS total {_FROM} {where} GROUP BY NULLIF(t.category, '') ORDER BY abs(total) DESC, category IS NULL, category`, com `where, params = _where(date_from, date_to, account_id, search)`. O rótulo é resolvido em Python: `label = "Sem categoria" if category is None else category_labels().get(category, category)` — a mesma regra de `list_expenses` (chave fora do seed devolve a própria chave). Cálculo determinístico em SQL, nunca IA (norma 23); junção e agregação em `app/queries` (norma 33).
- Alternativa descartada: somar em Python a partir de `list_expenses` com `page_size` grande — motivo: a lista é paginada a 100 no máximo; agregação é do SQL.
- Alternativa descartada: criar o agrupamento em `app/queries/spending.py` — motivo: o predicado de busca (`fold`, `_PAYEE_NAME_SQL`) vive em `expenses.py`; mover só o agrupamento duplicaria `_where` ou o obrigaria a ir junto, que é a dívida 025 inteira, não esta fatia. Fica registrado em "Dívida encontrada".
- Alternativa descartada: `GROUP BY t.category` cru — motivo: a ingestão grava `''` para "sem categoria"; `''` e `NULL` virariam dois grupos "Sem categoria", contrariando a lista, que já trata os dois como um.

### D2 — Desempate e chave de linha

- Escolha: empate de `abs(total)` decide por `category IS NULL` (nulo por último entre os iguais) e depois por `category` (chave, ordem binária) — ordem estável para os testes. No front, a `key` de cada linha é `group.category ?? ''`, não `label`: a chave "Não classificado" do seed tem rótulo "Sem categoria" e, se aparecer junto com gastos sem categoria, são duas linhas legítimas de mesmo rótulo (a lista também mostra "Sem categoria" nas duas). Comportamento aceito e documentado.
- Alternativa descartada: desempatar pelo rótulo pt-BR — motivo: exigiria o `CASE ... WHEN` de `_category_rank_clause` numa consulta de agregação por um caso raro (dois totais idênticos ao centavo).

### D3 — Endpoint `GET /api/transactions/expenses/by-category` no router existente, com validação compartilhada

- Escolha: em `app/routers/transactions.py`, duas funções privadas extraídas do handler atual e usadas pelos dois endpoints: `_date_bounds(from_, to) -> tuple[str | None, str | None]` (levanta o 422 "A data final precisa ser igual ou posterior à inicial." e devolve ISO) e `_search_term(q) -> str | None` (`strip`, menos de 2 caracteres → `None`). Handler `expenses_by_category(from_, to, account_id, q)` com os mesmos `Annotated[..., Query(...)]` de `expenses` (sem `page/page_size/sort/order`), `sum_by_category(...)` dentro de `try/finally: conn.close()`, resposta `CategoryTotalsResponse { groups: list[CategoryGroup], total_cents: int }` com `CategoryGroup { category: str | None, label: str, count: int, total_cents: int }` e `total_cents = sum(g.total_cents for g in groups)`. Rota declarada como `@router.get("/expenses/by-category")`; como `/expenses` não tem parâmetro de caminho, não há ambiguidade. O `/openapi.json` passa a listar o caminho com `from`, `to`, `account_id`, `q` (norma 3).
- Alternativa descartada: `GET /expenses?group_by=category` — motivo: mesma rota com duas formas de resposta; o cliente e o OpenAPI ficam ambíguos.
- Alternativa descartada: router novo `app/routers/categories.py` — motivo: é o mesmo domínio (`expenses`), mesmos filtros e mesma validação; um router por domínio (norma 29).
- Alternativa descartada: não devolver `total_cents` — motivo: custa uma soma e dá ao teste de API (R4) e ao leitor da resposta o total sem recalcular.

### D4 — Query separada, chave `['expenses', 'by-category', filtros]`, `keepPreviousData`

- Escolha: `src/features/expenses/api/get-category-totals.ts` · `CategoryTotalsQuery = Pick<ExpensesQuery, 'from' | 'to' | 'account' | 'search'>`; `getCategoryTotals(query)` monta `URLSearchParams` só com o não nulo (`from`, `to`, `account_id`, `q`) e chama `apiRequest<CategoryTotalsResponse>('/api/transactions/expenses/by-category?...')`; `categoryTotalsQueryOptions(query)` com `queryKey: ['expenses', 'by-category', query]` e `placeholderData: keepPreviousData`; `useCategoryTotals(query)`. O prefixo `['expenses']` faz qualquer invalidação da lista invalidar o bloco também. `ExpensesList` monta `{ from, to, account: accountKnown ? account : null, search }` uma vez e passa a `useExpenses` (espalhado com `page/sort/order`) e a `CategoryTotals` — os dois lêem o mesmo objeto de filtros.
- Alternativa descartada: embutir `groups` na resposta de `GET /expenses` — motivo: muda um contrato entregue e testado, obriga a lista a recalcular o agrupamento a cada troca de página (`page` não muda os grupos) e R8 exige que o erro de um não derrube o outro.
- Alternativa descartada: `useQueries` ou um hook combinado — motivo: dois `useQuery` com chaves derivadas do mesmo objeto já sincronizam por construção.

### D5 — `CategoryTotals` na feature, tabela, `useState` só para "Mostrar todas"

- Escolha: `src/features/expenses/components/category-totals.tsx` · `CategoryTotals({ query }: { query: CategoryTotalsQuery })`; chama `useCategoryTotals(query)`; `isPending` → carregando; `isError` → `Alert` com `refetch`; `data.groups.length === 0` → `null`; senão `<section className="mt-6" aria-labelledby={headingId}>` com `<h2 id={headingId}>` "Por categoria" e `<table aria-labelledby={headingId}>` (receita nova "Tabela de totais"): `<thead className="sr-only">` com "Categoria", "Gastos", "Total"; `<tbody>` com uma `<tr>` por grupo visível — `<td>` rótulo (`min-w-0 truncate`), `<td>` "N gasto"/"N gastos" (secundário, alinhado à direita), `<td>` `formatMoney(Math.abs(total_cents))` (valor monetário, alinhado à direita). `const [expanded, setExpanded] = useState(false)`; `visible = expanded ? groups : groups.slice(0, 8)`; se `groups.length > 8`, `Button variant="secondary"` abaixo da tabela com "Mostrar todas (N)" ou "Mostrar menos", `aria-expanded={expanded}`. O estado é efêmero de UI (`client-state`: não sobrevive a recarga por desenho, não muda o que a API devolve, não entra na URL). Valor exibido como `abs` porque o resumo da lista também mostra "R$ X no período" sem sinal, e o bloco é lido lado a lado com ele (R4).
- Alternativa descartada: `<ul>/<li>` — motivo: os testes existentes (componente e e2e) contam `listitem` na página inteira; a tabela é a semântica certa para três colunas alinhadas e não colide com essas contagens.
- Alternativa descartada: `expanded` na URL — motivo: não é filtro; um `?all=1` sobrevivendo a link e recarga só confunde.
- Alternativa descartada: montar `CategoryTotals` dentro de cada ramo de estado da lista — motivo: R8 pede independência; montado uma vez depois de `controls`, o bloco não some quando a lista está carregando ou em erro.
- Alternativa descartada: barra proporcional por categoria — motivo: fora de escopo do PRD ("gráfico ou visualização diferente de lista de linhas").

### D6 — Contrato JSON

- `GET /api/transactions/expenses/by-category?from=AAAA-MM-DD&to=AAAA-MM-DD&account_id=…&q=…` · todos opcionais, mesma semântica e validação de `GET /expenses` (`to < from` → 422; `q` curto → sem busca; `account_id` vazio → 422). Resposta 200: `{ "groups": [ { "category": "Groceries" | null, "label": "Supermercado", "count": 3, "total_cents": -14490 } ], "total_cents": -14490 }`. `total_cents` é negativo (dinheiro saindo, norma 22). `groups` ordenado por `abs(total_cents)` decrescente. Sem sessão → 401 como as demais rotas. Base vazia ou filtro sem gasto → `{ "groups": [], "total_cents": 0 }`.

## Interface

Receitas do `docs/design.md` usadas: contêiner de página, subtítulo (`h2`, com `mt-6` em vez de `mt-8` porque o bloco fica entre a barra e a lista, no espaçamento padrão entre blocos), valor monetário, botão secundário, carregando, erro. Receita nova a acrescentar ao `docs/design.md` nesta entrega:

| Padrão | Classes | Fatia |
|---|---|---|
| Tabela de totais | `<table className="mt-3 w-full text-sm">`; `<thead className="sr-only">`; `<tbody className="divide-y divide-gray-200">`; `<tr>` com `<td className="min-w-0 truncate py-2 text-gray-900">` (rótulo), `<td className="whitespace-nowrap py-2 pl-4 text-right text-gray-600 tabular-nums">` (contagem) e `<td className="whitespace-nowrap py-2 pl-4 text-right tabular-nums font-medium text-gray-900">` (total); botão secundário abaixo com `mt-3` | 008 |

### Tela: Gastos (`/app/expenses`)

De cima para baixo: título "Gastos" e texto de apoio (inalterados) → barra de controles (inalterada) → **bloco "Por categoria"** (novo) → lista de gastos e paginação (inalteradas).

- Bloco "Por categoria", com dados: `<h2>` "Por categoria"; tabela com uma linha por categoria, da maior para a menor: à esquerda o rótulo (ex.: "Supermercado", "Sem categoria"); à direita, em tom suave, "3 gastos" (ou "1 gasto"); mais à direita, em destaque, "R$ 144,90". Com mais de 8 categorias: só as 8 maiores e, abaixo, botão secundário "Mostrar todas (12)"; ao clicar, todas aparecem e o botão passa a "Mostrar menos". Nada na linha é clicável.
- Carregando (`role="status"`): "Carregando totais por categoria…" no lugar do bloco. Ao trocar filtro, o bloco anterior permanece até chegar o novo (`keepPreviousData`).
- Erro (`role="alert"`): "Não foi possível carregar os totais por categoria." + botão "Tentar de novo". A lista abaixo continua com o seu estado.
- Vazio: o bloco não aparece (nem o título). A lista mostra o vazio dela ("Nenhum gasto para esse filtro." / "Nenhum gasto registrado ainda.").
- Em 360px a tabela cabe nas três colunas: o rótulo trunca (`min-w-0 truncate`), contagem e total não quebram.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/queries/expenses.py` | `CategoryTotal` (dataclass) e `sum_by_category(conn, *, date_from, date_to, account_id, search)` com `GROUP BY NULLIF(t.category, '')` sobre `_FROM` + `_where`, ordem `abs(total) DESC, category IS NULL, category`, rótulo por `category_labels()` / "Sem categoria" (D1, D2) | — |
| alterar | `app/routers/transactions.py` | `_date_bounds(from_, to)` e `_search_term(q)` extraídos do handler atual; `CategoryGroup`, `CategoryTotalsResponse`; `GET /expenses/by-category` com `from`, `to`, `account_id`, `q` (D3, D6) | `api-requests` |
| alterar | `tests/test_expenses_api.py` | testes de `/api/transactions/expenses/by-category`: sem sessão → 401; base vazia → `groups == []`, `total_cents == 0`; três categorias com totais distintos vêm em ordem de `abs` decrescente com `label` do seed ("Compras") e `count` certo; `categoria=""` e categoria ausente caem num único grupo `category: null`, `label: "Sem categoria"`, ordenado pelo total como os demais (fica no meio quando o total manda); chave fora do seed devolve a própria chave como `label`; empate de total ordena nulo por último e depois pela chave; transferência e estorno não entram (`SPENDING`); `from`/`to` limitam; `account_id` limita; `q` limita e `q=a` é ignorado; `to < from` → 422; `account_id=` vazio → 422; **R4**: `sum(g["total_cents"])` e `total_cents` da resposta são iguais ao `total_cents` de `GET /expenses` com o mesmo `from/to/account_id/q`; `/openapi.json` lista o caminho com os quatro parâmetros opcionais | `api-requests`, `unit-testing` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/features/expenses/types/expense.ts` | `CategoryGroup { category: string \| null; label: string; count: number; total_cents: number }`, `CategoryTotalsResponse { groups: CategoryGroup[]; total_cents: number }`, `CategoryTotalsQuery = Pick<ExpensesQuery, 'from' \| 'to' \| 'account' \| 'search'>` (D4, D6) | — |
| criar | `src/features/expenses/api/get-category-totals.ts` | `getCategoryTotals(query)`, `categoryTotalsQueryOptions(query)` (chave `['expenses', 'by-category', query]`, `keepPreviousData`), `useCategoryTotals(query)` (D4) | `api-requests` |
| criar | `src/features/expenses/components/category-totals.tsx` | `CategoryTotals({ query })`: carregando, erro com "Tentar de novo", `null` quando vazio, tabela, "Mostrar todas (N)"/"Mostrar menos" com `useState` (D5) | `interface-design`, `client-state`, `error-handling`, `component-robustness` |
| criar | `src/features/expenses/components/__tests__/category-totals.test.tsx` | com handler próprio via `server.use`: mostra `<h2>` "Por categoria" e uma linha por grupo na ordem recebida com rótulo, "1 gasto"/"42 gastos" e `formatMoney(abs)`; `groups: []` → nada renderizado (nem o título); 8 grupos → sem botão; 12 grupos → 8 linhas e "Mostrar todas (12)"; clicar → 12 linhas e "Mostrar menos"; clicar de novo → 8; erro 500 → "Não foi possível carregar os totais por categoria." e "Tentar de novo" refaz e mostra a tabela; `role="status"` "Carregando totais por categoria…" enquanto pendente; `category: null` usa o `label` recebido e não quebra a `key`; chamada sai com `from`, `to`, `account_id`, `q` só quando não nulos | `component-testing`, `api-mocking` |
| alterar | `src/features/expenses/components/expenses-list.tsx` | objeto `filters = { from, to, account: accountKnown ? account : null, search }` compartilhado por `useExpenses({ page, sort, order, ...filters })` e `<CategoryTotals query={filters} />`, montado logo após `{controls}` em todos os ramos (extraído junto com `controls` num único fragmento `header`) (D4, D5) | `client-state`, `interface-design` |
| alterar | `src/testing/mocks/handlers.ts` | `filterExpenses(url)` extraído do handler atual (mesmo `from/to/account_id/q`) e reutilizado; handler `GET /api/transactions/expenses/by-category` que agrupa o resultado por `category` (chave = `category ?? null`, `label = category ?? 'Sem categoria'`), ordena por `abs` decrescente e devolve `{ groups, total_cents }` | `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | testes novos: com os dados padrão a tabela "Por categoria" mostra, nesta ordem, "Compras · 42 gastos · R$ 9.484,90", "Alimentação · 1 gasto · R$ 440,00", "Sem categoria · 1 gasto · R$ 430,00", "Transporte · 1 gasto · R$ 420,00" e nenhum botão "Mostrar todas"; `?account=acc-credit-1` → só "Compras" com a soma dos ids múltiplos de 3 e a chamada a `by-category` leva `account_id=acc-credit-1`; `?q=zzzz` → sem `<h2>` "Por categoria" e vazio "Nenhum gasto para esse filtro."; `by-category` 500 com `/expenses` 200 → alerta do bloco e a lista com 20 itens; "Próxima" não refaz `by-category` (contagem de chamadas); os `getAllByRole('listitem')` existentes continuam contando só a lista (a tabela não tem `li`) | `component-testing`, `api-mocking` |
| alterar | `e2e/expenses.spec.ts` | teste novo: login → `page.goto('/app/expenses?month=2026-08')` → `getByRole('heading', { level: 2, name: 'Por categoria' })` visível; `getByRole('table', { name: 'Por categoria' })` tem a linha "Supermercado" com "1 gasto" e "R$ 60,00" antes da linha "Saúde" com "R$ 45,00"; `getByRole('button', { name: /Mostrar todas/ })` ausente → `goto('/app/expenses?q=zzzz')` → título "Por categoria" ausente e "Nenhum gasto para esse filtro." visível | `e2e-testing` |
| alterar | `docs/design.md` | linha "Tabela de totais" na tabela de padrões acrescentados (fatia 008) | `interface-design` |

## Estimativa de tamanho

Jornadas: 1 (ver a composição do gasto por categoria) · Telas novas: 0 · Linhas alteradas (sem testes): ~70 Python (`queries/expenses.py` ~35, `routers/transactions.py` ~35) + ~180 em `src/` (tipos ~15, `get-category-totals.ts` ~30, `category-totals.tsx` ~95, `expenses-list.tsx` ~15, mocks ~25) + ~2 em `docs/design.md` · Fases previstas: 2 (endpoint com agrupamento em SQL + testes de API; `CategoryTotals`, query, mocks, testes de componente e e2e).

Nenhum sinal de "grande demais" dispara.

## Dívida encontrada

- Dívida 025 continua aberta e cresce um consumidor: o predicado de gasto com filtros (`_where`) vive em `app/queries/expenses.py` e é reutilizado por `list_expenses` e `sum_by_category` — os dois concordam por construção. `app/queries/spending.py:total_spending_cents` ainda monta o predicado de data por conta própria; a unificação (mover `_where` para `spending.py` e fazer `total_spending_cents` usá-lo) fica para o item 025 do roadmap, agora com três chamadores a migrar em vez de dois.
- Dívida 026 inalterada: `_PAYEE_NAME_SQL` (SQL) e `_chosen` (Python) seguem como duas fontes da precedência do nome do recebedor; esta fatia não toca nenhuma das duas.
- O `handler` de `/api/transactions/expenses` em `src/testing/mocks/handlers.ts` e o `spyOnExpensesRequests` de `expenses-list.test.tsx` duplicam o mesmo filtro (`filterForSpy`); esta fatia extrai `filterExpenses` nos mocks para o `by-category` usar, mas o teste continua com a cópia dele. Item de roadmap: o teste importar `filterExpenses` de `handlers.ts` e apagar `filterForSpy`.
