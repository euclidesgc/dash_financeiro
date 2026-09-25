# SPEC 017 — jinja-router-extraction

Dívida técnica, sem interface nova. Cinco routers das telas Jinja montam SQL e executam com `conn.execute` dentro do próprio arquivo: `app/routers/spending.py` (cruzamentos, candidatos, alvo da correção, grupos, naturezas, essencialidades, nome do grupo), `app/routers/rules.py` (lista de regras, regra por id, id por casamento, alcance, resíduo, candidatos, amostras, e de novo grupos, naturezas e essencialidades), `app/routers/summary.py` (base vazia), `app/routers/settings.py` (recebedor conhecido, CNPJ do recebedor) e `app/routers/commitments.py` (`conn.commit()` depois de `dismiss`/`resume`). Isso fere as normas 30 (router traduz HTTP, não monta consulta nem dá commit) e 33 (junção e agregação em `app/queries`), e o portão G7 (`scripts/gates/gate7_layer_boundary.sh`) não vê, porque só procura construções do SQLAlchemy.

O que o código já faz e esta SPEC reaproveita:

- `app/queries/*` · módulos de consulta com funções `(conn, ...) -> sqlite3.Row | list | int`, `__all__` explícito (`reach.py`, `crossings.py`, `categories.py`).
- `app/queries/spending.py` · `SPENDING` e `date_window(start, end)`, a janela opcional de datas.
- `app/taxonomy/*`, `app/settings/store.py` · o serviço que grava dá o próprio `commit` (`rules.py`, `override.py`, `catalogue.py`).

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | Cada SQL sai do router com o mesmo texto para uma função de consulta; os testes de tela existentes (`tests/test_*_screen.py`) seguem verdes sem alteração (D1). |
| R2 | Grupos, naturezas, essencialidades, nome do grupo e essencialidade de reserva em `app/queries/vocabulary.py`, usados pelas duas telas (D2). |
| R3 | `residue` sai de `app/taxonomy/classify.py` para `app/queries/rules.py` com janela opcional; a tela de regras chama sem janela, a de gastos com o período (D3). |
| R4 | `dismiss` e `resume` (`app/commitments/mark.py`) dão o próprio `commit`; o router não commita (D4). |
| R5 | G7 passa a recusar `.execute(`, `.executemany(`, `.executescript(`, `.commit(`, `.rollback(` e texto SQL em router; `scripts/gates/__tests__/gate7.test.sh` prova, e roda no CI (D5). |

## Decisões técnicas

### D1 — Uma função de consulta por pergunta, no módulo do assunto

- Escolha: `app/queries/rules.py` (lista, regra, id por casamento, `held_by_rule`, `rules_carrying`, `residue`, `rule_candidates`, `payee_samples`); `app/queries/vocabulary.py`; `app/queries/payees.py` (`payee_known`, `payee_cnpj`); `app/queries/transactions.py` (`base_is_empty`); `crossing_definitions` e `candidates` em `app/queries/crossings.py`; `correction_target` em `app/queries/reach.py`.
- `candidates` reusa o `_ROWS` de `crossing` com `LIMIT`: o bloco de candidatos e o cruzamento leem a mesma consulta; o desempate por chave passa a valer também nos candidatos.
- `held_by_rule` (toda linha segura pela regra) fica separada de `rule_reach` (só gasto): a tela de regras avisa "não alcançou nenhum lançamento" contando qualquer lançamento, e isso não muda.
- Alternativa descartada: serviço por tela (`app/<domínio>/service.py`) entre router e consulta — motivo: as telas só leem; uma camada que repassa argumentos não decide nada.

### D2 — Vocabulário da taxonomia num lugar só

- Escolha: `groups`, `group_name`, `natures`, `terms`, `fallback_term` em `app/queries/vocabulary.py`; `fallback_term` devolve o texto, não a linha.
- Motivo: as duas telas tinham as mesmas três consultas copiadas; a tela React de categorias vai precisar das mesmas.

### D3 — Resíduo com janela opcional

- Escolha: `residue(conn, *, start=None, end=None)` com `date_window`; sai de `classify.py`, que volta a só classificar.
- Alternativa descartada: duas funções (base inteira e período) — motivo: é a duplicação que o item existe para tirar.

### D4 — Quem grava, commita

- Escolha: `conn.commit()` no fim de `dismiss` e `resume`, como os outros serviços que gravam.

### D5 — G7 cobre o driver sqlite3

- Escolha: o padrão de G7 ganha `\.(execute|executemany|executescript|commit|rollback)\(` e string que começa com `SELECT`, `INSERT`, `UPDATE`, `DELETE` ou `WITH` seguidos de espaço. A marca `# gate7-ok` continua perdoando a linha.
- Prova pela reprovação: contra os cinco routers de `develop`, o portão novo acusa 45 linhas; contra os routers desta branch, zero. O teste do portão, rodado contra o G7 antigo, falha em 3 casos.

## Contrato

Sem mudança de API nem de OpenAPI.

## Interface

Sem interface nova.

## Arquivos

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `app/queries/rules.py` | consultas da tela de regras e resíduo (D1, D3) | `python-tipagem-estrita` |
| criar | `app/queries/vocabulary.py` | vocabulário da taxonomia (D2) | `python-tipagem-estrita` |
| criar | `app/queries/payees.py` | recebedor conhecido e CNPJ (D1) | — |
| criar | `app/queries/transactions.py` | base vazia (D1) | — |
| alterar | `app/queries/crossings.py` | `crossing_definitions`, `candidates` (D1) | — |
| alterar | `app/queries/reach.py` | `correction_target` (D1) | — |
| alterar | `app/taxonomy/classify.py` | sai `residue` (D3) | — |
| alterar | `app/commitments/mark.py` | `commit` em `dismiss`/`resume` (D4) | `python-unit-of-work` |
| alterar | `app/routers/{spending,rules,summary,settings,commitments}.py` | sem SQL, sem `execute`, sem `commit` | — |
| alterar | `scripts/gates/gate7_layer_boundary.sh` | padrão do driver sqlite3 (D5) | — |
| criar | `scripts/gates/__tests__/gate7.test.sh` | prova do portão (D5) | — |
| alterar | `.github/workflows/harness.yml` | roda o teste do G7 | — |
| criar | `tests/test_screen_queries.py` | funções novas e durabilidade de `dismiss`/`resume` | `python-testes-unitarios` |
| alterar | `tests/test_classify.py`, `tests/test_override.py` | import de `residue`; resíduo sem janela | `python-testes-unitarios` |

## Estimativa de tamanho

Jornadas: 0 novas · Telas novas: 0 · Linhas (sem testes): ~200 movidas · Fases previstas: 1.

## Dívida encontrada

- nenhuma
