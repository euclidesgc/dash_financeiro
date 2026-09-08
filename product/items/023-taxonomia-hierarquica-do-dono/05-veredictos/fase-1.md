VEREDICTO: APROVADO

O despacho me entregou só o objetivo e os critérios. Plano, brief, spec e histórico não vieram, e não abri `product/items/023-taxonomia-hierarquica-do-dono/`. Tudo abaixo é execução em base montada por mim, dentro de `/home/euclidesgc/development/.dash_wt/023`, árvore limpa, `HEAD` = `2744ec1`.

## Portões

| portão | resultado | saída |
|---|---|---|
| ruff check | OK | `All checks passed!` |
| ruff format --check | OK | `139 files already formatted` |
| mypy --strict | não se aplica | não instalado no `.venv`, sem seção em `pyproject.toml`, não existe `src/`. A norma 35 do projeto define o portão de lint como `scripts/lint.sh` (ruff check + ruff format) e declara `mypy --strict` item de roadmap. Registro como fora da DoD deste projeto, não como passe silencioso. |
| pytest | OK | `538 passed, 2 warnings in 40.37s`, código `0` — coletou 538, não é o caso do código 5 com zero testes |
| gates | OK | `✓ gates: limpos (árvore completa, 502 arquivo(s) considerados)`, código `0` — 502 > 0, mediu |

## Critérios de aceite

| # | tipo | passou | evidência executada |
|---|---|---|---|
| 1 | estrutural | sim | `app/taxonomy/seed.json`: `len(groups) = 12`; por `position` crescente os nomes saem `['Moradia','Transporte','Alimentação','Saúde','Educação','Assinaturas','Pessoal','Financeiro','Dependentes','Renda','Não é gasto','Outros']`; `sorted(positions) == list(range(1,13))` → `True`; `is_fallback` verdadeiro só em `['Outros']` |
| 2 | comportamental | sim | Banco temporário, `run_migrations`, 87 lançamentos carregados por `app.ingest.loader.ingest`, semeado por inserção direta minha a partir do vocabulário anterior, `classify_all`. Depois `seed_taxonomy(conn)`: sem exceção. `count(category_groups)=12`; nomes por `position` na ordem exigida (`True`); `count(category_rules)=80`; `count(tx WHERE rule_id IS NOT NULL)=83` (controle positivo); regras órfãs `=0`; após a 1ª `classify_all` (mudou 14) o `t.group_id != r.group_id` dá `0`; 2ª `classify_all` devolve `0`. `PRAGMA foreign_key_check` vazio |
| 3 | comportamental | sim | Regra do dono criada por `create_rule` (`category`/`Categoria do dono`, grupo `Transferências` id=9, `fixa`/`essencial`), lançamento pego por ela. Após `seed_taxonomy`: regra id 81 continua existindo, `('category','Categoria do dono','fixa','essencial')` preservados; `group_id` = 10 = id do `is_fallback=1` (`Outros`); o lançamento fica com `group_id`=10; `classify_all` devolve `0`; `foreign_key_check` vazio |
| 4 | comportamental | sim | As duas listas `rules` têm 80 entradas; a sequência de `(match_kind, match_value, nature, essentiality)` é igual elemento a elemento (`True`); os grupos usados pelas 80 regras novas ficam todos dentro dos doze (conjunto fora dos doze: `[]`) |
| 5 | comportamental | sim | Dois bancos, mesma base pelo mesmo caminho de ingestão (80 lançamentos: 76 de gasto, um por regra de categoria, mais transferência, estorno, positivo e categoria inalcançável). `antes` por inserção direta minha, `depois` por `seed_taxonomy`. Contagem de gasto = 77 nos dois (>0). Total = `-1075809` nos dois. `corte`: total `0`/`0`, média `0`/`0`, 0 linhas. `piso`: total `-113108`/`-113108`, média `-113108`/`-113108`, 12 linhas iguais elemento a elemento. Listagem `(pluggy_id, match_value, nature, essentiality)`: igual elemento a elemento, n=80 |
| 6 | comportamental | sim | 3 linhas: `('Same person transfer','Não é gasto')`, `('Same person transfer - CASH','Não é gasto')`, `('Transfer - Internal','Não é gasto')` |
| 7 | comportamental | sim | `AXES[0]` = `grupo`. `antes` 10 chaves, `depois` 11 chaves; soma `entries` `76`/`76` (>0, iguais); soma `amount_cents` `-119358`/`-119358`; `depois` sem nenhuma das quatro aposentadas e todas as chaves dentro dos doze; `antes` mostra as quatro aposentadas |
| 8 | comando | sim | `env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_taxonomy_remap.py tests/test_taxonomy_seed.py tests/test_taxonomy_literals.py` → `20 passed in 0.58s`, código `0`. `tests/test_taxonomy_remap.py` é novo, com `test_the_seed_reconciles_a_database_seeded_with_the_previous_vocabulary`, `test_an_owner_written_rule_that_loses_its_group_falls_into_the_escape` e `test_the_four_numbers_are_identical_before_and_after`. Os dois testes novos do varredor em `tests/test_taxonomy_literals.py` passam isolados (`-k "jinja or running_html"` → `2 passed`). `git diff develop...HEAD --stat -- scripts .harness` sai vazio: nenhum portão novo, `gates_runner.sh` intocado |

