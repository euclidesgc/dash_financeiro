# PLAN 049 — not-expense-total-sign

Branch: `bugfix/049-not-expense-total-sign`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a API passa a separar saídas e entradas e o rodapé passa a mostrá-las no mesmo passo; separados, um dos dois lados fica sem uso ou sem dado.
- **O primeiro commit da branch marca a 048 como `done`** (mergeada em `develop` no PR #50).
- **Os dois totais saem do SQL**, na mesma consulta da contagem: o front não soma lançamentos da página, que só tem 20 linhas.
- **`total_cents` fica** na resposta, com o mesmo valor: tirar o campo é mudança de contrato sem ganho para esta correção.
- **Na visão "Não são gastos" os dois lados aparecem sempre**, mesmo quando um deles é zero: a visão mistura sinais por definição, e o zero diz que aquele lado não teve nada.

## Fase 1 — Saídas e entradas separadas no rodapé

Ao final: na visão "Não são gastos", o rodapé mostra quanto saiu e quanto entrou no período, separados.

- [x] T1.1 — Totais separados na API
  - Arquivos: `app/queries/expenses.py`, `app/routers/transactions.py` (alterar)
  - O que fazer: a consulta de total devolve contagem, soma com sinal, soma das saídas e soma das entradas; `ExpensesPage` e `ExpensesResponse` ganham `outflow_cents` e `inflow_cents`.
  - Skills: python-schemas-pydantic-v2
  - Complexidade: baixa
- [x] T1.2 — Rodapé com os dois lados
  - Arquivos: `src/features/expenses/types/expense.ts`, `src/testing/mocks/handlers.ts`, `src/features/expenses/components/pagination.tsx`, `src/features/expenses/components/expenses-list.tsx` (alterar)
  - O que fazer: tipo e API simulada com os dois campos; `Pagination` recebe `outflowCents`, `inflowCents` e `splitFlows`; com `splitFlows` mostra "R$ X em saídas e R$ Y em entradas no período", sem ele mostra `|saídas| + entradas`; a lista liga `splitFlows` na visão "Não são gastos".
  - Skills: component-robustness, interface-design, api-mocking
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `tests/test_expenses_api.py`, `src/features/expenses/components/__tests__/expenses-list.test.tsx`, `src/features/expenses/components/__tests__/pagination.test.tsx` (alterar)
  - O que fazer: os testes de regressão passam; o teste do componente cobre os dois modos do rodapé e o lado zero.
  - Skills: component-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `uv run pytest` e `pnpm test` saem com código 0, e no commit `686e9e4` os testes `test_view_excluded_answers_the_outflows_and_the_inflows_apart` e `?view=excluded shows what went out and what came in apart, not their difference` falhavam. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `pnpm lint`, `pnpm typecheck` e `pnpm build` saem com código 0. (comando)
- [x] CA1.3 — As somas de saídas e de entradas são feitas no SQL de `app/queries/expenses.py`, e `src/features/expenses/components/pagination.tsx` não chama `Math.abs` sobre a soma com sinal. (estrutural)
- [x] CA1.4 — Com −R$ 1.000,00 e +R$ 1.000,00 marcados, a visão "Não são gastos" mostra `R$ 1.000,00 em saídas e R$ 1.000,00 em entradas no período`; a visão "Gastos" continua mostrando `R$ X no período`. (comportamental)

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
