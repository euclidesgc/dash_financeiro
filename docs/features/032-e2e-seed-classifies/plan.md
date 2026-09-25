# PLAN 032 — e2e-seed-classifies

Branch: `feature/032-e2e-seed-classifies`

Decisões registradas aqui (escolhido o mais simples):

- **Uma fase só**: ~45 linhas de fixture e um script; nada utilizável no meio de duas fases.
- **O primeiro commit da branch marca a 024 como `done`** (mergeada em `develop` no PR #18).

## Fase 1 — Seed do e2e classifica a base, em módulo testado

Ao final: `scripts/e2e-backend.sh` monta a base por `uv run python -m tests.e2e_seed`; a base sai com todo lançamento classificado como depois de uma sincronização, sem linha em `sync_runs`; carga recusada não classifica e o script não sobe o servidor.

- [x] T1.1 — Extrair o seed para `tests/e2e_seed.py` e classificar depois da carga `ok`
  - Arquivos: `tests/e2e_seed.py` (criar); `scripts/e2e-backend.sh` (alterar)
  - O que fazer: `seed(conn) -> IngestResult` com `seed_user(conn, "e2e", "senha-e2e-9k2")`, `seed_taxonomy`, `ingest` de `tests/data/e2e_transactions.json` e `tests/data/e2e_accounts.json` com `source="e2e"`; se `status != "ok"`, devolve sem classificar; senão `classify_all(conn)`, `DELETE FROM sync_runs` (mantém o `# Reason:`), `commit`. `main() -> int` migra, conecta, chama `seed`, fecha; `0` se `ok`, `1` senão. No script, o bloco `uv run python -c '…'` vira `uv run python -m tests.e2e_seed`.
  - Skills: python-tipagem-estrita
  - Complexidade: baixa
- [x] T1.2 — Testes de `tests/e2e_seed.py`
  - Arquivos: `tests/test_e2e_seed.py` (criar)
  - O que fazer: base temporária migrada; testes `test_the_seed_leaves_every_transaction_classified`, `test_classifying_again_after_the_seed_changes_nothing`, `test_the_seed_records_no_sync_run_and_creates_the_e2e_user`, `test_a_rejected_seed_load_classifies_nothing`, `test_main_exits_with_one_when_the_seed_load_is_rejected`, `test_main_exits_with_zero_on_a_clean_seed`.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `pnpm test:e2e` sai com código 0, com o backend montado por `scripts/e2e-backend.sh`. (comando)
- [x] CA1.3 — `scripts/e2e-backend.sh` não contém `python -c` e contém a linha `uv run python -m tests.e2e_seed`; os `export` e a subida do `uvicorn` não mudam (`git diff develop -- scripts/e2e-backend.sh` só remove o bloco `python -c` e acrescenta essa linha). (estrutural)
- [x] CA1.4 — Em `tests/e2e_seed.py`, `classify_all(conn)` aparece depois do teste `result.status != "ok"` com `return` e antes de `DELETE FROM sync_runs` e do `commit()`. (estrutural)
- [x] CA1.5 — Comportamento: depois do seed nenhum lançamento fica sem grupo, natureza ou essencialidade e ao menos um casa com regra; classificar de novo muda `0` linhas; `sync_runs` fica vazia e o usuário `e2e` existe; carga recusada não classifica nada e `main` devolve `1`; carga limpa devolve `0` (os seis testes de `tests/test_e2e_seed.py`). Tirar a chamada `classify_all(conn)` faz os dois primeiros falharem. (comportamental)

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
