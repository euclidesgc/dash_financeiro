# PLAN 054 — expenses-opens-current-month

Branch: `feature/054-expenses-opens-current-month`

Decisões na SPEC (D1 a D4). A captura em 375 px mostrou o seletor "Conta" passando 7 px da tela em qualquer período, também em `develop`: fora desta fatia, registrado no roadmap como 066. Uma fase: a mudança atravessa utilitário, tela, testes e documentos e só faz sentido inteira.

## Fase 1 — "Gastos" abre no mês corrente com o resultado no topo

- [x] T1.1 — Período padrão e nome do período
  - Arquivos: `src/features/expenses/utils/period.ts`
  - O que fazer: D1 e `formatPeriod` (D3).
  - Complexidade: baixa
- [x] T1.2 — Ordem da tela
  - Arquivos: `src/features/expenses/components/expenses-list.tsx`, `src/features/expenses/components/period-result.tsx`
  - O que fazer: D2 e a linha do período em `PeriodResult` (D3).
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `src/features/expenses/utils/__tests__/period.test.ts`, `src/features/expenses/components/__tests__/*.test.tsx`, `e2e/expenses.spec.ts`
  - O que fazer: casos de `readPeriod`/`writePeriod`/`formatPeriod`; padrão no mês corrente com data fixa; `period=all` onde o teste espera a lista inteira; e2e da abertura com relógio fixo e ordem visual.
  - Complexidade: média
- [x] T1.4 — Documentos
  - Arquivos: `docs/design.md`, `docs/features/005-filtrar-por-periodo/prd.md`, `docs/features/005-filtrar-por-periodo/spec.md`
  - O que fazer: reescrever no presente o padrão do período e a ordem da página.
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.3 — Com a data fixada em 15/09/2026, abrir "Gastos" pelo cabeçalho mostra "setembro de 2026", a API recebe `from=2026-09-01&to=2026-09-30`, o botão "Todo o período" está habilitado e os títulos "Resultado do período" e "Teto do mês" aparecem acima do campo "Buscar" na ordem do documento. (comportamental)
- [x] CA1.4 — Clicar "Todo o período" grava `period=all`, a API não recebe `from`/`to`, o resultado some, e depois de recarregar e trocar a ordenação o período continua "Todo o período". (comportamental)
- [x] CA1.5 — Voltar `readPeriod` a devolver `all` sem parâmetros faz falhar o teste do padrão em `period.test.ts` e o de `expenses-list.test.tsx`; desfeita a troca, voltam a passar. (comportamental)
- [x] CA1.6 — Em 375 px e 1280 px, a página aberta pelo cabeçalho mostra o resultado do período e o teto do mês antes dos filtros (captura no backend isolado do e2e). (comportamental)

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
