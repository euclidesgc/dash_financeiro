# PRD 054 — expenses-opens-current-month

## Valor

O painel existe para responder "estou dentro do plano este mês?". Hoje a página "Gastos" abre em "Todo o período", e nesse modo o resultado do período (entradas, gastos e saldo) e o teto do mês não aparecem: quem abre a página vê uma lista de todos os lançamentos e precisa descobrir que tem de escolher um mês para ver o número que importa. Quando escolhe, o resultado e o teto aparecem abaixo de uma barra de filtros com cinco controles, fora da primeira dobra no celular. Abrindo no mês corrente, com o resultado e o teto no topo, a resposta aparece sem nenhum clique.

## Usuários

O dono do painel, ao abrir "Gastos" para saber como está o mês.

## Requisitos

- **R1** — Ao abrir "Gastos" sem período escolhido (pelo cabeçalho ou pelo endereço sem período), a página mostra o mês corrente: o texto do mês diz o mês de hoje ("setembro de 2026"), a lista traz só os lançamentos dele, e o resultado do período e o teto do mês aparecem.
- **R2** — O resultado do período e o teto do mês ficam antes dos filtros (busca, conta, mês e datas, ordenação e visão); o total por categoria e a lista continuam depois dos filtros.
- **R3** — O resultado do período diz a que período se refere (o nome do mês ou as datas do intervalo), já que o seletor de mês agora fica abaixo dele.
- **R4** — "Todo o período" continua disponível: o botão mostra todos os lançamentos, fica desabilitado enquanto ele é o período mostrado, e a escolha sobrevive a recarregar a página e a trocar busca, conta, ordenação, visão ou página.
- **R5** — Mês escolhido, intervalo de datas e endereços já usados com `month`, `from` e `to` continuam funcionando como antes.

## Fora de escopo

- Lembrar o último período escolhido entre visitas.
- O foco automático do formulário do teto quando o mês não tem teto (item 064 do roadmap).
- Mudar o que o resultado e o teto calculam.

## Pontos em aberto

- nenhum