## Minha própria medição dos quatro números

A comparação do critério 5 usa dois bancos semeados em separado. Fiz também o teste mais duro, que é o remapeamento **no mesmo banco**: montei o estado "antes", copiei o arquivo SQLite, e rodei `seed_taxonomy` + `classify_all` na cópia.

Base: **87 lançamentos**, dos quais **84 contam como gasto** — 76 de gasto (um por regra de categoria do vocabulário anterior, valores em centavos distintos), 4 que casam com as quatro regras de descrição, 3 pegos por uma regra do dono, mais transferência, estorno e positivo (esses três fora do gasto). O `classify_all` posterior ao remapeamento mexeu em 14 lançamentos.

| medida | antes | depois | idêntico |
|---|---|---|---|
| gasto total (centavos) | `-1969490` | `-1969490` | sim |
| lançamentos considerados gasto | `84` | `84` | sim |
| `corte` — variável × supérfluo, total / média / linhas | `-93603` / `-93603` / `[('Farra do dono', -93603, 3)]` | idem | sim |
| `piso` — fixa × essencial, total / média / linhas | `-113108` / `-113108` / 12 chaves | idem | sim |

Sobre o piso de significado que você pediu: com a base que o critério 5 prescreve, a travessia `corte` sai **vazia dos dois lados** — nenhuma das 80 regras, nem no vocabulário anterior nem no atual, é `variável × supérfluo` (a distribuição por par é idêntica nos dois: 34 variável/importante, 21 eventual/importante, 5 fixa/importante, 3 eventual/essencial, 12 fixa/essencial, 5 variável/essencial). Comparar zero com zero ali não prova nada, então plantei uma regra do dono nesse par, com 3 lançamentos, e a igualdade se mantém com conteúdo.

Os outros três pontos que você mandou provar:

