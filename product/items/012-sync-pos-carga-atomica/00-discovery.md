# Discovery — 012-sync-pos-carga-atomica

**Item do roadmap:** `012` — A reclassificação, o recálculo de compromissos e a
reconstrução da escada rodam **dentro** do mesmo tratamento de erro da carga.

**Data:** 2026-09-07

## História

Como dono deste painel, quero que uma sincronização só se declare bem-sucedida
quando tudo o que ela precisa fazer tiver sido feito, para não ler tela velha
achando que é nova.

## Regras e exemplos

### R1 — Sucesso mentiroso é pior que falha

- **E1.1** — `_after` — classificar, recalcular compromissos, reconstruir a
  escada — rodava **depois** de a linha `ok` já estar gravada e **fora** de
  qualquer tratamento. Uma exceção ali derrubava a rota com `500` deixando um
  `sync_runs` que afirma sucesso com as tabelas derivadas paradas.
- **E1.2** — É o oposto do que o item `006` entregou. Ele matou a falha
  silenciosa; este caminho fazia a falha **mentir**, que é pior: o dono lê a tela
  seguinte com a marca de sincronizado e os números do estado anterior.
- **E1.3** — Achado estrutural do validador do `006`, lido no código e declarado
  como não provocado. Provocá-lo é o primeiro passo deste item.

### R2 — A linha rebaixa, e a mensagem diz o que ficou para trás

- **E2.1** — A execução que falha na pós-carga é **rebaixada** para `failed`, com
  mensagem que diz que os lançamentos entraram mas a classificação e os
  compromissos não foram recalculados, e que as telas mostram o estado anterior.
- **E2.2** — A rota devolve `200` com o aviso, nunca `500`: derrubar a página
  esconderia justamente o que precisa ser dito.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: rápida.** Uma fase.
