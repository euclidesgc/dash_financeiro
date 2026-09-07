# Veredicto — fase 2, rodada 2

**APROVADO.** Validação cega do `phase-validator`, agente novo, sem plano, brief
nem veredicto anterior no envelope. A rodada existe porque a rodada 1 devolveu
`CRITERIO_INVALIDO` no critério de guarda, corrigido por `D-002`.

## Portões

| Portão | Resultado |
|---|---|
| `scripts/lint.sh` | `All checks passed!`, código `0` |
| `pytest -q` na raiz | `461 passed`, código `0` |
| `scripts/gates/gates_runner.sh` | `gates: limpos (árvore completa, 373 arquivo(s) considerados)` |

## Critérios

| # | Tipo | Resultado | Evidência |
|---|---|---|---|
| 1 | comportamental | passou | `id="fatos"` e `id="metas"` uma vez cada; 5 `data-config` distintos, nome a nome iguais ao catálogo |
| 2 | comportamental | passou | loja vazia: `data-valor=""`, `Ausente`, "o painel usa 6 meses"; `data-alvo` `700002` → `350001`; `3 meses de reserva` duas vezes, `6 meses de reserva` nenhuma |
| 3 | comportamental | passou | três `400` nomeando o que recusaram, e `plan_facts` com a mesma linha antes e depois |
| 4 | comando | passou | `9 passed` |
| 5 | estrutural | passou | quatro PNG reais nas larguras do nome, rastreados, e `scripts/capturas.mjs` rastreado |
| 6 | comportamental | passou | seis medições, `campos=4`, `menorFonte=16px`; o validador auditou o script e confirmou que os dois modos carregam em larguras diferentes e que `campos > 0` é exigido |
| 7 | comando | passou | suíte e lint em `0` |
| 8 | comando | passou | catálogo sem `janela-dias` e sem nome ligado às quatro constantes de tolerância |
| 9 | comportamental | passou | com sessão as duas rotas respondem `200`; sem sessão, `302`. O validador rodou o controle por conta própria: `/configuracao-inventada` e `/configuracao/nada` dão `404` com sessão e `302` sem — a metade "com sessão" é o que carrega a prova |

## Achados fora dos critérios

Os três vieram marcados como **não reprova**.

1. **A medição de largura rodava com a barra de rolagem escondida**, e por isso
   `scrollWidth` dava exatamente igual a `innerWidth` nas seis medições — folga
   zero. **Corrigido**: `06-evidencias/viewport.mjs` perdeu o `--hide-scrollbars`
   e passou a medir com a barra que o navegador do dono tem. Remedido:
   `scrollWidth=360` contra `innerWidth=375`, `753` contra `768` e `1425` contra
   `1440` — quinze pixels de folga em cada largura, nos dois modos, em vez de
   nenhum. `scripts/capturas.mjs` mantém a barra escondida de propósito: ali a
   barra é ruído na imagem, não medida.
2. **A migração `010` é irreversível sobre a base do dono** — funde
   `plan_parameters` em `plan_facts` e derruba a tabela. Rodou limpa na base de
   validação e nenhum critério pede rollback. Vira aviso de entrega: convém
   copiar o arquivo da base antes do primeiro boot depois do merge.
3. O diff da fase inclui plano, divergência e veredictos anteriores, por serem
   parte do commit. O validador registrou que não abriu nenhum deles e julgou só
   pelos critérios e pela evidência que executou.
