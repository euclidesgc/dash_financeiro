# PLAN 034 — override-unnecessary-reclassify

Branch: `feature/034-override-unnecessary-reclassify`

Decisões registradas aqui:

- **Trilha de feature**: dívida registrada na entrega 015; tira um custo sem mudar o que o usuário vê.
- **Uma fase só**: a troca é atômica.
- **O primeiro commit da branch marca a 031 como `done`** (mergeada em `develop` no PR #35).

## Fase 1 — Marcação de não-gasto sem reclassificar

Ao final: marcar e desmarcar "não é gasto" gravam só o motivo; as trocas de categoria continuam reclassificando.

- [x] T1.1 — Escrita com reclassificação opcional
  - Arquivos: `app/taxonomy/override.py` (alterar)
  - O que fazer: `_write(..., *, reclassify: bool)`; `set_manual`, `restore_auto`, `apply_to_similar` com `True`; `set_not_expense`, `clear_not_expense` com `False`.
  - Skills: python-service-layer, python-tipagem-estrita
  - Complexidade: baixa
- [x] T1.2 — Testes pelo estado
  - Arquivos: `tests/test_override.py` (alterar)
  - O que fazer: o teste de marcação afirma o motivo gravado e persistido, sem afirmar reclassificação; um teste com grupo desatualizado à mão prova que marcar e desmarcar não o corrigem; outro prova que `set_manual` corrige.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — Em `app/taxonomy/override.py`, `set_not_expense` e `clear_not_expense` chamam `_write` com `reclassify=False`, e os outros três escritores com `reclassify=True`. (estrutural)
- [x] CA1.4 — Passar `reclassify=True` em `set_not_expense` faz falhar o teste do grupo desatualizado em `tests/test_override.py`; desfeita a troca, volta a passar. (comportamental)

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
