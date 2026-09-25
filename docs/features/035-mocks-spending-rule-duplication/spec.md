# SPEC 035 — mocks-spending-rule-duplication

## Contexto

- `app/queries/spending.py` define os predicados `SPENDING`, `INCOME` e `EXCLUDED`; `app/queries/expenses.py` os liga às três listas (`expenses`, `income`, `excluded`) e calcula o resultado do período somando `income` e `expenses`.
- `src/testing/mocks/handlers.ts::matchesView` reescreve a separação à mão, e o `period-result` simulado soma pelas mesmas listas. A cópia já diverge num canto: a API exige valor diferente de zero em `excluded`; a simulada não.
- O lançamento devolvido pela API não traz `is_transfer`, `is_refund` nem `refunded_by`: esses lançamentos saem de todas as listas antes de chegar à tela, e a API simulada não os representa.

## Decisões

### D1 — Tabela de casos em JSON, lida pelos dois lados

`src/testing/contracts/expense-views.json` guarda os casos `{ name, amount_cents, not_expense_reason, views }`, com `views` ⊂ `["expenses", "income", "excluded"]`. O pytest lê o arquivo pelo caminho; o Vitest o importa (`resolveJsonModule` ligado em `tsconfig.app.json`).

- Alternativa descartada: a API simulada chamar a regra da API — motivo: são linguagens diferentes; só um dado comum atravessa a fronteira.
- Alternativa descartada: gerar `matchesView` a partir da tabela — motivo: uma tabela de exemplos não é uma regra; o teste compara, a implementação continua explícita.

### D2 — O teste da API passa pela consulta pública

`tests/test_expense_views_contract.py` grava cada caso em `transactions` (banco migrado, sem sinalizadores) e confere, para cada lista, que `list_expenses(view=…)` devolve exatamente os casos esperados. Um segundo teste grava cada caso com `is_transfer`, `is_refund` ou `refunded_by` e confere que ele não aparece em lista nenhuma — é a premissa que dispensa a API simulada de representar esses campos.

### D3 — O teste da API simulada passa pela função exportada

`matchesView` passa a ser exportada de `handlers.ts`; `src/testing/mocks/__tests__/expense-views-contract.test.ts` confere cada caso nas três listas, e confere que o `period-result` simulado soma entradas e gastos pelas mesmas listas.

### D4 — A divergência encontrada se corrige

`matchesView` em `excluded` passa a exigir `amount_cents !== 0`, como a API.

## Arquivos afetados

| Ação | Arquivo | O quê | Skills |
|---|---|---|---|
| criar | `src/testing/contracts/expense-views.json` | tabela de casos | api-mocking |
| alterar | `tsconfig.app.json` | `resolveJsonModule` | code-standards |
| alterar | `src/testing/mocks/handlers.ts` | exporta `matchesView`; `excluded` exige valor diferente de zero | api-mocking |
| criar | `src/testing/mocks/__tests__/expense-views-contract.test.ts` | a API simulada contra a tabela | unit-testing |
| criar | `tests/test_expense_views_contract.py` | a API contra a tabela | python-testes-unitarios |

## Riscos

- Nenhum de comportamento: a tela não muda, e nenhum lançamento simulado tem valor zero.
