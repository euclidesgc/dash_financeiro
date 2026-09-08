VEREDICTO: CRITERIO_INVALIDO

Nada falhou. Um único critério — o RF-02(b), primeira busca — afirma um fato que a árvore do repositório contradiz por motivo legítimo, e é ele que impede o `APROVADO`.

**Recebi só o objetivo e os critérios.** Nenhum plano, brief, spec ou histórico veio no despacho. Uma ressalva de honestidade: um `grep -rn` meu usou o caminho `docs/../`, que expandiu para a raiz e imprimiu ~10 linhas de `product/items/023-taxonomia-hierarquica-do-dono/03-plan.md` e `.../05-veredictos/fase-1.md`. Foi acidente de caminho, não busca deliberada; não li mais nada dali e nenhuma conclusão minha se apoia nesse texto.

## Portões

| Portão | Resultado |
|---|---|
| ruff check | **OK** — `All checks passed!` |
| ruff format --check | **OK** — `143 files already formatted` |
| mypy --strict | **NÃO APLICÁVEL, e não conto como passe** — não existe `src/`, `mypy` não está no `.venv` nem em `pyproject.toml`. Registro como lacuna conhecida do projeto, não como medição feita |
| pytest | **OK** — `566 passed, 2 warnings in 39.82s`, exit `0`. 566 testes coletados, não zero |
| gates_runner.sh | **OK** — `✓ gates: limpos (árvore completa, 509 arquivo(s) considerados).` — **509 > 0**, medição real |

## Critérios da fase

| # | Tipo | Veredicto | Evidência executada |
|---|---|---|---|
| 1 | estrutural RF-01 | **cumprido** | Merge-base tem 11 `.sql`; HEAD tem 12. O diff traz só `A app/migrations/sql/012_taxonomy_tree.sql`. `pragma_table_info('categories')` devolve `[('id',0),('name',1),('group_id',1)]`; `pragma_foreign_key_list('categories')` devolve `[('category_groups','group_id','id')]` |
| 2a | comando RF-02 | **cumprido** | Imprime exatamente `77 False`, exit 0 |
| 2b | comando RF-02 | **CRITERIO_INVALIDO** (1ª busca) / **cumprido** (2ª busca) | Ver abaixo |
| 3 | estrutural RF-01/02 | **cumprido** | `len(categories)=77`; todas com exatamente `{name,label,group}`; 77 `name` distintos; nenhum `group` fora dos 12. `LABELS: dict[str,str] = category_labels()` nos dois routers |
| 4 | comportamental RF-01/05 | **cumprido** | `count(categories)=77`; órfãs `=0`; pares regra×categoria `=76` (controle positivo); discordâncias `=[]` |
| 5 | comportamental RF-08 | **cumprido** | `classify_all` sem exceção; `count(categories)=78`; categoria inventada com `group_id` do escape; lançamento com `rule_id=None` |
| 6 | comportamental RF-01 | **cumprido** | Categoria rebaixada à mão volta ao grupo certo na semeadura seguinte |
| 7 | comportamental RF-02 | **cumprido** | `GET /gastos/tabela?eixo=categoria` responde **200**, com `cell-label` e `cell-key` juntos na mesma linha |
| 8 | comando (8 RFs) | **cumprido** | Os seis arquivos: `75 passed`, exit `0`. `git diff develop...HEAD -- scripts/` **vazio** |

## Critérios de integração

| # | Tipo | Veredicto | Evidência executada (banco montado por mim, sem os helpers do avaliado) |
|---|---|---|---|
| I-1 | comportamental RF-06/07 | **cumprido** | Ver "os quatro números" abaixo |
| I-2 | comportamental RF-01/04/05 | **cumprido** | Vocabulário anterior por inserção direta, os quatro grupos aposentados cobertos, `PRAGMA foreign_keys=1`. `seed_taxonomy` sem exceção; órfãs `=0`; `foreign_key_check` vazio |
| I-3 | comportamental RF-03 | **cumprido** | Só migrações: as quatro tabelas de vocabulário vazias. Com o vocabulário anterior instalado e sem semear, `GET /gastos/tabela?eixo=grupo` responde **200** mostrando os três grupos antigos, e a interseção com os grupos novos é **vazia** |

## O critério que não é verificável como está escrito

**RF-02(b), primeira busca:** "não imprime nenhuma linha". Ela imprime uma: `tests/data/vocabulario_anterior.json:651`.

