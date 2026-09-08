# Decisões tomadas sem o humano — 027-configuracao-do-gemini

O dono autorizou autonomia para a fila inteira do roadmap em 07/09/2026, com a
régua já escrita na ratificação da divergência `D-001`: *opção técnica com uma
alternativa claramente certa e justificada é execução, não pergunta*. Este
arquivo é o que ele lê depois: **uma linha por decisão**, com a alternativa
descartada e o porquê. Nada aqui foi aprovado por ele.

Todas são reversíveis — o ponto de retorno limpo é o commit `a411509524af8db6f14b8183193bbf580637d5d7`,
anterior a qualquer trabalho autônomo desta corrida.

## Decisões

As decisões de terreno deste item estão na tabela **Decisões autônomas** de
`00-discovery.md`, uma linha por dúvida, com a alternativa descartada e o
porquê. Este arquivo não as duplica: ele registra o que a corrida decidiu
**sobre o processo**, e é onde entram as decisões de fase que aparecerem
durante a execução.

| # | Estágio ou fase | Decidido | Alternativa descartada | Por quê |
|---|---|---|---|---|
| P1 | discovery | Trilha rápida | Trilha completa | Nenhum dos quatro gatilhos dispara: sem contrato público, sem segunda frente de stack, e o requisito está fechado. A trilha rápida corta documentação, nunca verificação. |
| P2 | discovery → plan | Brief aprovado em modo autônomo | Esperar o dono | Ele pediu a fila inteira entregue sem parar para o óbvio. O `sha` da aprovação fica gravado, então o que foi aprovado é releível. |
| P3 | execução | Implementação em worktree própria, integrada em `develop` com `--no-ff` | Uma branch por vez na árvore principal | O dono pediu paralelismo explicitamente. Worktree isola a árvore de cada item e é o que permite seis frentes ao mesmo tempo sem trocar de branch sob um validador rodando — o defeito medido no item `012`. |

## Aprovações registradas em modo autônomo

Cada linha aqui é um `state.py approve --por autonomo` que o dono **não** deu.

| Estágio | Documento | O que foi aprovado | Quando |
|---|---|---|---|
| brief | `01-brief.md` | O problema, o escopo e os requisitos `RF-nn` deste item | 07/09/2026 |

## O que ficou para o humano

- Nada até aqui. O que aparecer durante a execução entra nesta lista, com o que trava.
