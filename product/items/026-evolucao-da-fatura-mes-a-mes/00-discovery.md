# Discovery — 026-evolucao-da-fatura-mes-a-mes

**Item do roadmap:** `026-evolucao-da-fatura-mes-a-mes` — o painel responde **como
fica a fatura do cartão mês a mês até zerar**, e não só quanto sai nos próximos 45
dias, com o mês em que cada parcelamento morre nomeado.

**Data:** 08/09/2026 · **Trilha declarada:** rápida

## O terreno, lido no código

O motor de compromissos já sabe quase tudo. `commitments`
(`app/migrations/sql/004_commitments.sql`) guarda `installment_current`,
`installment_total`, `installments_left` e `ends_month`; e `released_cash`
(`app/commitments/live.py`) já soma o caixa que cada série libera ao acabar.

O que **não** existe é a série mensal fechada. A previsão de hoje é uma janela de
45 dias (`app/commitments/calendar.py`), e nenhuma consulta soma "quanto ainda
falta pagar" de uma compra parcelada.

O item `024`, concluído, trouxe o que faltava do outro lado: o cartão passou a ser
entidade com **dia de fechamento, dia de vencimento, limite e taxa**. Sem dia de
fechamento não há fatura a projetar — há uma soma de parcelas, que é outra coisa.

## Regra, exemplo e pergunta

- **Regra.** O painel mostra, por mês, quanto a fatura de cada cartão vai somar
  até zerar, e o mês em que cada parcelamento morre.
- **Regra.** A curva sai do que já está lançado, não de previsão de gasto novo:
  ela responde "o que eu já devo, distribuído no tempo".
- **Regra.** O que decide o mês de uma parcela é o **dia de fechamento** do
  cartão, não o dia da compra.
- **Exemplo.** O dono olha a curva e vê que em março a fatura cai R$ 1.200 porque
  duas compras parceladas acabam em fevereiro. É essa a informação que decide
  antecipar ou não.
- **Pergunta em aberto:** nenhuma de produto.

## Os quatro gatilhos de trilha completa

| Gatilho | Resposta |
|---|---|
| Mexe em contrato público ou OpenAPI? | Não. |
| Toca autenticação, autorização ou dado pessoal? | Não. |
| Tem mais de uma frente de stack? | Não. |
| Requisito ambíguo que exija spec formal? | Não. |

**Trilha rápida.**

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| A curva projeta gasto novo? | **Não.** Ela distribui no tempo o que já está lançado. | Projetar gasto novo misturaria dívida com previsão de comportamento, e o painel já tem o mês típico para a segunda. Uma curva que soma as duas não responde nem "quanto eu devo" nem "quanto vou gastar". |
| O que decide o mês de uma parcela? | **O dia de fechamento do cartão**, que o `024` passou a guardar. Parcela lançada depois do fechamento cai na fatura seguinte. | Usar o dia da compra erra por até um mês inteiro justamente nas compras do fim do mês, que são as que o dono lembra. |
| E cartão sem dia de fechamento informado? | A curva **diz que não sabe** e mostra a série pelo mês do lançamento, nomeando a premissa. | Adivinhar um dia de fechamento é inventar o número que decide em que mês a dívida cai. |
| Onde a curva aparece? | Em `/comprometido`, que já é a tela do que está comprometido e quando sai da conta. | Tela nova para uma leitura que pertence a uma pergunta que a tela existente já faz. |
| Até onde a curva vai? | Até o mês em que a última parcela conhecida acaba. | Horizonte fixo cortaria parcelamento longo exatamente onde ele importa. |
