# Brief — 022-mes-corrente-como-abertura-padrao

**Item:** `022-mes-corrente-como-abertura-padrao` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

Duas coisas, e as duas são a mesma: **`/gastos` não responde pelo presente.**

**A tela abre no passado.** `app/queries/period.py:41-47` devolve seis meses fechados,
terminando no último dia do mês anterior. O mês em curso **nunca** aparece na abertura.
A decisão é deliberada e a razão está escrita no código: o mês em curso abriria a tela
sobre um punhado de dias. O preço dela, medido na base de 05/09/2026: a janela de hoje
mostra 732 lançamentos e R$ 103.772,33 — meio ano de história — quando a pergunta que
muda uma decisão é "como está indo este mês".

**A tela é a única que descarta a data pedida.** `app/routers/spending.py:98` chama
`default_period(screen_date(None).date)`. O `None` ali é literal: `/gastos` chama o
leitor único que o `016` construiu e **joga fora o `?data=` que o dono digitou**. As
outras cinco telas do painel respondem pela data pedida; `/gastos` responde sempre pela
data de referência do processo. Duas telas abertas lado a lado com a mesma URL de data
discordam sobre qual dia é hoje, e a que discorda é a que decide onde cortar gasto.

## Escopo

`/gastos` abre no mês corrente — do dia 01 até a data de referência da tela — e responde
pela data pedida em `?data=`, com os mesmos três estados que as outras cinco telas já
têm: sem pedido, pedido aceito, pedido recusado. Escolher outro período continua sendo
do dono.

Junto, as duas consequências que a troca expõe deixam de ser silenciosas: o que já está
postado no mês depois da data de referência é **nomeado** na tela em vez de sumir, e a
"média mensal" só se chama média mensal quando a janela cobre meses inteiros.

## Não-escopo

- **`app/plan/objective.py` não passa a consumir a janela da tela.** Ele monta a própria
  e continua montando: a reserva alvo é propriedade da base, não da navegação.
- **A janela não termina no fim do mês.** A tela responde "quanto saiu", não "quanto vai
  sair" — o comprometido é que responde a segunda, e já responde.
- **Nenhuma outra tela muda de janela padrão.**

## Requisitos

- **RF-01.** A janela padrão de `/gastos` vai do dia 01 do mês da data de referência da
  tela até a própria data de referência, inclusive.
- **RF-02.** `/gastos` lê `?data=` pelo leitor único (`app/routers/reference.py`), e a
  janela padrão sai da data que esse leitor devolve.
- **RF-03.** Quando a data pedida é recusada, `/gastos` responde pela data de referência
  do processo e **diz** que recusou, com o mesmo texto de recusa das outras telas.
- **RF-04.** Quando não há `?data=`, `/gastos` responde pela data de referência do
  processo e não acusa recusa nenhuma.
- **RF-05.** `inicio` e `fim` explícitos continuam vencendo o padrão, e período
  inválido continua caindo no padrão em vez de derrubar a tela.
- **RF-06.** Quando existem lançamentos do mês corrente datados **depois** da data de
  referência, a tela informa quantos são e quanto somam. Eles não entram em nenhum
  total da janela.
- **RF-07.** O rótulo do valor por cruzamento é "média mensal" apenas quando a janela
  começa no dia 01 de um mês e termina no último dia de um mês. Fora disso o rótulo é
  "no período" e o número é o total do período, sem divisão.
- **RF-08.** Nenhum total muda para uma janela que já cobria meses inteiros: os números
  congelados de `docs/plano.md` medidos sobre seis meses fechados continuam iguais.

## Riscos

- **A abertura sobre poucos dias parece uma tela vazia.** É o efeito pretendido e o
  preço declarado do item; a linha do RF-06 e o rótulo do RF-07 são o que impedem que
  ela seja lida como perda de dado.
- **Testes existentes assumem a janela de seis meses fechados.** Os que afirmam a
  abertura mudam junto; os que passam `inicio` e `fim` explícitos não são tocados —
  e se algum passar sem mudar nada, a mudança não alcançou a abertura.
