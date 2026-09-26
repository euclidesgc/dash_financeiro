# PRD 071 — Consultor de IA: resumo de gastos por categoria e mês a mês

## Valor

O dono pergunta no Consultor "quanto gastei por categoria em agosto?" ou "como foram meus gastos mês a
mês desde junho?" e recebe os mesmos totais das telas do painel, numa pergunta só, sem o consultor
precisar listar lançamento por lançamento nem somar por conta própria.

## Usuários

O dono do painel, logado, na tela `/app/advisor`.

## Requisitos

- **R1** — Perguntado sobre gastos por categoria num período (e, se quiser, numa conta), o consultor
  responde com o total de cada categoria, o gasto, as entradas e o saldo do período, com os mesmos
  números da tela de gastos.
- **R2** — Perguntado mês a mês num período, o consultor responde com entradas, gastos e saldo de cada
  mês que teve lançamento.
- **R3** — Transferência entre contas próprias, estorno e lançamento marcado como "não é gasto" ficam
  fora dos totais, como no painel; valores em reais no formato do painel, negativo = dinheiro que saiu.
- **R4** — Soma ou diferença que o painel não devolveu continua bloqueada pela guarda de números.
- **R5** — Abaixo da resposta, a tela diz o que o consultor consultou: "seus lançamentos", "o resumo de
  gastos" ou os dois.
- **R6** — Uma pergunta simples gasta o mínimo de chamadas à IA: o consultor já sabe as categorias do
  painel e não precisa adivinhar filtro. Excesso de chamadas vira mensagem em português que diz quanto
  esperar (quando o provedor informa) ou que a cota do dia acabou.

## Fora de escopo

- Gráfico no chat; comparação com teto ou meta; projeção de parcelas e dívidas (itens 073 a 075).

## Pontos em aberto

- Nenhum.
