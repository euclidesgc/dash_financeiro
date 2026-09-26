# PRD 073 — Consultor de IA: projeção de parcelas, financiamentos e contas recorrentes

## Valor

O dono pergunta no Consultor "quanto vou pagar de parcela e financiamento nos próximos meses?" e recebe,
mês a mês, o que já está contratado para sair, separado por origem, e o que termina em cada mês. Com
isso ele vê quando o aperto alivia sem abrir fatura por fatura.

## Usuários

O dono do painel, logado, na tela `/app/advisor`.

## Requisitos

- **R1** — Perguntado quanto sai nos próximos meses, o consultor responde com o total de cada mês e
  o total por origem: compras parceladas, financiamentos e contas recorrentes e assinaturas.
- **R2** — O horizonte padrão são 6 meses, a partir do mês seguinte a hoje; o dono pode pedir de 1 a
  24 meses. Pedido fora disso vira resposta que diz o limite.
- **R3** — Cada linha da projeção diz de onde vem: descrição do lançamento ou do contrato, conta,
  valor da parcela, parcela k/n no primeiro e no último mês do horizonte e o mês da última parcela.
  A resposta diz o que termina em cada mês.
- **R4** — A compra parcelada conta até a última parcela e some dos meses seguintes. O financiamento
  conta pelo contrato cadastrado na tela Configuração (valor, prazo, primeiro vencimento), e o boleto
  que paga esse financiamento não conta de novo entre as contas recorrentes.
- **R5** — Contrato sem valor de parcela e parcela sem número não são adivinhados: a resposta diz que
  ficaram de fora e por quê.
- **R6** — Todo valor da resposta vem da projeção calculada pelo painel; valor que ela não devolveu
  troca a resposta pelo aviso de sempre.
- **R7** — Abaixo da resposta, a nota diz que o consultor consultou as parcelas e contas dos próximos
  meses.

## Fora de escopo

- Gasto do dia a dia sem série (mercado, delivery) e renda na projeção.
- Tabela ou gráfico da projeção dentro do chat; editar contrato pelo chat.

## Pontos em aberto

- Nenhum.
