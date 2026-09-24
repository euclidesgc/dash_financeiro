# SPEC 016 — entradas

Décima sexta fatia da SPA. Na página "Gastos" (`/app/expenses`), o controle "Mostrar" ganha a terceira opção "Entradas": a mesma lista, com os mesmos filtros e ordenação, passa a mostrar salário e outras receitas (valor positivo que não é transferência própria nem estorno), com o valor em verde e o rodapé "N entradas · R$ X no período". Com período filtrado, um bloco "Resultado do período" (entradas, gastos, saldo) aparece acima do "Teto do mês" em qualquer vista. Na vista de entradas, cada linha tem a ação "Não é entrada" (mesmo controle e mesmos motivos da fatia 015); o marcado vai para "Não são gastos", que passa a listar positivos e negativos, e volta por "Voltar a contar". De quebra, a fatia fecha a dívida 033: o predicado de entrada, hoje escrito à mão em três módulos do plano, passa a ter um dono, `INCOME` em `app/queries/spending.py` — e por isso a marcação manual também sai da mediana de receita que o plano projeta, sem que o plano e a tela discordem.

O que o código já faz hoje, e que esta SPEC reaproveita (nada disto se recria):

- `app/queries/spending.py` · `OUTFLOW`, `SPENDING = OUTFLOW + not_expense_reason IS NULL`, `EXCLUDED = OUTFLOW + IS NOT NULL`, `date_window`, `total_spending_cents`.
- `app/plan/objective.py:17`, `app/projection/monthly.py:13`, `app/projection/forecast.py:12` · três cópias literais de `amount_cents > 0 AND is_transfer = 0 AND is_refund = 0` (sem `refunded_by IS NULL`). A dívida 033 do roadmap cita `app/plan/forecast.py` e `app/plan/monthly.py`; os arquivos estão em `app/projection/`.
- `app/queries/expenses.py` · `View = Literal["expenses", "excluded"]`, `_PREDICATE`, `_where(view, …)`, `sum_expenses`/`list_expenses`/`sum_by_category` com `view`, `get_expense` sem predicado.
- `app/taxonomy/override.py` · `Reason`, `NotAnOutflowError`, `set_not_expense` (recusa quem não satisfaz `OUTFLOW`), `clear_not_expense`, `_require`, `_write`.
- `app/routers/transactions.py` · `Expense`, `NOT_AN_OUTFLOW`, `_date_bounds`, `_search_term`, `GET /expenses`, `GET /expenses/by-category`, `GET /expenses/month-signal` (sem `view`), `PUT`/`DELETE /{id}/not-expense`. `tests/test_route_guard.py` exige 401 em rota nova sozinho.
- `src/features/expenses/` · `types/expense.ts` (`ExpenseView`, `ExpensesQuery.view`, `CategoryTotalsQuery`), `api/get-expenses.ts` (`view` só quando `excluded`), `api/get-month-signal.ts` (modelo de fetcher com `from`/`to` e chave `['expenses', 'month-signal', query]`), `api/set-not-expense.ts`, `api/clear-not-expense.ts`, `components/view-select.tsx` (`VIEW_OPTIONS`), `components/not-expense-control.tsx` (modo `excluded` com "Voltar a ser gasto"; modo `expenses` com "Não é gasto" → seletor "Motivo"), `components/expense-item.tsx` (`amountColor`, selo do motivo em `excluded`, `CategoryPicker` fora dele), `components/expenses-list.tsx` (`readView`/`writeView`, `filters`, `header` com `MonthCeiling` só em mês+`expenses` e `CategoryTotals` sempre; `lastExcluded` + aviso "Desfazer"; textos por vista; `noun` na `Pagination`), `components/month-ceiling.tsx` (modelo de bloco com carregando/erro/`scope === 'none' → null`), `utils/reason-labels.ts`.
- `src/testing/mocks/handlers.ts` · `fakeExpenses` (todos negativos), `filterExpenses(url)` lê `view`, handlers de `/api/transactions/*`, `similarTo` já filtra `amount_cents < 0`.
- `tests/data/e2e_transactions.json` · 2026-09: MERCADO DO BAIRRO −84,90, TED PARA POUPANCA −500,00 (transferência própria), **SALARIO +6.000,00 (05/09)**, POSTO CENTRAL −150,00; `e2e/expenses.spec.ts` em `serial`, o teste de 015 é o modelo (mexe e devolve a base).
- `docs/design.md` · "Painel de situação" (002), "Painel com número e selo" (014), "Aviso com desfazer" (015), "Valor monetário" (001: negativo `text-red-700`, positivo `text-gray-900`), "Barra de controles de lista" (004).

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `VIEW_OPTIONS` em `view-select.tsx` ganha `{ value: 'income', label: 'Entradas' }` por último; `ExpenseView` ganha `'income'`; `readView`/`writeView` em `expenses-list.tsx` aceitam e gravam `?view=income` (D5). |
| R2 | `GET /api/transactions/expenses?view=income` usa o predicado `INCOME` (D1, D2) com os mesmos `_where`, `sort`, `order`, `page`, `from`/`to`, `account_id`, `q`; `ExpenseItem` rende as mesmas colunas (D6). |
| R3 | `Pagination` recebe `noun = { one: 'entrada', many: 'entradas' }`; `total_cents` vem de `sum_expenses(view="income")`; o valor de cada linha positiva usa `text-green-700` (D6). O rodapé já formata `Math.abs(totalCents)`. |
| R4 | `GET /api/transactions/expenses/period-result` devolve `{ income_cents, spending_cents, balance_cents }` calculado em SQL por `period_result()` em `expenses.py` (D3, D4); `PeriodResult` em `components/period-result.tsx` rende "Resultado do período" acima de `MonthCeiling`, em qualquer vista, com saldo verde (> 0), vermelho (< 0) ou neutro (= 0) (D7). |
| R5 | `ExpensesList` só monta `<PeriodResult>` quando `period.kind !== 'all'` (D7). |
| R6 | Em `view === 'income'`, `ExpenseItem` não rende `CategoryPicker` nem selo; `NotExpenseControl` mostra "Não é entrada" (D6). |
| R7 | O mesmo `NotExpenseControl` (seletor "Motivo" com `REASON_OPTIONS`, "Confirmar"/"Cancelar") chama `PUT /api/transactions/{id}/not-expense`, que agora aceita entrada (D2); `onSuccess` invalida `['expenses']`, chave que cobre a lista e `period-result`; o aviso "Desfazer" em `ExpensesList` diz "{descrição} não conta mais como entrada." (D5, D6). |
| R8 | `EXCLUDED` passa a cobrir positivo e negativo marcados (D1); no modo `excluded`, a linha mostra o selo do motivo, o valor com a cor do sinal e o botão "Voltar a contar" (`DELETE …/not-expense`), que devolve a linha a "Gastos" ou "Entradas" conforme o sinal (D6). |
| R9 | `header` de `ExpensesList` rende `MonthCeiling` e `CategoryTotals` só com `view === 'expenses'` (D5). `by-category` e `month-signal` não mudam. |
| R10 | `INCOME` e `INFLOW` exigem `is_transfer = 0 AND is_refund = 0 AND refunded_by IS NULL`: transferência e estorno automáticos não aparecem em `income` nem em `excluded`; `set_not_expense` recusa quem não satisfaz `OUTFLOW` nem `INFLOW` com 422 (D1, D2). |
| R11 | `not_expense_reason` continua fora de `_TRANSACTION_COLUMNS` do `loader.py` (015/D1): nada muda na ingestão; o teste de API repete `_load` com a entrada marcada e prova que a marca fica. |

