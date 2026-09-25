# PLAN 019 — pluggy-extract-env-handling

Branch: `feature/019-pluggy-extract-env-handling`

Decisões registradas aqui:

- **Nomes novos em inglês** (norma 16), mesmo nos scripts de `ingestao/` que ainda têm nomes em português; renomear o resto está fora desta fatia.
- **O primeiro commit da branch marca a 018 como `done`** (mergeada em `develop` no PR #25).

## Fase 1 — Scripts com funções limpas e serviço sem `SystemExit`

Ao final: o comando manual lê as credenciais como o painel, e o serviço de sincronização chama a consolidação por uma função que levanta exceção própria e não imprime.

- [x] T1.1 — Credenciais e consolidação limpas
  - Arquivos: `ingestao/pluggy_extract.py`, `ingestao/pluggy_consolidate.py`, `app/sync/fetch.py` (alterar)
  - O que fazer: D1, D2, D3 e D4 da SPEC.
  - Skills: python-tratamento-de-erros, python-tipagem-estrita
  - Complexidade: baixa
- [x] T1.2 — Testes
  - Arquivos: `tests/test_pluggy_scripts.py` (criar), `tests/test_sync_fetch.py` (alterar)
  - O que fazer: `read_credentials` lê o arquivo de `DASH_ENV_FILE`, deixa a variável de ambiente valer sobre o arquivo e, sem credencial, levanta `MissingCredentialsError` citando o nome e nunca o valor; `consolidate()` sem dados brutos levanta `NoRawAccountsError` sem imprimir; `consolidate()` com dados devolve as contagens sem imprimir; `main()` da consolidação sem dados sai com `SystemExit`; `fetch_from_pluggy` com contas vazias levanta `PluggyFetchError` com "a consolidação dos dados brutos falhou".
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — `grep -n "SystemExit" app/sync/fetch.py app/sync/__init__.py` não encontra nada (o `app/sync/__main__.py` é ponto de entrada de comando e sai com o código do `main`); `grep -n "ENV_PATH\|carregar_env" ingestao/pluggy_extract.py` não encontra nada; `ingestao/` não importa `app`. (estrutural)
- [x] CA1.4 — Com `DASH_ENV_FILE` apontando para um arquivo com as duas credenciais, `read_credentials()` as devolve; uma variável de ambiente já definida vence o arquivo; sem `PLUGGY_CLIENT_SECRET`, `MissingCredentialsError` cita o nome da variável. (comportamental)
- [x] CA1.5 — Sem `data/raw/accounts_*.json`, `consolidate()` levanta `NoRawAccountsError` e nada é impresso; `fetch_from_pluggy` com a Pluggy devolvendo zero contas levanta `PluggyFetchError` com "a consolidação dos dados brutos falhou". (comportamental)

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
