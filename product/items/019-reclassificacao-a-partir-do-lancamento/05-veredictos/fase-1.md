VEREDICTO: APROVADO

O despacho mandou só o objetivo da fase e os critérios — nenhum plano, brief, spec ou histórico veio junto, e nada dentro de `product/items/019-.../` foi aberto. Árvore limpa, um commit sob julgamento: `970f7d3`.

## Portões

```
lint:   OK   — "All checks passed!" / "164 files already formatted"   (exit 0)
pytest: OK   — 652 passed, 2 warnings in 57.70s                        (exit 0)
gates:  OK   — "✓ gates: limpos (árvore completa, 558 arquivo(s) considerados)" (exit 0)
mypy:   N/A  — não existe `src/`, mypy não está no `.venv` nem no pyproject.
               A norma 35 declara `mypy --strict` item de roadmap.
               Não é um portão que passou: é um portão que este stack não tem.
```

O portão de gates mediu **558 arquivos** (> 0). O pytest coletou **652 testes**. Códigos de saída capturados em arquivo, nunca por `| tail`.

## Critérios de aceite

| # | Tipo | Critério | Veredicto | Evidência |
|---|---|---|---|---|
| 1 | estrutural | `app/queries/reach.py` exporta as quatro funções; as três primeiras executam o mesmo gabarito com `SPENDING` importado | **cumprido** | `reach.py:3` importa `SPENDING`; `:11-14` define o gabarito com `count(*)` e `coalesce(sum(...), 0)`; `:24`, `:28`, `:32` são cada uma um `return conn.execute(...)` de uma linha — nenhuma monta instrução própria |
| 2 | comportamental | prefixo comum não contamina a medição | **cumprido** | `payee_reach("mercado livre")` = `2, -15000`; `payee_reach("mercado livre pago")` = `1, -2500`; `category_reach(...)` = `3, -17500` |
| 3 | comportamental | a gravação devolve os mesmos dois números da prévia | **cumprido** | `2, -15000`, idênticos; `expression_for` produz `^mercado\ livre$`; uma linha só em regras por descrição; `count` de transações com essa regra = `2`; o irmão de prefixo com regra nula |
| 4 | comportamental | regra mais antiga continua segurando o beneficiário | **cumprido** | Com `^mercado` semeada: resultado `entries=0`; duas regras; a prévia continua `2`; `holders` devolve exatamente uma linha, `match_value='^mercado'` |
| 5 | comportamental | corrigir duas vezes deixa uma regra | **cumprido** | `0` → `1` com `created=True` → `1` com `created=False`; o join devolve uma linha só |
| 6 | comportamental | grupo novo no topo, já carregando os lançamentos | **cumprido** | topo `12` → grupo novo com `position=13`, `is_fallback=0`; a regra aponta para `13`; duas transações no grupo novo |
| 7 | comportamental | recusas sem resíduo, com controle positivo | **cumprido** | Grupo inválido e beneficiário desconhecido, ambos `RuleError`; depois delas, zero regras por descrição e os mesmos 12 grupos; a terceira chamada, válida, leva a contagem a `1` |
| 8 | comportamental | escrita, grupo e reclassificação são uma transação só | **cumprido** | Com a reclassificação trocada por uma que apaga e levanta: o erro sobe; zero regras, 12 grupos, o grupo novo não existe, e as três transações voltam idênticas, linha por linha |
| 9 | estrutural | a leitura do lançamento traz `id` e `payee`, e o teste afirma as seis chaves | **cumprido** | `axes.py:69-71`; execução minha devolveu as seis chaves; a afirmação está em `tests/test_axes.py:198-207` |
| 10 | comando | a seleção de oito arquivos de teste sai com `0`, sem portão novo | **cumprido** | `63 passed in 3.03s`, exit `0`. `git diff --name-only develop..HEAD -- scripts/` volta vazio |

## A prova que montei por conta própria

**Prévia e gravação alcançam o mesmo conjunto — provado por identidade de linha, não só por contagem.** Numa base com irmão de prefixo:

```
preview row set == written row set: ['t-ml-1', 't-ml-2'] == ['t-ml-1', 't-ml-2']
```

O casamento é ancorado de verdade, e testei também um beneficiário com metacaractere de regex (`Loja (a+b) S.A`) ao lado de um irmão que um escape faltando pegaria (`Loja aab SA`): prévia e gravação coincidiram.

**Norma 25 sustentada.** Com transferência, estorno e a linha estornada sob o mesmo beneficiário: prévia, gravação e releitura, todas `(2, -15000)`.

**Nada da classificação existente mudou.** Extraí `develop` com `git archive` (sem trocar de branch), montei a mesma base nos dois códigos e comparei totais de gasto, resíduo, os dois cruzamentos, os cinco eixos, os grupos, as regras e a classificação linha por linha. Os dois JSON saíram **byte a byte idênticos** (7272 bytes cada, `diff -u` sem saída).

**Recusa não deixa resíduo, nem invisível.** Testei também o grupo repetido e o caso em que o grupo é inserido e só então a regra é recusada. Nos dois, o estado voltou ao de antes — conferido por uma **segunda conexão** ao mesmo arquivo, que é onde um `INSERT` sem commit se esconderia.

## Achados que não reprovam

1. **O contador de reclassificados não é a mesma medida que o alcance.** A escrita devolve o total de linhas que a reclassificação mexeu — inclui transferência, estorno e lançamento de outro beneficiário cuja classificação deslocou. Num caso de beneficiário só-de-transferência, a chamada voltou alcance `0` e reclassificados `1`. Nenhum critério desta fase usa esse campo, e as duas medidas certas estão corretas. Mas é exatamente o tipo de campo que uma tela mostra como "N lançamentos corrigidos" e volta a dizer um número diferente do da prévia. Vale decidir na fase da tela: ou o campo some, ou vira o alcance.
2. **A divergência do critério 4 é por desenho, e depende da tela para não mentir.** Quando uma regra de id menor já segura o beneficiário, a prévia diz `2` e a gravação alcança `0`. `holders` existe para explicá-lo — mas a promessa "a tela nunca diz um número e faz outro" só se cumpre se a tela realmente o renderizar nesse caso.
3. **A reclassificação marca regra e grupo também em transferência e estorno** (5 linhas físicas contra 2 no alcance). Comportamento pré-existente, intocado, e as consultas de dinheiro filtram por gasto.
4. **O alcance mede história inteira, sem janela de período.** Coerente com uma correção que vale para sempre, mas a tela mostra período — cuidado ao justapor os dois números.

## Instrumentos do implementer

Nenhum. Os dez critérios foram verificados com base montada por mim em diretório temporário, nunca a base do dono. A suíte do avaliado foi executada como portão e como o critério 10, não como prova de comportamento.