## Decisões técnicas

### D1 — `INFLOW`/`INCOME` em `spending.py`; `EXCLUDED` cobre os dois sinais; os três módulos do plano importam `INCOME` (dívida 033)

- Escolha: em `app/queries/spending.py`, `_CLEAN = "is_transfer = 0 AND is_refund = 0 AND refunded_by IS NULL"`; `OUTFLOW = f"amount_cents < 0 AND {_CLEAN}"`; `INFLOW = f"amount_cents > 0 AND {_CLEAN}"`; `SPENDING = f"{OUTFLOW} AND not_expense_reason IS NULL"`; `INCOME = f"{INFLOW} AND not_expense_reason IS NULL"`; `EXCLUDED = f"amount_cents <> 0 AND {_CLEAN} AND not_expense_reason IS NOT NULL"`. `app/plan/objective.py` (`_INCOME`), `app/projection/monthly.py` (`_INCOME`) e `app/projection/forecast.py` (`_INCOME_DAYS`) trocam a string à mão por `{INCOME}` importado. Consequência assumida: a mediana de receita do plano e o dia do salário passam a ignorar (a) crédito com `refunded_by` preenchido e (b) entrada marcada pelo dono como "não é entrada" — é exatamente o que a dívida 033 pede: plano e tela lendo a mesma regra, para que um salário duplicado marcado na tela não continue inflando a projeção.
- Alternativa descartada: `INCOME` sem `refunded_by IS NULL`, para preservar os números do plano byte a byte — motivo: um crédito estornado não é receita, e `OUTFLOW` já aplica a mesma regra ao gasto; manter a assimetria seria carregar o erro só para não mexer num teste.
- Alternativa descartada: `EXCLUDED = f"({OUTFLOW} OR {INFLOW}) AND …"` — motivo: `amount_cents <> 0` diz o mesmo em uma comparação e sem parênteses no meio de um `WHERE` composto por `_where`.
- Alternativa descartada: deixar as três cópias e fechar a 033 depois — motivo: ao marcar uma entrada na tela, o plano continuaria contando; a divergência que a dívida existe para impedir seria criada por esta fatia.

