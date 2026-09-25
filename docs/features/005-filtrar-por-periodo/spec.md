# SPEC 005 — filtrar por período

Quinta fatia da SPA. Acrescenta à página "Gastos" (`/app/expenses`) o filtro por mês ou por intervalo de datas, guardado na URL, aplicado em SQL antes da ordenação e da paginação, e o total em reais do período no resumo da lista. Nenhum endpoint novo: a fatia estende `GET /api/transactions/expenses`, o hook e a lista que as fatias 003 e 004 entregaram.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/queries/expenses.py` · `list_expenses(conn, *, page, page_size, sort, order) -> ExpensesPage(items, total)`; `_SELECT` e `_TOTAL` terminam em `WHERE {SPENDING}`; `_page_sql(sort, order)` monta `ORDER BY … LIMIT ? OFFSET ?` e devolve os parâmetros do `ORDER BY` (o `CASE` de categoria, D2 da 004).
- `app/queries/spending.py` · `SPENDING` e `total_spending_cents(conn, start, end)` com o mesmo predicado de data (`date >= ?`, `date <= ?`) e `coalesce(sum(amount_cents), 0)` — a forma que esta fatia copia para dentro da consulta de gastos.
- `app/routers/transactions.py` · `page`, `page_size`, `sort`, `order` em `Annotated[..., Query(...)]`; `ExpensesResponse(items, page, page_size, total)`; rota `def`.
- `src/features/expenses/types/expense.ts` · `ExpensesQuery { page, sort, order }`, `ExpensesResponse`.
- `src/features/expenses/api/get-expenses.ts` · `getExpenses(query)` com `URLSearchParams`; `expensesQueryOptions(query)` com `queryKey: ['expenses', query]` e `keepPreviousData`; `useExpenses(query)`.
- `src/features/expenses/components/expenses-list.tsx` · `readPage`, `readSort`, `readOrder`, `writeSorting` (apaga `page` e os padrões), quatro estados, `SortControls` fora dos ramos de estado, `Pagination` preservando os demais parâmetros.
- `src/features/expenses/components/sort-controls.tsx` · renderiza a "Barra de controles de lista" (`mt-6 flex flex-wrap items-end gap-3`) com o `<select>` "Ordenar por" e o botão de direção.
- `src/features/expenses/components/pagination.tsx` · "Página X de Y · N gastos"/"1 gasto".
- `src/utils/format-money.ts` · `formatMoney(cents)` (`Intl.NumberFormat('pt-BR', BRL)`; negativo sai "-R$ 84,90").
- `src/components/ui/button.tsx` · `Button` com `variant`; receita "Campo de formulário" (label + input) no `docs/design.md`.
- `src/testing/mocks/handlers.ts` · `fakeExpenses` (45 gastos, datas decrescentes de 2026-08-01 até 2026-06-18: 1 em agosto, 31 em julho, 13 em junho), `sortExpenses`, handler que ordena e fatia.
- `tests/data/e2e_transactions.json` · dois gastos, ambos em setembro de 2026: "POSTO CENTRAL" (01/09, −R$ 150,00) e "MERCADO DO BAIRRO" (02/09, −R$ 84,90); `e2e/expenses.spec.ts` já loga e abre "Gastos".

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `PeriodControls` (novo, na feature) mostra, na barra de controles, um grupo "Mês" com o botão "Mês anterior", o texto do mês selecionado (ex.: "setembro de 2026"), o botão "Próximo mês" e o botão "Todo o período". |
| R2 | Sem `month`, `from`, `to` nem `period` na URL, o período é o mês corrente (`currentMonth()`). Com `period=all`, o cliente não manda `from`/`to` e o servidor não filtra (`date_from=None`, `date_to=None`); o texto do mês exibe "Todo o período" e o botão "Todo o período" fica desabilitado. |
| R3 | `month=YYYY-MM` na URL é traduzido no cliente por `monthRange(month)` em `from=YYYY-MM-01` e `to=YYYY-MM-<último dia>` (D4); o servidor aplica `t.date >= ? AND t.date <= ?` (D1). |
| R4 | "Mês anterior"/"Próximo mês" gravam `shiftMonth(base, ±1)`, com `base` = mês da URL ou, sem mês, `currentMonth()` (calendário local de hoje). |
| R5 | Dois `<input type="date">` "De" e "Até" gravam `from`/`to` diretos na URL; qualquer escrita de intervalo apaga `month`, e qualquer escrita de mês apaga `from`/`to` (D4). Na leitura, se os dois vierem juntos, `month` tem precedência. Com `to < from` no cliente, o campo recém-alterado vence e o outro é apagado — a API nunca recebe intervalo invertido. |
| R6 | `from`/`to` (derivados ou diretos) entram em `ExpensesQuery` e, portanto, em toda chamada e na chave da query; "Anterior"/"Próxima" só trocam `page` (`new URLSearchParams(searchParams)`). |
| R7 | `month`, `from` e `to` moram na URL (`client-state`); recarregar ou compartilhar reproduz o período. Escrita de filtro usa `replace: true`. |
| R8 | Toda escrita de período chama `params.delete('page')` (mesma forma de `writeSorting`). |
| R9 | `writePeriod` só toca `month`, `from`, `to`, `period` e `page`; `writeSorting` só toca `sort`, `order` e `page`. Os dois partem de `new URLSearchParams(searchParams)`. |
| R10 | A resposta ganha `total_cents` (soma de `amount_cents` do filtro inteiro, calculada no mesmo `SELECT` do `count(*)`, D1). `Pagination` ganha a prop `totalCents` e o resumo vira "Página X de Y · N gastos · R$ 3.210,00 no período" (`formatMoney(-totalCents)`: o total do filtro é negativo por construção; mostra-se quanto saiu). |
| R11 | Com filtro ativo (`month` ou `from`/`to` presentes) e `total === 0`, o vazio diz "Nenhum gasto nesse período."; sem filtro continua "Nenhum gasto registrado ainda.". Os controles ficam fora dos ramos, para o usuário poder sair do período vazio. |
| R12 | Os quatro estados de `ExpensesList` não mudam de forma; a chave `['expenses', { page, sort, order, from, to }]` faz "Tentar de novo" refazer com o período atual e a troca de período mostrar a lista anterior com paginação desabilitada (`keepPreviousData`), como já ocorre na ordenação. |

## Decisões técnicas

### D1 — Predicado de data e `total_cents` na consulta, num único `SELECT` de contagem e soma

- Escolha: `app/queries/expenses.py` ganha `_where(date_from: str | None, date_to: str | None) -> tuple[str, list[str]]` que devolve `"WHERE {SPENDING}"` mais `" AND t.date >= ?"` e/ou `" AND t.date <= ?"` conforme os limites, com os parâmetros na mesma ordem. `_SELECT` e `_TOTAL` deixam de embutir o `WHERE`; `_page_sql(sort, order, where)` concatena `_SELECT` + `where` + `ORDER BY … LIMIT ? OFFSET ?`, e a tupla do `execute` é `(*where_params, *order_params, page_size, offset)` (o `WHERE` precede o `ORDER BY` no SQL, logo seus `?` vêm primeiro). `_TOTAL` vira `SELECT count(*), coalesce(sum(t.amount_cents), 0) FROM transactions AS t` + `where`; `ExpensesPage` ganha `total_cents: int`. `list_expenses(conn, *, page, page_size, sort="date", order="desc", date_from: str | None = None, date_to: str | None = None)`. Comparação de texto ISO `YYYY-MM-DD` é ordem cronológica, como `total_spending_cents` já faz.
- Alternativa descartada: chamar `total_spending_cents(conn, start, end)` de `spending.py` para a soma — motivo: seriam três consultas por página e dois lugares para o mesmo predicado divergirem (a soma sem o `AND` que a lista tem é o painel mentindo, invariante 25). Contagem e soma no mesmo `SELECT` só podem ver o mesmo filtro.
- Alternativa descartada: somar `amount_cents` dos itens no cliente — motivo: só cobre a página atual (R10 pede o filtro inteiro) e cálculo financeiro é SQL, nunca cliente (norma 23).

### D2 — O router recebe `from`/`to` como `date` e responde 422 a intervalo invertido

- Escolha: `from_: Annotated[date | None, Query(alias="from")] = None` e `to: Annotated[date | None, Query()] = None` (`from` é palavra reservada em Python; o `alias` mantém o nome da API). O FastAPI valida `YYYY-MM-DD` e devolve 422 para `2026-13-01`, `01/09/2026` ou `hoje` sem regex à mão. Se os dois vierem e `to < from_`, a rota levanta `HTTPException(status_code=422, detail="A data final precisa ser igual ou posterior à inicial.")`. Repassa `date_from=from_.isoformat() if from_ else None` (idem `to`) a `list_expenses`. Só um limite é aceito (intervalo aberto). O `/openapi.json` passa a listar `from` e `to` com `format: date` (norma 3).
- Alternativa descartada: `str` com `Query(pattern=r"^\d{4}-\d{2}-\d{2}$")` — motivo: aceita `2026-02-31`; `date` rejeita, e o OpenAPI fica com o formato certo.
- Alternativa descartada: validar `to >= from` dentro de `list_expenses` — motivo: é regra de entrada HTTP, e o módulo de consulta não conhece código de status (norma 30 no sentido inverso).

### D3 — Contrato JSON

- `GET /api/transactions/expenses?page=1&page_size=20&sort=date&order=desc&from=2026-09-01&to=2026-09-30` · `from`/`to` opcionais, ISO `YYYY-MM-DD`, inclusivos; data inválida ou `to < from` → 422. A resposta ganha `total_cents: int` (sempre presente, também sem filtro; `0` quando `total` é `0`; negativo ou zero por construção do `SPENDING`). Os demais campos não mudam. Não se ecoa `from`/`to`: o cliente já os tem na URL.

### D4 — Período mora na URL; mês é do cliente, intervalo é da API

- Escolha: dois formatos na URL do app, mutuamente excludentes na escrita: `?month=2026-09` (o que o usuário pediu, legível e compartilhável) ou `?from=2026-09-01&to=2026-09-15` (intervalo livre; um dos dois pode faltar). Funções puras em `src/features/expenses/utils/period.ts`: `readMonth(value): string | null` (regex `^\d{4}-(0[1-9]|1[0-2])$`), `readIsoDate(value): string | null` (regex `^\d{4}-\d{2}-\d{2}$` e dia válido pelo `daysInMonth`), `daysInMonth(year, month)` (`new Date(Date.UTC(year, month, 0)).getUTCDate()`, só aritmética), `monthRange(month): { from, to }`, `shiftMonth(month, delta)` (aritmética de ano/mês em inteiros), `currentMonth()` (`new Date()` local, `getFullYear`/`getMonth` — é o único ponto que lê o relógio; o mês que o usuário vê é o do calendário dele), `formatMonth(month)` ("setembro de 2026", por um array com os doze nomes em pt-BR — sem `Intl` com fuso). `readPeriod(searchParams): Period` devolve `{ kind: 'all' } | { kind: 'month', month } | { kind: 'range', from, to }` com `month` prevalecendo, depois `from`/`to`, depois `period=all`; sem nenhum deles, o mês corrente. `toDateBounds(period): { from: string | null; to: string | null }` alimenta `ExpensesQuery`, que ganha `from: string | null` e `to: string | null`; `getExpenses` só acrescenta ao `URLSearchParams` os que não são nulos. `writePeriod(params, period)` apaga `page`, apaga `month`, `from`, `to` e `period` e grava só os do `period` (`period=all` para todo o período).
- Alternativa descartada: só `from`/`to` na URL e o seletor de mês virar um atalho que grava o intervalo — motivo: perde a noção de "mês selecionado" para "Mês anterior"/"Próximo mês" (teria de reinferir mês a partir do intervalo) e a URL fica menos legível (`?month=2026-09` vs `?from=2026-09-01&to=2026-09-30`).
- Alternativa descartada: `month` também na API — motivo: dois parâmetros que descrevem o mesmo filtro no servidor duplicam validação; um intervalo cobre o mês e o SQL não muda.
- Alternativa descartada: `useState` para o período — motivo: R7 exige sobreviver a recarga e link; `client-state` manda filtro para a URL.

### D5 — `PeriodControls` é componente da feature, na mesma barra de `SortControls`

- Escolha: `src/features/expenses/components/period-controls.tsx` · `PeriodControls({ period, onMonthChange, onRangeChange, onClear })`, controlado pela URL. Estrutura: `<fieldset>` com `<legend>` "Mês" contendo "Mês anterior", `<span aria-live="polite">` com `formatMonth(month)` / "Todo o período" / "Período personalizado", "Próximo mês", e o botão "Todo o período"; depois dois campos "De" e "Até" (`<input type="date">` com `id` de `useId()`, `value` da URL ou `''`). Os botões são `Button variant="secondary"`; os de mês têm o texto visível como nome acessível. `onChange` de um campo chama `onRangeChange({ from, to })` já com a regra de "campo recém-alterado vence" aplicada no componente pai (`expenses-list.tsx`), que é quem conhece a URL. A barra (`div` da receita "Barra de controles de lista") sobe de `sort-controls.tsx` para `expenses-list.tsx`, e `SortControls` passa a devolver só os seus dois controles: os quatro grupos convivem na mesma linha e quebram em 360px.
- Alternativa descartada: segunda barra de controles só para o período — motivo: restrição da fatia (uma barra) e dois `mt-6` seguidos empilham espaço sem conteúdo entre eles.
- Alternativa descartada: React Hook Form + Zod para "De"/"Até" (skill `forms`) — motivo: não há envio nem schema; cada campo grava na URL ao mudar, como o `<select>` da 004.
- Alternativa descartada: um `<input type="month">` — motivo: sem suporte no Firefox e no Safari de desktop; os dois botões cobrem R1 e R4 em todo navegador.

## Interface

Receitas do `docs/design.md` usadas: contêiner de página, título de página, texto de apoio, barra de controles de lista, campo de formulário, botão secundário, lista, linha de lançamento, paginação, carregando, vazio, erro.

Receita nova a acrescentar em "Padrões acrescentados pelas entregas":

| Padrão | Classes | Fatia |
|---|---|---|
| Grupo de período | `<fieldset className="flex flex-col gap-1">` com `<legend className="text-sm font-medium text-gray-900">`; linha `flex flex-wrap items-center gap-2`; texto do mês `min-w-40 text-center text-sm text-gray-900 tabular-nums`; `<input type="date">` com as classes do `<input>` da receita "Campo de formulário" mais `min-h-10` (sem `w-full`) | 005 |

### Tela: Gastos (`/app/expenses`)

- Título do documento, `<h1>` "Gastos" e texto de apoio "Todos os gastos das suas contas e cartões." não mudam.
- Barra de controles, logo abaixo do texto de apoio e antes dos estados da lista, sempre visível, nesta ordem, quebrando de linha em 360px:
  1. Grupo "Mês": botão secundário "Mês anterior" · texto do mês ("setembro de 2026"; com `period=all` "Todo o período"; com intervalo livre "Período personalizado") · botão secundário "Próximo mês" · botão secundário "Todo o período" (`disabled` quando o período já é todo o período).
  2. Campo "De" (`<label>` + `<input type="date">`) e campo "Até" (idem). Com mês selecionado, os dois mostram os limites do mês (`monthRange`), para o usuário ver o que está filtrando; editar um deles troca para intervalo.
  3. "Ordenar por" + `<select>` e o botão "Decrescente"/"Crescente" (inalterados).
- Carregando (`role="status"`): "Carregando gastos…" — inalterado; troca de período mostra a lista anterior com "Anterior"/"Próxima" desabilitados (`keepPreviousData`).
- Vazio sem filtro: "Nenhum gasto registrado ainda." — inalterado.
- Vazio com filtro: "Nenhum gasto nesse período." (mesma receita "Vazio").
- Erro (`role="alert"`): "Não foi possível carregar os gastos." + "Tentar de novo" — inalterado.
- Com dados: lista da 003 na ordem da 004; resumo da paginação "Página 1 de 3 · 42 gastos · R$ 3.210,00 no período" ("1 gasto" no singular); "Anterior"/"Próxima" mantêm `month`/`from`/`to`/`sort`/`order`.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/queries/expenses.py` | `_where(date_from, date_to)`; `_SELECT`/`_TOTAL` sem `WHERE` embutido; `_TOTAL` com `count(*)` e `coalesce(sum(t.amount_cents), 0)`; `_page_sql(sort, order, where)`; `ExpensesPage.total_cents`; `list_expenses(..., date_from=None, date_to=None)` (D1) | — |
| alterar | `app/routers/transactions.py` | `from_: Annotated[date \| None, Query(alias="from")]`, `to: Annotated[date \| None, Query()]`; `HTTPException(422)` para `to < from`; `ExpensesResponse.total_cents: int` (D2, D3) | `api-requests` |
| alterar | `tests/test_expenses_api.py` | sem `from`/`to` a resposta traz `total_cents` igual à soma de todos os gastos (e `0` na base vazia); `from=2026-09-01&to=2026-09-30` devolve só os de setembro, `total` e `total_cents` do filtro inteiro com `page_size=1`; limites inclusivos (gasto em `2026-09-30` entra, `2026-10-01` não); só `from` ou só `to` funciona; transferência dentro do período não entra em `total_cents`; `sort=amount` respeita o filtro; `from=2026-13-01`, `from=01/09/2026`, `from=2026-02-31` e `from=2026-09-10&to=2026-09-01` → 422; o `/openapi.json` lista `from` e `to` com `format: date` | `api-requests`, `unit-testing` |

