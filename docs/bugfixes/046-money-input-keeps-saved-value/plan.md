# PLAN 046 — money-input-keeps-saved-value

Branch: `bugfix/046-money-input-keeps-saved-value`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: esquema, os dois formulários e o rótulo do painel mudam juntos; separados, um campo aceitaria o formato brasileiro e o outro não.
- **O primeiro commit da branch marca a 045 como `done`** (mergeada em `develop` no PR #46).
- **Campo de texto, não `type="number"`**: só o texto cru permite ler "1.500,00" e distinguir "vazio" de "ilegível".
- **Vazio é erro, não pedido de remoção**: tirar o teto ou o limite é um botão próprio, visível só quando há valor gravado. Sem confirmação: desfaz-se digitando o valor de novo.
- **Ponto sozinho com uma ou duas casas é decimal** ("120.50"), com três casas é milhar ("1.500"): cobre quem digita no teclado numérico sem vírgula sem ambiguidade para valores inteiros de milhar.
- **O valor gravado aparece como "1.500,00"** no campo, no mesmo formato que se pede para digitar.

## Fase 1 — Campo de dinheiro no formato brasileiro

Ao final: "1.500,00" grava R$ 1.500,00 no teto e no limite; nada apaga o valor a não ser "Remover teto" / "Remover limite"; o botão do painel diz "Alterar teto" quando há teto.

- [x] T1.1 — Leitura do valor em formato brasileiro
  - Arquivos: `src/utils/money-text.ts` (criar), `src/utils/money-text-schema.ts` (alterar), `src/utils/cents.ts` (remover)
  - O que fazer: `parseMoneyText` e `formatMoneyInput`; o esquema recusa com uma mensagem por motivo, e o formulário converte o texto aceito em centavos pela mesma leitura.
  - Skills: forms, code-standards
  - Complexidade: baixa
- [x] T1.2 — Formulários e painel
  - Arquivos: `src/features/expenses/components/ceiling-form.tsx`, `src/features/categories/components/category-limit-form.tsx`, `src/features/expenses/components/month-ceiling.tsx`, `src/features/categories/components/category-item.tsx` (alterar)
  - O que fazer: campo de texto com `inputMode="decimal"`, botão explícito de remoção, rótulo "Alterar teto" e nome "Alterar limite de …" quando há valor.
  - Skills: forms, interface-design, component-robustness
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `src/utils/__tests__/money-text.test.ts` (criar), `src/utils/__tests__/cents.test.ts` (remover), testes dos dois formulários, do painel e da lista de categorias, `e2e/categories.spec.ts`, `e2e/expenses.spec.ts` (alterar)
  - O que fazer: leitura de cada formato aceito e de cada recusa; remoção só pelo botão; jornadas e2e digitando no formato brasileiro.
  - Skills: unit-testing, component-testing, e2e-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm test` sai com código 0, e no commit `7a33940` os seis testes de regressão listados em `investigation.md` falhavam. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — Em `ceiling-form.tsx` e `category-limit-form.tsx` o campo é `type="text"` com `inputMode="decimal"`, e o único ponto que manda `null` à API é o botão de remoção. (estrutural)
- [x] CA1.4 — `parseMoneyText` devolve 150000 para "1.500,00", "1500", "1.500", "R$ 1.500,00" e "1500,00"; 150050 para "1500,5" e "1500.50"; e recusa "", "abc", "15,00,0", "1,999" e "-5" com o motivo certo. (comportamental)
- [x] CA1.5 — No navegador, com teto gravado, digitar "1.500,00" e salvar mostra "de R$ 1.500,00" no painel; o botão diz "Alterar teto"; "Remover teto" volta a "Sem teto definido". (comportamental)

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