### D2 — `View` ganha `"income"`; `set_not_expense` aceita saída ou entrada; erro renomeado para `NotCountableError`

- Escolha: em `app/queries/expenses.py`, `View = Literal["expenses", "excluded", "income"]`, `_PREDICATE["income"] = INCOME`. Nada mais muda ali para listar: `_where`, `_SELECT`, ordenação e `sum_expenses` já são agnósticos ao sinal (`abs(t.amount_cents)` no sort por valor). Em `app/taxonomy/override.py`, `set_not_expense` checa `SELECT 1 … WHERE id = ? AND ({OUTFLOW} OR {INFLOW})`; `NotAnOutflowError` vira `NotCountableError` (mensagem "lançamento não conta como gasto nem como entrada"). No router, `NOT_AN_OUTFLOW` vira `NOT_COUNTABLE = "Só um lançamento que conta como gasto ou como entrada pode ser marcado."`. `clear_not_expense` não muda. `GET /expenses/by-category` e `/month-signal` não mudam de código; `by-category?view=income` passa a ser aceito por herdar `View`, e o front nunca o chama (R9).
- Alternativa descartada: endpoint `PUT /{id}/not-income` separado — motivo: mesma coluna, mesmos motivos, mesma resposta; seria um segundo handler idêntico e um segundo fetcher no front.
- Alternativa descartada: manter o nome `NotAnOutflowError` — motivo: o nome mentiria (uma entrada passa) e o rename custa três linhas em dois arquivos e um teste.

### D3 — `period_result()` em `app/queries/expenses.py`, duas somas em SQL e a subtração em Python

- Escolha: `@dataclass(frozen=True) class PeriodResult: income_cents: int; spending_cents: int; balance_cents: int` e `def period_result(conn, *, date_from, date_to, account_id, search) -> PeriodResult` que chama `sum_expenses(view="income", …)` e `sum_expenses(view="expenses", …)` com os mesmos filtros e devolve `balance_cents = income_cents + spending_cents` (`spending_cents` é negativo, como todo `total_cents` do domínio — invariante 22). Cálculo determinístico, testado, sem IA (invariante 23). O router só traduz (norma 30).
- Alternativa descartada: uma única consulta com `SUM(CASE WHEN …)` — motivo: teria de repetir `INCOME` e `SPENDING` dentro de um `CASE` sobre um `WHERE` frouxo; duas chamadas a `sum_expenses` reaproveitam `_where` e ficam legíveis, e são duas somas indexadas por data.
- Alternativa descartada: devolver `spending_cents` positivo (valor absoluto) — motivo: todo total do domínio carrega o sinal; o front já usa `Math.abs` onde mostra.