### Ferramental (raiz)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `docs/design.md` | receita "Grupo de período" | `interface-design` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/features/expenses/types/expense.ts` | `ExpensesResponse.total_cents: number`; `ExpensesQuery` ganha `from: string \| null` e `to: string \| null`; `Period` (D4) | — |
| criar | `src/features/expenses/utils/period.ts` | `readMonth`, `readIsoDate`, `daysInMonth`, `monthRange`, `shiftMonth`, `currentMonth`, `formatMonth`, `readPeriod`, `toDateBounds`, `writePeriod` (D4) | `client-state` |
| criar | `src/features/expenses/utils/__tests__/period.test.ts` | `monthRange('2026-02')` → `2026-02-01`/`2026-02-28` e `2028-02` → `-29`; `shiftMonth('2026-01', -1)` → `2025-12` e `('2026-12', 1)` → `2027-01`; `formatMonth('2026-09')` → "setembro de 2026"; `readMonth('2026-13')`, `readIsoDate('2026-02-31')` → `null`; `readPeriod` com `month` e `from` juntos devolve o mês; `writePeriod` apaga `page` e o formato concorrente | `unit-testing` |
| alterar | `src/features/expenses/api/get-expenses.ts` | acrescenta `from`/`to` ao `URLSearchParams` só quando não nulos | `api-requests` |
| criar | `src/features/expenses/components/period-controls.tsx` | `PeriodControls` (D5): grupo "Mês" com "Mês anterior", texto do mês, "Próximo mês", "Todo o período"; campos "De" e "Até" | `interface-design`, `client-state`, `component-robustness` |
| alterar | `src/features/expenses/components/sort-controls.tsx` | devolve os dois controles sem a `div` da barra (a barra sobe para `expenses-list.tsx`) | `interface-design` |
| alterar | `src/features/expenses/components/expenses-list.tsx` | `readPeriod`/`toDateBounds` da URL; `handleMonthChange` (`shiftMonth` a partir do mês ou de `currentMonth()`), `handleRangeChange` (campo recém-alterado vence), `handleClear`; barra de controles com `PeriodControls` + `SortControls`; vazio "Nenhum gasto nesse período." quando há filtro; `Pagination` recebe `totalCents` | `client-state`, `interface-design`, `component-robustness` |
| alterar | `src/features/expenses/components/pagination.tsx` | prop `totalCents: number`; resumo "Página X de Y · N gastos · R$ … no período" com `formatMoney(-totalCents)` | `interface-design` |
| alterar | `src/features/expenses/components/__tests__/pagination.test.tsx` | resumo inclui "R$ 3.210,00 no período" para `totalCents: -321000`; `R$ 0,00` para `0` | `component-testing` |
| alterar | `src/testing/mocks/handlers.ts` | handler lê `from`/`to`, filtra `fakeExpenses` por comparação de string antes de ordenar e fatiar, devolve `total` e `total_cents` do filtro | `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | padrão: texto "Todo o período", botão "Todo o período" desabilitado, API sem `from`/`to`, resumo "45 gastos · R$ … no período"; `?month=2026-07` → API com `from=2026-07-01&to=2026-07-31`, texto "julho de 2026", "31 gastos", campos "De"/"Até" preenchidos; "Mês anterior" a partir de `?month=2026-07` → `?month=2026-06` (13 gastos); "Próximo mês" a partir de `?month=2026-07` → `?month=2026-08` (1 gasto, "MERCADO DO BAIRRO"); `?month=2026-09` → "Nenhum gasto nesse período." com os controles visíveis; "Todo o período" apaga `month`; preencher "De" `2026-07-10` e "Até" `2026-07-20` a partir de `?month=2026-07` → URL `?from=2026-07-10&to=2026-07-20` sem `month`, texto "Período personalizado"; `?month=2026-07&from=2026-01-01` usa o mês; `?month=2026-07&page=2&sort=amount` + "Mês anterior" → apaga `page`, mantém `sort=amount`; "Próxima" com `?month=2026-07` → `?month=2026-07&page=2`; `?month=13` cai em "Todo o período"; controles aparecem no estado de erro | `component-testing`, `api-mocking` |
| alterar | `e2e/expenses.spec.ts` | teste novo: login → "Gastos" → resumo "2 gastos · R$ 234,90 no período" → `page.goto('/app/expenses?month=2026-08')` → "Nenhum gasto nesse período." → clicar "Próximo mês" → URL contém `month=2026-09`, texto "setembro de 2026", 2 itens → preencher "De" e "Até" com `2026-09-02` → URL contém `from=2026-09-02` e não contém `month`, 1 item "MERCADO DO BAIRRO", resumo "1 gasto · R$ 84,90 no período" → `page.reload()` mantém o item e os campos → "Todo o período" → 2 itens e URL sem `from` | `e2e-testing` |

## Estimativa de tamanho

Jornadas: 1 (restringir a lista de gastos a um período) · Telas novas: 0 · Linhas alteradas (sem testes): ~45 Python (`queries/expenses.py` ~25, `routers/transactions.py` ~20) + ~230 em `src/` (tipos ~12, `utils/period.ts` ~70, api ~6, `period-controls` ~80, `sort-controls` −4, `expenses-list` ~45, `pagination` ~6, mocks ~15) + ~3 de doc · Fases previstas: 2 (endpoint com `from`/`to` e `total_cents` + testes de API; utilitário de período, controles na tela, resumo, mocks, testes de componente e e2e).

Nenhum sinal de "grande demais" dispara.

## Dívida encontrada

- `app/queries/spending.py` · `total_spending_cents` e `app/queries/expenses.py` passam a ter, cada um, o mesmo predicado de data sobre `SPENDING`. Dois lugares para a mesma regra; quando um terceiro consumidor aparecer (fatia 008, agrupar por categoria), o `_where(date_from, date_to)` desta fatia deve subir para `spending.py` e `total_spending_cents` usá-lo. Item novo de roadmap, posicionado antes da 008.
