# PLAN 060 — plain-language-copy

Branch: `feature/060-plain-language-copy`

Decisões registradas aqui:

- **Trilha de feature**: muda o texto combinado de telas que existem.
- **Uma fase só**: são trocas de texto independentes, sem estado novo.

## Fase 1 — Textos que o dono entende

Ao final: nenhuma tela manda rodar comando, mostra endereço como texto de link ou usa termo interno sem explicação.

- [x] T1.1 — Telas antigas
  - Arquivos: `app/settings/catalog.py`, `app/advisor/gaps.py`, `app/advisor/gemini.py`, `app/routers/summary.py`, `app/templates/{configuracao,consultor}.html`, `app/templates/fragments/{gastos_correcao,resumo_sincronizacao}.html` (alterar)
  - O que fazer: `SCREEN_LABELS` e `screen_label` no catálogo, `where_label` nas perguntas, links com o nome da tela, Resumo sem `COMMAND`.
  - Complexidade: baixa
- [x] T1.2 — SPA
  - Arquivos: `sync-panel.tsx`, `category-totals.tsx`, `balance-item.tsx`, `balances-list.tsx`, `routes/dashboard.tsx`, `routes/connections.tsx` (alterar)
  - O que fazer: os textos de R3 a R6 do PRD.
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `tests/test_{configuracao,resumo,consultor}_screen.py`, `tests/test_{advisor,settings}.py`, testes de componente e `e2e/{sync,expenses}.spec.ts` (alterar)
  - O que fazer: afirmar o texto novo; novos casos para link sem endereço na Configuração e Resumo sem comando.
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.3 — `grep -rnE "Sinal só por mês|Pedida na tela|Nunca atualizado|python -m app.sync|>Concluída" app src` não encontra nada. (estrutural)
- [x] CA1.4 — `GET /configuracao` não tem nenhum `<a href="…">/`; `GET /` com a base vazia não tem `python -m` na seção de sincronização (`tests/test_configuracao_screen.py`, `tests/test_resumo_screen.py`). (comportamental)

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
