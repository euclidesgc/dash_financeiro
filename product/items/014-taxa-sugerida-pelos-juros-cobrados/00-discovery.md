# Discovery — 014-taxa-sugerida-pelos-juros-cobrados

**Origem:** o dono perguntou se o painel não consegue descobrir as taxas
sozinho. A resposta, medida, é **sim para o cheque especial e não para o
cartão** — e o porquê do "não" é a parte que interessa.

**Data:** 2026-09-07

## História

Como dono deste painel, quero que ele me sugira a taxa a partir do que o banco
já me cobrou, com a incerteza à vista, para eu confirmar em vez de digitar do
zero.

## Regras e exemplos

### R1 — Os juros cobrados estão na base

- **E1.1** — A base tem `Saída JUROS LIMITE DA CONTA` (8 vezes, R$ 3.605,09),
  `COBRANCA DE JUROS` (8, R$ 392,14), `Saída JUROS EXCESSO LIM CONTA` e
  `Juros do rotativo`. É o preço que o banco cobrou, não o que o contrato diz.
- **E1.2** — `JUROS DE MORA` **não** entra: multa por atraso de um boleto não é
  o preço de carregar saldo negativo.

### R2 — A taxa sai do saldo diário, não da média do mês

- **E2.1** — O banco cobra sobre o saldo negativo de **cada dia**. Dividir os
  juros pela média entre o saldo do início e o do fim do mês dá 2,30% num mês e
  14,81% no seguinte, porque a conta atravessa o mês entrando e saindo do
  vermelho.
- **E2.2** — O saldo diário é **reconstruível**: o saldo de hoje menos os
  lançamentos, andando para trás. Dividindo os juros do mês pelo saldo médio dos
  **dias negativos**, a dispersão cai muito: o `itau` fica em **4,22% ao mês**
  de mediana, com faixa de 2,10% a 6,80% em 7 meses.
- **E2.3** — O `docs/plano.md` traz 3,52% para o cheque especial, medido por
  outro caminho. Mesma ordem de grandeza, e a diferença é explicável: o ciclo de
  cobrança não casa com o mês do calendário e o IOF é cobrado à parte.

### R3 — Saldo pequeno não produz taxa, produz tarifa

- **E3.1** — Um mês da `CAIXA` dá **81,41%** — R$ 30,94 de cobrança sobre um
  saldo médio negativo de R$ 38,01. Não é juro proporcional; é tarifa mínima
  dominando a razão.
- **E3.2** — Abaixo de um piso de saldo, o mês é descartado. Com o piso, a
  `CAIXA` fica em 8,04% de mediana sobre 5 meses.

### R3b — O banco cobra em atraso, e casar o juro com o mês errado inventa faixa

- **E3b.1** — Na `CAIXA` os oito `COBRANCA DE JUROS` caem entre os dias 01 e 03:
  o lançamento de 01/09 é o preço de **agosto**, não de setembro. Casando o
  lançamento com o mês em que ele foi lançado, as taxas saem `383, 741, 867,
  1153`; casando com o mês que ele remunera, saem praticamente constantes — que é
  como um cheque especial contratado se parece.
- **E3b.2** — A mediana quase não se move, mas a **faixa mostrada ao dono se
  inventa**: a tela dizia "variou de 3,83% a 11,53%" onde a dispersão real é bem
  menor. E era o **mês em curso**, com cinco dias de saldo sob um mês inteiro de
  juros, que produzia o extremo de 11,53%.
- **E3b.3** — O mês em curso fica de fora, e o juro dos primeiros dias conta para
  o mês anterior. Achado do validador cego, fora da letra dos critérios.

### R4 — Cartão não tem taxa a derivar, e isso não é limitação de dado

- **E4.1** — O saldo de um cartão é **fatura**, não dívida rotativa: fatura paga
  inteira não cobra juro nenhum. Os R$ 2,15 e R$ 14,17 do `Mercado Pago` são
  encargos pequenos, não rotativo sobre o saldo — dividi-los pelo saldo daria
  0,06% ao mês, um número falso.
- **E4.2** — Por isso o relatório de origem escreveu "a confirmar" para o
  cartão. O painel escreve o mesmo, e diz por quê.

### R5 — Sugestão, nunca fato

- **E5.1** — A faixa medida do `itau` vai de 2,10% a 6,80%. Adotar a mediana em
  silêncio seria o painel decidindo o que ele não sabe, e a incerteza é grande
  demais para esconder.
- **E5.2** — O campo vem **preenchido** com a sugestão, o texto ao lado diz de
  onde ela veio e mostra a faixa, e nada é gravado sem o dono apertar Salvar.
  É a mesma régua do invariante 26: o que só o humano sabe é parâmetro editável.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: rápida.** Uma fase.
