# SPEC 029 — jinja-labels-from-schema

Dívida técnica, sem interface nova. Desde a 023 o rótulo em pt-BR de cada categoria mora na coluna `categories.label`, e desde a 010 o dono renomeia e cria categorias pela tela React. As duas telas Jinja que mostram categoria ainda montam o mapa de rótulos do arquivo de seed, uma vez, no import do módulo: `app/routers/spending.py` e `app/routers/rules.py` têm `LABELS: dict[str, str] = seed_labels()`. Rótulo renomeado e categoria criada não chegam a elas.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/queries/categories.py` · consultas sobre `categories` (`list_categories`, `get_category`).
- `app/templates/fragments/celula.html` · `cell_name(key, labels)` mostra o rótulo e, se diferir, a chave; sem rótulo, a chave uma vez (R4).
- `app/routers/spending.py::_table_context` · no eixo recebedor, sobrepõe o mapa com `payee_labels(conn)`.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `_base` e `_panel_context` de `spending.py` recebem `category_labels(conn)` a cada requisição (D1). |
| R2 | `_context` de `rules.py` usa `category_labels(conn)` a cada requisição (D1). |
| R3 | `category_labels` lê todas as linhas de `categories`, inclusive as criadas pelo dono (D1). |
| R4 | Chave sem linha em `categories` fica fora do mapa; `cell_name` segue mostrando a chave. |

## Decisões técnicas

### D1 — Uma consulta `category_labels(conn)` lida em requisição

- Escolha: `category_labels(conn) -> dict[str, str]` em `app/queries/categories.py` (`SELECT name, label FROM categories`); as duas constantes `LABELS` saem, e `_base` passa a receber `conn`.
- Motivo: norma 33 (consulta mora em `app/queries`); uma tabela pequena, uma leitura por tela.
- Alternativa descartada: cache invalidado ao renomear — motivo: estado a mais para uma consulta de dezenas de linhas.
- Alternativa descartada: reusar `list_categories` — motivo: exclui "Não classificado" e faz junção com `transactions` para contar uso, que as telas não precisam.

`seed_labels()` continua existindo: os testes do seed e da migração 020 comparam contra ele.

## Contrato

Sem mudança de API nem de OpenAPI.

## Interface

Sem interface nova. As telas Jinja mudam só os nomes que mostram.

## Arquivos

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/queries/categories.py` | `category_labels(conn)` (D1) | `python-tipagem-estrita` |
| alterar | `app/routers/spending.py` | sem `LABELS`; `_base(conn, …)` e `_panel_context` leem `category_labels` | — |
| alterar | `app/routers/rules.py` | sem `LABELS`; `_context` lê `category_labels` | — |
| alterar | `tests/test_taxonomy_tree.py` | sem as asserções sobre `LABELS` dos routers | — |
| alterar | `tests/test_gastos_screen.py` | rótulo lido de `categories`; casos de R1, R3 | `python-testes-de-integracao-httpx` |
| alterar | `tests/test_regras_screen.py` | casos de R2, R3 | `python-testes-de-integracao-httpx` |
| alterar | `tests/test_categories_api.py` | caso de `category_labels` | `python-testes-unitarios` |

## Estimativa de tamanho

Jornadas: 0 novas · Telas novas: 0 · Linhas (sem testes): ~15 · Fases previstas: 1.

## Dívida encontrada

- nenhuma
