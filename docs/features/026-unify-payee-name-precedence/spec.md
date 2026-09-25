# SPEC 026 — unify-payee-name-precedence

## Contexto

- `app/payees/names.py::_chosen` decide o nome exibido de um recebedor (`payee`) em Python, sobre uma consulta que agrega `transactions` por `payee` com `MIN` (`_FROM_PLUGGY`) e sobre as linhas de `payee_names` (fontes `dono` e `cnpj`). `display_name`, `labels` e `ranked` saem dela.
- `app/queries/expenses.py::_PAYEE_NAME_SQL` reescreve a mesma precedência em SQL, **por linha** de `transactions`, só para a busca `q`; o `payee_name` de cada item da lista vem de `labels()` (Python). São duas cópias da regra, e com granularidades diferentes (grupo × linha).

## Decisões

### D1 — A precedência existe uma vez, em SQL, em `app/queries/payees.py`

`app/queries/payees.py` ganha as constantes de origem (`OWNER`, `PLUGGY`, `LOOKUP`, `LEGAL`, `DESCRIPTION`) e `RESOLVED_PAYEES`: uma consulta com uma linha por `payee` (`payee`, `name`, `source`), montada a partir de uma única tupla ordenada `(expressão, origem)`. `name` é o primeiro nome não vazio da precedência ou `NULL`; `source` é a origem dele ou `descricao`. A agregação por `payee` com `MIN` é a de hoje.

- Alternativa descartada: manter `_chosen` em Python e montar o SQL a partir da mesma tupla — motivo: continuariam dois avaliadores da regra (Python e SQL), e a divergência que a dívida quer evitar migraria para a tradução entre eles. Norma 33: agregação e junção ficam em `app/queries`.

### D2 — `display_name` lê `RESOLVED_PAYEES`; `_chosen` e `_FROM_PLUGGY` saem

`app/payees/names.py::display_name` executa `RESOLVED_PAYEES` e devolve `{payee: {"name": name or payee, "source": source}}`, o mesmo formato de hoje. `labels` e `ranked` não mudam. As constantes de origem continuam importáveis de `app.payees.names` (reexportação explícita, `mypy --strict`).

### D3 — A lista de gastos junta `RESOLVED_PAYEES` e lê dela o nome e a busca

Em `app/queries/expenses.py`, `_FROM` troca os dois `LEFT JOIN payee_names` por `LEFT JOIN (RESOLVED_PAYEES) AS pn ON pn.payee = t.payee`; `_SELECT` passa a trazer `pn.name AS payee_name`; a busca usa `fold(pn.name)`. `_PAYEE_NAME_SQL` e a chamada a `labels()` saem. `pn.payee` é único (agrupado), então a junção não multiplica linhas e `_TOTAL`/`_BY_CATEGORY` seguem certos. Com `t.payee` nulo não há junção, e o nome é `NULL` como hoje.

- Efeito combinado: a busca passa a olhar o nome **do recebedor** (agregado), não o da linha — é o nome que a lista mostra (R2). Hoje nenhum `payee` carrega dois valores no mesmo nível, então nenhum resultado muda na base atual.

## Arquivos afetados

| Ação | Arquivo | O quê | Skills |
|---|---|---|---|
| alterar | `app/queries/payees.py` | constantes de origem, tupla de precedência e `RESOLVED_PAYEES` | python-tipagem-estrita |
| alterar | `app/payees/names.py` | `display_name` sobre `RESOLVED_PAYEES`; remove `_chosen` e `_FROM_PLUGGY`; reexporta as origens | python-tipagem-estrita |
| alterar | `app/queries/expenses.py` | junção com `RESOLVED_PAYEES`, `payee_name` e busca por `pn.name`; remove `_PAYEE_NAME_SQL` e `labels()` | python-tipagem-estrita |
| alterar | `tests/test_payee_names.py`, `tests/test_expenses_api.py` | casos que provam uma regra só | python-testes-de-integracao-httpx |

## Riscos

- A subconsulta agrega `transactions` inteira a cada página. A base é de um usuário (milhares de linhas); a suíte e o e2e medem o tempo.
