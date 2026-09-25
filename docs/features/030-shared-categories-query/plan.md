# PLAN 030 — shared-categories-query

Branch: `feature/030-shared-categories-query`

Decisões registradas aqui:

- **Trilha de feature**: dívida registrada na entrega 010; muda onde o pedido e o tipo moram, sem mudar o que as telas fazem.
- **Uma fase só**: a troca é atômica.
- **O primeiro commit da branch marca a 029 como `done`** (mergeada em `develop` no PR #33).

## Fase 1 — Um pedido de categorias compartilhado

Ao final: as duas telas leem as categorias pelo mesmo hook, com o mesmo tipo e a mesma chave.

- [x] T1.1 — Tipo e hook compartilhados
  - Arquivos: `src/types/category.ts` (criar), `src/hooks/use-categories.ts` (criar)
  - O que fazer: `Category` e `CategoriesResponse` com o formato completo da API; `categoriesQueryKey = ['categories'] as const`, `getCategories`, `categoriesQueryOptions`, `useCategories`.
  - Skills: api-requests, project-structure
  - Complexidade: baixa
- [x] T1.2 — Consumidores no compartilhado
  - Arquivos: `src/features/expenses/**`, `src/features/categories/**`, `src/testing/mocks/handlers.ts` (alterar); os dois `api/get-categories.ts` e `src/features/categories/types/category.ts` (apagar)
  - O que fazer: `useCatalogue`/`useCategories` das features viram `useCategories` de `@/hooks/use-categories`; `CatalogueCategory` e `Category` de `expense.ts` viram `Category` de `@/types/category`; as seis invalidações usam `categoriesQueryKey`.
  - Skills: code-standards
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.3 — `grep -rn "'/api/categories'" src --include=*.ts --include=*.tsx` fora de `src/testing/` aparece só em `src/hooks/use-categories.ts` e em mutações; `grep -rn "\['categories'\]" src` fora de `__tests__/` aparece só em `src/hooks/use-categories.ts`; `grep -rn "CatalogueCategory\|CatalogueResponse\|useCatalogue" src` não encontra nada. (estrutural)
- [x] CA1.4 — Trocar o valor de `categoriesQueryKey` faz falhar os testes que conferem a invalidação da lista de categorias; desfeita a troca, voltam a passar. (comportamental)

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
