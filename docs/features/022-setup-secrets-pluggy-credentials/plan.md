# PLAN 022 — setup-secrets-pluggy-credentials

Branch: `feature/022-setup-secrets-pluggy-credentials`

Decisão registrada: o primeiro commit da branch marca a 039 como `done` (mergeada em `develop` no PR #29).

## Fase 1 — Página de configuração fiel ao código

- [x] T1.1 — Reescrever a página e completar o exemplo
  - Arquivos: `docs/setup-secrets.md`, `.env.example`
  - O que fazer: D1 a D3 da SPEC.
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `grep -c "PLUGGY_CLIENT_ID\|PLUGGY_CLIENT_SECRET\|DASH_SYNC_SOURCE" docs/setup-secrets.md` é maior que 0 e `grep -n "DATABASE_URL\|SECRET_KEY\|APP_ENV\|CORS_ORIGINS\|gitleaks" docs/setup-secrets.md` não encontra nada. (estrutural)
- [x] CA1.2 — Toda variável da página aparece em `app/config.py` ou `app/sync/__init__.py`. (estrutural)
- [x] CA1.3 — `grep -x "DASH_SYNC_SOURCE=" .env.example` encontra a linha; `uv run pytest`, `bash scripts/lint.sh` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)

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
