# SPEC 004 — ordenar gastos

Quarta fatia da SPA. Acrescenta à página "Gastos" (`/app/expenses`, fatia 003) a escolha do critério de ordenação (data, valor, categoria) e da direção, guardadas na URL e aplicadas em SQL antes da paginação. Nenhum arquivo novo de domínio: a fatia estende o endpoint, o hook e a lista que a 003 entregou.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/queries/expenses.py` · `list_expenses(conn, *, page, page_size) -> ExpensesPage`, SQL `_PAGE` com `WHERE {SPENDING} ORDER BY t.date DESC, t.id DESC LIMIT ? OFFSET ?` e `_TOTAL`; depois do `fetchall`, troca `category` (chave crua da Pluggy, ex.: `"Groceries"`) pelo rótulo de `app.taxonomy.seed.category_labels()` (`{"Groceries": "Supermercado", …}`, 79 entradas) e resolve `payee_name`.
- `app/routers/transactions.py` · `GET /api/transactions/expenses` com `page`/`page_size` em `Annotated[int, Query(...)]`, modelos `Expense` e `ExpensesResponse`; rota `def` (SQLite bloqueante).
- `src/features/expenses/api/get-expenses.ts` · `PAGE_SIZE`, `getExpenses(page)`, `expensesQueryOptions(page)` (`queryKey: ['expenses', { page }]`, `placeholderData: keepPreviousData`), `useExpenses(page)`.
- `src/features/expenses/components/expenses-list.tsx` · lê `?page` com `useSearchParams` (`readPage`), quatro estados, `ExpenseItem`, `Pagination`, correção de página além da última com `replace`.
- `src/app/routes/expenses.tsx` · `<h1>` "Gastos" e texto de apoio "Todos os gastos das suas contas e cartões, do mais recente ao mais antigo."
- `src/components/ui/button.tsx` · `Button` com `variant` `primary | secondary | danger`; receita "Campo de formulário" no `docs/design.md` (label + input).
- `src/testing/mocks/handlers.ts` · `fakeExpenses` (45 gastos; categorias "Compras", "Alimentação" e uma nula) e o handler de `/api/transactions/expenses` que só fatia por página.
- `tests/data/e2e_transactions.json` · três lançamentos (um único gasto, "MERCADO DO BAIRRO", `categoria: "Groceries"`); `e2e/expenses.spec.ts` já aceita "1 gasto" ou "2 gastos".

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `SortControls` (novo, na feature) renderiza `<label>` "Ordenar por" ligado a um `<select>` nativo com `<option>` "Data" (`date`), "Valor" (`amount`), "Categoria" (`category`). |
| R2 | Ao lado do `<select>`, um `Button variant="secondary"` cujo texto é a direção atual ("Decrescente" ou "Crescente") e cujo clique inverte `order`; `aria-label` "Inverter direção da ordenação". |
| R3 | Sem `sort`/`order` na URL o cliente usa `date`/`desc` e o servidor tem os mesmos padrões (`sort: Literal[...] = "date"`, `order: Literal[...] = "desc"`); o SQL resultante é o mesmo da 003 (`t.date DESC, t.id DESC`). |
| R4 | `sort=date` ordena por `t.date {order}` com desempate `t.id DESC`. |
| R5 | `sort=amount` ordena por `abs(t.amount_cents) {order}`: `desc` põe o maior gasto primeiro. Todo gasto é negativo (`SPENDING`), então `abs` é o "quanto saiu". |
| R6 | `sort=category` ordena por `CASE WHEN t.category IS NULL OR t.category = '' THEN 1 ELSE 0 END ASC` (sempre; "Sem categoria" por último nas duas direções) e depois pela posição alfabética do **rótulo**, calculada em Python a partir de `category_labels()` e passada como parâmetros de um `CASE t.category WHEN ? THEN ? …` (D2). Chave sem rótulo no seed cai no `ELSE` (última posição entre as rotuladas) e desempata por `t.category`. |
| R7 | A ordenação é `ORDER BY` do SQL antes de `LIMIT/OFFSET`; `sort`/`order` vão em toda chamada (`getExpenses({ page, sort, order })`), e "Anterior"/"Próxima" só trocam `page`, preservando os outros parâmetros (`new URLSearchParams(searchParams)`). |
| R8 | `sort` e `order` moram na URL (`?sort=amount&order=asc`); o valor padrão de cada um é apagado, não gravado (`client-state`). Recarregar ou compartilhar reproduz a ordem; trocar ordenação usa `replace: true` (filtro), paginação não. |
| R9 | Trocar `sort` ou `order` chama `params.delete('page')`. |
| R10 | Os quatro estados de `ExpensesList` não mudam; a chave da query passa a `['expenses', { page, sort, order }]`, então trocar a ordenação refaz a busca e "Tentar de novo" refaz com a ordenação atual. Os controles ficam **fora** dos ramos de estado: aparecem também em carregando, erro e vazio, para o usuário poder sair de uma ordenação que deu erro. |

## Decisões técnicas

### D1 — Lista branca de colunas no módulo de consulta; o router só valida com `Literal`

- Escolha: `app/queries/expenses.py` declara `Sort = Literal["date", "amount", "category"]`, `Order = Literal["asc", "desc"]` e um dicionário `_SORT_SQL: dict[Sort, str]` com a expressão de cada critério (`"t.date"`, `"abs(t.amount_cents)"`, a expressão `CASE` de D2). `_ORDER_SQL = {"asc": "ASC", "desc": "DESC"}`. A cláusula é montada como `f"ORDER BY {prefix}{_SORT_SQL[sort]} {_ORDER_SQL[order]}, t.id DESC"` — só valores do dicionário entram na string; a entrada do usuário nunca é interpolada. `list_expenses(conn, *, page, page_size, sort: Sort = "date", order: Order = "desc")`. O router declara `sort: Annotated[Sort, Query()] = "date"` e `order: Annotated[Order, Query()] = "desc"` importando os dois `Literal` do módulo de consulta; valor fora deles vira 422 pelo FastAPI (norma 32). O `/openapi.json` passa a listar os dois `enum` (norma 3).
- Alternativa descartada: receber o nome da coluna e validar com uma lista no router — motivo: o router não monta consulta (norma 30), e a lista de colunas é conhecimento da consulta.

### D2 — Ordem por categoria segue o rótulo pt-BR, via `CASE` parametrizado gerado de `category_labels()`

- Escolha: o rótulo não está no banco (dívida 023), mas o R6 pede ordem "pelo rótulo", e a chave crua trai o requisito de forma visível (`Groceries`→"Supermercado" e `Housing`→"Casa" trocam de lugar). Uma função `_category_rank_clause() -> tuple[str, list[str | int]]` ordena os rótulos de `category_labels()` com chave `unicodedata.normalize("NFKD", label).encode("ascii", "ignore").casefold()` (para "Água" não cair depois de "Z", como faria o `BINARY` do SQLite) e devolve `"CASE t.category " + "WHEN ? THEN ? " * n + "ELSE ? END"` com os parâmetros `[chave, posição, chave, posição, …, n]`. `_SORT_SQL["category"]` é `CASE WHEN t.category IS NULL OR t.category = '' THEN 1 ELSE 0 END, <rank> {order}, t.category`; o prefixo de nulos não recebe direção. São 79 pares, 159 parâmetros, bem abaixo do limite do SQLite (999); os parâmetros do `ORDER BY` precedem os de `LIMIT ? OFFSET ?` na tupla do `execute`. A função roda por chamada (`category_labels()` já relê o JSON; é um arquivo pequeno e a base tem poucos milhares de linhas).
- Alternativa descartada: ordenar pela chave crua com `CASE` de nulos e registrar como dívida — motivo: entrega uma ordem que o usuário vê errada na primeira tela ("Casa" depois de "Supermercado") e a dívida 023 já existe; não vale abrir uma segunda para não a resolver.
- Alternativa descartada: resolver a dívida 023 aqui (migração com coluna `label` em `categories` e `JOIN`) — motivo: mexe em esquema, seed e reconciliação (`seed_taxonomy`) por uma fatia de ordenação; é o item 023 do roadmap, com seu próprio PR. Quando ele entrar, `_category_rank_clause` vira `c.label` e some.

### D3 — Contrato JSON

- `GET /api/transactions/expenses?page=1&page_size=20&sort=date&order=desc` · `sort` ∈ `date | amount | category` (padrão `date`), `order` ∈ `asc | desc` (padrão `desc`); qualquer outro valor → 422. A resposta não muda (`items`, `page`, `page_size`, `total`); não se ecoa `sort`/`order` porque o cliente já os tem na URL. Desempate universal `t.id DESC`.

### D4 — Ordenação mora na URL; padrão por critério só no cliente

- Escolha: `expenses-list.tsx` ganha `readSort` e `readOrder` (mesma forma de `readPage`: valor fora da lista vale o padrão). Constantes na feature: `SORTS = ['date', 'amount', 'category'] as const`, `ORDERS = ['asc', 'desc'] as const`, `DEFAULT_ORDER_BY_SORT = { date: 'desc', amount: 'desc', category: 'asc' }`. Ao trocar o critério, grava `sort` e `order = DEFAULT_ORDER_BY_SORT[sort]` (categoria começa em A→Z, que é o que se espera de "por categoria"; o servidor continua com padrão `desc`, por isso `order=asc` vai explícito na URL quando é o padrão do critério mas não o do servidor). Ao inverter, grava `order` invertido. Nos dois casos `page` é apagado e `setSearchParams(params, { replace: true })`. `sort=date` e `order=desc` são apagados da URL (padrão global). `expensesQueryOptions({ page, sort, order })` com `queryKey: ['expenses', { page, sort, order }]`; `getExpenses` monta a URL com `URLSearchParams`.
- Alternativa descartada: `useState` para a ordenação — motivo: R8 exige sobreviver a recarga e link; `client-state` manda ordenação para a URL.
- Alternativa descartada: padrão por critério também no servidor (`order: Order | None`) — motivo: dois padrões dependentes num `Query` complicam o OpenAPI por nada; o cliente já decide.

### D5 — `SortControls` é componente da feature, com `<select>` nativo

- Escolha: `src/features/expenses/components/sort-controls.tsx` · `SortControls({ sort, order, onSortChange, onOrderToggle })`, controlado. `<select>` nativo (três opções fixas, sem busca) com `id` de `useId()` e `<label>` visível; nada de Radix. O botão é o `Button variant="secondary"` existente. Fica na feature porque só a lista de gastos usa; a 016 ("entradas") decide se sobe.
- Alternativa descartada: `Select` de `components/ui/form/` (skill `forms`) — motivo: não é formulário (sem schema, sem envio, sem React Hook Form) e o componente ainda não existe; criá-lo para um `<select>` de três opções é a pasta "para o futuro" que `project-structure` proíbe.

## Interface

Receitas do `docs/design.md` usadas: contêiner de página, título de página, texto de apoio, campo de formulário (a parte do `<label>`), botão secundário, lista, linha de lançamento, paginação, carregando, vazio, erro.

Receita nova a acrescentar em "Padrões acrescentados pelas entregas":

| Padrão | Classes | Fatia |
|---|---|---|
| Barra de controles de lista | `<div className="mt-6 flex flex-wrap items-end gap-3">`; cada controle em `flex flex-col gap-1`; `<select>` com as classes do `<input>` da receita "Campo de formulário" mais `min-h-10` (sem `w-full`); botão secundário alinhado pela base | 004 |

### Tela: Gastos (`/app/expenses`)

- Título do documento e `<h1>` "Gastos" não mudam.
- Texto de apoio passa a "Todos os gastos das suas contas e cartões." (a ordem já não é sempre "do mais recente ao mais antigo").
- Barra de controles (receita nova), logo abaixo do texto de apoio e **antes** dos estados da lista, sempre visível:
  - `<label>` "Ordenar por" + `<select>` com "Data", "Valor", "Categoria"; o selecionado reflete a URL.
  - Botão secundário com o texto da direção atual: "Decrescente" (para `desc`) ou "Crescente" (para `asc`); `aria-label` "Inverter direção da ordenação"; `type="button"`.
  - Em 360px os dois controles quebram de linha (`flex-wrap`), nada sai da tela.
- Carregando (`role="status"`): "Carregando gastos…" — inalterado; em troca de ordenação a lista anterior fica visível com os botões de paginação desabilitados (`keepPreviousData`), como já ocorre na troca de página.
- Vazio: "Nenhum gasto registrado ainda." — inalterado.
- Erro (`role="alert"`): "Não foi possível carregar os gastos." + "Tentar de novo" — inalterado.
- Com dados: lista e paginação da 003, na ordem pedida; "Anterior"/"Próxima" mantêm `sort`/`order` na URL.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/queries/expenses.py` | `Sort`, `Order`, `_SORT_SQL`, `_ORDER_SQL`, `_category_rank_clause()`; `_PAGE` deixa de ter `ORDER BY` fixo e passa a ser montado por `_page_sql(sort, order)`; `list_expenses(..., sort="date", order="desc")` (D1, D2) | — |
| alterar | `app/routers/transactions.py` | `sort: Annotated[Sort, Query()] = "date"`, `order: Annotated[Order, Query()] = "desc"`, repassados a `list_expenses` (D3) | `api-requests` |
| alterar | `tests/test_expenses_api.py` | sem `sort`/`order` a ordem continua `date DESC, id DESC`; `sort=date&order=asc` inverte; `sort=amount&order=desc` põe −R$ 300 antes de −R$ 50 e `asc` o contrário; `sort=category&order=asc` com `Housing` ("Casa"), `Groceries` ("Supermercado") e `""` devolve Casa, Supermercado, sem categoria — e `desc` devolve Supermercado, Casa, sem categoria (nulo sempre por último); chave fora do seed fica depois das rotuladas; dois gastos com mesmo valor desempatam por `id DESC`; `sort=amount&page=2` respeita a ordem; `sort=payee` e `order=up` → 422 | `api-requests`, `unit-testing` |
| alterar | `tests/data/e2e_transactions.json` | acrescenta `e2e-t-4`: "POSTO CENTRAL", `-150.0`, `2026-09-01`, `categoria: "Housing"` (gasto), para o e2e ter dois gastos com data, valor e categoria distintos | `e2e-testing` |

