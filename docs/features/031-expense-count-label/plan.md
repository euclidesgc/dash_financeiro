# PLAN 031 — expense-count-label

Branch: `feature/031-expense-count-label`

Decisões registradas aqui:

- **Trilha de feature**: dívida registrada na entrega 011; muda onde a regra de plural mora, sem mudar o que as telas mostram.
- **Uma fase só**: a troca é atômica.
- **O primeiro commit da branch marca a 030 como `done`** (mergeada em `develop` no PR #34).

## Fase 1 — Uma regra de singular e plural

Ao final: toda contagem com singular e plural na interface passa por `formatCount`.

- [ ] T1.1 — Utilitário compartilhado
  - Arquivos: `src/utils/format-count.ts` (criar), `src/utils/__tests__/format-count.test.ts` (criar)
  - O que fazer: `CountNoun`, `EXPENSE_NOUN = { one: 'gasto', many: 'gastos' }`, `formatCount(count, noun)`; testes para 0, 1, 2 e substantivo composto.
  - Skills: unit-testing, naming-conventions
  - Complexidade: baixa
- [ ] T1.2 — Consumidores
  - Arquivos: `src/features/expenses/components/{pagination,category-totals,similar-offer,expenses-list}.tsx`, `src/features/categories/components/category-item.tsx`, `src/testing/mocks/handlers.ts` (alterar)
  - O que fazer: trocar cada ternário de singular e plural por `formatCount`; `Pagination.noun` passa a `CountNoun` com `EXPENSE_NOUN` como padrão.
  - Skills: code-standards
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [ ] CA1.2 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [ ] CA1.3 — `grep -rnE "=== 1 \?|count === 1\)" src --include=*.ts --include=*.tsx` fora de `__tests__/` e de `src/utils/format-count.ts` não encontra nada. (estrutural)
- [ ] CA1.4 — Trocar em `formatCount` a condição do singular para `count <= 1` faz falhar o teste do zero em `format-count.test.ts`; desfeita a troca, volta a passar. (comportamental)

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
