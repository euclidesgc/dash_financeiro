# PLAN 038 — e2e-ceiling-reload-flaky

Branch: `bugfix/038-e2e-ceiling-reload-flaky`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: um arquivo de teste.
- **O primeiro commit da branch marca a 036 como `done`** (mergeada em `develop` no PR #22).
- **Limpeza garantida pela API, não retentativa nem prazo maior**: o defeito é a limpeza depender do teste passar; tempo de espera não muda isso.
- **Os casos iguais ao do teto entram juntos**: o limite de Supermercado e as duas marcas de não-gasto e não-entrada são desfeitos do mesmo jeito no mesmo arquivo.

## Fase 1 — Uma falha na tela de gastos não suja a base dos testes seguintes

Ao final: um teste de `e2e/expenses.spec.ts` que falha no meio deixa a base como o seed a criou, e a repetição seguinte começa limpa.

- [x] T1.1 — Limpeza depois de cada teste
  - Arquivos: `e2e/expenses.spec.ts` (alterar)
  - O que fazer: `test.afterEach` com a fixture `request` entra com o usuário do e2e (`POST /api/auth/login`), grava teto nulo (`PUT /api/plan/ceiling`), acha a chave de Supermercado em `GET /api/categories` e grava limite nulo (`PUT /api/categories/<chave>/limit`), lista `GET /api/transactions/expenses?view=excluded` de 01/08/2026 a 30/09/2026 e apaga a marca (`DELETE /api/transactions/<id>/not-expense`) de AÇOUGUE SÃO JORGE e SALARIO. Toda resposta passa por `expectOk`, que exige `response.ok()`.
  - Skills: e2e-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0. (comando)
- [x] CA1.2 — `pnpm exec playwright test e2e/expenses.spec.ts --repeat-each=20` sai com código 0, e `pnpm test:e2e` sai com código 0. (comando)
- [x] CA1.3 — `e2e/expenses.spec.ts` tem um `test.afterEach` que usa a fixture `request`, e cada chamada dele à API passa por `expectOk`. (estrutural)
- [x] CA1.4 — Com uma asserção que falha logo depois do primeiro "Salvar" do teto, `--repeat-each=2` do teste do teto falha nas duas voltas **na asserção forçada**, não em "Sem teto definido.". (comportamental)

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
