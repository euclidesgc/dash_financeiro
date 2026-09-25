# PLAN 026 — unify-payee-name-precedence

Branch: `feature/026-unify-payee-name-precedence`

Decisões registradas aqui:

- **Trilha de feature**: dívida registrada na SPEC 007; muda-se onde a regra mora, sem mudar o que o usuário vê na base atual.
- **Uma fase só**: a troca é atômica — mover a regra sem trocar os dois leitores deixaria três cópias.
- **O primeiro commit da branch marca a 022 como `done`** (mergeada em `develop` no PR #30).

## Fase 1 — Uma precedência só para o nome do recebedor

Ao final: a precedência do nome existe só em `app/queries/payees.py`; a tela de recebedores e a lista de gastos (nome exibido e busca) leem dela.

- [x] T1.1 — Precedência em SQL
  - Arquivos: `app/queries/payees.py` (alterar)
  - O que fazer: constantes `OWNER`, `PLUGGY`, `LOOKUP`, `LEGAL`, `DESCRIPTION`; tupla ordenada `(expressão, origem)`; `RESOLVED_PAYEES` com `payee`, `name` (nulo sem nome) e `source`, agregando `transactions` por `payee` com `MIN` e juntando `payee_names` de `dono` e `cnpj`.
  - Complexidade: baixa
- [x] T1.2 — `display_name` lê a consulta
  - Arquivos: `app/payees/names.py` (alterar)
  - O que fazer: `display_name` executa `RESOLVED_PAYEES` e devolve `{"name": name or payee, "source": source}`; remove `_chosen` e `_FROM_PLUGGY`; reexporta as origens.
  - Complexidade: baixa
- [x] T1.3 — Lista de gastos junta a consulta
  - Arquivos: `app/queries/expenses.py` (alterar)
  - O que fazer: `_FROM` com `LEFT JOIN (RESOLVED_PAYEES) AS pn`; `_SELECT` com `pn.name AS payee_name`; busca por `fold(pn.name)`; `_item` lê `row["payee_name"]`; remove `_PAYEE_NAME_SQL` e `labels()`.
  - Complexidade: baixa
- [x] T1.4 — Testes
  - Arquivos: `tests/test_payee_names.py`, `tests/test_expenses_api.py` (alterar)
  - O que fazer: `test_the_list_shows_the_same_name_the_payees_screen_resolves` (para cada origem, `payee_name` do item = `display_name` do `payee`, e `None` quando a origem é `descricao`); `test_the_search_follows_the_name_of_the_payee_not_of_the_row` (duas linhas do mesmo `payee` com `merchant_name` diferentes: busca pelo nome escolhido acha as duas, pelo outro não acha nenhuma); `test_a_looked_up_name_is_searched_below_the_merchant_name`.
  - Skills: python-testes-de-integracao-httpx
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — `grep -rn "merchant_name" app/payees app/queries/expenses.py` não encontra nada; a ordem das origens aparece uma vez só, em `app/queries/payees.py`. (estrutural)
- [x] CA1.4 — O `payee_name` de cada item da lista é o `name` de `display_name` para o mesmo `payee` (ou nulo quando a origem é `descricao`), e a busca `q` acha um gasto pelo nome exibido e não pelo nome de nível inferior; inverter duas origens na tupla faz os testes de precedência falharem nas duas telas. (comportamental)

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
