# PLAN 055 — balances-month-plan-card

Branch: `feature/055-balances-plan-card`

## Fase 1 — cartão do plano do mês na tela de saldos

Tarefas:

1. Criar `MonthPlanCard` em `src/features/expenses/components/month-plan-card.tsx`
   lendo `useMonthSignal` e `usePeriodResult` com o intervalo do mês corrente.
2. Renderizar o cartão em `src/app/routes/dashboard.tsx`, entre `SyncPanel` e
   `BalancesList`.
3. Registrar a receita em `docs/design.md`.

Critérios de aceite:

- (comportamental) Com o relógio em 25/09/2026, o cartão pede os dois endpoints
  com `from=2026-09-01` e `to=2026-09-30` e mostra o título
  "Plano de setembro de 2026" — `month-plan-card.test.tsx`.
- (comportamental) Com teto, mostra gasto, selo, teto, resultado com sinal,
  "Sobram … até o teto" ou "Passou … do teto", e o link
  "Ver o mês em detalhe" para `/expenses?month=2026-09`.
- (comportamental) Sem teto, mostra "Sem teto", a explicação e o link
  "Definir o teto do mês".
- (comportamental) Carregando mostra `role="status"`; erro mostra o alerta e
  "Tentar de novo" busca de novo.
- (comportamental) Depois do login, o cartão está na tela de saldos e o link
  leva a Gastos com `?month=AAAA-MM` — `login-to-balances.test.tsx` e
  `e2e/month-plan-card.spec.ts`.
- (estrutural) `month-plan-card.tsx` não faz conta com centavos além de
  `Math.abs` para exibir e da escolha de cor pelo sinal.
- (comando) `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e
  `pnpm test:e2e` verdes.
