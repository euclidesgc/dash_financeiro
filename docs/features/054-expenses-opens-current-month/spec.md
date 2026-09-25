# SPEC 054 — expenses-opens-current-month

## Contexto

- `src/features/expenses/utils/period.ts` · `readPeriod` devolve `{ kind: 'all' }` quando a URL não tem `month`, `from` nem `to`; `writePeriod` apaga os três para `all`.
- `src/features/expenses/components/expenses-list.tsx` monta o cabeçalho na ordem: barra de filtros → `PeriodResult` (só fora de `all`) → `MonthCeiling` (só em mês, na visão de gastos) → `CategoryTotals`.
- `src/features/expenses/components/period-controls.tsx` calcula o texto do mês ("Todo o período", `formatMonth`, "Período personalizado") dentro do componente.

## Decisões

### D1 — Sem período na URL é o mês corrente; "Todo o período" é `period=all`

`readPeriod` lê `month`, depois `from`/`to`, depois `period=all`; sem nenhum deles devolve `{ kind: 'month', month: currentMonth() }`. `writePeriod` apaga `month`, `from`, `to` e `period` e, para `all`, grava `period=all`. O mês corrente não é escrito na URL ao abrir: o endereço limpo continua sendo "o mês de hoje" em qualquer dia.

- Alternativa descartada: redirecionar `/expenses` para `?month=AAAA-MM` — motivo: uma entrada a mais no histórico e um endereço salvo que congela o mês.
- Alternativa descartada: guardar a escolha em Zustand ou `localStorage` — motivo: filtro de lista mora na URL (skill `client-state`), e lembrar entre visitas está fora do escopo.

### D2 — Resultado e teto antes da barra de filtros

`ExpensesList` renderiza `PeriodResult` e `MonthCeiling` antes da barra, com as mesmas condições de hoje; `CategoryTotals` fica depois dela. A barra passa a ter `mt-6` herdado do bloco anterior sem mudar as classes da receita.

### D3 — O resultado nomeia o período

`formatPeriod(period)` em `utils/period.ts` devolve "Todo o período", `formatMonth(month)` ou, em intervalo, "de dd/mm/aaaa a dd/mm/aaaa" (com "a partir de" / "até" quando falta uma ponta). `PeriodResult` recebe `periodLabel` e o mostra numa linha `text-sm text-gray-600` logo abaixo do título "Resultado do período", que não muda. `PeriodControls` continua mostrando "Período personalizado" no seletor.

### D4 — Limpar as duas datas volta para "Todo o período"

Campos "De" e "Até" vazios significam intervalo sem pontas, o mesmo que "Todo o período"; o comportamento de hoje se mantém.

## Arquivos afetados

| Ação | Arquivo | O quê | Skills |
|---|---|---|---|
| alterar | `src/features/expenses/utils/period.ts` | D1, `formatPeriod` (D3) | client-state, routing |
| alterar | `src/features/expenses/components/expenses-list.tsx` | ordem do cabeçalho (D2), `periodLabel` | interface-design |
| alterar | `src/features/expenses/components/period-result.tsx` | linha do período (D3) | interface-design |
| alterar | testes em `src/features/expenses/**/__tests__/` | padrão no mês corrente; testes de "todo o período" usam `period=all` | component-testing, unit-testing |
| alterar | `e2e/expenses.spec.ts` | relógio fixo no teste de abertura; ordem visual; "Todo o período" por clique | e2e-testing |
| alterar | `docs/design.md`, `docs/features/005-filtrar-por-periodo/prd.md` e `spec.md` | padrão e ordem reescritos no presente | — |

## Riscos

- Teste que abre `/expenses` sem período passa a depender da data do relógio: todo teste que espera a lista inteira passa a pedir `period=all`, e os que testam o padrão fixam a data.
