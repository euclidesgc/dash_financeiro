# PRD 027 — expenses-list-mock-unification

## Valor

Os testes da lista de gastos simulam a API com uma cópia própria da regra que filtra, separa entradas de gastos e ordena os lançamentos — uma cópia diferente da que a simulação padrão usa. Se a regra da simulação padrão mudar (por exemplo, um filtro novo ou outra forma de separar entradas), esses testes seguem verdes com a regra antiga e deixam de provar o que a tela faz. Com uma regra só na simulação, uma mudança nela vale para todos os testes da lista.

## Usuários

Quem mantém o painel, ao mudar filtro, ordenação ou separação de entradas da lista de gastos.

## Requisitos

- **R1** — Os testes da lista de gastos que registram as chamadas feitas à API respondem com a mesma página que a simulação padrão responderia para a mesma chamada.
- **R2** — A regra de filtro, de separação entre entrada, gasto e não-gasto, e de ordenação da lista existe uma vez só na simulação da API.
- **R3** — Nenhum teste deixa de verificar o que verifica hoje, e nenhum teste é pulado ou afrouxado.

## Fora de escopo

- A duplicação entre a simulação e a regra real da API (item 035 do roadmap).
- Mudar a tela da lista de gastos.

## Pontos em aberto

- nenhum
