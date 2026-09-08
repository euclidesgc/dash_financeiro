VEREDICTO: APROVADO

Portões (branch `029-.../fase-1-arvore-sintatica`, `git log develop..HEAD` = 1 commit, tocando só `tests/test_route_guard.py`)

```
ruff:   OK  — "All checks passed!"
format: OK  — "164 files already formatted"; EXIT=0
mypy:   N/A — não faz parte da DoD desta stack (norma 35). Não conta como aprovado nem como reprovado.
pytest: OK  — "656 passed, 2 warnings in 60.31s"; EXIT=0
gates:  OK  — "✓ gates: limpos (árvore completa, 562 arquivo(s) considerados)."; EXIT=0 — mediu 562 > 0
```

## Critérios de aceite

| # | Critério | Veredicto | Evidência |
|---|---|---|---|
| 1 | `estrutural` — `ast`, função de acusação, `ast.parse` + `ast.walk`, sem busca de texto | cumprido | `import ast` na linha 1; a função de acusação recebe o mapeamento e devolve lista ordenada; `ast.parse` e `ast.walk` presentes. Controle positivo antes da ausência. `grep` pela busca de texto antiga: sem saída, exit 1 |
| 2 | `comportamental` — quatro formas diretas | cumprido | Executado fora da suíte do avaliado: quatro acusados, contagem 4 |
| 3 | `comportamental` — apelido de import nos dois sentidos | cumprido | Dois acusados. `grep -rl "date.today()"` nesses arquivos não encontra nada — é exatamente a diferença que o item fecha |
| 4 | `comportamental` — comentário e literal ignorados, com a chave presente | cumprido | Mapeamento com o módulo, acusados vazio — as duas afirmações, separadas |
| 5 | `comportamental` — profundidade e cache | cumprido | Acusados exatamente `['cards/detail/screen.py', 'cards/screen.py']` |
| 6 | `comportamental` — os módulos de rota reais | cumprido | 17 chaves, todas `.py`, acusados vazio |
| 7 | `comando` — a suíte do guarda | cumprido | `12 passed`; `EXIT=0` lido sem cano |

## Prova própria 1 — a acusação alcança o que a busca de texto não vê

Sete módulos escritos por mim, todos acusados, enquanto `grep -rl "date.today()"` só encontrou um: `import datetime as dt` + `dt.date.today()`; `from datetime import date as hoje` + `hoje.today()`; `import datetime` + `datetime.datetime.now()`; `from datetime import datetime as DT` + `DT.now().date()`; chamada quebrada em duas linhas; chamada dentro de método dentro de função aninhada com apelido; `import datetime as clock` + `clock.datetime.now()`.

## Prova própria 2 — a acusação não é enganada por texto

Sete iscas, nenhuma acusada e todas presentes no mapeamento: comentário, literal simples, docstring de módulo, f-string, nome de variável, chave de dicionário, e `from app.models import date` seguido de `date.today()` — que não é o relógio da biblioteca padrão, e onde a busca de texto daria falso positivo.

## Prova própria 3 — mutação: o teste morde

Cópia fora do repositório com a acusação revertida para busca de texto: `3 failed, 9 passed`. Falharam exatamente o das formas diretas (só uma acusada), o do apelido (nenhuma) e o do comentário e literal (falso positivo). O verde de hoje é sustentado pela árvore sintática, não por sorte.

## Prova própria 4 — nada do item anterior regrediu

Profundidade, chave por caminho relativo, exclusão de cache e nenhum módulo de rota real acusado: verificados, e os quatro testes antigos continuam entre os 12 que passam.

## Achados que não reprovam

A rede ainda tem quatro buracos, todos formas legítimas de perguntar as horas que passam limpas: `datetime.utcnow()`; `date.fromtimestamp(time.time())`; referência ligada (`today = date.today` e depois `today()`), porque a chamada vira nome simples e o resolvedor só olha acesso a atributo; e reatribuição (`d = date` e depois `d.today()`), porque o mapa de apelidos lê só `import` e `from ... import`, não atribuição.

## Instrumentos do implementer

Nenhum critério dependeu da suíte do avaliado como prova. Os critérios 2 a 6 foram reexecutados através das funções sob julgamento, com módulos que eu mesmo escrevi. O critério 7 é, por construção, a execução da suíte.