- **Natureza e essencialidade por lançamento**: a leitura `(pluggy_id, match_value, nature, essentiality)` sai igual elemento a elemento nos 87 lançamentos do remapeamento em lugar, e nos 80 da comparação entre bancos. O item mexe em grupo e só em grupo — visível no eixo `grupo`, cujas chaves trocam de `['Comer fora e lazer','Dívidas e juros','Serviços e assinaturas','Transferências',...]` para os doze, com soma de `entries` e de `amount_cents` inalteradas.
- **Nenhuma regra órfã**: `0` em todos os cenários, e `PRAGMA foreign_key_check` vazio depois de cada `seed_taxonomy`. Forcei também o caso do lançamento sem regra apontando para grupo que some: cai no fallback `Outros`, sem violação de chave.
- **Norma 25**: transferência (`is_transfer=1`, `-999901`), estorno (`is_refund=1`, `-777701`) e valor positivo (`+555501`) ficam com `entra_no_gasto=0` nos dois bancos. A exclusão é pelas colunas escritas na ingestão, nunca pelo grupo — por isso mover `Transferências` para `Não é gasto`/`Financeiro`/`Pessoal` não desloca um centavo.
- **Carga não quebra por vocabulário**: carreguei 8 lançamentos com categorias que a semente não conhece, incluindo os quatro nomes de grupo aposentados, um nome de grupo novo, categoria vazia, categoria ausente, acentos e `O'Reilly & Cia -- 100%`. `ingest status ok`, 8 aceitos, 0 rejeições, nenhuma exceção; todos registrados em `categories` (exceto vazio e nulo, que `_record_categories` filtra por desenho) e todos classificados em `Outros` / `eventual` / `importante`. Zero lançamentos sem grupo, natureza ou essencialidade; segunda classificação devolve `0`.

## Achados que não reprovam

1. **`docs/plano.md`, linhas 129-131**, ainda declara o vocabulário antigo como canônico: `**Grupo** (10): Moradia · Educação · Transporte · Alimentação · Comer fora e lazer · Saúde · Serviços e assinaturas · Dívidas e juros · Transferências · Outros.` São dez grupos e quatro nomes que deixaram de existir. Não é critério desta fase, mas as normas 7 e 8 do projeto pedem reconciliação de doc no mesmo PR. A linha 34 (`Transferências entre contas próprias … R$ 20.272,00`) é número congelado e português corrente, não o nome do grupo — essa não mexe.
2. **`seed_taxonomy` sozinha deixa inconsistência transitória.** Ela só reescreve `transactions.group_id` de quem apontava para grupo que sumiu; o lançamento cujo grupo antigo sobreviveu mas cuja regra mudou de grupo fica desatualizado até a `classify_all` seguinte — 14 dos 87 no meu cenário. Não vaza: `seed_taxonomy` só é chamada por `app/taxonomy/seed.py:106` (a CLI), e `app/ingest/__main__.py` sempre encadeia `seed_command()` → `classify_command()`. Vale saber que rodar `python -m app.taxonomy.seed` isolado exige a classificação na sequência.
3. **O varredor de literais estreitou em `.html`**: `tests/test_taxonomy_literals.py:30` passa a ignorar linha de `.html` sem `{{` ou `{%`. É exatamente o que o critério 8 pede, e era necessário porque o grupo novo `Assinaturas` colide com texto de interface em `app/templates/fragments/comprometido_assinaturas.html:4`. Efeito colateral: um bloco Jinja quebrado em várias linhas passa a poder carregar um nome de vocabulário sem ser acusado. Fora do alcance da varredura (que só lê `app/`), `ingestao/pluggy_consolidate.py:42` carrega `"Assinaturas"` como literal.
4. **O branch está 5 commits atrás de `develop`** (item 022). O `.gitignore` do branch ainda é o `data/` de antes da correção, e não o `/data/` de `develop`; a fixture está commitada mesmo assim (`tests/data/vocabulario_anterior.json`, blob `4dc6b62`) e o branch não toca o arquivo, então a versão de `develop` prevalece no merge. Só não vale re-adicionar a fixture depois de um rebase sem conferir.
5. Confirmei que `tests/data/vocabulario_anterior.json` é **JSON-idêntico** a `git show develop:app/taxonomy/seed.json`. Sem isso, o estado "antes" seria uma ficção, e toda a comparação valeria pouco.

## Instrumentos do implementer

Só o **critério 8**, que é de comando e por construção executa a suíte do avaliado. Os critérios 1 a 7 e as quatro medições que você pediu por fora foram provados com banco, semeadura "antes" e comparação escritos por mim.