### Ferramental (raiz)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `docs/design.md` | receita "Barra de controles de lista" | `interface-design` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/features/expenses/types/expense.ts` | `ExpenseSort = 'date' \| 'amount' \| 'category'`, `ExpenseOrder = 'asc' \| 'desc'`, `ExpensesQuery { page: number; sort: ExpenseSort; order: ExpenseOrder }` | — |
| alterar | `src/features/expenses/api/get-expenses.ts` | `getExpenses(query: ExpensesQuery)` monta a URL com `URLSearchParams` (`page`, `page_size`, `sort`, `order`); `expensesQueryOptions(query)` com `queryKey: ['expenses', query]`; `useExpenses(query)` | `api-requests` |
| criar | `src/features/expenses/components/sort-controls.tsx` | `SortControls` (D5): `<label>` "Ordenar por", `<select>` "Data"/"Valor"/"Categoria", botão "Decrescente"/"Crescente" | `interface-design`, `client-state` |
| alterar | `src/features/expenses/components/expenses-list.tsx` | `SORTS`, `ORDERS`, `DEFAULT_ORDER_BY_SORT`, `readSort`, `readOrder`; `SortControls` antes dos estados; `handleSortChange`/`handleOrderToggle` (D4); paginação preserva os demais parâmetros; texto de apoio não é daqui | `client-state`, `interface-design`, `component-robustness` |
| alterar | `src/app/routes/expenses.tsx` | texto de apoio "Todos os gastos das suas contas e cartões." | `interface-design` |
| alterar | `src/testing/mocks/handlers.ts` | handler lê `sort`/`order` e ordena `fakeExpenses` antes de fatiar: data, `Math.abs(amount_cents)`, categoria por `localeCompare('pt-BR')` com nulo por último; desempate `id` decrescente. `generateFakeExpenses` ganha um item com categoria "Transporte" e um com valor bem maior (−R$ 1.200,00) para as ordens serem distinguíveis | `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | padrão: `<select>` em "Data" e botão "Decrescente", URL sem `sort`/`order`; escolher "Valor" → URL `?sort=amount`, API chamada com `sort=amount&order=desc` e primeiro item −R$ 1.200,00; escolher "Categoria" → `?sort=category&order=asc`, botão "Crescente", primeiro selo "Alimentação"; clicar "Crescente" → `order=desc`; em `?page=2`, trocar a ordenação apaga `page`; "Próxima" com `?sort=amount` vai para `?sort=amount&page=2`; `?sort=foo&order=bar` cai no padrão; os controles aparecem no estado de erro | `component-testing`, `api-mocking` |
| alterar | `e2e/expenses.spec.ts` | teste novo: login → "Gastos" → primeiro item "MERCADO DO BAIRRO" (02/09) → escolher "Valor" → URL contém `sort=amount` e primeiro item "POSTO CENTRAL" (−R$ 150,00) → clicar "Decrescente" → URL contém `order=asc` e primeiro item "MERCADO DO BAIRRO" → `page.reload()` mantém "Crescente" e a ordem → escolher "Categoria" → primeiro "POSTO CENTRAL" ("Casa") | `e2e-testing` |

## Estimativa de tamanho

Jornadas: 1 (reordenar a lista de gastos) · Telas novas: 0 · Linhas alteradas (sem testes): ~50 Python (`queries/expenses.py` ~40, `routers/transactions.py` ~6, fixture e2e ~20 de JSON) + ~150 em `src/` (tipos ~10, api ~15, `sort-controls` ~55, `expenses-list` ~40, rota 1, mocks ~30) + ~3 de doc · Fases previstas: 2 (endpoint com `sort`/`order` + testes de API; controles na tela + mocks + testes de componente + e2e).

Nenhum sinal de "grande demais" dispara.

## Dívida encontrada

- Dívida 023 (`category-labels-in-schema`, roadmap): o rótulo pt-BR da categoria continua só em `app/taxonomy/seed.json`. Esta fatia contorna com o `CASE` parametrizado de D2 (159 parâmetros por consulta); quando o 023 entrar, `_category_rank_clause` deve ser substituída por `ORDER BY c.label` e removida. Já registrada; não abre item novo.
- `src/features/expenses/api/get-expenses.ts` monta a URL por interpolação de string; a skill `api-requests` prevê parâmetros de busca pelo cliente. Esta fatia troca por `URLSearchParams` no próprio arquivo, sem item de roadmap.
