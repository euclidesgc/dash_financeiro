VEREDICTO: APROVADO

Nada de plano, brief, spec ou histórico chegou até mim. O arquivo de despacho trazia só o objetivo e os critérios, como prometido, e não abri `product/items/023-taxonomia-hierarquica-do-dono/`.

## Portões

| Portão | Resultado |
|---|---|
| pytest | **OK** — `566 passed, 2 warnings in 44.39s`, exit `0` (capturado em arquivo, não pelo `tail`). Não é o caso de exit `5`: 566 testes coletados e executados. |
| lint (`scripts/lint.sh`) | **OK** — `All checks passed!` / `143 files already formatted`, exit `0`. |
| gates (`gates_runner.sh`) | **OK** — `✓ gates: limpos (árvore completa, 509 arquivo(s) considerados).`, exit `0`. **509 > 0**, então mediu de fato. |
| mypy | **Não se aplica nesta stack** — `.venv/bin/mypy` não existe, `mypy` não aparece em `pyproject.toml` nem em `.github/workflows/`, e não há `src/`. Registro como não aplicável, não como aprovado sem medir. |

Árvore limpa; o objeto julgado é o commit único `f9cbb6d`. Atenção: `git diff develop..HEAD` engana aqui, porque `develop` andou à frente. A comparação certa é contra o merge-base `1bc7710`.

## Critérios de aceite da fase

| # | Critério | Veredicto | Evidência |
|---|---|---|---|
| 1 | `estrutural` RF-01 — migração 012, 11→12 arquivos, pragmas | **cumprido** | `git diff --name-status 1bc7710..HEAD -- app/migrations/sql/` traz só `A 012_taxonomy_tree.sql`; nenhum `M`. Em banco vazio temporário: `migrations applied: 12`; `pragma_table_info` devolve `('id',0) ('name',1) ('group_id',1)`; `pragma_foreign_key_list` devolve uma linha `('category_groups','group_id','id')`. |
| 2 | `comando` RF-02 — semente lida + ausência da lista paralela | **cumprido** | (a) imprime exatamente `77 False`. (b) primeiro grep: nenhuma linha (exit 1); segundo grep: os cinco arquivos esperados. **Confirmei que a exclusão é honesta**: rodei o mesmo grep *sem* `--exclude` e a única ocorrência em toda a árvore é `tests/data/vocabulario_anterior.json:651`, arquivo que veio da fase 1, não é tocado por esta fase e é referenciado só por `tests/test_taxonomy_remap.py`. |
| 3 | `estrutural` RF-01, RF-02 — `seed.json` e `LABELS` | **cumprido** | 77 entradas; histograma de campos `{('group','label','name'): 77}`; 77 nomes distintos; zero `group` fora dos 12. `seed.py:19 def category_labels()`; `spending.py:40` e `rules.py:25` com `LABELS: dict[str,str] = category_labels()`. |
| 4 | `comportamental` RF-01, RF-05 — 77 / 0 / 76 / nenhuma | **cumprido** | Banco temporário migrado + `seed_taxonomy`: `77`, `0`, `76`, `[]`. Controle positivo `76` confirmado. Cláusula da mensagem de falha: conduzi a própria função de teste com duas discordâncias plantadas por fora do repositório e a falha nomeia as duas. |
| 5 | `comportamental` RF-08 — categoria inventada | **cumprido** | `classify_all` não levantou, `changed=1`; `count(categories)` 77→**78**; linha com `group_id` = id do grupo de escape; lançamento com `rule_id=None`. |
| 6 | `comportamental` RF-01 — semente corrige rebaixamento à mão | **cumprido** | Depois do `UPDATE` à mão, grupo de escape; depois do segundo `seed_taxonomy`, o grupo certo. |
| 7 | `comportamental` RF-02 — rótulo da árvore em `/gastos/tabela` | **cumprido** | `GET /gastos/tabela?eixo=categoria` responde **200**; no recorte da linha: `<span class="cell-label">Financiamento imobiliário</span><span class="cell-key">Real estate financing</span>`, com a cifra `−R$ 1.234,56`. |
| 8 | `comando` — pytest dos seis arquivos, sem portão novo | **cumprido** | `75 passed`, exit **0**. `git diff --name-status 1bc7710..HEAD -- scripts/` **vazio**: nenhum gate novo. |

## Critérios de integração

