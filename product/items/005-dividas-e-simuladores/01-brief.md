# Brief — 005-dividas-e-simuladores

Escrito no presente. Cada requisito é `RF-nn`.

## A escada

- **RF-01** — Existe a tabela `debts`, com nome, tipo, saldo em centavos, taxa
  mensal, prazo restante, parcela e a origem de cada linha.
- **RF-02** — A carga cria um degrau por **conta bancária com saldo negativo**
  (tipo `overdraft`) e um por **cartão com saldo negativo** (tipo `card`), a
  partir de `accounts`. Na base de 05/09/2026 são 2 e 4, somando
  **R$ 11.190,18** e **R$ 16.744,62**.
- **RF-03** — A carga cria o degrau do **financiamento imobiliário** a partir de
  `data/manual/financiamento_caixa.json`: saldo **R$ 238.585,18**, 370 meses, e
  taxa mensal derivada de `(1 + 8,9899%)^(1/12) − 1` = **0,7200% a.m.**
- **RF-04** — A carga cria o degrau do **CDC do veículo** a partir de
  `data/manual/cdc_safra_veiculo.json`, com saldo igual ao **valor presente das
  parcelas ainda não vencidas**, descontadas à taxa do contrato: 45 parcelas de
  R$ 1.235,33 a 1,63% a.m. dão **R$ 39.176,36**. É o que a lei manda o banco
  oferecer na quitação antecipada.
- **RF-05** — Se um dos arquivos de `data/manual/` não existir, a carga segue sem
  o degrau correspondente e sem erro: o painel roda numa máquina que não tem os
  contratos.
- **RF-06** — A escada ordena por **taxa mensal decrescente**. Com as quatro
  taxas conhecidas, a ordem é cheque especial → cartões → CDC → imóvel.
- **RF-07** — A tela mostra, em cada degrau, o saldo, a taxa mensal e **quanto de
  juros aquele degrau custa por mês**.

## A taxa que ninguém sabe

- **RF-08** — Degrau sem taxa **não entra na escada**. Ele aparece num bloco
  próprio, que diz que falta a taxa e que sem ela não dá para saber onde o
  próximo real rende mais.
- **RF-09** — Na base de 05/09/2026, com os arquivos de contrato presentes, os
  **seis** degraus de conta e cartão nascem sem taxa, e os dois de contrato
  nascem com taxa.
- **RF-10** — A taxa se edita na tela, em ponto percentual mensal com duas casas,
  e a escada se reordena **na resposta da mesma requisição**, sem reingestão e
  sem reiniciar o processo.
- **RF-11** — Taxa negativa, acima de 100% a.m., ou ilegível é recusada com
  mensagem que nomeia o valor inválido, e nada é gravado.
- **RF-12** — A taxa é apagável: limpar o campo devolve o degrau ao bloco dos sem
  taxa.
- **RF-13** — Nenhuma taxa aparece como literal no código. As duas de contrato
  vêm do arquivo; as outras, da tela.

## O simulador

- **RF-14** — O simulador recebe um degrau e um aporte, e devolve **quantas
  parcelas somem** e **quantos juros deixam de ser pagos**.
- **RF-15** — Para um degrau com prazo e parcela, as parcelas eliminadas são as
  do fim do cronograma, calculadas pelo valor presente — não estimadas por
  divisão.
- **RF-16** — Aporte maior ou igual ao saldo **quita** o degrau: todas as
  parcelas somem e o excedente volta como sobra, nunca como parcela negativa.
- **RF-17** — Degrau **sem prazo** — cheque especial e cartão — não tem parcela a
  eliminar. O simulador devolve os **juros mensais evitados**, que é
  `aporte × taxa`, limitado ao saldo.
- **RF-18** — Aporte zero ou negativo é recusado com mensagem, e nada é
  simulado.
- **RF-19** — O simulador é função determinística e testada. Nenhuma parte dele
  passa por IA.

## O Duster

- **RF-20** — A tela traz dois campos editáveis que começam vazios: **saldo de
  quitação antecipada** do CDC e **custo mensal de transporte sem o carro**.
- **RF-21** — Com os dois vazios, a tela mostra o que já dá para afirmar: o saldo
  do CDC, a taxa de 1,63% a.m., o custo de juros do mês e a parcela de
  **R$ 1.235,33** como fluxo mensal preso.
- **RF-22** — Preenchido o saldo de quitação, a tela mostra a diferença entre ele
  e o valor presente — o desconto da quitação — e o mantém entre requisições.

## A tela

- **RF-23** — `GET /dividas` serve a tela, atrás da sessão como toda rota.
- **RF-24** — A tela obedece à linguagem visual: cor e espaço só de
  `tokens.css`, foco visível, sem rolagem horizontal do corpo de 375 a 1440, e
  `prefers-reduced-motion` respeitado.
- **RF-25** — Estado vazio acionável: base sem dívida nenhuma diz o que fazer.
- **RF-26** — O Resumo leva à tela de Dívidas.
- **RF-27** — Nenhum número medido nesta base aparece como literal no código.
