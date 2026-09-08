# Brief — 024-cartoes-como-entidade

**Item:** `024-cartoes-como-entidade` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

**Não existe cartão de crédito no modelo deste painel.** Existe conta cujo tipo é
`CREDIT`: `accounts` (`app/migrations/sql/001_schema.sql:17-25`) guarda identificador,
nome, tipo, subtipo, instituição e saldo, e mais nada. Limite, taxa, dia de fechamento
e dia de vencimento — as quatro coisas que decidem o que um cartão custa e quando ele
cobra — não têm onde morar.

A taxa mora em `debts.monthly_rate_bp`, por dívida e não por conta, e um cartão entra na
escada com taxa nula (`app/debts/ladder.py:83`). Degrau sem taxa não entra na escada
(`app/debts/ladder.py:174-183`), e a tela diz quantos ficaram de fora. O item `014`
registrou por que a taxa do cartão não pode ser derivada: o saldo de um cartão é fatura,
fatura paga inteira não cobra juro, e derivar dos encargos daria 0,06% ao mês — um
número falso que pareceria medido.

A consequência está medida no roadmap desde o item `005`: **R$ 16.744,62 de cartão ficam
fora da escada de dívida**, e o marco "dívidas caras zeradas" do objetivo é calculado
sem eles. O painel ordena onde o próximo real rende mais ignorando a dívida que
provavelmente é a mais cara de todas.

## Escopo

O cartão passa a ser entidade do painel, com limite, taxa mensal, dia de fechamento e
dia de vencimento informados pelo dono em `/configuracao`. Os cartões da base nascem
cadastrados com os campos vazios. Informada a taxa, o cartão entra na escada de dívida
na posição que a taxa dele determina.

## Não-escopo

- **A curva da fatura mês a mês é o item `026`.** Aqui fechamento e vencimento são
  guardados, não usados para projetar.
- **Nenhuma taxa é sugerida para cartão.** O `014` já decidiu isso e a decisão não
  se reabre.
- **`accounts` não ganha coluna.** É espelho da fonte, reescrito a cada carga.

## Requisitos

- **RF-01.** Existe entidade de cartão com limite em centavos, taxa mensal, dia de
  fechamento e dia de vencimento, todos opcionais e todos editáveis.
- **RF-02.** Toda conta de crédito da base tem cartão correspondente, com os quatro
  campos vazios enquanto o dono não os informar. Conta de crédito que apareça numa
  sincronização posterior também ganha o seu.
- **RF-03.** A entidade de cartão sobrevive à sincronização: uma carga nova não apaga
  nem sobrescreve o que o dono informou.
- **RF-04.** Os quatro campos se editam em `/configuracao`, com a mesma gramática de
  digitação do item `015`: dinheiro na forma `1.234,56`, taxa em por cento ao mês, dia
  como inteiro de 1 a 31.
- **RF-05.** Valor fora da gramática é recusado com a tela de pé e mensagem em português
  que diz a forma aceita — nunca gravado, nunca 500.
- **RF-06.** A taxa mensal do cartão tem **uma** casa. A escada de dívida a lê de lá, e
  o campo de taxa de `/dividas` para um degrau de cartão escreve na mesma casa.
- **RF-07.** Com a taxa informada, o cartão entra na escada ordenado pela taxa e sai da
  lista de dívidas sem taxa. Sem a taxa, nada muda em relação a hoje.
- **RF-08.** Reconstruir a escada não perde nenhum dos quatro campos.

## Riscos

- **A escada muda de números assim que uma taxa entra.** É o efeito pretendido — os
  R$ 16.744,62 param de ficar de fora —, e por isso os testes que afirmam a escada de
  hoje precisam continuar valendo para a base **sem** taxa informada.
- **Duas casas para a taxa.** É o defeito que o `015` fechou e que este item pode
  reintroduzir. RF-06 é o que se verifica, e a verificação é estrutural: só uma tabela
  guarda taxa de cartão.