### D4 — Contrato JSON

- `GET /api/transactions/expenses?view=expenses|excluded|income` · em `income`, `items`, `total` e `total_cents` são das entradas (`total_cents` positivo); `view=x` → 422 do FastAPI.
- `GET /api/transactions/expenses/period-result?from&to&account_id&q` · 200 `{ "income_cents": 600000, "spending_cents": -23490, "balance_cents": 576510 }`; `from`/`to` opcionais (mesmo `_date_bounds`, 422 se `to < from`); `q` passa por `_search_term`. Sem sessão → 401 pelo guard. Rota declarada junto de `by-category` e `month-signal`, antes das rotas `/{transaction_id}/…`.
- `PUT /api/transactions/{id}/not-expense` · agora 200 também para entrada; 422 "Só um lançamento que conta como gasto ou como entrada pode ser marcado." para transferência/estorno automáticos ou valor zero.
- `/openapi.json` lista `/api/transactions/expenses/period-result` e `income` no enum de `view` (norma 3).

### D5 — `view=income` na URL; textos por vista num mapa; `PeriodResult` no `header`; teto e categorias só em `expenses`

- Escolha: `readView` devolve `'income'` para `'income'`, `'excluded'` para `'excluded'`, senão `'expenses'`; `writeView` grava `view` sempre que diferente de `expenses`. `get-expenses.ts` passa `view` quando `query.view !== 'expenses'`. Em `expenses-list.tsx`, `const VIEW_TEXT: Record<ExpenseView, { loading, error, emptyFiltered, emptyAll, noun, excludedNotice }>` concentra os textos (hoje espalhados em ternários): `expenses` mantém os atuais; `excluded` mantém "Nenhum lançamento marcado como não-gasto." nos dois vazios e `lançamento(s)`; `income`: "Carregando entradas…", "Não foi possível carregar as entradas.", "Nenhuma entrada nesse período.", "Nenhuma entrada registrada ainda.", `entrada`/`entradas`, e o aviso "{descrição} não conta mais como entrada.". `header`: barra → `{period.kind !== 'all' ? <PeriodResult query={{ from, to, account, search }} /> : null}` → `{period.kind === 'month' && view === 'expenses' ? <MonthCeiling …/> : null}` → `{view === 'expenses' ? <CategoryTotals query={filters} /> : null}`.
- Alternativa descartada: mostrar `PeriodResult` só quando `from` **e** `to` estão preenchidos — motivo: um intervalo "desde 01/09" ainda é um período com resultado; `period.kind !== 'all'` é o que a tela chama de "período filtrado" (R5) e o endpoint aceita as bordas opcionais como os outros.
- Alternativa descartada: `CategoryTotals` também em `excluded` (como hoje) — motivo: R9 pede só em "Gastos"; e "Por categoria" de um misto de positivos e negativos marcados somaria sinais opostos.

### D6 — `NotExpenseControl` e `ExpenseItem` com rótulos por vista; positivo em verde; "Voltar a contar"

