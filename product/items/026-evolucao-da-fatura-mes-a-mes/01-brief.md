# Brief — 026-evolucao-da-fatura-mes-a-mes

**Item:** `026-evolucao-da-fatura-mes-a-mes` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

O painel sabe o que sai da conta nos **próximos 45 dias**
(`app/commitments/calendar.py`) e não sabe o que acontece depois. Para uma dívida
de cartão feita de compras parceladas, isso responde a pergunta errada: 45 dias
mostram uma fatura parecida com a do mês passado, e escondem que ela cai pela
metade em abril porque três parcelamentos morrem em março.

O motor de compromissos já guarda o que a resposta exige — a parcela atual, o
total de parcelas, quantas faltam e o mês em que a série acaba —, e já calcula
quanto caixa cada série libera ao terminar. **O que falta é a série mensal
fechada:** nenhuma consulta hoje soma "quanto ainda falta pagar" de uma compra
parcelada, nem distribui esse saldo pelos meses em que ele vai vencer.

Sem isso, a decisão de antecipar um parcelamento — ou de não fazer a próxima
compra em dez vezes — é tomada pela intuição do tamanho da fatura de hoje.

## Escopo

> Reconciliado em D-006.

O painel responde **como fica a fatura de cada cartão mês a mês até zerar**, com
o mês em que cada parcelamento morre nomeado e o quanto a fatura cai quando ele
morre. A curva distribui no tempo o que já está lançado: o dia de fechamento do
cartão decide de qual fatura cada parcela faz parte, e o dia de vencimento decide
em que mês essa fatura sai da conta — o mês que a curva nomeia, porque é essa a
pergunta que a tela em que ela vive responde. Os dois dias vieram do item `024`.

## Não-escopo

> Reconciliado em D-006.

- **A curva não projeta gasto novo.** Ela responde "o que eu já devo, distribuído
  no tempo", não "quanto vou gastar". A projeção de comportamento é o mês típico,
  e ela já existe.
- **Nenhum campo novo do cartão.** Limite, taxa, fechamento e vencimento vieram do
  `024` e são consumidos como estão — inclusive o vencimento decidindo o mês em
  que a fatura sai da conta é o campo existente cumprindo o papel que já era
  dele, não campo novo.
- **A janela de 45 dias não muda.** Ela responde outra pergunta — o que sai da
  conta amanhã — e continua respondendo.
- **Nenhum cálculo de juros de rotativo.** A curva soma o que está parcelado; se
  o dono não paga a fatura inteira, isso é outro item.

## Requisitos

> Reconciliado em D-006.

- **RF-01.** Existe uma série mensal por cartão, do mês corrente até o mês em que
  a última parcela conhecida vence, com o valor que a fatura soma em cada mês.
- **RF-02.** O **dia de fechamento** do cartão decide de qual fatura cada parcela
  faz parte: parcela lançada depois do fechamento entra na fatura seguinte. O
  **dia de vencimento** decide em que mês essa fatura sai da conta, e é esse o mês
  que a série nomeia — a mesma leitura de "quando o dinheiro sai" que o calendário
  de 45 dias já usa.
- **RF-03.** Quando falta o dia de fechamento, a série é construída pelo mês do
  lançamento, e a tela **declara essa premissa** em vez de fingir que sabe.
  Quando o fechamento existe mas falta o dia de vencimento, a série usa o mês do
  fechamento, sem deslocamento, e a tela declara a premissa do vencimento
  ausente.
- **RF-04.** Cada parcelamento vivo tem o mês em que ele acaba nomeado, e o quanto
  a fatura cai no mês seguinte à morte dele.
- **RF-05.** A soma da série de um cartão é igual ao total que ainda falta pagar
  daquele cartão — a curva e o total não podem discordar.
- **RF-06.** A curva aparece em `/comprometido`, junto do que já responde quando o
  dinheiro sai.
- **RF-07.** Cartão sem parcelamento vivo mostra série vazia com o estado nomeado,
  e não uma curva de zeros.
- **RF-08.** Nenhum total existente de `/comprometido` muda: o caixa liberado, a
  lista de assinaturas e o calendário de 45 dias continuam iguais.

## Riscos

> Reconciliado em D-006.

- **A curva discordar do total.** É o risco central, e RF-05 é o critério que o
  mede: as duas leituras saem da mesma base e têm de fechar.
- **O dia de fechamento ou o de vencimento mudar o mês de uma parcela e ninguém
  notar.** Por isso RF-03 exige que a premissa seja declarada quando um dos dois
  não é conhecido.
