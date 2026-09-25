# PLAN 027 — expenses-list-mock-unification

Branch: `feature/027-expenses-list-mock-unification`

Decisões registradas aqui:

- **Trilha de feature**: dívida registrada na entrega 008; muda-se onde a regra da simulação mora, sem mudar o que a tela faz.
- **Uma fase só**: a troca é atômica.
- **O primeiro commit da branch marca a 026 como `done`** (mergeada em `develop` no PR #31).

## Fase 1 — Uma página da lista só na simulação

Ao final: o espião dos testes da lista responde com a mesma função que o handler padrão usa.

- [x] T1.1 — Página exportada
  - Arquivos: `src/testing/mocks/handlers.ts` (alterar)
  - O que fazer: `export function expensesPage(url: URL)` com filtro, ordenação, fatiamento, `total` e `total_cents`; o handler de `GET /api/transactions/expenses` devolve `HttpResponse.json(expensesPage(url))`.
  - Complexidade: baixa
- [x] T1.2 — Espião sem cópia
  - Arquivos: `src/features/expenses/components/__tests__/expenses-list.test.tsx` (alterar)
  - O que fazer: `spyOnExpensesRequests` registra `url.searchParams` e devolve `HttpResponse.json(expensesPage(url))`; o handler de "keeps the previous rows while the next page loads" responde com `expensesPage(url)` depois do atraso; remove `filterForSpy`, `matchesViewForSpy`, `sortForSpy` e imports órfãos.
  - Skills: component-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.3 — `grep -rn "ForSpy" src` não encontra nada; `matchesView` e o comparador de ordenação aparecem uma vez só em `src/`, em `src/testing/mocks/handlers.ts`. (estrutural)
- [x] CA1.4 — Mudar a regra de `matchesView` em `handlers.ts` (por exemplo, a visão padrão aceitar entradas) faz falhar testes de `expenses-list.test.tsx` que usam o espião; desfeita a mudança, voltam a passar. (comportamental)

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
