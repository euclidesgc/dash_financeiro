# Discovery — 028-consultor-comparativo-de-divida

**Item do roadmap:** `028-consultor-comparativo-de-divida` — o consultor responde à
pergunta que decide dinheiro: **é melhor ficar no cheque especial ou pegar um
empréstimo, e qual proposta quita tudo mais barato**.

**Data:** 08/09/2026 · **Trilha declarada:** rápida

## O terreno

Hoje `/consultor` explica o número e pergunta o fato que falta, mas não compara
caminhos de dívida. As taxas que a comparação exige passaram a existir agora: o
item `024` deu ao cartão limite e taxa mensal com uma casa só, e o `025` tirou os
dois financiamentos do arquivo escrito à mão e os pôs numa tabela editável na
tela. Antes dos dois, a comparação responderia com confiança um número que não
mediu.

**A restrição que desenha o item é a norma 23: quem calcula é função testada,
nunca o modelo.** Se ele computasse "esse empréstimo te economiza R$ 3.400" e
errasse por um ponto percentual, o erro cairia na unidade central do produto e
destruiria a confiança em tudo o mais.

**A consequência prática:** nenhuma proposta de empréstimo está nos dados de
hoje. O item precisa de uma forma de **informar propostas** — taxa, prazo, valor
liberado, custo de contratação — para ter o que comparar contra o cheque especial
já medido.

## Regra, exemplo e pergunta

- **Regra.** A comparação é código determinístico: custo total de cada caminho,
  mês a mês, até zerar. O modelo lê o resultado e explica a escolha.
- **Regra.** O dono informa as propostas na tela, com os quatro campos que um
  banco oferece: taxa mensal, prazo, valor liberado e custo de contratação.
- **Regra.** O painel não recomenda o que não mediu: proposta sem taxa não entra
  na comparação, e a tela diz por quê.
- **Exemplo.** Com o cheque especial do `itau` a 4,22% ao mês e uma proposta de
  empréstimo a 2,1% em 24 meses, a comparação mostra quanto cada caminho custa até
  zerar, e o modelo explica qual e por quê — citando só números que a tabela traz.
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
| Quem calcula? | **Função testada, sempre.** O modelo recebe o resultado pronto e explica. | A norma 23 existe porque um número errado na unidade central deste produto destrói a confiança em tudo o mais. Não se reabre. |
| Onde as propostas se informam? | **Em `/configuracao`**, junto do resto do que só o humano sabe, na forma que os itens `024` e `025` já estabeleceram para entidade editável. | Tela nova para uma entidade que é exatamente do mesmo tipo das duas que acabaram de nascer. |
| O que é "mais barato"? | **Custo total até zerar**, em centavos, somando juros e custo de contratação. | Comparar só a taxa mensal ignora prazo e tarifa, e é assim que uma proposta pior parece melhor. |
| Proposta sem taxa entra? | **Não**, e a tela diz que ficou de fora — mesma regra que a escada de dívida já aplica a degrau sem taxa. | Estimar a taxa que falta é o painel decidindo o que não sabe. |
| O que o modelo pode dizer? | Só número que aparece literalmente no contexto que ele recebe, dígito a dígito — a regra que o item `009` já impõe. | — |
| E sem chave de IA? | A comparação aparece igual, com os números; o que falta é a leitura em prosa, e a tela diz isso. | O cálculo não pode depender da IA, por construção. |
