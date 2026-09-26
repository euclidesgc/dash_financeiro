# PRD 075 — Consultor de IA: quais dívidas quitar para liberar dinheiro no mês

## Valor

O dono pede no Consultor "lista as contas que eu poderia ir quitando para liberar minha liquidez" e
recebe as dívidas e compras parceladas na ordem de quanto cada real pago na quitação deixa de sair
por mês. Com um valor disponível, ele vê o que quitar com esse dinheiro e quanto passa a sobrar por
mês, sem abrir planilha.

## Usuários

O dono do painel, logado, na tela `/app/advisor`.

## Requisitos

- **R1** — Perguntado o que quitar para liberar dinheiro no mês, o consultor lista as dívidas com
  parcela a vencer (financiamentos com parcela cadastrada e compras parceladas), cada uma com o valor
  para quitar hoje, a parcela que deixa de sair, quanto ela libera por real pago, quantas parcelas
  faltam e o mês da última, da que mais libera para a que menos libera.
- **R2** — Empate na relação vai primeiro para a de menor valor para quitar.
- **R3** — Sem o saldo de quitação informado, o valor é a soma das parcelas que faltam e a dívida vem
  marcada "estimativa pelo teto — informe o saldo de quitação". Nenhum desconto de juros é estimado;
  compra parcelada se quita pelo valor nominal.
- **R4** — Cheque especial, saldo de cartão e contrato sem parcela cadastrada aparecem à parte, com
  o valor para quitar e o motivo: não liberam parcela, e o saldo do cartão pode já incluir as compras
  parceladas da lista, então os dois não se somam.
- **R5** — Dado um valor disponível agora, o consultor diz quais dívidas quitar com ele, descendo a
  lista e pulando o que não cabe, o total gasto, a sobra e a parcela liberada no total. Valor que não
  quita nenhuma diz isso; valor zero ou negativo vira resposta que diz o que corrigir.
- **R6** — Todo valor da resposta vem da conta feita pelo painel; valor que ela não devolveu troca a
  resposta pelo aviso de sempre. A nota abaixo da resposta diz que o consultor consultou as dívidas
  que mais liberam dinheiro no mês.

## Fora de escopo

- Juros economizados ao quitar cheque especial e cartão (a escada de dívidas já mostra).
- Registrar o saldo de quitação pelo chat; escolha ótima que não siga a ordem da lista.

## Pontos em aberto

- Nenhum.
