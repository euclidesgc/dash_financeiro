# PLAN 035 — mocks-spending-rule-duplication

Branch: `feature/035-mocks-spending-rule-duplication`

Decisões registradas aqui:

- **Trilha de feature**: dívida registrada na entrega 016; muda a garantia dos testes, não o que o usuário vê.
- **Uma fase só**: tabela, os dois testes e a correção da divergência só fazem sentido juntos.
- **O primeiro commit da branch marca a 034 como `done`** (mergeada em `develop` no PR #36).

## Fase 1 — Tabela de casos comum à API e à API simulada

Ao final: uma tabela de casos decide a separação em gastos, entradas e "não é gasto" para a API e para a API simulada, e as duas passam nela.

- [ ] T1.1 — Tabela de casos
  - Arquivos: `src/testing/contracts/expense-views.json` (criar), `tsconfig.app.json` (alterar)
  - O que fazer: casos de saída e entrada, com e sem motivo, e de valor zero, com e sem motivo; ligar `resolveJsonModule`.
  - Skills: api-mocking, code-standards
  - Complexidade: baixa
- [ ] T1.2 — API simulada alinhada
  - Arquivos: `src/testing/mocks/handlers.ts` (alterar)
  - O que fazer: exportar `matchesView`; `excluded` exige `amount_cents !== 0`.
  - Skills: api-mocking
  - Complexidade: baixa
- [ ] T1.3 — Testes dos dois lados
  - Arquivos: `tests/test_expense_views_contract.py` (criar), `src/testing/mocks/__tests__/expense-views-contract.test.ts` (criar)
  - O que fazer: a API por `list_expenses` em cada lista, com e sem sinalizadores de transferência e estorno; a API simulada por `matchesView` e pelo `period-result`.
  - Skills: python-testes-unitarios, unit-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [ ] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [ ] CA1.3 — `tests/test_expense_views_contract.py` e `src/testing/mocks/__tests__/expense-views-contract.test.ts` leem `src/testing/contracts/expense-views.json`, e nenhum dos dois escreve casos próprios de separação. (estrutural)
- [ ] CA1.4 — Trocar `INCOME` por `INFLOW` no `_PREDICATE` de `app/queries/expenses.py` faz falhar o teste da API; desfeita a troca, volta a passar. (comportamental)
- [ ] CA1.5 — Tirar `amount_cents !== 0` de `excluded` em `matchesView` faz falhar o teste da API simulada; desfeita a troca, volta a passar. (comportamental)

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
