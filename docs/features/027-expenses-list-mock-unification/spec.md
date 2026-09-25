# SPEC 027 — expenses-list-mock-unification

## Contexto

- `src/testing/mocks/handlers.ts` responde `GET /api/transactions/expenses` com `filterExpenses(url)` (período, conta, busca e `matchesView`), `sortExpenses` e o fatiamento da página.
- `src/features/expenses/components/__tests__/expenses-list.test.tsx::spyOnExpensesRequests` substitui esse handler para registrar os parâmetros das chamadas e, para responder, reescreve a mesma regra: `filterForSpy`, `matchesViewForSpy`, `sortForSpy` e o fatiamento.

## Decisões

### D1 — A página da lista sai de uma função exportada dos mocks

`handlers.ts` ganha `expensesPage(url: URL): ExpensesPage`, com o corpo que o handler padrão monta hoje (filtro, ordenação, página, `total`, `total_cents`). O handler padrão passa a devolver `HttpResponse.json(expensesPage(url))`, e o espião do teste também, depois de registrar `url.searchParams`.

- Alternativa descartada: exportar só `filterExpenses` e `sortExpenses` e manter o fatiamento no teste — motivo: o fatiamento e os totais continuariam em duas cópias; o espião só precisa observar a chamada, não recompor a resposta.

### D2 — As cópias do teste saem

`filterForSpy`, `matchesViewForSpy` e `sortForSpy` são removidas de `expenses-list.test.tsx`, com os imports que só elas usavam.

## Arquivos afetados

| Ação | Arquivo | O quê | Skills |
|---|---|---|---|
| alterar | `src/testing/mocks/handlers.ts` | `expensesPage(url)` exportada; handler padrão usa ela | api-mocking, code-standards |
| alterar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | espião responde com `expensesPage(url)`; remove as três cópias | component-testing |

## Riscos

- Nenhum: o comportamento da simulação não muda; a suíte inteira prova que as respostas são as mesmas.
