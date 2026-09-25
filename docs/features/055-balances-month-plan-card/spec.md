# SPEC 055 — balances-month-plan-card

## Decisões

- **Nenhum endpoint novo e nenhum cálculo no front** (invariante 23). O cartão
  lê dois endpoints que já existem, os dois com `from` e `to` do mês corrente:
  - `GET /api/transactions/expenses/month-signal`: gasto, teto, selo e o que
    sobra (`remaining_cents`), todos calculados no servidor;
  - `GET /api/transactions/expenses/period-result`: `balance_cents`, o
    resultado do período.
  O front só formata dinheiro e escolhe a cor pelo sinal.
- O mês é o do relógio do navegador (`currentMonth()`), fixado na montagem do
  componente; o intervalo vem de `monthRange()`, o mesmo da tela de Gastos.
- As chaves de consulta são as mesmas de Gastos (`['expenses', 'month-signal',
  …]`, `['expenses', 'period-result', …]`): o cache é compartilhado e a
  invalidação depois de sincronizar ou reclassificar já alcança o cartão.
- O componente mora em `features/expenses` porque só usa a API dessa feature;
  a rota `dashboard` o compõe, respeitando a regra de uma feature não importar
  de outra.
- O link aponta para `/expenses?month=AAAA-MM`, parâmetro que Gastos já lê.

## Arquivos

- `src/features/expenses/components/month-plan-card.tsx` (novo)
- `src/app/routes/dashboard.tsx` (renderiza o cartão entre `SyncPanel` e
  `BalancesList`)
- `docs/design.md` (receita "Cartão do plano do mês")
- Testes: `src/features/expenses/components/__tests__/month-plan-card.test.tsx`,
  `src/app/__tests__/login-to-balances.test.tsx`, `e2e/month-plan-card.spec.ts`
