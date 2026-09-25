# PLAN 065 — category-label-max-length

Branch: `bugfix/065-category-label-max-length`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a regra do nome mora num ponto do servidor (`_check_label`) e os dois formulários já mostram o `detail` do 422 embaixo do campo.
- **O primeiro commit da branch marca a 063 como `done`** (mergeada em `develop` no PR #54).
- **Teto de 40 caracteres**: o maior nome do catálogo tem 33; 40 é o teto do nome de grupo e do nome de cenário, rótulos do mesmo tipo.
- **A regra no domínio, não no esquema Pydantic**: um `max_length` no `CategoryInput` responderia 422 com a lista em inglês da Pydantic, e contaria os espaços das pontas que a regra tira antes de gravar.
- **Número repetido na SPA, amarrado por teste**: a SPA não lê `app/settings/limits.py`; um teste do pytest compara os dois números.

## Fase 1 — Nome de categoria com teto no servidor e nos campos

Ao final: um nome de categoria acima de 40 caracteres é recusado pelo servidor com mensagem em português, e os campos de criar e renomear param no mesmo teto.

- [ ] T1.1 — Teto no servidor
  - Arquivos: `app/settings/limits.py`, `app/taxonomy/catalogue.py`, `app/routers/categories.py` (alterar)
  - O que fazer: `CATEGORY_LABEL_MAX`; `LabelTooLongError` em `_check_label`, medido depois do `strip`; tradução para 422 com "O nome da categoria pode ter no máximo 40 caracteres.".
  - Skills: python-tratamento-de-erros
  - Complexidade: baixa
- [ ] T1.2 — Teto na SPA
  - Arquivos: `src/features/categories/types/category-label-schema.ts`, `src/features/categories/components/create-category-form.tsx`, `src/features/categories/components/rename-category-form.tsx`, `src/testing/mocks/handlers.ts` (alterar)
  - O que fazer: `CATEGORY_LABEL_MAX` exportado e usado no `.max()` do esquema e no `maxLength` dos dois campos; a API simulada recusa o nome longo com o mesmo 422.
  - Skills: forms, api-mocking
  - Complexidade: baixa
- [ ] T1.3 — Testes
  - Arquivos: `tests/test_categories_api.py`, `src/features/categories/types/__tests__/category-label-schema.test.ts`, `src/features/categories/components/__tests__/create-category-form.test.tsx`, `src/features/categories/components/__tests__/categories-list.test.tsx`, `e2e/categories.spec.ts`
  - O que fazer: os testes de regressão passam.
  - Skills: component-testing, e2e-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `uv run pytest` sai com código 0, e no commit `e27c574` os testes `test_post_refuses_a_label_one_over_the_ceiling_with_422_and_writes_nothing`, `test_patch_refuses_a_label_one_over_the_ceiling_with_422_and_keeps_the_old_one` e `test_the_spa_holds_the_category_label_to_the_server_ceiling` falhavam. (comando)
- [ ] CA1.2 — `pnpm test` sai com código 0, e no commit `e27c574` os testes `a name one over the ceiling is refused with the server message`, `the name field stops at the 40 characters the server accepts` e `the rename field stops at the 40 characters the server accepts` falhavam. (comando)
- [ ] CA1.3 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh`, `pnpm lint`, `pnpm typecheck`, `pnpm build` e `pnpm test:e2e` saem com código 0, e no commit `e27c574` o e2e `creates, uses, renames and deletes a category and leaves the base as it found it` falhava. (comando)
- [ ] CA1.4 — O número 40 do teto do nome de categoria aparece no servidor só em `app/settings/limits.py`, e na SPA só em `src/features/categories/types/category-label-schema.ts`. (estrutural)
- [ ] CA1.5 — Um nome de 40 caracteres com espaços nas pontas é aceito e gravado sem os espaços; um de 41 recebe 422 e nada muda na lista. (comportamental)

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
