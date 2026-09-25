# PLAN 048 — date-range-typing

Branch: `bugfix/048-date-range-typing`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: o rascunho dos campos e a gravação do intervalo inteiro mudam juntos; separados, a lista continuaria recebendo metade do intervalo.
- **O primeiro commit da branch marca a 047 como `done`** (mergeada em `develop` no PR #49).
- **O filtro acompanha cada data completa**, sem botão "Aplicar": o calendário e a digitação seguem o mesmo caminho, e o comportamento de aplicar na hora, combinado na 005, fica.
- **Intervalo invertido não se corrige sozinho**: mensagem e filtro intacto, em vez de apagar o outro campo.
- **A regressão é e2e**: só o navegador real tem os segmentos do campo de data.

## Fase 1 — Datas digitadas filtram a lista

Ao final: digitar "De" e "Até" pelo teclado filtra os gastos pelo período digitado; "Até" antes de "De" mostra a mensagem e mantém o filtro.

- [ ] T1.1 — Rascunho dos campos de data
  - Arquivos: `src/features/expenses/components/period-controls.tsx`, `src/features/expenses/utils/period.ts`, `src/features/expenses/components/expenses-list.tsx` (alterar)
  - O que fazer: rascunho local por campo, reiniciado quando o período da URL muda; `readTypedDate` para data completa; campo vazio com `validity.badInput` não conta como apagado; intervalo invertido mostra a mensagem e marca os campos com `aria-invalid`; `onRangeChange(from, to)` grava o intervalo inteiro.
  - Skills: client-state, component-robustness, interface-design, forms
  - Complexidade: média
- [ ] T1.2 — Testes
  - Arquivos: `e2e/expenses.spec.ts`, `src/features/expenses/components/__tests__/expenses-list.test.tsx`, `src/features/expenses/utils/__tests__/period.test.ts` (alterar)
  - O que fazer: os testes de regressão passam; `readTypedDate` aceita data completa e recusa ano pela metade; na lista, campo incompleto e ano pela metade não mudam a URL, e intervalo invertido mostra a mensagem sem mudar a URL.
  - Skills: component-testing, unit-testing, e2e-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `pnpm test:e2e` sai com código 0, e no commit `56ed6dd` o teste `filters the expenses by a range typed by keyboard in both fields` falhava. (comando)
- [ ] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0. (comando)
- [ ] CA1.3 — `src/features/expenses/components/period-controls.tsx` guarda o texto dos campos em estado local e só chama `onRangeChange` com as duas pontas completas ou vazias e não invertidas; `handleRangeChange` em `expenses-list.tsx` não apaga mais uma ponta do intervalo. (estrutural)
- [ ] CA1.4 — Com o "De" em 01/09/2026, um "Até" em 20/08/2026 mostra `"Até" não pode ser antes de "De".`, os dois campos ficam com `aria-invalid="true"` e a URL não muda. (comportamental)
- [ ] CA1.5 — Um campo de data vazio com `validity.badInput` (segmento pela metade) ou com ano abaixo de 1000 não muda a URL nem apaga o outro campo. (comportamental)

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
