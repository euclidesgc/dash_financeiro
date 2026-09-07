# Brief — 004-resumo-e-projecao

A tela inicial do painel. Escrito no presente; cada requisito é `RF-nn` e é o
que passa a valer.

Hoje a rota `/` serve uma tela mínima e provisória, com título e o botão
**Sair**. Ela é substituída.

## Requisitos

### As três posições

- **RF-01** — A tela mostra a **posição consolidada**, soma dos saldos de todas
  as contas. Na base de 05/09/2026 vale **−R$ 27.449,71**, ao centavo o número
  congelado em `docs/plano.md`.
- **RF-02** — A tela mostra o **caixa**, soma das contas bancárias:
  **−R$ 10.705,09**. É o que entra no cheque especial.
- **RF-03** — A tela mostra a **dívida de cartão**, soma das contas de crédito:
  **−R$ 16.744,62**, que é a linha "Cartões" da escada de dívida do plano.
- **RF-04** — Os três números têm nome próprio na tela e são lidos juntos. A
  posição é a soma dos outros dois, e a tela mostra que é.

### Quanto sobra

- **RF-05** — A tela mostra a **renda mensal esperada**, mediana das receitas dos
  seis meses completos anteriores ao mês de referência, excluídas transferência
  entre contas próprias e estorno: **R$ 12.226,21**.
- **RF-06** — A mediana é escolhida sobre a média porque 03/2026 traz
  R$ 42.210,26 de crédito atípico. A média daria R$ 16.605,25 e projetaria uma
  renda que não existe. A mediana o neutraliza sem regra especial.
- **RF-07** — A tela mostra o **gasto mensal esperado**, mediana dos gastos dos
  mesmos seis meses, pelo mesmo filtro de gasto que o `002` já usa:
  **−R$ 17.677,46**.
- **RF-08** — A tela mostra **quanto sobra**: renda esperada menos gasto
  esperado, **−R$ 5.451,25/mês**. O número é negativo e a tela não o suaviza.
- **RF-09** — Cada um dos três é declarado como projeção do histórico, com a
  janela de seis meses nomeada na tela.

### A projeção de 45 dias

- **RF-10** — A projeção cobre **45 dias** a partir da data de referência,
  inclusive — a mesma janela do calendário do `003`, e ela vem de lá, não é
  recortada de novo.
- **RF-11** — A projeção corre sobre a **posição consolidada**, e a tela diz
  isso em texto. Os 54 lançamentos com data futura da base estão todos em conta
  de cartão; projetar o caixa exigiria a data de vencimento de cada fatura, que
  a base não traz.
- **RF-12** — Cada dia da projeção soma três parcelas: o **compromisso datado**
  daquele dia, vindo do calendário do `003`; a **renda esperada**, creditada no
  dia mediano das entradas observadas, que é o **dia 14**; e o **gasto
  variável**, diluído em partes iguais pelos dias do mês.
- **RF-13** — O gasto variável é o gasto mensal esperado menos o comprometido
  mensal: **−R$ 9.650,67/mês**. Sem ele a projeção soma renda inteira contra
  gasto pela metade e a linha sobe R$ 7.276,37 em 45 dias, dizendo que o buraco
  se fecha sozinho.
- **RF-14** — Na base de 05/09/2026 a projeção sai de **−R$ 27.449,71** e chega a
  **−R$ 34.441,79** em 20/10/2026, com o pior ponto em **−R$ 40.722,95** no dia
  **13/10/2026**. São **−R$ 6.992,08** no período.
- **RF-15** — A tela nomeia o **pior ponto** e a sua data. É ele que decide se o
  mês entra no cheque especial, não o valor do último dia.
- **RF-16** — A projeção é função determinística e testada. Nenhuma parte dela
  passa por IA.

### A linha do tempo

- **RF-17** — A projeção aparece como **escala graduada**, o elemento de
  assinatura da linguagem visual, com o eixo do tempo marcado.
- **RF-18** — A linha se lê **sem gráfico**: cada ponto de virada — início, pior
  ponto e fim — tem data e valor em texto, com `font-variant-numeric:
  tabular-nums`. Sem rede a tela continua respondendo à pergunta.
- **RF-19** — Cada dia com movimento é legível, com data, o que entra, o que sai
  e o saldo projetado ao fim do dia.

### A tela

- **RF-20** — A rota `GET /` passa a servir o Resumo, e aceita `?data=AAAA-MM-DD`
  como data de referência, igual às telas do `002` e do `003`.
- **RF-21** — A tela leva ao resto do painel: um caminho visível para
  `/gastos`, `/comprometido` e `/regras`.
- **RF-22** — A tela obedece à linguagem visual: cor e espaço só de
  `tokens.css`, contraste AA nos dois temas, foco visível, sem rolagem
  horizontal do corpo de 375 a 1440, e `prefers-reduced-motion` respeitado.
- **RF-23** — Estado vazio acionável: base sem lançamento nenhum mostra o que
  fazer, não uma tela em branco.
- **RF-24** — Nenhum número medido nesta base aparece como literal no código de
  produção.
