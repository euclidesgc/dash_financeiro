# PRD 074 — Consultor de IA: quanto juntar para quitar uma dívida

## Valor

O dono pergunta no Consultor "quanto eu preciso juntar para quitar o carro?" e recebe o valor para
quitar hoje e, dada uma data ou um valor que consegue guardar por mês, quanto guardar ou em que mês
chega lá. Com isso ele decide qual dívida atacar sem abrir planilha.

## Usuários

O dono do painel, logado, na tela `/app/advisor`.

## Requisitos

- **R1** — Perguntado quais dívidas tem, o consultor lista cheque especial, saldo de cartão,
  financiamentos e compras parceladas com parcela a vencer, cada uma com o valor para quitar hoje e,
  quando é parcelada, a soma das parcelas que faltam e o mês da última.
- **R2** — Para uma dívida e uma data (ou "em N meses"), o consultor diz o valor para quitar nessa
  data, contando as parcelas pagas até lá, e quanto guardar por mês.
- **R3** — Para uma dívida e um valor guardado por mês, o consultor diz em que mês o dinheiro
  guardado alcança o valor para quitar, ou que não alcança.
- **R4** — O saldo de quitação que só o banco informa não é adivinhado. Sem ele, a resposta diz que
  não foi informado, que se registra na tela Dívidas, e usa a soma das parcelas que faltam como
  teto. Nenhum desconto de juros é estimado.
- **R5** — Compra parcelada se quita pelo valor nominal das parcelas que faltam; a resposta diz isso.
- **R6** — Data que já passou e valor mensal zero ou negativo viram resposta que diz o que corrigir.
- **R7** — Todo valor da resposta vem da conta feita pelo painel; valor que ela não devolveu troca a
  resposta pelo aviso de sempre. A nota abaixo da resposta diz que o consultor consultou o valor
  para quitar as dívidas.

## Fora de escopo

- Ordenar dívidas pelo que liberam no mês (fatia seguinte).
- Registrar o saldo de quitação pelo chat; rendimento do dinheiro guardado.

## Pontos em aberto

- Nenhum.
