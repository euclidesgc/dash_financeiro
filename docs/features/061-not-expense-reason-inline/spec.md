# SPEC 061 — not-expense-reason-inline

## Decisões

- **O controle sai da coluna da direita.** `ExpenseItem` tem duas faixas dentro do `<li>`: a linha (descrição à esquerda; data, categoria e valor à direita) e, abaixo dela, uma faixa alinhada à direita com o `NotExpenseControl`. O controle em si não muda: fechado é um botão, aberto é o seletor com Confirmar e Cancelar, que agora tem a largura da linha inteira para quebrar.
- **Sem estado novo.** A mudança é só de marcação; nenhuma prop, chamada de API ou cache muda.

## Arquivos afetados

- `src/features/expenses/components/expense-item.tsx` (alterar)
- `src/features/expenses/components/__tests__/expense-item.test.tsx` (criar)

## Skills aplicáveis

`interface-design`, `component-testing`.
