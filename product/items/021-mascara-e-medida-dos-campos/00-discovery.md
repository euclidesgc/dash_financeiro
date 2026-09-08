# Discovery — 021-mascara-e-medida-dos-campos

**Item do roadmap:** todo campo de digitação declara o que aceita e cabe no que
aceita: campo de dinheiro chega ao servidor já na forma que o leitor único exige,
campo de texto tem teto de comprimento, e a largura de cada um é proporcional ao
que ele guarda.

**Data:** 08/09/2026 · **Trilha declarada:** rápida

## O terreno, medido hoje

**26 campos de digitação** vivem nos templates, e **nenhum deles** tem
`maxlength`, `pattern`, `minlength` ou `required` — a contagem é zero, medida por
varredura. O que existe, no máximo, é dica de teclado e texto de exemplo.

O item é de varredura, e por isso veio depois do que ele varre: os campos de
cartão, financiamento, configuração da IA e proposta de empréstimo nasceram nesta
mesma corrida e entram na conta.

**Três achados dos validadores desta corrida pertencem a este item:**

- A gramática de dinheiro **aceita dígito não-ASCII** — arábico-índico e de
  largura cheia são lidos e gravados corretamente, porque a classe de dígito da
  expressão regular casa todo decimal Unicode. O número sai certo; o que
  surpreende é a aceitação.
- Uma **taxa de exatamente 100% ao mês** passa num financiamento imobiliário.
  Está dentro do teto que a própria mensagem anuncia, e é absurdo financeiro para
  aquele tipo de dívida.
- **Bytes crus viram nome ilegível** no campo de nome da proposta, e como o nome
  é a chave de gravação, o dono não consegue sobrescrever a linha redigitando.

## Regra, exemplo e pergunta

- **Regra.** Todo campo declara ao navegador o que aceita: teto de comprimento,
  modo de teclado, obrigatoriedade.
- **Regra.** A largura de cada campo é proporcional ao que ele guarda.
- **Regra.** A digitação produz o que o leitor aceita, em vez de devolver uma
  recusa que o dono tem de decifrar.
- **Exemplo.** O campo de aporte, de no máximo 12 algarismos, e a pergunta livre
  ao consultor, de 500 caracteres, hoje têm a mesma medida na tela.
- **Pergunta que o discovery fecha:** máscara ao digitar exige o primeiro arquivo
  JavaScript próprio do projeto. Resolvida abaixo.

## Os quatro gatilhos de trilha completa

Nenhum dispara: sem contrato público, sem segunda frente de stack, sem dado
pessoal novo, e o requisito é de forma, não de cálculo. **Trilha rápida.**

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Máscara ao digitar, ao sair do campo, ou nenhuma? | **Nenhuma máscara.** O campo declara teto, modo de teclado, obrigatoriedade e largura; a formatação continua sendo do servidor, que já é a única casa da gramática. | Máscara ao digitar exige o primeiro arquivo JavaScript próprio do projeto, que hoje só tem duas bibliotecas por CDN e um bloco embutido. É dívida nova para resolver um problema que o teto e a dica de teclado já reduzem — e máscara que formata para uma forma que o leitor recusa é pior que máscara nenhuma. |
| O teto do campo é declarado onde? | **Nos dois lados**, com o mesmo número: no atributo do campo e no leitor do servidor. Autorização é do servidor; o atributo é experiência de uso (norma 13). | Só no cliente é enfeite: um POST à mão passa por cima. |
| A largura sai de onde? | **Dos tokens de medida que o item `017` criou**, não de número novo. | Número novo na folha de estilo é a quarta escala de medida do projeto. |
| Dígito não-ASCII continua aceito? | **Não.** A gramática passa a ler só dígito ASCII, num lugar só. | Aceitar é surpreendente, e a surpresa mora no campo que decide dinheiro. |
| O teto de taxa continua em 100% ao mês? | **Sim, no leitor genérico** — mas o financiamento passa a ter teto próprio, coerente com o tipo de dívida. | Um teto só para cheque especial e imóvel deixa passar absurdo em um dos dois. |
| Campo de texto ganha teto onde não tinha? | **Sim**, nos três que hoje não têm: apelido de beneficiário, nome de cenário e expressão da regra. O único teto do projeto era o da pergunta ao consultor. | Texto sem teto é o caminho mais curto para um `INSERT` que não cabe. |