- Escolha: em `not-expense-control.tsx`, `const MARK_TEXT: Record<'expenses' | 'income', { button, ariaLabel(name), error }>` = `expenses`: "Não é gasto" / `Marcar ${name} como não-gasto` / "Não foi possível marcar como não-gasto."; `income`: "Não é entrada" / `Marcar ${name} como não-entrada` / "Não foi possível marcar como não-entrada.". O fluxo (seletor "Motivo", "Confirmar", "Cancelar", "Salvando…", "Tentar de novo", `Escape`) é o mesmo código. Modo `excluded`: botão "Voltar a contar" (`aria-label` `Voltar ${name} a contar`), erro "Não foi possível voltar a contar." — um rótulo que serve ao gasto e à entrada (R8). Em `expense-item.tsx`: `amountColor` = `amount_cents < 0 ? 'text-red-700' : amount_cents > 0 ? 'text-green-700' : 'text-gray-900'` (vale nas três vistas; em `expenses` nunca há positivo); em `income` a coluna da direita é data → valor → controle, sem `CategoryPicker` nem selo (R6; categorizar entradas está fora de escopo).
- Alternativa descartada: selo só-leitura da categoria na entrada — motivo: entrada raramente tem categoria útil e R6 diz "não tem categoria"; um selo vazio ou "Sem categoria" ocuparia espaço sem informação.
- Alternativa descartada: componente `NotIncomeControl` separado — motivo: mesmo estado, mesma mutation, mesmo endpoint; só mudam quatro strings.
- Alternativa descartada: manter "Voltar a ser gasto" e acrescentar "Voltar a ser entrada" por sinal — motivo: R8 pede um rótulo que sirva aos dois; e o botão vive na vista mista.

### D7 — `PeriodResult`: fetcher próprio, chave sob `['expenses']`, bloco no molde do "Painel de situação"

- Escolha: `types/expense.ts`: `PeriodResultQuery = Pick<ExpensesQuery, 'from' | 'to' | 'account' | 'search'>`, `PeriodResultResponse { income_cents; spending_cents; balance_cents }`. `api/get-period-result.ts` (molde de `get-month-signal.ts`): `getPeriodResult(query)` monta `from`, `to`, `account_id`, `q`; `periodResultQueryOptions` com chave `['expenses', 'period-result', query]` e `keepPreviousData`; `usePeriodResult`. Por estar sob `['expenses']`, a invalidação de `useSetNotExpense`/`useClearNotExpense` já a cobre (R7) sem mexer nas mutations. `components/period-result.tsx`: `PeriodResult({ query })` com carregando (`role="status"` "Carregando resultado do período…"), erro (`Alert` "Não foi possível carregar o resultado do período." + "Tentar de novo") e dados: `<section aria-labelledby>` com `<h2>` "Resultado do período" e um `<dl>` de três pares — "Entradas" (`formatMoney(income_cents)`, `text-green-700`), "Gastos" (`formatMoney(Math.abs(spending_cents))`, `text-red-700`), "Saldo" (`formatMoney(Math.abs(balance_cents))` com sinal "−" prefixado quando negativo; `text-green-700` se > 0, `text-red-700` se < 0, `text-gray-900` se 0). Receita nova "Painel de resultado" no `design.md` (ver Interface).
- Alternativa descartada: calcular no front a partir de `total_cents` das duas listas — motivo: exigiria duas consultas paginadas por vista; e cálculo financeiro fica no servidor, em SQL (invariante 23, norma 33).
- Alternativa descartada: incluir o resultado na resposta de `GET /expenses` — motivo: acoplaria a lista paginada a um agregado que não depende de página nem de vista; um fetcher por operação (`project-structure`).

## Interface

Receitas do `docs/design.md` usadas: barra de controles de lista (004), linha de lançamento (003), selo de status cinza (motivo), aviso com desfazer (015), painel de situação (002), subtítulo `h2`, carregando, vazio, erro, botão principal/secundário. Receitas novas a acrescentar nesta entrega:

| Padrão | Classes | Fatia |
|---|---|---|
| Painel de resultado | `<section>` com `<h2 className="mt-6 text-lg font-semibold">`; `<dl className="mt-2 flex flex-wrap gap-x-8 gap-y-2 rounded-md border border-gray-200 p-4">`; cada par em `<div className="min-w-0">` com `<dt className="text-sm text-gray-600">` e `<dd className="tabular-nums font-medium">` + cor do sinal | 016 |
| Valor de entrada | par do "Valor monetário" para positivo que é receita: `text-green-700` | 016 |

### Tela: Gastos (`/app/expenses`) — qualquer vista, com período filtrado

