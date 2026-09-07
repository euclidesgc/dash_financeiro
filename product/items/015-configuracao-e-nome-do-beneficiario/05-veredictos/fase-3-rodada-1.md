# Veredicto — fase 3, rodada 1

**APROVADO.** Validação cega do `phase-validator`, agente novo, sem plano, brief
nem veredicto anterior no envelope.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | `All checks passed!`, código `0` |
| `pytest -q` na raiz | `480 passed`, código `0` |
| `scripts/gates/gates_runner.sh` | `gates: limpos (árvore completa, 384 arquivo(s) considerados)` |

## Critérios

| # | Tipo | Resultado | Evidência |
|---|---|---|---|
| 1 | comando | passou | `53`, `338`, `169`, `338`, `404`, `0` e `148` — os sete batem exatamente |
| 2 | comando | passou | `19 passed`; o validador leu o teste e confirmou que a asserção discrimina: o beneficiário tem razão social diferente do nome consultado, então cair na razão social reprovaria |
| 3 | comportamental | passou | 30 linhas, a primeira é `debito prestacao hab`, nenhuma linha sem `data-origem` (o pareamento foi conferido linha a linha, não só a contagem), e `sort -c -n` em `0` |
| 4 | comportamental | passou | `Consórcio Coimex` `0` / `3` / `0`, e `data-comprometido="-802679"` idêntico nas três |
| 5 | comportamental | passou | `200` nas duas; "tempo esgotou" e apelido preservado na primeira; `14 dígitos` e **zero** tentativas de rede na segunda. O validador leu o script, conferiu o contador de rede e verificou no código que `digits()` roda antes de `httpx.get` |
| 6 | estrutural | passou | quatro PNG válidos e versionados; o de 375 foi aberto e é a lista real |
| 7 | comando | passou | suíte e lint em `0` |
| 8 | comando | passou | nenhum número medido em `app/*.py`, e os sete novos em `tests/test_frozen_numbers.py` |
| 9 | comando | passou | nenhuma referência a `display_name` ou `payee_names` nos seis diretórios de motor, e o validador conferiu por conta própria que nenhum `JOIN` à mão apareceu ali |
| 10 | comando | passou | `httpx` em `project.dependencies`; contraprova feita com nome ausente levanta `AssertionError` |
| 11 | comportamental | passou | com sessão `200` nas duas rotas novas; contraprova própria: `/configuracao/inventada` dá `404` com sessão. Sem sessão, `302` nas duas |

## Achados fora dos critérios

Os dois vieram marcados como **não reprova**.

1. **Servidor órfão na porta 8015**, deixado por mim. O `uvicorn` do validador
   falhou com `address already in use` e a porta respondeu mesmo assim, contra
   uma base que já tinha apelidos gravados: a primeira medição do critério 4
   falhou por isso. O validador achou a causa, matou o processo, subiu o seu,
   confirmou por `/proc/<pid>/environ` qual base o listener usava e refez os dois
   critérios afetados. É defeito de ambiente meu, não do código entregue — e o
   conserto é de processo: **encerrar o servidor de trabalho antes de despachar o
   validador**. A porta `8000`, do painel do dono, não foi tocada.
2. **Comentário que contradizia a linha que anotava**, em
   `app/routers/settings.py`: ele terminava dizendo que a contagem vive em
   `tests/test_frozen_numbers.py` logo acima de `PAYEES = 30`. **Corrigido** —
   o comentário passa a separar o que é decisão de produto (quantos a tela
   oferece) do que foi medido nesta base (quantos existem e quanto cobrem), que
   é o que de fato só vive no teste. Não há teste que falhe sem esta correção:
   ela é de prosa, e inventar um `grep` pelo texto do comentário seria testar a
   redação, não o comportamento.
