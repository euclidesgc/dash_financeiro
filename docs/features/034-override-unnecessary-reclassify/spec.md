# SPEC 034 — override-unnecessary-reclassify

## Contexto

- `app/taxonomy/override.py::_write` executa a escrita, chama `classify.classify_all` e confirma a transação; os cinco escritores do módulo passam por ela.
- `classify_all` lê de `transactions` só `payee`, `category`, `category_source`, `rule_id`, `group_id`, `nature` e `essentiality` (além das tabelas de regras e do catálogo). `not_expense_reason` não entra na decisão.
- `set_not_expense` e `clear_not_expense` escrevem só `not_expense_reason`.

## Decisões

### D1 — `_write` recebe `reclassify` obrigatório por nome

`_write(conn, statement, params, *, reclassify: bool)`: com `True`, reclassifica dentro da mesma transação, como hoje; com `False`, só escreve e confirma. `set_manual`, `restore_auto` e `apply_to_similar` passam `True`; `set_not_expense` e `clear_not_expense`, `False`.

- Alternativa descartada: duas funções (`_write` e `_write_and_reclassify`) — motivo: duplicaria o bloco de rollback e commit, que é o invariante que a função guarda.
- Alternativa descartada: padrão `reclassify=True` — motivo: o próximo escritor decidiria sem perceber; o argumento obrigatório força a pergunta.

### D2 — A prova é pelo estado, sem dublê

O teste deixa um lançamento com a classificação desatualizada de propósito (grupo trocado à mão) e confere que marcar e desmarcar como "não é gasto" não o corrigem, enquanto `set_manual` corrige.

- Alternativa descartada: substituir `classify_all` por um dublê que conta chamadas — motivo: amarra o teste à implementação; o estado mostra o efeito que importa.

## Arquivos afetados

| Ação | Arquivo | O quê | Skills |
|---|---|---|---|
| alterar | `app/taxonomy/override.py` | `_write` com `reclassify` por nome; chamadores passam o valor | python-service-layer, python-tipagem-estrita |
| alterar | `tests/test_override.py` | o teste de marcação deixa de afirmar reclassificação; testes novos provam R1 e R2 pelo estado | python-testes-unitarios |

## Riscos

- Nenhum de comportamento: a coluna escrita não entra na classificação; os testes de API e de tela existentes provam que a resposta não muda.
