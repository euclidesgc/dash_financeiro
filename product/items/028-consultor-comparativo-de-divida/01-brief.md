# Brief — 028-consultor-comparativo-de-divida

**Item:** `028-consultor-comparativo-de-divida` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

A pergunta que decide mais dinheiro na vida do dono deste painel é: **fico no
cheque especial ou pego um empréstimo, e qual proposta quita tudo mais barato?**
Ela não tem resposta aqui.

`/consultor` explica o número e pergunta o fato que falta, mas não compara
caminhos de dívida. A escada de `/dividas` ordena por taxa mensal — o que
responde "onde o próximo real rende mais", e não "quanto custa cada caminho até
zerar". Taxa maior não é sempre pior: um empréstimo a 2,1% em 48 meses pode custar
mais que um cheque especial a 4,22% quitado em oito, e é a soma até zerar que diz
qual, não a comparação de duas porcentagens.

Até agora a comparação nem era possível. As taxas que ela exige passaram a existir
nesta rodada: o item `024` deu ao cartão taxa mensal com uma casa só, e o `025`
tirou os dois financiamentos do arquivo escrito à mão. Antes deles, a comparação
responderia com confiança um número que não mediu.

**E falta a outra metade dos dados:** nenhuma proposta de empréstimo está na base.
Sem uma forma de informá-las, não há o que comparar contra o que já foi medido.

## Escopo

O painel compara caminhos de dívida por **custo total até zerar**, em código
determinístico, e o consultor lê o resultado e explica a escolha. O dono informa
as propostas de empréstimo na tela, com os campos que um banco oferece: taxa
mensal, prazo, valor liberado e custo de contratação.

## Não-escopo

- **A IA não calcula.** Ela recebe o resultado pronto e explica. É a norma 23, e
  ela não se reabre.
- **Nenhuma recomendação automática de contratar.** A comparação mostra os
  números; a decisão é do dono.
- **Nenhuma simulação de renegociação parcial** ou de portabilidade. Comparar os
  caminhos que existem já é o item.
- **A escada de `/dividas` não muda.** Ela responde outra pergunta e continua
  respondendo.

## Requisitos

- **RF-01.** Existe entidade de proposta de empréstimo, guardada no banco, com
  taxa mensal, prazo em meses, valor liberado e custo de contratação, editável em
  `/configuracao` como as demais entidades do dono.
- **RF-02.** Existe função determinística e testada que devolve o **custo total
  até zerar** de um caminho de dívida, em centavos, somando juros e custo de
  contratação. Nenhum número da comparação vem do modelo.
- **RF-03.** A comparação mostra, lado a lado, o custo total de continuar como
  está e o de cada proposta informada, com a diferença entre eles nomeada.
- **RF-04.** Proposta sem taxa **não entra** na comparação, e a tela diz quantas
  ficaram de fora e por quê — a mesma regra que a escada já aplica a degrau sem
  taxa.
- **RF-05.** O consultor explica o resultado citando **apenas** números que
  aparecem literalmente no contexto que ele recebe, dígito a dígito.
- **RF-06.** Sem chave de IA, a comparação aparece igual, com todos os números, e
  a tela diz que a leitura em prosa está indisponível.
- **RF-07.** Valor fora da gramática de digitação é recusado com a tela de pé e
  mensagem em português — nunca gravado, nunca 500.
- **RF-08.** Nenhum número existente muda: a escada, o objetivo e o comprometido
  continuam com os mesmos totais.

## Riscos

- **A IA citar um número que ela mesma compôs.** É o risco que a norma 23 existe
  para impedir, e RF-05 é o que se verifica — não por leitura, mas conferindo que
  toda cifra da resposta aparece no contexto.
- **A comparação parecer conselho.** A tela mostra custo, não recomendação de
  contratar. O texto precisa deixar isso claro sem depender da IA para dizê-lo.
- **Propostas envelhecerem em silêncio.** Uma proposta de banco vale por dias.
  Sem data, o painel compara contra um número que já não existe.