Abaixo da barra de controles e acima do "Teto do mês": `<h2>` "Resultado do período" e o painel com "Entradas" R$ 6.000,00 (verde), "Gastos" R$ 234,90 (vermelho), "Saldo" R$ 5.765,10 (verde; negativo em vermelho com "−"; zero em cinza escuro). Em 360px os três pares quebram em linhas.

- Carregando: "Carregando resultado do período…" (`role="status"`).
- Erro: `Alert` "Não foi possível carregar o resultado do período." + "Tentar de novo".
- Sem período ("todo o período"): o bloco não existe.

### Tela: Gastos — modo "Entradas" (`?view=income`)

Barra igual, "Mostrar" com "Entradas" selecionado (opções na ordem "Gastos", "Não são gastos", "Entradas"). Sem "Teto do mês" e sem "Por categoria". Lista: esquerda descrição, recebedor, conta; direita data → valor em verde → botão secundário "Não é entrada". Rodapé: "Página 1 de 1 · 1 entrada · R$ 6.000,00 no período".

- Carregando: "Carregando entradas…" (`role="status"`).
- Vazio com filtro: "Nenhuma entrada nesse período."; sem filtro: "Nenhuma entrada registrada ainda.".
- Erro: `Alert` "Não foi possível carregar as entradas." + "Tentar de novo".
- "Não é entrada": no lugar do botão, `<label>` "Motivo" + `<select>` com foco ("Transferência entre minhas contas" selecionada, "Estorno", "Outro") + "Confirmar" (principal) + "Cancelar"; `Escape` cancela; "Salvando…" com botões `disabled`; erro (`role="alert"`) "Não foi possível marcar como não-entrada." + "Tentar de novo".
- Depois de confirmar: aviso verde "SALARIO não conta mais como entrada." com "Desfazer" acima da lista; a linha some; rodapé e "Resultado do período" já vêm sem ela. Se era a última, o vazio "Nenhuma entrada nesse período." aparece abaixo do aviso. "Desfazer"/"Desfazendo…"/"Não foi possível desfazer." como em 015.

### Tela: Gastos — modo "Não são gastos" (`?view=excluded`)

Como em 015, com duas mudanças: a lista traz também os positivos marcados (valor em verde; negativos em vermelho) e o botão de cada linha é "Voltar a contar" ("Salvando…"; erro "Não foi possível voltar a contar." + "Tentar de novo"). Sem "Por categoria". Vazio: "Nenhum lançamento marcado como não-gasto." (inalterado).

### Tela: Gastos — modo "Gastos"

