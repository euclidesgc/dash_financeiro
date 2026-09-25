# PLAN 028 — manual-category-classify-precedence

Branch: `feature/028-manual-category-classify-precedence`

Decisões registradas aqui (escolhido o mais simples):

- **Trilha de feature, não de bugfix**: a precedência da regra por descrição foi combinada na SPEC 009 (D4) e o item está na tabela de dívidas; muda-se um comportamento combinado, com PRD/SPEC/PLAN como nas dívidas 024 e 032.
- **Uma fase só**: ~10 linhas de código; nada utilizável no meio.
- **O primeiro commit da branch marca a 032 como `done`** (mergeada em `develop` no PR #19).

## Fase 1 — Ajuste manual decide o agrupamento

Ao final: um gasto com categoria manual fica no grupo, natureza e essencialidade da regra da categoria escolhida (ou no fallback, sem regra), mesmo com regra por descrição casando o recebedor; voltar para a automática devolve a precedência da descrição; a prévia da correção por recebedor nas telas Jinja conta só lançamentos automáticos.

- [ ] T1.1 — Ramo manual em `_match`
  - Arquivos: `app/taxonomy/classify.py` (alterar)
  - O que fazer: constante `MANUAL = "manual"`; o `SELECT` de `classify_all` inclui `category_source`; em `_match`, se `row["category_source"] == MANUAL`, devolver `categories.get(row["category"])` antes de olhar `expressions`.
  - Skills: python-tipagem-estrita
  - Complexidade: baixa
- [ ] T1.2 — Prévia e holders só com linhas automáticas
  - Arquivos: `app/queries/reach.py` (alterar)
  - O que fazer: `payee_reach` filtra `payee = ? AND category_source = 'auto'`; `_HOLDERS` ganha `AND t.category_source = 'auto'`.
  - Complexidade: baixa
- [ ] T1.3 — Testes
  - Arquivos: `tests/test_classify.py`, `tests/test_reach.py`, `tests/test_corrections.py`, `tests/test_override.py` (alterar)
  - O que fazer: `test_a_manual_category_beats_the_expression_rule_that_matches_its_payee`, `test_a_manual_row_without_category_rule_falls_into_the_fallback_not_the_expression_rule`, `test_restoring_auto_gives_the_expression_rule_back_its_precedence`, `test_an_auto_row_still_follows_the_expression_rule_before_the_category_rule` (existente `test_an_expression_rule_beats_the_category_rule_it_overlaps` cobre), `test_payee_reach_and_holders_leave_manual_rows_out`, `test_a_correction_over_a_payee_with_a_manual_row_reaches_what_the_preview_promised`, `test_set_manual_moves_a_row_held_by_an_expression_rule_to_the_category_group`, `test_a_sync_keeps_the_manual_row_in_the_category_group`.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [ ] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [ ] CA1.3 — Em `app/taxonomy/classify.py::_match`, o teste de `category_source` manual vem antes do laço sobre as regras por descrição e devolve só a busca por categoria; o ramo automático é o de antes. (estrutural)
- [ ] CA1.4 — Em `app/queries/reach.py`, `payee_reach` e `_HOLDERS` filtram `category_source = 'auto'`; `category_reach` e `rule_reach` não mudam. (estrutural)
- [ ] CA1.5 — Comportamento: linha manual com recebedor casado por regra por descrição fica no grupo/natureza/essencialidade da regra da categoria escolhida; manual sem regra de categoria (ou "Sem categoria") cai no fallback; voltar para automática devolve a linha à regra por descrição; linha automática segue a regra por descrição antes da de categoria; uma sincronização mantém a linha manual no grupo da categoria; prévia e holders da correção por recebedor ignoram linhas manuais e o resultado bate com a prévia. Tirar o ramo manual de `_match` faz os testes de manual falharem. (comportamental)

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
