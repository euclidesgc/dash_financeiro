# Veredicto — fase 2, rodada 1

**CRITERIO_INVALIDO.** Validação cega do `phase-validator`, agente novo, sem
plano, brief nem veredicto anterior no envelope.

Nenhum portão falhou e nenhum critério verificável falhou: os oito primeiros
passaram com evidência executada. O bloqueio é do **critério 9**, que nomeia uma
rota que só a fase 3 cria e, como está escrito, é aprovado por qualquer URL
inventada.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | `All checks passed!`, código `0` |
| `pytest -q` na raiz | `461 passed`, código `0` |
| `scripts/gates/gates_runner.sh` | `gates: limpos (árvore completa, 371 arquivo(s) considerados)` |

## Critérios

| # | Tipo | Resultado | Evidência |
|---|---|---|---|
| 1 | comportamental | passou | `id="fatos"` e `id="metas"` uma vez cada; 5 `data-config` distintos, iguais aos 5 nomes de `CATALOG` |
| 2 | comportamental | passou | "o painel usa 6 meses" na primeira leitura; `data-alvo` `700002` → `350001`, metade exata; `3 meses de reserva` duas vezes e `6 meses de reserva` nenhuma |
| 3 | comportamental | passou | três `400`, cada um nomeando o que recusou, e `plan_facts` intacta depois das três |
| 4 | comando | passou | `9 passed` em `tests/test_configuracao_screen.py` |
| 5 | estrutural | passou | os quatro PNG existem, de 176 a 190 KB, com a largura do nome confirmada por `file`; `scripts/capturas.mjs` rastreado |
| 6 | comportamental | passou | seis medições, `scrollWidth == innerWidth` nas três larguras nos dois modos, `campos=4`, `menorFonte=16px` |
| 7 | comando | passou | suíte completa e lint em `0` |
| 8 | comando | passou | catálogo sem `janela-dias` e sem nome ligado às quatro constantes de tolerância |
| 9 | comportamental | **inválido** | o "Então" literal é atendido, mas não prova nada: a guarda é middleware e devolve `302` para qualquer caminho sem sessão. Com sessão, `POST /configuracao/cnpj` responde `404` — a rota é da fase 3 |

O validador registrou também que os critérios 4 e 7 são a suíte do próprio
avaliado, e que ele não dependeu de `tests/test_route_guard.py` para julgar o
critério 9: mediu os dois `302` e o `404` por fora, com `curl`.

## Achado fora dos critérios

**Não reprova.** A guarda de sessão responde `302` a caminho inexistente em vez
de `404`. É deliberado — não contar ao anônimo quais caminhos existem, o que casa
com a invariante 24 — e já está ratificado em `D-001`. Mas é a causa direta de o
critério 9 passar por construção, e qualquer critério futuro que use "responde
302 sem sessão" como prova de guarda terá o mesmo defeito.

## O que abriu a rodada 2

`D-002`, registrada e reconciliada no `03-plan.md`: cada rota é cobrada na fase
que a cria, e o critério passa a exigir as duas metades — com sessão a rota
responde diferente de `404`, sem sessão responde `302`. Nada mudou no código da
fase por causa disso.