Não é reprovação, por três razões que medi:

1. **A premissa factual do critério já era falsa quando a fase começou.** O critério diz que "hoje" a busca imprime quatro linhas. Rodei `git grep` nas revisões: essa lista bate **exatamente**, número de linha por número de linha, com a árvore **anterior à fase 1**. No merge-base desta fase a mesma busca já imprimia **cinco** linhas.
2. **O arquivo que sobra é exigido por este mesmo documento.** `tests/data/vocabulario_anterior.json` é a cópia congelada do `seed.json` pré-023 criada pela fase 1 — daí a linha 651 idêntica. Os três critérios de integração o nomeiam e dependem dele. Apagar `"category_labels"` dele para satisfazer o grep seria adulterar a prova de que os outros critérios dependem.
3. **O alvo substantivo do critério está cumprido, e verifiquei separadamente.** Em `app/` são zero ocorrências; em qualquer `tests/*.py` são zero. A única sobra é dado de teste congelado, que não é a semente e não é lido como semente.

A segunda busca de (b) passa por inteiro.

## Minha própria medição — os quatro números

**Tamanho da base:** 80 lançamentos por banco, **77 contados como gasto na janela** — não é comparação de zero com zero.

| Medida | antes | depois | idênticos |
|---|---|---|---|
| `total_spending_cents` | `-127549` | `-127549` | **sim** |
| lançamentos que satisfazem `SPENDING` | `77` | `77` | **sim** (e > 0) |
| `corte` — total / média / linhas | `-2001` / `-2001` / 10 | idem | **sim, elemento a elemento** |
| `piso` — total / média / linhas | `-4756` / `-4756` / 12 | idem | **sim, elemento a elemento** |
| natureza e essencialidade por lançamento | 80 comparados | 80 comparados | **0 divergentes** |

**Achado de método que corrigi, e que vale registrar:** na primeira rodada o cruzamento `corte` deu zero contra zero — aprovação sem medição. A causa não é o código: **nenhum dos dois vocabulários declara uma única regra `variável × supérfluo`**. Só o dono marca supérfluo, editando regra na tela. Refiz o probe marcando 10 categorias nesse par nos dois bancos, e só então o cruzamento passou a ter conteúdo para comparar.

**Norma 25:** transferência, estorno e positivo não contam como gasto em nenhum dos dois bancos.

**A carga não quebra por vocabulário.** 12 categorias hostis pela ingestão real: acento, aspas duplas e simples, injeção SQL, emoji, 300 caracteres, barra e contrabarra, quebra de linha — todas registradas e nascidas no grupo de escape. Vazia, nula e ausente do payload: carregadas e classificadas no escape. A tabela continua de pé depois da injeção; `foreign_key_check` vazio.

**Nenhuma categoria órfã, em nenhum caminho.** Onze medições em três caminhos, **órfãs = 0 em todas**. **Controle negativo:** `group_id=9999` é recusado com `FOREIGN KEY constraint failed`, e `NULL` com `NOT NULL constraint failed`.

## Achados que não reprovam

1. **`develop` andou e agora tem `013`, `014` e `015`, mas nenhum `012`.** Simulei o merge: funciona, esquema correto, `foreign_key_check` vazio. Nenhuma das outras toca `categories`. É seguro; vale só saber que o número saiu do lugar.
2. **O `012` derruba e recria a tabela `categories`, e na base do dono isso apaga as categorias já registradas.** É dado derivado, que a `classify_all` seguinte repõe — mas quem só rodar as migrações e abrir o painel vê a tabela vazia até classificar.
3. **`tests/test_classify.py::test_the_observed_categories_are_recorded` afrouxou de `==` para `<=`.** A mudança é justificada, mas o teste deixou de provar que *nada além* do observado foi registrado. Sugestão: assertar o conjunto observado contra `names - {as 77 da semente}`.
4. **`seed_taxonomy` sozinha não deixa o banco coerente**: rodá-la isolada exige a classificação na sequência.
5. Norma 24 confirmada nas rotas exercitadas.

## Instrumentos do implementer

Só o critério 8, que é por construção a execução da suíte do avaliado, e a leitura de uma mensagem de falha no critério 4 — cuja saída provei com probe meu. Todo o resto foi verificado em bancos que montei eu, sem os helpers do avaliado.
