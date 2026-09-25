# PLAN 029 — jinja-labels-from-schema

Branch: `feature/029-jinja-labels-from-schema`

Decisões registradas aqui (escolhido o mais simples):

- **Trilha de feature**: item da tabela de dívidas, muda um comportamento combinado (de onde as telas Jinja leem o rótulo), como nas dívidas 024, 028 e 032.
- **Uma fase só**: ~15 linhas de código; nada utilizável no meio.
- **O primeiro commit da branch marca a 027 como `done`** (mergeada em `develop` no PR #32).

## Fase 1 — Telas Jinja leem o rótulo da tabela de categorias

Ao final: a tela de gastos por eixo e a de regras mostram o rótulo atual de cada categoria, inclusive renomeada ou criada pelo dono, sem reiniciar o servidor.

- [x] T1.1 — Consulta `category_labels`
  - Arquivos: `app/queries/categories.py` (alterar)
  - O que fazer: `category_labels(conn) -> dict[str, str]` com `SELECT name, label FROM categories`.
  - Skills: python-tipagem-estrita
  - Complexidade: baixa
- [x] T1.2 — Routers sem `LABELS` de import
  - Arquivos: `app/routers/spending.py`, `app/routers/rules.py` (alterar)
  - O que fazer: remover `LABELS` e o import de `seed_labels`; `_base` recebe `conn` e usa `category_labels(conn)`; `_panel_context` e `rules._context` usam `category_labels(conn)`.
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `tests/test_taxonomy_tree.py`, `tests/test_gastos_screen.py`, `tests/test_regras_screen.py`, `tests/test_categories_api.py` (alterar)
  - O que fazer: tirar as asserções sobre `LABELS` dos routers; `test_a_category_whose_label_differs_from_its_name_shows_both` lê o rótulo de `categories`; `test_a_renamed_category_shows_its_new_label_on_the_table_the_panel_and_the_detail`, `test_a_category_the_owner_created_shows_its_label_on_the_table`, `test_a_renamed_category_shows_its_new_label_on_the_rules_screen`, `test_a_category_the_owner_created_shows_its_label_among_the_loose_categories`, `test_category_labels_reads_every_row_of_categories`.
  - Skills: python-testes-de-integracao-httpx
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — `grep -rn "seed_labels\|LABELS" app/routers/spending.py app/routers/rules.py` não devolve nada; `category_labels` está em `app/queries/categories.py`. (estrutural)
- [x] CA1.4 — Comportamento: depois de `UPDATE categories SET label = …` com o servidor já no ar, a tabela, o painel e a lista aberta de `/gastos` e a tela `/regras` mostram o rótulo novo; uma categoria inserida em `categories` com rótulo próprio aparece com esse rótulo nas duas telas; voltar a ler `seed_labels()` nos routers faz esses testes falharem. (comportamental)

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
