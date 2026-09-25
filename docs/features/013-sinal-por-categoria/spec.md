# SPEC 013 — sinal por categoria

Décima terceira fatia da SPA. No bloco "Por categoria" da página "Gastos" (`/app/expenses`, fatia 008), cada categoria com limite mensal (fatia 012) passa a mostrar, quando o filtro é um mês fechado, um selo "Dentro" / "Atenção" / "Acima", o texto "R$ gasto de R$ limite · NN%" e, no topo do bloco, "N categorias acima do limite". Fora de um mês fechado, nenhum sinal e o aviso "Sinal só por mês". O cálculo é do servidor: a resposta de `GET /api/transactions/expenses/by-category` ganha o limite e o sinal por grupo, a contagem de "Acima" e o escopo do sinal; o cliente só formata.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/queries/expenses.py` · `_FROM` já faz `LEFT JOIN categories AS c ON c.name = t.category` (com o comentário de que `categories.name` é `UNIQUE`); `_BY_CATEGORY` seleciona `category`, `label`, `count`, `total`; `CategoryTotal(category, label, count, total_cents)`; `sum_by_category(conn, *, date_from, date_to, account_id, search)` com `GROUP BY NULLIF(t.category, '')`.
- `app/routers/transactions.py` · `_date_bounds(from_, to) -> (str | None, str | None)` (ISO ou `None`), `_search_term(q)`, `CategoryGroup`, `CategoryTotalsResponse { groups, total_cents }`, handler `expenses_by_category`.
- `app/taxonomy/catalogue.py` · `set_monthly_limit`, `InvalidLimitError`; `categories.monthly_limit_cents INTEGER NULL CHECK (> 0)` (migração `021`). Não existe nenhuma função de sinal/limite em `app/plan/` (`objective.py`, `timeline.py`, `whatif.py` tratam do plano de recuperação, não de limite por categoria) nem em `app/queries/spending.py`; o `_last_day(month)` de `app/plan/objective.py` é privado e recebe `AAAA-MM`, não serve para comparar duas datas.
- `src/features/expenses/types/expense.ts` · `CategoryGroup { category, label, count, total_cents }`, `CategoryTotalsResponse { groups, total_cents }`, `CategoryTotalsQuery`.
- `src/features/expenses/api/get-category-totals.ts` · chave `['expenses', 'by-category', query]`, `keepPreviousData`.
- `src/features/expenses/components/category-totals.tsx` · `CategoryTotals({ query })`: carregando (`role="status"`), erro (`Alert` + "Tentar de novo"), `null` quando vazio, `<section aria-labelledby>` com `<h2>` "Por categoria", `<table>` com `<thead className="sr-only">` (Categoria, Gastos, Total) e `<tr key={group.category ?? ''}>` com três `<td>`; `VISIBLE_GROUPS = 8` e o botão "Mostrar todas (N)"/"Mostrar menos".
- `src/features/expenses/components/expenses-list.tsx` · `filters: CategoryTotalsQuery = { from, to, account, search }` vindo de `readPeriod` + `toDateBounds` (mês → `monthRange`, primeiro e último dia); `<CategoryTotals query={filters} />`.
- `src/features/categories/api/set-category-limit.ts` · `useSetCategoryLimit` invalidando só `['categories']` (dívida deixada pela SPEC 012 para esta fatia).
- `src/utils/format-money.ts:formatMoney(cents)`.
- `src/testing/mocks/handlers.ts` · `filterExpenses(url)`, `groupByCategory(items)` (chave = `item.category`, que nos mocks é o **rótulo**), handler `GET /api/transactions/expenses/by-category`; `fakeCategories` com `monthly_limit_cents` (Alimentação `80000`, Compras `150000`, demais `null`); `fakeExpenses` (45 gastos de 2026-06-18 a 2026-08-01: em 2026-08 só o id 45, "Compras" -8490; 2026-07 tem os ids 14–44).
- `tests/data/e2e_transactions.json` · 2026-08: "AÇOUGUE SÃO JORGE" -60,00 (`Groceries` → "Supermercado"), "FARMACIA CENTRAL" -45,00 (`Health` → "Saúde"). `e2e/categories.spec.ts` já define e apaga limite pela tela e visita `/app/expenses?month=2026-08`.
- `docs/design.md` · "Selo de status" com pares verde/âmbar/cinza, "Selo de erro" (par vermelho), "Tabela de totais" (008).

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `signal_for(spent_cents, limit_cents)` em `app/taxonomy/limits.py`: `over` se `spent > limit`, `warning` se `spent * 5 >= limit * 4`, senão `within` (D1). O router só aplica quando `is_whole_month(date_from, date_to)` (D2). A linha mostra o selo "Dentro" (verde), "Atenção" (âmbar) ou "Acima" (vermelho) conforme `group.signal` (D5). |
| R2 | A resposta traz `limit_cents` por grupo (D3); a linha com `signal !== null` mostra `${formatMoney(spent)} de ${formatMoney(limit)} · ${percent}%`, com `spent = Math.abs(total_cents)` e `percent = Math.round((spent / limit) * 100)` — só formatação (D5). |
| R3 | `limit_cents: null` ⇒ `signal: null` no servidor (D3); no cliente a linha sem `signal` renderiza exatamente o que a fatia 008 renderiza (D5). |
| R4 | `is_whole_month` falso ⇒ `signal_scope: 'none'` e `signal: null` em todos os grupos, com `limit_cents` ainda preenchido (D2, D3); o bloco mostra "Sinal só por mês" quando `signal_scope === 'none'` e algum grupo tem `limit_cents !== null`; a tabela segue igual (D5). |
| R5 | `over_limit_count` no topo da resposta, contado no servidor (D3); com `> 0`, `<p>` "1 categoria acima do limite" / "N categorias acima do limite" entre o `<h2>` e a tabela; com `0`, nada (D5). |
| R6 | Nada muda na chave da query: `['expenses', 'by-category', filters]` já troca ao mudar o período; o sinal viaja na mesma resposta (D4). |
| R7 | Sinal, limite, escopo e contagem saem de `app/taxonomy/limits.py` e do router, em inteiros; o cliente só calcula a porcentagem de exibição e a formatação (D1, D3, D5). Norma 23. |

## Decisões técnicas

### D1 — Regra pura em `app/taxonomy/limits.py`: `signal_for` e `is_whole_month`

- Escolha: módulo novo `app/taxonomy/limits.py` com `Signal = Literal["within", "warning", "over"]`, `Scope = Literal["month", "none"]`, `def signal_for(spent_cents: int, limit_cents: int | None) -> Signal | None` (`None` se `limit_cents is None`; `"over"` se `spent_cents > limit_cents`; `"warning"` se `spent_cents * 5 >= limit_cents * 4`; senão `"within"`; só inteiros, sem ponto flutuante) e `def is_whole_month(date_from: str | None, date_to: str | None) -> bool` (ambos não nulos, `date_from` termina em `-01`, `date_to == f"{date_from[:7]}-{monthrange(y, m)[1]:02d}"`). O limite é atributo da categoria (`catalogue.set_monthly_limit` já mora em `app/taxonomy`), então a regra que o interpreta fica no mesmo domínio.
- Alternativa descartada: função dentro de `app/queries/expenses.py` — motivo: `app/queries` é junção e agregação em SQL (norma 33); uma regra sem SQL ali é teste de unidade misturado com fixture de banco.
- Alternativa descartada: `app/plan/` — motivo: o pacote é o plano de recuperação (piso, reserva, alavancas); o limite por categoria não é dele, e a fatia 014 (teto do mês) é quem terá algo em `plan`.
- Alternativa descartada: calcular o sinal em SQL (`CASE WHEN`) — motivo: a regra dos 80% ficaria em texto SQL sem teste isolado; em Python ela é uma função de quatro linhas testada com seis casos.

### D2 — Escopo do sinal decidido pelas datas normalizadas, no router

- Escolha: `expenses_by_category` calcula `scope: Scope = "month" if is_whole_month(date_from, date_to) else "none"` a partir do que `_date_bounds` devolveu, e monta cada `CategoryGroup` com `signal=signal_for(abs(g.total_cents), g.limit_cents) if scope == "month" else None`; `over_limit_count = sum(1 for g in groups if g.signal == "over")`. O front já manda `from`/`to` como primeiro e último dia do mês quando o filtro é `?month=` (`monthRange`), então o servidor reconhece o mês sem parâmetro novo.
- Alternativa descartada: parâmetro `month=AAAA-MM` no endpoint — motivo: dois jeitos de dizer o mesmo período; o contrato entregue em 008 já é suficiente e o teste de API prova que `from=2026-08-01&to=2026-08-31` é mês fechado e `to=2026-08-30` não é.
- Alternativa descartada: proporcionalizar o limite fora do mês fechado — motivo: premissa registrada no PRD (menos honesto que não mostrar).

### D3 — Contrato JSON de `GET /api/transactions/expenses/by-category`

- Escolha: `_BY_CATEGORY` ganha `max(c.monthly_limit_cents) AS limit_cents` (a junção com `categories` já existe em `_FROM`; `max` porque o grupo é uma categoria só e o agregado deixa a intenção explícita); `CategoryTotal` ganha `limit_cents: int | None`. No router, `CategoryGroup` ganha `limit_cents: int | None` e `signal: Signal | None`; `CategoryTotalsResponse` ganha `over_limit_count: int` e `signal_scope: Scope`. Resposta 200: `{ "groups": [ { "category": "Groceries", "label": "Supermercado", "count": 1, "total_cents": -6000, "limit_cents": 5000, "signal": "over" }, { "category": "Health", "label": "Saúde", "count": 1, "total_cents": -4500, "limit_cents": null, "signal": null } ], "total_cents": -10500, "over_limit_count": 1, "signal_scope": "month" }`. Com `from`/`to` que não formam um mês fechado, ou sem `from`/`to`: todos os `signal: null`, `over_limit_count: 0`, `signal_scope: "none"`, `limit_cents` ainda preenchido. Demais validações, 401 e ordenação como em 008. Front: `CategoryGroup` ganha `limit_cents: number | null` e `signal: CategorySignal | null` (`type CategorySignal = 'within' | 'warning' | 'over'`); `CategoryTotalsResponse` ganha `over_limit_count: number` e `signal_scope: 'month' | 'none'`.
- Alternativa descartada: endpoint separado `/expenses/limits` — motivo: o cliente teria de cruzar duas listas por chave; R6 pede que tudo mude junto com o filtro, e um campo a mais na resposta existente custa uma coluna no SQL.
- Alternativa descartada: devolver `percent` do servidor — motivo: é arredondamento de exibição, não regra; o servidor entrega os dois inteiros e o cliente formata (norma 23 não é violada: nenhuma decisão depende do percentual).

### D4 — Sem query nova; `useSetCategoryLimit` passa a invalidar `['expenses']`

- Escolha: `get-category-totals.ts` fica intocado; a resposta maior chega pela mesma chave. Em `set-category-limit.ts`, `onSuccess` invalida `['categories']` e `['expenses']` — o bloco "Por categoria" agora depende do limite, e o prefixo `['expenses']` cobre `['expenses', 'by-category', …]`, como `useRenameCategory` já faz.
- Alternativa descartada: invalidar só `['expenses', 'by-category']` — motivo: chave mais específica sem ganho; a lista de gastos é barata e o padrão dos outros hooks é o prefixo.

### D5 — `CategoryTotals` mostra selo, texto do limite, resumo e aviso; nenhuma coluna nova

- Escolha: em `category-totals.tsx`, a primeira `<td>` de cada linha passa a empilhar: linha 1 `flex items-center gap-2` com o rótulo (`min-w-0 truncate`) e, se `group.signal !== null`, um `<span>` selo de status (`shrink-0`) com "Dentro" (`bg-green-100 text-green-800`), "Atenção" (`bg-amber-100 text-amber-800`) ou "Acima" (`bg-red-100 text-red-800`); linha 2, só com `signal !== null`, `<p className="text-xs text-gray-600 tabular-nums">` "R$ 60,00 de R$ 50,00 · 120%". As colunas de contagem e total não mudam. Entre o `<h2>` e a tabela: se `data.over_limit_count > 0`, `<p className="mt-2 text-sm font-medium text-red-800">` "1 categoria acima do limite" / "N categorias acima do limite"; se `data.signal_scope === 'none'` e `data.groups.some((g) => g.limit_cents !== null)`, `<p className="mt-2 text-sm text-gray-600">` "Sinal só por mês". Mapa `SIGNAL_LABELS: Record<CategorySignal, { text: string; className: string }>` no próprio arquivo (uso único; não vai para `components/ui/`). A porcentagem: `Math.round((Math.abs(total_cents) / limit_cents) * 100)`, sempre com `limit_cents > 0` garantido pelo `CHECK` do banco.
- Alternativa descartada: quarta coluna "Sinal" — motivo: em 360px as três colunas já usam a largura; selo junto do rótulo e o texto embaixo cabem sem quebrar a receita "Tabela de totais".
- Alternativa descartada: barra de progresso — motivo: fora de escopo ("gráfico") e o PRD pede selo e porcentagem.
- Alternativa descartada: recalcular o sinal no cliente a partir de `limit_cents` — motivo: R7; o cliente só lê `signal`.

## Interface

Receitas do `docs/design.md` usadas: subtítulo, tabela de totais (008), selo de status (pares verde e âmbar), selo de erro (par vermelho), texto secundário. Receita nova a acrescentar ao `docs/design.md` nesta entrega:

| Padrão | Classes | Fatia |
|---|---|---|
| Célula com selo e subtexto | primeira `<td>` da "Tabela de totais" com `<div className="flex items-center gap-2">` (rótulo `min-w-0 truncate` + selo de status `shrink-0`) e abaixo `<p className="text-xs text-gray-600 tabular-nums">` | 013 |

### Tela: Gastos (`/app/expenses`) — só o que muda no bloco "Por categoria"

- Com dados e filtro em mês fechado (`?month=2026-08`): `<h2>` "Por categoria"; se houver categoria em "Acima", logo abaixo, em vermelho: "1 categoria acima do limite" (ou "3 categorias acima do limite"); tabela como em 008, onde a linha de categoria **com limite** mostra o rótulo seguido do selo "Dentro" (verde), "Atenção" (âmbar) ou "Acima" (vermelho) e, embaixo, em tom suave, "R$ 60,00 de R$ 50,00 · 120%"; a linha **sem limite** fica idêntica à de 008. Contagem e total à direita, inalterados.
- Com dados e filtro em intervalo ou todo o período: sem selo e sem subtexto em nenhuma linha; se alguma categoria da tabela tem limite, abaixo do `<h2>`, em tom suave: "Sinal só por mês". Sem categoria com limite, nada a mais.
- Carregando, erro e vazio: inalterados ("Carregando totais por categoria…", "Não foi possível carregar os totais por categoria." + "Tentar de novo", bloco ausente).
- Em 360px: o rótulo trunca antes do selo (`min-w-0 truncate` + `shrink-0`); o subtexto fica na linha de baixo; não há rolagem horizontal.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `app/taxonomy/limits.py` | `Signal`, `Scope`, `signal_for(spent_cents, limit_cents)`, `is_whole_month(date_from, date_to)` (D1) | — |
| alterar | `app/queries/expenses.py` | `_BY_CATEGORY` com `max(c.monthly_limit_cents) AS limit_cents`; `CategoryTotal.limit_cents: int \| None`; `sum_by_category` preenche (D3) | — |
| alterar | `app/routers/transactions.py` | `CategoryGroup.limit_cents`, `.signal`; `CategoryTotalsResponse.over_limit_count`, `.signal_scope`; `expenses_by_category` aplica `is_whole_month`, `signal_for` e conta os `over` (D2, D3) | `api-requests` |
| criar | `tests/test_limits.py` | `signal_for`: `None` sem limite; `(0, 100)` → `within`; `(79, 100)` → `within`; `(80, 100)` → `warning`; `(100, 100)` → `warning`; `(101, 100)` → `over`; `(4, 5)` → `warning` (inteiros, sem ponto flutuante). `is_whole_month`: `("2026-08-01", "2026-08-31")` → `True`; `("2026-02-01", "2026-02-28")` → `True`; `("2024-02-01", "2024-02-29")` → `True`; `("2026-08-01", "2026-08-30")`, `("2026-08-02", "2026-08-31")`, `("2026-07-01", "2026-08-31")`, `(None, "2026-08-31")`, `(None, None)` → `False` | `unit-testing` |
| alterar | `tests/test_expenses_api.py` | `by-category` com `from=2026-08-01&to=2026-08-31`: categoria com limite `5000` e gasto -6000 → `limit_cents: 5000`, `signal: "over"`, `over_limit_count: 1`, `signal_scope: "month"`; gasto -4000 com limite `5000` → `"warning"`; -3000 → `"within"`; sem limite → `limit_cents: None`, `signal: None`; grupo `category: None` → `limit_cents: None`; mesmo cenário com `to=2026-08-30`, só `from`, ou sem datas → todos `signal: None`, `over_limit_count: 0`, `signal_scope: "none"` e `limit_cents` mantido; `PUT /api/categories/{key}/limit` seguido de `by-category` reflete o sinal; contrato de 008 (`total_cents`, ordem, `label`) inalterado; `/openapi.json` mostra `limit_cents`, `signal`, `over_limit_count`, `signal_scope` no schema da resposta | `api-requests`, `unit-testing` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/features/expenses/types/expense.ts` | `CategorySignal`; `CategoryGroup.limit_cents`, `.signal`; `CategoryTotalsResponse.over_limit_count`, `.signal_scope` (D3) | — |
| alterar | `src/features/expenses/components/category-totals.tsx` | selo por `signal`, subtexto "R$ X de R$ Y · NN%", resumo "N categorias acima do limite", aviso "Sinal só por mês" (D5) | `interface-design`, `component-robustness` |
| alterar | `src/features/categories/api/set-category-limit.ts` | `onSuccess` invalida também `['expenses']` (D4) | `api-requests` |
| alterar | `src/testing/mocks/handlers.ts` | handler de `by-category`: `signal_scope` = `'month'` se `from` termina em `-01` e `to` é o último dia do mesmo mês (cálculo inline com `Date.UTC(y, m, 0)`); por grupo, `limit_cents` = `fakeCategories.find((c) => c.label === group.label)?.monthly_limit_cents ?? null`; `signal` pela mesma regra inteira (`spent > limit` → `'over'`; `spent * 5 >= limit * 4` → `'warning'`; senão `'within'`) só em `'month'`; `over_limit_count` | `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/category-totals.test.tsx` | com `server.use` e resposta explícita: grupo `signal: 'over'` mostra selo "Acima" e "R$ 60,00 de R$ 50,00 · 120%"; `'warning'` → "Atenção"; `'within'` → "Dentro"; `signal: null` com `limit_cents: null` → sem selo e sem subtexto; `over_limit_count: 1` → "1 categoria acima do limite"; `2` → "2 categorias acima do limite"; `0` → texto ausente; `signal_scope: 'none'` com algum `limit_cents` → "Sinal só por mês"; `'none'` sem nenhum limite → aviso ausente; `'month'` → aviso ausente; porcentagem arredondada (`total_cents: -33333`, `limit_cents: 100000` → "33%") | `component-testing`, `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | `?month=2026-07` com o mock padrão: "Compras" (limite 150000, gasto do mês acima disso) mostra "Acima" e "1 categoria acima do limite"; "Alimentação" (limite 80000, 1 gasto) mostra "Dentro"; "Transporte" sem selo; sem parâmetro de período (todo o período) → "Sinal só por mês" e nenhum selo | `component-testing`, `api-mocking` |
| alterar | `src/features/categories/components/__tests__/categories-list.test.tsx` | o espião de `invalidateQueries` ao salvar limite passa a esperar também `{ queryKey: ['expenses'] }` | `component-testing` |
| alterar | `e2e/expenses.spec.ts` | teste novo: login → "Categorias" → "Definir limite de Supermercado" → `50` → Enter → "Limite: R$ 50,00" → `goto('/app/expenses?month=2026-08')` → linha "Supermercado" da tabela "Por categoria" contém "Acima" e "R$ 60,00 de R$ 50,00 · 120%"; "1 categoria acima do limite" visível; linha "Saúde" sem "Dentro"/"Atenção"/"Acima" → `goto('/app/expenses?from=2026-08-01&to=2026-08-15')` → "Sinal só por mês" visível e nenhum selo → "Categorias" → limite de Supermercado apagado (campo vazio + Enter) → "Sem limite" → `goto('/app/expenses?month=2026-08')` → sem selo e sem "acima do limite" (deixa a base como encontrou, como `categories.spec.ts` faz) | `e2e-testing` |
| alterar | `docs/design.md` | linha "Célula com selo e subtexto" (fatia 013) | `interface-design` |
| alterar | `docs/roadmap.md` | item 013 → `review` ao abrir o PR | — |

## Estimativa de tamanho

Jornadas: 1 (ver, no mês, se cada categoria está dentro, em atenção ou acima do limite) · Telas novas: 0 · Linhas alteradas (sem testes e sem mocks): ~60 Python (`limits.py` ~25, `queries/expenses.py` ~6, `routers/transactions.py` ~25) + ~65 em `src/` (tipos ~8, `category-totals.tsx` ~50, `set-category-limit.ts` ~1) + ~1 em `docs/design.md`; ~130 no total · Fases previstas: 2 (1: `limits.py`, coluna no SQL, contrato do router, `tests/test_limits.py`, testes de API, handler MSW; 2: tipos, `CategoryTotals`, invalidação no hook de limite, testes de componente, e2e, `design.md`).

Sinais de "grande demais": 1 jornada, 0 telas novas, 2 fases, ~130 linhas — nenhum dispara.

## Dívida encontrada

- `src/testing/mocks/handlers.ts:groupByCategory` usa `item.category` (o **rótulo**, "Compras") como `category` do grupo, enquanto a API real devolve a **chave** (`Shopping`); por isso o mock desta fatia procura o limite em `fakeCategories` pelo `label`, não pela `key`. Item de roadmap: o mock agrupar por `category_key` e devolver `label` do `fakeCategories`, alinhando o contrato simulado ao real.
- Dívidas 025 (predicado de gasto duplicado entre `expenses.py` e `spending.py`) e 026 (`_PAYEE_NAME_SQL` vs `_chosen`) inalteradas; esta fatia não toca nenhuma delas.
- `app/plan/objective.py:_last_day(month)` e o `is_whole_month` novo calculam o último dia do mês cada um por si (`calendar.monthrange`); são duas linhas em domínios diferentes, sem consumidor comum ainda. Se a fatia 014 (teto do mês) precisar dos dois, unifica-se num utilitário de datas nessa fatia.
