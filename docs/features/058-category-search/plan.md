# PLAN — Buscar categoria na página "Categorias"

Documentos: [PRD](prd.md) · [SPEC](spec.md)

## Fase 1 — Busca e prioridade no catálogo

### Tarefas

1. Criar `arrangeCategories(categories, search)` em `src/features/categories/utils/arrange-categories.ts`, devolvendo `{ inUse, others }` já filtrados pelo termo normalizado.
2. Em `CategoriesList`, acima da lista, o campo "Buscar categoria" (`type="search"`) com botão "Limpar busca"; abaixo, o resumo "N com gastos ou limite aparecem primeiro; depois, M sem uso." e uma única `<ul>` com `inUse` seguido de `others`.
3. Sem resultado, o bloco vazio "Nenhuma categoria com “termo”. Confira a grafia ou crie a categoria acima."
4. Registrar a receita "Busca em lista carregada" em `docs/design.md`.

### Critérios de aceite

- `comando`: `pnpm vitest run src/features/categories` passa.
- `comportamental`: com o catálogo de teste, a lista vem em `Alimentação, Compras, Lazer, Transporte, Pet shop, Supermercado` (teste "lists categories with spending or limit first…").
- `comportamental`: digitar `alimentacao` deixa só "Alimentação"; "Limpar busca" volta às 6 linhas (teste "filters the catalogue by name ignoring accents…").
- `comportamental`: digitar `xyz` mostra o bloco vazio com o termo (teste "tells when no category matches the search").
- `comportamental`: salvar limite em "Pet shop" (sem uso) mostra "Limite: R$ 300,00" na mesma linha (teste "saving a limit sends PUT…").
- `estrutural`: `docs/design.md` tem a linha "Busca em lista carregada" com a fatia 058.
