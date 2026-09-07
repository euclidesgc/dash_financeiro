# Discovery — 013-objetivo-cenario-vazio-e-ponto-espurio

**Item do roadmap:** `013` — A tela do objetivo **nomeia a lista vazia**, e
leitura com data recusada **não grava ponto** na linha do tempo.

**Data:** 2026-09-07

## História

Como dono deste painel, quero que a tela do objetivo explique por que uma
alavanca rende zero e não suje a linha do tempo com um erro de digitação meu.

## Regras e exemplos

### R1 — Alavanca em zero porque a lista está vazia é diferente de alavanca que não rende

- **E1.1** — O cenário `base` promete "as assinaturas marcadas caem e a lista de
  corte é cortada" e entrega hoje **exatamente o número do `nada muda`**, porque
  nenhuma assinatura foi marcada e o cruzamento `variável × supérfluo` não tem
  uma linha sequer.
- **E1.2** — O número está certo, e a prosa parece mentir: quem lê vê dois atos
  rendendo zero e conclui que os atos não valem nada. A tela passa a dizer que a
  lista está vazia, e onde preenchê-la.

### R2 — Erro de digitação na URL não é ponto de progresso

- **E2.1** — Toda leitura de `/objetivo` grava um ponto por cenário. Data fora da
  faixa aceita cai em hoje e **gravava assim mesmo**: um `?data=0001-01-01`
  injetava três linhas com a data de hoje, indistinguíveis depois de uma leitura
  legítima.
- **E2.2** — A leitura com data recusada passa a **não gravar**, e a tela diz que
  não gravou. A linha do tempo é a única medida de progresso que este produto
  aceita; sujá-la por acidente é caro.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: rápida.** Uma fase.
