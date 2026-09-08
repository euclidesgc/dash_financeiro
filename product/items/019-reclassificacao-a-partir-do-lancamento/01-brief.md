# Brief — 019-reclassificacao-a-partir-do-lancamento

**Item:** `019-reclassificacao-a-partir-do-lancamento` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

A correção de classificação está na tela errada e na língua errada.

Quem vê o erro está em `/gastos`, com o lançamento aberto na frente: um débito de
R$ 89,90 que caiu em `Outros` e claramente é assinatura. Para corrigir, ele
precisa sair dali, abrir `/regras`, e traduzir o que viu para outro vocabulário —
uma expressão regular sobre o beneficiário, ou o nome cru que a fonte mandou.
Entre ver o erro e corrigi-lo há uma tradução, e é nela que a correção morre.

**O tamanho disso está medido na base de 05/09/2026, e o número é constrangedor
justamente porque a tela diz o contrário:** o resíduo sem regra é **zero** — a
tela que existe para achar classificação faltando afirma que não falta nada —
enquanto **244 lançamentos e R$ 16.556,28**, 7,6% do gasto, estão no grupo de
escape `Outros` por regra explícita. O `mercadolivre` aparece partido em três
beneficiários distintos que somam R$ 1.679,53.

Uma classificação errada não é detalhe estético neste painel: é o par natureza ×
essencialidade que monta a lista de corte, e é a lista de corte que responde onde
cortar sem virar monge.

## Escopo

A correção começa no lançamento aberto em `/gastos`: o dono escolhe o grupo,
cria grupo novo ali mesmo se nenhum servir, e a tela diz **antes de gravar**
quantos lançamentos e quanto dinheiro a correção alcança — os do mesmo
beneficiário e os da mesma categoria de origem. A correção vira regra, entra na
mesma transação da reclassificação, e a tela seguinte já mostra os totais novos.

## Não-escopo

- **`/regras` continua existindo**, e continua sendo onde se vê e edita o conjunto
  inteiro de regras. Este item acrescenta a porta que faltava.
- **Nenhuma regra nova é escrita para encolher o escape.** Encolher os 244
  lançamentos é o dono usando a porta nova, não o item pré-classificando por ele.
- **A árvore de categorias não muda.** Ela veio do item `023` e é consumida como
  está.
- **Nenhuma marca presa a um lançamento.** A correção é regra, sempre.

## Requisitos

- **RF-01.** No lançamento aberto em `/gastos`, o dono escolhe grupo e categoria
  da árvore, e a natureza e a essencialidade que vão junto.
- **RF-02.** Antes de gravar, a tela informa **quantos lançamentos e quanto
  dinheiro** a correção alcança pelo beneficiário do lançamento, e quantos pela
  categoria de origem. Os dois números são contagem exata, não estimativa.
- **RF-03.** A correção grava uma **regra**, e a reclassificação da base inteira
  acontece na mesma transação da escrita.
- **RF-04.** O dono cria grupo novo sem sair do lançamento, e o grupo novo passa a
  existir na árvore como qualquer outro.
- **RF-05.** Corrigir de novo o mesmo beneficiário **atualiza** a regra existente
  em vez de criar uma segunda que compete com ela.
- **RF-06.** Depois de gravar, a tela mostra quantos lançamentos mudaram de fato —
  e esse número pode ser menor que a prévia, quando outra regra já pegava parte
  deles.
- **RF-07.** Escolha inválida — grupo que não existe, categoria fora do grupo,
  beneficiário desconhecido — é recusada com a tela de pé e mensagem em português,
  nunca gravada e nunca 500.
- **RF-08.** Nenhum total de gasto muda por causa da tela: o que muda os números é
  a regra gravada, e só ela.

## Riscos

- **A prévia discordar do resultado.** É o risco central, e RF-06 é o que o trata:
  a diferença é legítima e a tela a nomeia em vez de escondê-la.
- **Duas regras competindo pelo mesmo beneficiário.** RF-05 é o que impede, e a
  verificação é comportamental: corrigir duas vezes deixa uma regra, não duas.
- **A correção parecer não ter funcionado** quando outra regra de precedência
  maior continua pegando o lançamento. A tela precisa dizer isso, não silenciar.
