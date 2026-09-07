# Brief — 014-taxa-sugerida-pelos-juros-cobrados

- **RF-01** — O painel deriva uma taxa mensal observada por conta **bancária**
  com saldo negativo, a partir dos lançamentos de juros que a base traz.
- **RF-02** — Lançamento de **mora** não entra: multa por atraso não é o preço de
  carregar saldo negativo.
- **RF-03** — O denominador é o saldo médio dos **dias negativos** do mês,
  reconstruído a partir do saldo atual andando para trás pelos lançamentos.
- **RF-04** — A reconstrução para no primeiro lançamento da conta: antes dele não
  há história, e inventar zero inventaria dias no azul.
- **RF-05** — Mês cujo saldo médio negativo fica abaixo de um piso é
  **descartado**: ali a tarifa mínima domina a razão e ela deixa de ser taxa. Um
  mês desta base dá 81,41% sobre R$ 38,01.
- **RF-06** — Conta com menos de três meses de juros cobrados não produz
  sugestão.
- **RF-07** — A sugestão é a **mediana** dos meses, e a tela mostra também o
  **menor e o maior** — a faixa do `itau` vai de 2,10% a 6,80%.
- **RF-08** — Na base de 05/09/2026 a sugestão do `itau` é **4,22% ao mês** sobre
  7 meses, e a da `CAIXA` é **8,04%** sobre 4 meses.
- **RF-09** — **Cartão não recebe sugestão.** O saldo de um cartão é fatura, e
  fatura paga inteira não cobra juro; os encargos pequenos que aparecem não são
  rotativo sobre o saldo, e derivar deles daria um número falso.
- **RF-10** — O campo de taxa vem **preenchido** com a sugestão, e o texto ao
  lado diz de onde ela veio, sobre quantos meses, e qual a faixa.
- **RF-11** — Nada é gravado sem o dono salvar. A sugestão não vira fato sozinha.
- **RF-12** — Nenhum número medido nesta base aparece como literal no código.
