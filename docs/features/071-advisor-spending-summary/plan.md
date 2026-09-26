# PLAN 071 — advisor-spending-summary

Branch: `feature/071-advisor-spending-summary`

## Fase 1 — Resumo de gastos, menos chamadas e excesso claro

- [x] T1.1 — Totais por mês
  - Arquivos: `app/queries/expenses.py` (alterar)
  - O que fazer: `monthly_totals(conn, *, date_from, date_to, account_id)` agrupado por mês com `INCOME` e `SPENDING`.
  - Complexidade: baixa

- [x] T1.2 — Ferramenta `spending_summary` e prompt com categorias
  - Arquivos: `app/advisor/tools.py`, `app/advisor/chat.py` (alterar)
  - O que fazer: ferramenta sobre `period_result`, `sum_by_category` e `monthly_totals`, em `TOOLS`; `system_prompt(today, categories)` lista as categorias e diz qual ferramenta usar.
  - Complexidade: média

- [x] T1.3 — 429 do Gemini com espera ou cota diária
  - Arquivos: `app/advisor/gemini_provider.py` (alterar)
  - Complexidade: baixa

- [x] T1.4 — Testes da fase 1
  - Arquivos: `tests/test_monthly_totals.py` (criar); `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`, `tests/test_advisor_providers.py` (alterar)
  - Complexidade: média

### Critérios de aceite da fase 1

- [x] CA1.1 — (comportamental) `monthly_totals` soma entradas e gastos por mês e deixa fora transferência própria, estorno e "não é gasto"; provado em `tests/test_monthly_totals.py`.
- [x] CA1.2 — (comportamental) `spending_summary` devolve por categoria, entradas, gastos, saldo e meses com os mesmos centavos de `sum_by_category`, `period_result` e `monthly_totals`, em reais formatados; entrada inválida vira erro com a lista do que existe.
- [x] CA1.3 — (comportamental) Os dois adaptadores recebem `spending_summary` entre as ferramentas; o prompt lista as categorias do painel; resposta que soma duas categorias por conta própria é trocada pelo aviso.
- [x] CA1.4 — (comportamental) 429 do Gemini com `retryDelay` diz quantos segundos esperar; com cota diária diz que a cota do dia acabou.
- [x] CA1.5 — (comando) `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh` e `uv run pytest` passam.

## Fase 2 — Tela diz o que o consultor consultou

- [x] T2.1 — Descrição por ferramenta
  - Arquivos: `src/features/advisor/components/chat-message-item.tsx`, `src/features/advisor/components/__tests__/*` (alterar)
  - Complexidade: baixa

### Critérios de aceite da fase 2

- [x] CA2.1 — (comportamental) Resposta que usou as duas ferramentas mostra "consultou seus lançamentos e o resumo de gastos".
- [x] CA2.2 — (comando) `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` passam.

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
