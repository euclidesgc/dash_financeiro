# Brief — 021-mascara-e-medida-dos-campos

**Item:** `021-mascara-e-medida-dos-campos` · **Trilha:** rápida

> Este documento funde PRD e spec.

## Problema

**Nenhum dos 26 campos de digitação deste painel declara o que aceita.** A
contagem de `maxlength`, `pattern`, `minlength` e `required` em todos os
templates é **zero**. O que existe, no máximo, é dica de teclado e texto de
exemplo — dica, não regra.

O efeito é duplo. O dono descobre o limite **depois** de digitar, por uma recusa
que ele tem de decifrar; e a largura não diz nada sobre o conteúdo, então o campo
de aporte, de no máximo 12 algarismos, e a pergunta livre ao consultor, de 500
caracteres, ocupam a mesma medida na tela.

O item `015` fechou metade do laço: a **leitura** ficou estrita, e `5000.00`
deixou de virar R$ 500.000,00 em silêncio no campo que decide a venda do carro.
Falta a outra metade: a **digitação** produzir o que o leitor aceita.

E a varredura desta corrida encontrou três frestas na própria gramática: dígito
não-ASCII é aceito num campo de dinheiro; taxa de exatamente 100% ao mês passa
num financiamento imobiliário; e bytes crus viram nome ilegível num campo que é
chave de gravação, deixando a linha impossível de sobrescrever.

## Escopo

Todo campo de digitação declara ao navegador o que aceita — teto de comprimento,
modo de teclado, obrigatoriedade — e tem largura proporcional ao que guarda. A
gramática do servidor fecha as três frestas medidas. O teto é o mesmo dos dois
lados, e a autorização continua sendo do servidor.

## Não-escopo

- **Nenhuma máscara ao digitar**, e nenhum arquivo JavaScript próprio. A decisão
  e a alternativa descartada estão em `00-discovery.md`.
- **Nenhuma regra nova de folha de estilo.** A largura sai dos tokens de medida
  do item `017`.
- **Nenhuma mudança no que a gramática aceita além das três frestas nomeadas.**

## Requisitos

- **RF-01.** Todo campo de digitação de dinheiro, taxa e prazo declara teto de
  comprimento e modo de teclado coerentes com o que o leitor do servidor aceita.
- **RF-02.** Todo campo de texto livre declara teto de comprimento, e o servidor
  recusa acima dele: apelido de beneficiário, nome de cenário, expressão da regra
  e nome de proposta — os que hoje não têm teto nenhum.
- **RF-03.** O teto declarado no campo e o teto cobrado pelo servidor são **o
  mesmo número**, e existe um lugar só onde ele está escrito.
- **RF-04.** A largura de cada campo é proporcional ao que ele guarda, usando os
  tokens de medida existentes — nenhuma regra nova de estilo.
- **RF-05.** A gramática de dinheiro aceita **apenas dígito ASCII**. Dígito
  arábico-índico e de largura cheia são recusados com mensagem em português.
- **RF-06.** O financiamento tem teto de taxa próprio, coerente com o tipo de
  dívida, e o leitor genérico mantém o dele.
- **RF-07.** Nome que chega com bytes ilegíveis é recusado, e não gravado como
  texto impossível de redigitar.
- **RF-08.** Nenhuma tela deixa de aceitar valor que hoje ela aceita
  legitimamente — em especial prazo de 420 meses e valor de 12 algarismos.

## Riscos

- **Passar a recusar o que era legítimo.** É o risco central, e RF-08 é o que o
  mede: os valores reais do dono continuam entrando.
- **O teto do cliente e o do servidor divergirem.** RF-03 é o que impede, e a
  verificação é estrutural: um lugar só onde o número está escrito.
