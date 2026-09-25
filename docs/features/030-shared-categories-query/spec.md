# SPEC 030 — shared-categories-query

## Contexto

- `src/features/expenses/api/get-categories.ts` (`useCategories`) e `src/features/categories/api/get-categories.ts` (`useCatalogue`) buscam `GET /api/categories` com a mesma chave `['categories']`, cada uma com um tipo: `Category`/`CategoriesResponse` em `src/features/expenses/types/expense.ts` (só `key` e `label`) e `CatalogueCategory`/`CatalogueResponse` em `src/features/categories/types/category.ts` (o formato completo da API).
- Seis mutações das duas features invalidam a lista escrevendo `['categories']` à mão.
- Pela regra de estrutura, o que duas features usam vai para o compartilhado (`src/hooks/`, `src/types/`).

## Decisões

### D1 — Um tipo, com o formato completo da API

`src/types/category.ts` define `Category` (`key`, `label`, `is_system`, `usage_count`, `monthly_limit_cents`) e `CategoriesResponse`. As duas features importam daí; `Category`/`CategoriesResponse` saem de `expense.ts` e `src/features/categories/types/category.ts` é apagado.

- Alternativa descartada: manter um tipo reduzido (`key`, `label`) para a lista de gastos — motivo: as duas leituras dividem a mesma entrada do cache, então o dado é sempre o completo; dois tipos para o mesmo objeto são justamente a divergência que o item remove.

### D2 — Um pedido, com a chave exportada

`src/hooks/use-categories.ts` exporta `categoriesQueryKey`, `getCategories`, `categoriesQueryOptions` e `useCategories`. As duas telas usam `useCategories`; as seis invalidações usam `categoriesQueryKey`. Os dois `get-categories.ts` das features são apagados.

- Alternativa descartada: mover só o hook e deixar `['categories']` literal nas invalidações — motivo: renomear a chave num lugar deixaria invalidações apontando para uma chave que ninguém lê, sem teste que acuse.

## Arquivos afetados

| Ação | Arquivo | O quê | Skills |
|---|---|---|---|
| criar | `src/types/category.ts` | `Category`, `CategoriesResponse` | project-structure, code-standards |
| criar | `src/hooks/use-categories.ts` | chave, fetcher, query options e hook | api-requests |
| apagar | `src/features/expenses/api/get-categories.ts`, `src/features/categories/api/get-categories.ts`, `src/features/categories/types/category.ts` | cópias | project-structure |
| alterar | `src/features/expenses/types/expense.ts` | remove `Category`, `CategoriesResponse` | code-standards |
| alterar | consumidores em `src/features/expenses/`, `src/features/categories/` e `src/testing/mocks/handlers.ts` | importam do compartilhado; invalidações usam `categoriesQueryKey` | api-requests |

## Riscos

- Nenhum de comportamento: a chave continua `['categories']` e a resposta é a mesma; a suíte inteira prova.
