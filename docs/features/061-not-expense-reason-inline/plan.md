# PLAN 061 — not-expense-reason-inline

Branch: `feature/061-not-expense-picker-below-row`

Decisões registradas aqui:

- **Trilha de feature**: muda a disposição de um controle que existe.
- **Uma fase só**: uma troca de marcação e o teste que a prende.

## Fase 1 — Motivo abaixo da linha

Ao final: abrir "Não é gasto" não espreme a descrição do lançamento.

- [x] T1.1 — Faixa do controle abaixo da linha
  - Arquivos: `src/features/expenses/components/expense-item.tsx` (alterar)
  - O que fazer: a linha vira um `div` flexível dentro do `<li>`; o `NotExpenseControl` vai para uma faixa `flex justify-end` abaixo dela.
  - Complexidade: baixa
- [x] T1.2 — Teste
  - Arquivos: `src/features/expenses/components/__tests__/expense-item.test.tsx` (criar)
  - O que fazer: abrir o seletor e afirmar que ele está no item, mas fora da linha da descrição.
  - Complexidade: baixa

### Critérios de aceite

- **C1** (comando) — `pnpm test src/features/expenses/components/__tests__/expense-item.test.tsx` passa; com o `expense-item.tsx` anterior, o mesmo teste falha.
- **C2** (comportamental) — em 1280px e 375px, com o seletor aberto, a descrição do lançamento aparece inteira, como com ele fechado.
