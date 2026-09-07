# Brief — 008-simulador-e-base-de-fatos

- **RF-01** — `GET /simulador` serve a tela, atrás da sessão, e o Resumo leva
  até ela.
- **RF-02** — O formulário recebe tipo (`receita` ou `despesa`), valor mensal,
  valor único, prazo em meses e um nome opcional.
- **RF-03** — Receita **soma** ao resultado mensal e despesa **subtrai**.
- **RF-04** — O simulador chama a **mesma** função de simulação do item `007`,
  com o efeito mensal injetado. Não existe segundo motor.
- **RF-05** — A resposta principal é em **dias**: a diferença entre os meses até
  o objetivo antes e depois, vezes trinta, com o sinal dizendo se aproxima ou
  afasta.
- **RF-06** — Quando um dos dois lados não tem data, a resposta **não é um
  número**: a tela diz que a diferença é entre chegar e não chegar.
- **RF-07** — Quando não há data dos dois lados **e** o resultado mensal depois é
  positivo, a tela diz que a sobra é menor que os juros da escada — não que o
  resultado é negativo.
- **RF-08** — Valor ilegível, tipo desconhecido, prazo não inteiro e valor não
  positivo são recusados por mensagem que **nomeia o campo**, e nada é gravado.
- **RF-09** — Um cenário com nome é guardado; o mesmo nome substitui o anterior.
- **RF-10** — Cenário sem nome não é guardado, e simular sem nome não grava nada.
- **RF-11** — Existe a tabela `plan_facts` com nome, rótulo, valor, unidade,
  origem, data de captura e validade.
- **RF-12** — Fato com validade no passado é marcado como **vencido** na tela.
- **RF-13** — A tela obedece à linguagem visual; nenhum número medido aparece
  como literal no código.
