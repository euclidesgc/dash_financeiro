# SPEC 028 — manual-category-classify-precedence

Dívida técnica, sem interface nova. A classificação de agrupamento (`app/taxonomy/classify.py::classify_all`) escreve `rule_id`, `group_id`, `nature` e `essentiality` de cada lançamento. `_match` tenta primeiro as regras por descrição (regex sobre `payee`) e só depois a regra por categoria (`category_rules.match_kind = 'category'`). Desde a 009 existe `transactions.category_source` (`'auto' | 'manual'`), mas `_match` não o lê: um lançamento ajustado à mão cujo recebedor casa com uma regra por descrição fica no grupo da regra, não no da categoria escolhida. As telas Jinja (`app/routers/spending.py`, `app/routers/rules.py`, `app/queries/axes.py`) agrupam por `group_id`, `nature` e `essentiality`, então divergem da lista React, que agrupa por `category`.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/taxonomy/override.py` · `set_manual`, `apply_to_similar` e `restore_auto` escrevem `category`/`category_source` e chamam `classify_all` na mesma transação.
- `app/ingest/loader.py` · a ingestão preserva `category` quando `category_source = 'manual'` e nunca escreve `category_source`; `app/sync/__init__.py::_after` roda `classify_all` depois da carga.
- `app/queries/reach.py` · `payee_reach` (prévia da correção por recebedor), `holders` (regra que já segura o recebedor) e `rule_reach` (alcance medido depois da escrita) compartilham o molde `_REACH`.
- `app/routers/spending.py::_result_context` · se `result.entries == 0` e a prévia é maior que zero, pega `holders(...)[0]` para explicar quem segurou o recebedor.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `_match` devolve `categories.get(category)` sem olhar regras por descrição quando `category_source = 'manual'` (D1). |
| R2 | Manual sem regra de categoria (inclusive `category IS NULL`) → `_match` devolve `None` → `classify_all` usa o fallback (D1). |
| R3 | `restore_auto` grava `category_source = 'auto'` e chama `classify_all`, que volta ao caminho de hoje (D1). |
| R4 | O ramo `auto` de `_match` não muda (D1). |
| R5 | `payee_reach` e `holders` passam a considerar só `category_source = 'auto'` (D2). |
| R6 | A ingestão não toca `category_source`; `_after` reclassifica com a mesma regra (D1). Teste de sincronização prova. |

## Decisões técnicas

### D1 — Linha manual se classifica só pela regra da categoria escolhida

- Escolha: `classify_all` passa a ler `category_source`; em `_match`, `if row["category_source"] == MANUAL: return categories.get(row["category"])`. Constante `MANUAL = "manual"` em `classify.py`.
- Alternativa descartada: manual cai nas regras por descrição quando a categoria escolhida não tem regra — motivo: é exatamente o sintoma (a regra por descrição decide no lugar do dono); "Sem categoria" manual seria reclassificado por descrição.
- Alternativa descartada: usar `categories.group_id` para a linha manual — motivo: natureza e essencialidade só existem em `category_rules`; `group_id` e o par natureza/essencialidade viriam de fontes diferentes.
- Alternativa descartada: pular a linha manual em `classify_all` (manter o que estava) — motivo: o `group_id` gravado antes do ajuste é o da regra por descrição; ficaria preso nele.

### D2 — A prévia da correção por recebedor conta só o que a correção move

- Escolha: `_REACH` recebe o filtro já com `category_source = 'auto'` em `payee_reach`; `_HOLDERS` ganha `AND t.category_source = 'auto'`. `category_reach` e `rule_reach` não mudam (a primeira mede a categoria de origem, a segunda o que a regra segura depois da escrita).
- Motivo: com D1, uma linha manual do recebedor não é movida pela regra nova; sem D2 a prévia prometeria N e o resultado entregaria menos (RF-02), e, quando todas as linhas do recebedor fossem manuais sem regra de categoria, `holders(...)[0]` levantaria `IndexError` na tela.
- Alternativa descartada: manter a prévia total e explicar os manuais na mensagem — motivo: tela Jinja antiga, sem receita de texto para isso; a prévia exata dispensa a explicação.

## Contrato

Sem mudança de API nem de OpenAPI.

## Interface

Sem interface nova. As telas Jinja mudam só os números que mostram.

## Arquivos

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/taxonomy/classify.py` | `MANUAL`; `SELECT` com `category_source`; ramo manual em `_match` (D1) | `python-tipagem-estrita` |
| alterar | `app/queries/reach.py` | filtro `category_source = 'auto'` em `payee_reach` e `_HOLDERS` (D2) | — |
| alterar | `tests/test_classify.py` | casos de R1, R2, R3, R4 | `python-testes-unitarios` |
| alterar | `tests/test_reach.py` | caso de R5 (prévia e holders sem manuais) | `python-testes-unitarios` |
| alterar | `tests/test_corrections.py` | correção de recebedor com linha manual: resultado bate com a prévia | `python-testes-unitarios` |
| alterar | `tests/test_override.py` | `set_manual` sobre recebedor com regra por descrição vai para o grupo da categoria; sincronização mantém (R6) | `python-testes-unitarios` |

## Estimativa de tamanho

Jornadas: 0 novas · Telas novas: 0 · Linhas (sem testes): ~10 · Fases previstas: 1.

## Dívida encontrada

- nenhuma