Inalterado, exceto o bloco "Resultado do período" acima do "Teto do mês" quando há período.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/queries/spending.py` | `_CLEAN`, `INFLOW`, `INCOME`; `EXCLUDED` com `amount_cents <> 0` (D1) | — |
| alterar | `app/plan/objective.py` | `_INCOME` usa `{INCOME}` importado (D1) | — |
| alterar | `app/projection/monthly.py` | `_INCOME` usa `{INCOME}` importado (D1) | — |
| alterar | `app/projection/forecast.py` | `_INCOME_DAYS` usa `{INCOME}` importado (D1) | — |
| alterar | `app/queries/expenses.py` | `View` com `"income"`, `_PREDICATE["income"]`; `PeriodResult`, `period_result()` (D2, D3) | — |
| alterar | `app/taxonomy/override.py` | `NotAnOutflowError` → `NotCountableError`; `set_not_expense` aceita `OUTFLOW OR INFLOW` (D2) | — |
| alterar | `app/routers/transactions.py` | `NOT_COUNTABLE`; `PeriodResultResponse`; `GET /expenses/period-result` (D2, D3, D4) | `api-requests` |
| alterar | `tests/test_spending.py` | `INCOME` e `INFLOW` exportados; positivo com `refunded_by` ou `not_expense_reason` fica fora de `INCOME`; `EXCLUDED` pega positivo e negativo marcados (via `SELECT count(*) WHERE {EXCLUDED}`) | `unit-testing` |
| alterar | `tests/test_projection.py` | salário marcado com `not_expense_reason = 'other'` sai da mediana de `income_cents` e do `income_day`; crédito com `refunded_by` idem | `unit-testing` |
| alterar | `tests/test_override.py` | `set_not_expense` em entrada grava; transferência positiva e estorno positivo → `NotCountableError`; renomear o teste existente de saída | `unit-testing` |
| alterar | `tests/test_expenses_api.py` | `view=income` lista só positivos limpos, `total_cents` positivo, ordena por `abs`; `period-result`: 401 sem sessão, `{income, spending, balance}` com `from`/`to`, com `account_id`, com `q`, `to < from` → 422; `PUT` em entrada → 200, some de `income`, aparece em `excluded` junto com um gasto marcado, `period-result` cai, `by-category` e `month-signal` iguais; `DELETE` devolve; `_load` repetido mantém a marca (R11); `PUT` em transferência positiva → 422 com a mensagem nova; `/openapi.json` lista `period-result` e `income` | `api-requests`, `unit-testing` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/features/expenses/types/expense.ts` | `ExpenseView` com `'income'`; `PeriodResultQuery`, `PeriodResultResponse` (D5, D7) | — |
| alterar | `src/features/expenses/api/get-expenses.ts` | `view` na URL quando `!== 'expenses'` (D5) | `api-requests` |
| criar | `src/features/expenses/api/get-period-result.ts` | `getPeriodResult`, `periodResultQueryOptions` (`['expenses', 'period-result', query]`), `usePeriodResult` (D7) | `api-requests` |
| criar | `src/features/expenses/components/period-result.tsx` | `PeriodResult({ query })`: carregando, erro, painel de resultado com cor por sinal (D7) | `interface-design`, `error-handling` |
| alterar | `src/features/expenses/components/view-select.tsx` | opção "Entradas" (D5) | `interface-design` |
| alterar | `src/features/expenses/components/not-expense-control.tsx` | `MARK_TEXT` por vista; "Voltar a contar" em `excluded` (D6) | `interface-design` |
| alterar | `src/features/expenses/components/expense-item.tsx` | `amountColor` por sinal; sem `CategoryPicker`/selo em `income` (D6) | `interface-design` |
| alterar | `src/features/expenses/components/expenses-list.tsx` | `readView`/`writeView` com `income`; `VIEW_TEXT`; `PeriodResult` no `header` quando `period.kind !== 'all'`; `CategoryTotals` só em `expenses`; `noun` e aviso por vista (D5) | `client-state`, `interface-design` |
| alterar | `src/testing/mocks/handlers.ts` | três `fakeExpenses` positivos em 2026-08 (ex.: id 46 "SALARIO EMPRESA X" 600000, 47 "PIX RECEBIDO" 15000, 48 "RENDIMENTO CDB" 3250), `not_expense_reason: null`; `filterExpenses`: `income` → `amount_cents > 0 && reason === null`, `excluded` → `reason !== null`, senão `amount_cents < 0 && reason === null`; handler `GET /api/transactions/expenses/period-result` somando pelos mesmos filtros; `PUT …/not-expense` sem restrição de sinal (D4) | `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/view-select.test.tsx` | três opções na ordem; `onChange('income')` | `component-testing` |
| alterar | `src/features/expenses/components/__tests__/not-expense-control.test.tsx` | `view='income'`: "Não é entrada", `aria-label`, mesmo `PUT`, erro "Não foi possível marcar como não-entrada."; `excluded`: "Voltar a contar" e erro "Não foi possível voltar a contar." | `component-testing`, `api-mocking` |
| criar | `src/features/expenses/components/__tests__/period-result.test.tsx` | carregando; erro + "Tentar de novo"; dados com "Entradas", "Gastos", "Saldo" e classes verde/vermelha/neutra; `q`/`account_id` na URL chamada | `component-testing`, `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | `?view=income&month=2026-08` → 3 entradas em verde, sem "Por categoria" nem "Teto do mês", rodapé "3 entradas · R$ 6.182,50 no período", nenhum `combobox` de categoria; "Resultado do período" com `?month=2026-08` em `expenses` e em `income`, ausente sem período; marcar "SALARIO EMPRESA X" → aviso "… não conta mais como entrada.", some da lista, "Entradas" do resultado cai; "Desfazer" devolve; `?view=excluded` lista o positivo marcado junto de um negativo marcado, "Voltar a contar" devolve; `readView('income')`; trocar "Mostrar" grava `?view=income` e apaga `page` | `component-testing`, `api-mocking` |
| alterar | `e2e/expenses.spec.ts` | teste novo (antes de "goes back…"): login → `?month=2026-09` → "Resultado do período" com "Entradas" R$ 6.000,00, "Gastos" R$ 234,90, "Saldo" R$ 5.765,10 → "Mostrar" = "Entradas" → URL contém `view=income`, linha SALARIO, "1 entrada · R$ 6.000,00 no período", sem "Por categoria" → "Não é entrada" → motivo "Outro" → "Confirmar" → aviso "SALARIO não conta mais como entrada.", "Nenhuma entrada nesse período.", "Entradas" R$ 0,00 e "Saldo" negativo em vermelho → `reload` mantém → "Mostrar" = "Não são gastos" → linha SALARIO com selo "Outro", "1 lançamento · R$ 6.000,00 no período" → "Voltar a contar" → "Mostrar" = "Entradas" → "1 entrada · R$ 6.000,00 no período" (base como encontrou) | `e2e-testing` |
| alterar | `docs/design.md` | linhas "Painel de resultado" e "Valor de entrada" (fatia 016) | `interface-design` |
| alterar | `docs/roadmap.md` | item 033 → `done` (fechado por esta fatia; corrigir os caminhos para `app/projection/`); item 016 → `review` ao abrir o PR | — |

## Estimativa de tamanho

Jornadas: 1 (ver o que entrou e se o período fechou no positivo; "Não é entrada" é a correção da própria lista, no mesmo molde em que 015 tratou o gasto) · Telas novas: 0 · Linhas alteradas (sem testes e sem mocks): ~60 Python (`spending.py` ~8, três módulos do plano ~9, `expenses.py` ~18, `override.py` ~8, `transactions.py` ~30) + ~175 em `src/` (tipos ~10, `get-expenses.ts` ~2, `get-period-result.ts` ~30, `period-result.tsx` ~70, `view-select.tsx` ~1, `not-expense-control.tsx` ~20, `expense-item.tsx` ~8, `expenses-list.tsx` ~35) + ~3 em docs; ~240 no total · Fases previstas: 2 (1: `INFLOW`/`INCOME`/`EXCLUDED`, os três módulos do plano, `View` com `income`, `period_result`, `override.py`, rota `period-result` e mensagem nova, testes Python, handlers MSW; 2: tipos, `get-period-result.ts`, `PeriodResult`, `ViewSelect`, `NotExpenseControl`, `ExpenseItem`, `ExpensesList`, testes de componente, e2e, `design.md`, `roadmap.md`).

Sinais de "grande demais": 1 jornada, 0 telas novas, 2 fases, ~240 linhas — nenhum dispara.

## Dívida encontrada

- `docs/roadmap.md` item 033 aponta `app/plan/forecast.py` e `app/plan/monthly.py`; os arquivos vivem em `app/projection/`. Corrige-se na linha do item ao fechá-lo nesta fatia (documento canônico sem cicatriz, norma 7).
- `src/testing/mocks/handlers.ts` passa a duplicar também a regra de entrada (`filterExpenses` com `income`) e o cálculo de `period-result`; é o papel do mock, registrado como nas SPECs 013–015.
- Dívidas 026 (precedência do nome do recebedor), 031 (plural de "gasto" em três lugares — `VIEW_TEXT` desta fatia é mais um consumidor de `noun`, o que reforça o item) e 034 (`_write` reclassifica sem necessidade) inalteradas.
