# Brief — 025-financiamentos-na-tela

**Item:** `025-financiamentos-na-tela` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

As duas maiores dívidas do painel moram em arquivo JSON escrito à mão.
`app/debts/ladder.py:93-101` lê `data/manual/financiamento_caixa.json` e
`data/manual/cdc_safra_veiculo.json`, ambos fora do versionamento.

Isso contraria a norma 26 do projeto — *o que só o humano sabe é parâmetro editável na
tela, nunca constante no código* — no lugar em que ela mais importa. O financiamento do
imóvel é a dívida que a escada existe para **não** amortizar antes da reserva: a 0,72%
ao mês ele é o mais barato de todos, e a decisão de não pagá-lo adiantado depende de um
número que hoje só se corrige abrindo um editor de texto.

E o número envelhece. O saldo devedor do imóvel foi lido do aplicativo do banco em
05/09/2026; a cada mês que passa ele é menor, e nada no painel diz que o número está
velho nem oferece onde corrigi-lo.

## Escopo

Os dois financiamentos se editam em `/configuracao`, com os campos que o formato de hoje
já tem: saldo devedor, taxa mensal, prazo em meses e valor da parcela. A leitura passa a
ter uma origem só — o banco de dados —, e a importação dos arquivos existentes acontece
uma vez, sem que nenhum número mude de valor.

## Não-escopo

- **O saldo do CDC do veículo não passa a ser digitado.** Ele continua calculado como
  valor presente das parcelas não vencidas; o que se edita são os ingredientes.
- **A escada não muda de fórmula.** As duas contas de hoje ficam como estão; o que muda
  é de onde vêm os números que elas consomem.
- **Nenhum financiamento novo é cadastrável nesta entrega além dos dois tipos que já
  existem.** Cadastro genérico de contrato é item que ninguém pediu.

## Requisitos

- **RF-01.** Existe entidade de financiamento, guardada no banco, com os campos que os
  dois formatos de hoje usam: taxa mensal, prazo em meses, saldo devedor, valor da
  parcela e data do primeiro vencimento.
- **RF-02.** A migração importa os dois arquivos JSON quando eles existem, e a escada
  reconstruída depois da importação tem **exatamente** os mesmos degraus, com os mesmos
  saldos, taxas e prazos que tinha antes dela.
- **RF-03.** Depois da importação, `app/debts/ladder.py` não lê mais arquivo nenhum de
  `data/manual/`.
- **RF-04.** Numa base sem os arquivos, o painel sobe sem financiamento nenhum e a
  escada continua respondendo — como já acontece hoje.
- **RF-05.** Os campos se editam em `/configuracao`, com a gramática de digitação do
  item `015`: dinheiro na forma `1.234,56`, taxa em por cento ao mês, prazo em inteiro
  de meses.
- **RF-06.** Gravar um financiamento reconstrói a escada na mesma requisição, e a tela
  seguinte já mostra a ordem nova.
- **RF-07.** O saldo do financiamento do veículo continua sendo calculado a cada
  reconstrução, e continua diminuindo sozinho conforme as parcelas vencem.
- **RF-08.** Valor fora da gramática é recusado com a tela de pé e mensagem em
  português — nunca gravado, nunca 500.

## Riscos

- **A importação mudar um número.** É o risco central do item, e RF-02 é o critério que
  o mede: a escada antes e depois tem de ser idêntica, degrau a degrau.
- **A taxa anual do imóvel virar taxa mensal errada.** A conversão já existe no código e
  é aplicada uma vez, na importação. Depois disso o campo é mensal e não se reconverte.
