# Discovery — 019-reclassificacao-a-partir-do-lancamento

**Item do roadmap:** `019-reclassificacao-a-partir-do-lancamento` — a correção de
classificação começa onde o erro aparece: no lançamento aberto em `/gastos`, o
dono escolhe o grupo, cria grupo novo ali mesmo se nenhum servir, e a tela diz
antes de gravar quantos lançamentos e quanto dinheiro a correção alcança.

**Data:** 08/09/2026 · **Trilha declarada:** rápida

## O terreno

Hoje a correção só existe em `/regras`, num vocabulário que não é o de quem olha
o gasto: uma expressão regular sobre o beneficiário, ou o nome cru que a fonte
mandou. Quem vê o erro está em `/gastos`, com o lançamento aberto na frente, e
tem de traduzir o que viu para outra tela e outra linguagem.

O item `023`, concluído, mudou o terreno: a classificação passou a ser uma árvore
de duas alturas — grupo, e dentro dele categoria —, e escolher grupo passou a ser
escolher grupo **e** categoria. Construir esta correção sobre o vocabulário plano
de antes teria sido construí-la duas vezes.

**Medido na base de 05/09/2026:** o resíduo sem regra é **zero** — a tela que
existe para achar classificação faltando afirma que não falta nada — enquanto
**244 lançamentos e R$ 16.556,28**, 7,6% do gasto, estão no grupo de escape
`Outros` por regra explícita, com `mercadolivre` partido em três beneficiários
distintos que somam R$ 1.679,53.

## Regra, exemplo e pergunta

- **Regra.** A correção começa no lançamento, em `/gastos`, e não numa tela à
  parte.
- **Regra.** A tela diz **antes de gravar** quantos lançamentos e quanto dinheiro
  a correção alcança — os do mesmo beneficiário e os da mesma categoria de origem.
- **Regra.** A correção vira **regra**, nunca exceção de uma linha. `classify_all`
  recalcula a base inteira a cada sincronização, então uma marca presa a um
  lançamento é apagada na carga seguinte, em silêncio.
- **Regra.** Escolher grupo arrasta natureza e essencialidade junto, porque uma
  regra atribui os três de uma vez e nenhum deles aceita nulo.
- **Exemplo.** O dono abre um lançamento do `mercadolivre` que caiu em `Outros`,
  escolhe `Pessoal`, e a tela diz: isto alcança 41 lançamentos e R$ 1.679,53.
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
| A correção grava regra ou marca o lançamento? | **Regra, sempre.** | Marca presa a um lançamento é apagada pela reclassificação da carga seguinte, em silêncio — o painel voltaria a mentir sem que ninguém tivesse desfeito nada. |
| Sobre o quê a regra casa? | **Sobre o beneficiário do lançamento aberto**, que é o que o dono reconhece; a tela mostra também o alcance pela categoria de origem, para ele ver os dois números antes de escolher. | Casar pela categoria crua da fonte usa o vocabulário que o item `023` acabou de tirar do caminho. |
| A prévia é estimativa ou contagem? | **Contagem exata**, feita na mesma consulta que a gravação vai usar. | Estimativa que erra é pior que prévia nenhuma: ela convida a gravar. |
| Criar grupo novo ali mesmo? | **Sim**, com a mesma tela e sem sair do lançamento — mas a categoria continua vindo da árvore do `023`. | Obrigar a ir a outra tela para criar o grupo devolve o dono ao problema que o item existe para resolver. |
| A escrita entra na mesma transação da reclassificação? | **Sim.** É o que `app/taxonomy/rules.py` já faz, e o item `012` fechou o "sucesso mentiroso" que a alternativa produz. | Duas transações deixam a base metade reclassificada, somando e mentindo. |
| A tela de regras deixa de existir? | **Não.** Ela continua sendo onde se vê e edita o conjunto inteiro. | Este item acrescenta a porta que faltava, não fecha a que existe. |
