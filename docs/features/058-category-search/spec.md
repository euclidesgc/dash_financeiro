# SPEC — Buscar categoria na página "Categorias"

## Decisões

- **Filtro no cliente.** `GET /api/categories` já devolve o catálogo inteiro (~80 itens) com `usage_count` e `monthly_limit_cents`; filtrar e ordenar no navegador não pede mudança de API e responde a cada tecla, sem espera.
- **Estado da busca em `useState`.** É um filtro efêmero da página; não precisa sobreviver a recarga nem ser compartilhado por URL.
- **Uma só lista, ordenada.** Categorias "em uso" (`usage_count > 0` ou limite definido) vêm primeiro, cada grupo na ordem da API. Uma lista única com `key` estável mantém a linha montada quando ela muda de grupo (ao definir um limite), então o formulário aberto não é perdido.
- **Normalização.** `NFD` sem diacríticos, minúsculas, sem espaços nas pontas, aplicada ao termo e ao nome.

## Arquivos

- `src/features/categories/utils/arrange-categories.ts` — `normalizeSearchText`, `isCategoryInUse`, `arrangeCategories`.
- `src/features/categories/components/categories-list.tsx` — campo de busca, resumo da ordem, estado vazio da busca.
- `docs/design.md` — receita "Busca em lista carregada".

## Skills

`client-state`, `component-testing`, `unit-testing`, `interface-design`.
