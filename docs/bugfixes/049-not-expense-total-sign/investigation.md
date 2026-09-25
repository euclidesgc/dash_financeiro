# Investigação: total da visão "Não são gastos" anula saídas com entradas

## Relato
- **Sintoma:** na tela de gastos, com "Mostrar: Não são gastos", o rodapé da lista soma o dinheiro que saiu com o que entrou e mostra o resultado sem sinal. Uma transferência entre contas próprias marcada dos dois lados (−R$ 1.000,00 numa conta, +R$ 1.000,00 na outra) aparece como "R$ 0,00 no período".
- **Esperado:** o rodapé diz quanto saiu e quanto entrou, separados: "R$ 1.000,00 em saídas e R$ 1.000,00 em entradas no período".
- **Como reproduzir:** marcar como "Não é gasto" um gasto de R$ 1.000,00 e, em "Entradas", marcar como "Não é entrada" uma entrada de R$ 1.000,00; abrir "Não são gastos".
- **Onde:** `src/features/expenses/components/pagination.tsx` (`formatMoney(Math.abs(totalCents))`), alimentado por `data.total_cents` em `src/features/expenses/components/expenses-list.tsx`; a API (`app/queries/expenses.py`, consulta `_TOTAL`) só devolve a soma com sinal.

## Causa raiz
A visão "Não são gastos" é a única que mistura sinais: o filtro `EXCLUDED` (`app/queries/spending.py`) aceita qualquer valor diferente de zero marcado, enquanto "Gastos" só traz saídas e "Entradas" só traz entradas. A API devolve um único número, `total_cents`, a soma com sinal de tudo o que o filtro trouxe; nessa visão, saídas e entradas se anulam. O rodapé foi escrito para as visões de um sinal só e tira o sinal da soma com `Math.abs`, então a diferença entre saídas e entradas aparece como se fosse o total do período.

## Evidência
- Teste de regressão (commit `686e9e4`):
  - `src/features/expenses/components/__tests__/expenses-list.test.tsx`, `?view=excluded shows what went out and what came in apart, not their difference`: com −R$ 1.000,00 e +R$ 1.000,00 marcados, o rodapé mostra `R$ 0,00 no período`.
  - `tests/test_expenses_api.py`, `test_view_excluded_answers_the_outflows_and_the_inflows_apart`: a resposta de `GET /api/transactions/expenses?view=excluded` não tem como separar os dois lados (`KeyError: 'outflow_cents'`).

## Correção proposta
- `app/queries/expenses.py` — a consulta de total passa a somar, no SQL, as saídas (`outflow_cents`, negativo ou zero) e as entradas (`inflow_cents`, positivo ou zero) além da contagem e da soma com sinal; `list_expenses` lê tudo numa consulta só.
- `app/routers/transactions.py` — `ExpensesResponse` ganha `outflow_cents` e `inflow_cents`; `total_cents` fica, com o mesmo significado.
- `src/features/expenses/types/expense.ts` e `src/testing/mocks/handlers.ts` — o tipo e a API simulada acompanham os dois campos.
- `src/features/expenses/components/pagination.tsx` — recebe `outflowCents` e `inflowCents` em vez de `totalCents`. Na visão "Não são gastos" mostra "R$ X em saídas e R$ Y em entradas no período", sempre os dois lados. Nas outras visões mostra o dinheiro movimentado, `|saídas| + entradas`, que nunca desconta um lado do outro.
- **Risco:** o texto do rodapé das visões "Gastos" e "Entradas" não muda. Quem lê `total_cents` (só a lista, hoje) continua recebendo o mesmo valor.

## Fora da correção
Nenhum.

## Pontos em aberto
Nenhum.