| # | Critério | Veredicto | Evidência |
|---|---|---|---|
| I1 | `comportamental` RF-06, RF-07 — os quatro números | **cumprido** | Montei os dois bancos eu mesmo. `depois`: `count(categories)=78`; lançamentos na janela `77 > 0`. Total e contagem idênticos; ambas as travessias idênticas. **Ressalva medida abaixo: `corte` compara zero com zero como o critério está escrito.** |
| I2 | `comportamental` RF-01, RF-04, RF-05 — semente sobre o vocabulário anterior | **cumprido** | Estado anterior com **10 / 6 / 7 / 10** categorias apontando para os quatro grupos aposentados. `seed_taxonomy` não levantou nenhuma `FOREIGN KEY constraint failed`. Depois: 12 grupos, 77 categorias, órfãs `0`, e `Same person transfer` aponta para `Não é gasto`. |
| I3 | `comportamental` RF-03 — a tela só com as migrações | **cumprido** | Sem semear e sem classificar, `GET /gastos/tabela?eixo=grupo` responde **200** com os três grupos antigos e **nenhum** dos seis novos. |

## A minha própria medição: nenhum número se moveu

Base construída por mim, idêntica nos dois bancos: **80 lançamentos** cada lado — 76 de gasto, um por regra do vocabulário anterior, com valores distintos e datas em dois meses; mais um com categoria inventada; mais transferência, estorno e positivo.

| Medida | antes | depois | Igual dígito a dígito |
|---|---|---|---|
| `total_spending_cents` | **−787727** | **−787727** | sim |
| lançamentos que satisfazem `SPENDING` | **77** | **77** | sim |
| `corte`, *sem plantar* | 0 / 0 / 0 linhas | 0 / 0 / 0 linhas | sim, **mas vácuo** |
| `corte`, **plantado nos dois lados** | **−20007** / −10004 / 2 linhas | **−20007** / −10004 / 2 linhas | sim |
| `piso` | **−123563** / −61782 / 12 linhas | **−123563** / −61782 / 12 linhas | sim |

**Natureza e essencialidade:** 80 linhas comparadas, todas iguais, zero divergências.

**Norma 25:** transferência, estorno e positivo ficam fora do gasto nos dois bancos.

**A carga não quebra por vocabulário:** categoria com acento, com aspas duplas, simples e crase, e duas de injeção SQL — todas registradas com o grupo de escape e classificadas. A tabela sobreviveu intacta às injeções. Categoria vazia e ausente não geram linha, mas o lançamento é classificado no escape. **Zero lançamentos sem grupo, natureza ou essencialidade.**

**Órfãs:** `0` em todos os cenários. **Controle negativo:** plantei uma órfã com `PRAGMA foreign_keys = OFF` e a consulta devolveu **1**, voltando a `0` ao removê-la — a medição não é vácuo. E a chave estrangeira é cobrada de verdade na conexão da aplicação.

## Achados que não reprovam

1. **A travessia `corte` do critério de integração I1 não prova nada como está escrita.** Nenhum dos dois vocabulários declara regra de categoria no par `variável × supérfluo`. Construída só com as 76 regras, aquela travessia compara `0` com `0`. Só marquei o critério como cumprido porque plantei o par eu mesmo, nos dois lados — que é exatamente como o dono marca supérfluo na tela. A mesma fraqueza está em `test_the_four_numbers_agree_with_all_migrations_applied_and_the_tree_seeded`, em `tests/test_taxonomy_integration.py:41`: ele guarda a regressão de `piso`, não a de `corte`.
2. **Dois dos quatro números não podem se mover, por construção.** `SPENDING` não lê nenhuma coluna de taxonomia. Quem carrega a prova de neutralidade são as duas travessias e a comparação de natureza e essencialidade lançamento a lançamento.
3. **A lista de discordâncias sai truncada no modo que o próprio critério 8 usa.** Sob `-q`, pytest trunca; a enumeração completa só aparece com `-v`.
4. **`012_taxonomy_tree.sql` descarta o conteúdo anterior da tabela `categories` na subida**, em vez de migrá-lo. É recuperável — `classify_all` re-registra as categorias observadas e `seed_taxonomy` re-semeia as 77, e provei que a recuperação funciona —, mas é uma migração sem volta.

## Instrumentos do implementer

Reproduzi por conta própria, com base montada por mim e fora do repositório, **todos os oito critérios da fase e os três de integração**. A suíte do avaliado foi load-bearing em dois pontos, ambos inevitáveis: o critério 8, que é literalmente "este comando sai com código 0", e a cláusula da mensagem de falha do critério 4 — cujo cenário de falha foi injetado por mim.
