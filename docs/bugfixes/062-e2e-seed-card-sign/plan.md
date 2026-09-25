# PLAN 062 — e2e-seed-card-sign

Branch: `bugfix/062-e2e-seed-card-sign`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a causa está no dado de teste, dois arquivos.
- **Corrigir o dado, não o código**: a ingestão aplica o invariante 22 corretamente; o seed é que não imitava a Pluggy.
- **Prova pela posição consolidada**: o teste compara `positions()` do seed com o número esperado, o mesmo cálculo que o Resumo antigo mostra.

## Fase 1 — Cartão da base de teste como dívida

Ao final: na base de teste, o cartão entra negativo e a posição consolidada desconta a dívida do cartão.

- [x] T1.1 — Saldo do cartão com o sinal da Pluggy
  - Arquivos: `tests/data/e2e_accounts.json`, `tests/test_typed_limits.py` (alterar)
  - O que fazer: trocar o saldo das contas `CREDIT` de negativo para positivo, como a Pluggy manda.
  - Complexidade: baixa
- [x] T1.2 — Teste de regressão
  - Arquivos: `tests/test_e2e_seed.py`
  - O que fazer: o teste da posição consolidada do seed passa.
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `uv run pytest` sai com código 0, e no commit `5441c7a` o teste `test_the_seed_card_enters_as_debt_and_lowers_the_consolidated_position` falhava. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — Nenhuma conta `CREDIT` passada à ingestão nos testes tem saldo negativo. (estrutural)
- [x] CA1.4 — Depois do seed, `positions()` devolve caixa `1234`, cartão `-4500` e consolidada `-3266`. (comportamental)

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
