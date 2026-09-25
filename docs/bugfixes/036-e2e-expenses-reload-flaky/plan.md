# PLAN 036 — e2e-expenses-reload-flaky

Branch: `bugfix/036-e2e-expenses-reload-flaky`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: dois arquivos de código e um de teste.
- **O primeiro commit da branch marca a 017 como `done`** (mergeada em `develop` no PR #21).
- **`flushSync` na navegação, não retentativa no e2e**: o teste ponta a ponta está certo; quem perde a edição é a tela.

## Fase 1 — Filtro da tela de gastos não perde a edição anterior

Ao final: duas mudanças de filtro em sequência rápida na tela de gastos terminam com as duas na URL, e o período editado no e2e sobrevive ao reload.

- [ ] T1.1 — URL e tela mudam juntas a cada filtro
  - Arquivos: `src/app/router.tsx` (alterar); `src/features/expenses/components/expenses-list.tsx` (alterar)
  - O que fazer: em `router.tsx`, `AppRouter` passa `flushSync={flushSync}` (de `react-dom`) ao `RouterProvider`. Em `expenses-list.tsx`, uma função local `commitParams(params: URLSearchParams): void` chama `setSearchParams(params, { replace: true, flushSync: true })`; `commitPeriod`, `handleSortChange`, `handleOrderToggle`, `handleAccountChange`, `handleViewChange` e `handleSearchCommit` passam por ela. Os dois `useEffect` que corrigem a URL não mudam.
  - Skills: routing, client-state
  - Complexidade: média
- [ ] T1.2 — Testes de regressão
  - Arquivos: `src/features/expenses/components/__tests__/expenses-list-fast-edits.test.tsx` (criar)
  - O que fazer: monta `ExpensesList` com `createMemoryRouter` e `RouterProvider` com `flushSync`; dentro de um `act` faz a primeira edição, espera a URL mudar e faz a segunda. Casos `an end date typed before the start date renders keeps the start date` e `a sort chosen before the account filter renders keeps the account`.
  - Skills: component-testing
  - Complexidade: média

### Critérios de aceite da fase 1

- [ ] CA1.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0. (comando)
- [ ] CA1.2 — `pnpm exec playwright test e2e/expenses.spec.ts --repeat-each=20` sai com código 0, e `pnpm test:e2e` sai com código 0. (comando)
- [ ] CA1.3 — Em `src/app/router.tsx`, `RouterProvider` recebe `flushSync={flushSync}` importado de `react-dom`; em `expenses-list.tsx`, toda chamada de `setSearchParams` fora de `useEffect` passa `flushSync: true`. (estrutural)
- [ ] CA1.4 — Comportamento: com "De" mudado para 10/07/2026 e "Até" para 20/07/2026 antes de a tela redesenhar, a URL termina em `?from=2026-07-10&to=2026-07-20`; com a conta escolhida e a ordenação mudada antes de redesenhar, a URL guarda `account` e `sort=amount` (os dois testes de `expenses-list-fast-edits.test.tsx`). Tirar o `flushSync: true` faz os dois falharem. (comportamental)

## DoD da entrega

- [ ] DoD1 — Todas as tarefas e critérios do plano marcados
- [ ] DoD2 — Suíte de testes inteira passa
- [ ] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [ ] DoD4 — Tipos de todos os `tsconfig` sem erros
- [ ] DoD5 — Console dos testes sem erro nem aviso
- [ ] DoD6 — `build` passa
- [ ] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [ ] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [ ] DoD9 — Nenhuma worktree ou branch temporária sobrando
