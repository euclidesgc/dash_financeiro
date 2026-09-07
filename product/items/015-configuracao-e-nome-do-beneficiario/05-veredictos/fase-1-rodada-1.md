# Veredicto — fase 1, rodada 1

**APROVADO.** Validação cega do `phase-validator`, agente novo, sem plano, brief
nem veredicto anterior no envelope.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | `All checks passed!`, código `0` |
| `pytest -q` na raiz | `451 passed`, código `0` |
| `scripts/gates/gates_runner.sh` | `gates: limpos (árvore completa, 360 arquivo(s) considerados)` |

## Critérios

| # | Tipo | Resultado | Evidência |
|---|---|---|---|
| 1 | comando | passou | `1`, `1`, `0` nas três consultas de esquema |
| 2 | comando | passou | migração sobre base não vazia: `['010_settings.sql']`, linha preexistente com `kind` `fato`, e `quitacao-cdc 3500000 fato centavos plan_parameters` numa linha só |
| 3 | comando | passou | `recusado` para `5000.00`, `inf`, `nan`, `1e308`, `nan` e `200`; `250000` e `352`; código `0` |
| 4 | comando | passou | `18 passed` em `tests/test_settings.py` |
| 5 | comando | passou | `plan_parameters` só em `app/migrations/sql/`; nenhuma das três exceções antigas; `def parse_money` uma vez |
| 6 | comportamental | passou | cenário construído para poder reprovar: taxa de cada dívida respondida antes, `/consultor` passou a perguntar `quitacao-cdc` (contagem `1`), e depois da gravação `/simulador` traz `R$ 35.000,00` no bloco `id="fatos"` e a pergunta some (contagem `0`) |
| 7 | comando | passou | suíte completa e lint em `0`, `451` ≥ `433` |

O validador registrou que os critérios 4 e 7 são a suíte do próprio avaliado, e
que os critérios 2 e 3 usam scripts de evidência escritos pelo implementador —
leu os dois antes de aceitar, conferiu que chamam o código real, e fez a leitura
de volta do critério 2 por fora, com `app.query`.

## Achados fora dos critérios

Os dois vieram marcados pelo próprio veredicto como **não reprova**, e por isso
não abriram rodada nova.

1. **`app/advisor/gaps.py::WANTED` não derivava do catálogo.** O consultor
   mantinha a própria tupla, com o mesmo texto repetido: uma pergunta
   acrescentada, renomeada ou reordenada em `CATALOG` não chegava a
   `/consultor`, e nada na suíte falhava por isso — a mesma classe de defeito que
   esta fase fechou no banco. **Corrigido**, com o teste
   `test_a_question_added_to_the_catalogue_reaches_the_advisor`, que falha sem a
   correção porque acrescenta um fato ao catálogo e cobra que o consultor
   pergunte por ele.
2. **`_reference` cai em `date.today()` em vez de `reference_date()`**, em
   `app/routers/whatif.py` e `app/routers/advisor.py`. `DASH_TODAY` é ignorado no
   caminho de fallback, e é esse `today` que decide se um fato está vencido.
   Pré-existente, do item `008`, fora do diff desta fase: virou item de roadmap,
   como manda a norma 12.
