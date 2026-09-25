# PLAN 037 — e2e-suite-repeatable

Branch: `bugfix/037-e2e-suite-repeatable`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: infraestrutura do e2e e um teste Python.
- **O primeiro commit da branch marca a 038 como `done`** (mergeada em `develop` no PR #23).
- **Restauração pelo arquivo, não rota de desfazer nem asserção mais frouxa**: sincronização é histórico e não tem desfazer na API; e o teste de "Nunca atualizado" continua exigindo a base nunca sincronizada.
- **Backup do SQLite, não cópia de arquivo**: o servidor está de pé com conexões abertas; a API de backup passa pelas travas do banco.

## Fase 1 — A suíte ponta a ponta aguenta várias voltas seguidas

Ao final: `pnpm test:e2e --repeat-each=3` passa inteiro, e cada teste de sincronização começa e termina na base do seed.

- [x] T1.1 — Cópia do seed e restauração
  - Arquivos: `playwright.config.ts` (alterar); `scripts/e2e-backend.sh` (alterar); `tests/e2e_restore.py` (criar)
  - O que fazer: `playwright.config.ts` define `process.env.DASH_E2E_DIR` com `mkdtempSync` só se ainda não existir (o processo dos testes herda o do principal). `scripts/e2e-backend.sh` usa `DASH_E2E_DIR` como pasta, copia `dash.sqlite` para `seed.sqlite` depois do seed e antes do servidor, e apaga a pasta na saída. `tests/e2e_restore.py` tem `restore(snapshot, target)`, que copia pela `sqlite3.Connection.backup`, e `main(argv)` com os dois caminhos.
  - Skills: e2e-testing
  - Complexidade: baixa
- [x] T1.2 — Testes de sincronização partem da base do seed
  - Arquivos: `e2e/restore-seeded-base.ts` (criar); `e2e/sync.spec.ts` (alterar)
  - O que fazer: `restoreSeededBase()` chama `uv run python -m tests.e2e_restore <pasta>/seed.sqlite <pasta>/dash.sqlite` e falha se `DASH_E2E_DIR` não existir. `e2e/sync.spec.ts` chama em `test.beforeEach` e `test.afterEach`.
  - Skills: e2e-testing
  - Complexidade: baixa
- [x] T1.3 — Teste da restauração
  - Arquivos: `tests/test_e2e_restore.py` (criar)
  - O que fazer: um banco semeado, a cópia, uma linha nova em `sync_runs` no banco vivo com uma conexão aberta; depois de `restore`, a conexão aberta lê `sync_runs` vazio. `main` com argumentos errados sai com 1.
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest`, `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0. (comando)
- [x] CA1.2 — `pnpm test:e2e --repeat-each=3` sai com código 0. (comando)
- [x] CA1.3 — `e2e/sync.spec.ts` chama `restoreSeededBase` em `test.beforeEach` e em `test.afterEach`, e a asserção `getByText('Nunca atualizado')` continua no primeiro teste. (estrutural)
- [x] CA1.4 — Sem a restauração, `pnpm exec playwright test e2e/sync.spec.ts --repeat-each=2` falha em "Nunca atualizado"; com ela, passa. (comportamental)

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
