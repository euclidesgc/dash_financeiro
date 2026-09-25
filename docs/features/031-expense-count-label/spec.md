# SPEC 031 — expense-count-label

## Contexto

- `src/features/expenses/components/pagination.tsx` escolhe `noun.one`/`noun.many` com `total === 1`.
- `src/features/expenses/components/category-totals.tsx` escreve "1 gasto"/"N gastos" e "1 categoria acima do limite"/"N categorias acima do limite" à mão.
- `src/features/expenses/components/similar-offer.tsx` escreve "gasto parecido"/"gastos parecidos" e "1 gasto"/"N gastos" à mão.
- `src/features/categories/components/category-item.tsx` (`usageText`) escreve "Nenhum gasto"/"1 gasto"/"N gastos".
- `src/testing/mocks/handlers.ts` monta a mensagem 409 de categoria em uso com o mesmo ternário.

## Decisões

### D1 — O utilitário mora em `src/utils/`, não em `src/features/expenses/utils/`

`src/utils/format-count.ts` exporta `CountNoun` (`{ one, many }`), `EXPENSE_NOUN` e `formatCount(count, noun)`, que devolve `"<count> <one|many>"`.

- Alternativa descartada: `src/features/expenses/utils/`, como diz o item do roadmap — motivo: a tela de categorias também escreve a contagem de gastos, e uma feature não importa de outra; pela regra de estrutura, o que duas features usam vai para o compartilhado.

### D2 — Singular só para 1, sem `Intl.PluralRules`

- Alternativa descartada: `Intl.PluralRules('pt-BR')` — motivo: a regra do CLDR para português põe o 0 no singular ("0 gasto"), o que mudaria o texto que as telas mostram hoje.

### D3 — O substantivo continua sendo do chamador

`Pagination` mantém a prop `noun`, agora do tipo `CountNoun`, com `EXPENSE_NOUN` como padrão. Frases com adjetivo ("gasto parecido") passam o substantivo completo.

## Arquivos afetados

| Ação | Arquivo | O quê | Skills |
|---|---|---|---|
| criar | `src/utils/format-count.ts` | `CountNoun`, `EXPENSE_NOUN`, `formatCount` | project-structure, naming-conventions |
| criar | `src/utils/__tests__/format-count.test.ts` | 0, 1, 2 e substantivo composto | unit-testing |
| alterar | `pagination.tsx`, `category-totals.tsx`, `similar-offer.tsx`, `expenses-list.tsx`, `category-item.tsx` | usam `formatCount` | code-standards |
| alterar | `src/testing/mocks/handlers.ts` | mensagem 409 usa `formatCount` | api-mocking |

## Riscos

- Nenhum de comportamento: os textos são os mesmos; os testes de componente existentes provam.
