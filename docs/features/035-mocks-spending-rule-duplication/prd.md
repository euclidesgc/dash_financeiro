# PRD 035 — mocks-spending-rule-duplication

## Valor

Os testes de tela rodam contra uma API simulada que decide sozinha o que é gasto, o que é entrada e o que foi marcado como "não é gasto". Essa decisão é uma cópia da regra da API real. Se a regra da API mudar, os testes de tela continuam verdes com a regra antiga, e o painel pode passar a mostrar números que nenhum teste de tela conferiu. Com a entrega, as duas regras respondem a uma mesma tabela de casos, e qualquer divergência deixa um teste vermelho do lado que ficou para trás.

## Usuários

Quem mantém o painel: quem muda a regra de gasto e entrada na API, e quem escreve testes de tela confiando que a API simulada separa os lançamentos como a real.

## Requisitos

- **R1** — Existe uma única tabela de casos de separação (valor do lançamento e motivo de "não é gasto", com a lista em que ele aparece: gastos, entradas, não é gasto ou nenhuma), lida pelos testes da API e pelos testes da API simulada.
- **R2** — A API real passa em todos os casos da tabela; um lançamento de transferência entre contas próprias ou de estorno não aparece em lista nenhuma.
- **R3** — A API simulada passa em todos os casos da tabela, e o resultado do período dela (entradas, gastos e saldo) sai da mesma separação.
- **R4** — Mudar a regra da API sem atualizar a tabela deixa um teste da API vermelho; atualizar a tabela sem mudar a API simulada deixa um teste de tela vermelho.
- **R5** — O que a tela mostra não muda; nenhum teste é pulado ou afrouxado.

## Fora de escopo

- Gerar a API simulada a partir da API real.
- As demais regras da API simulada (categorias, busca, ordenação, sinal do mês).

## Pontos em aberto

- nenhum
