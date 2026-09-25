# PRD 005 — filtrar por período

## Valor

O dono do painel isola os gastos de um mês (ou de um intervalo de datas) para saber quanto saiu naquele período, sem ter que ler a lista inteira.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", já vendo a lista paginada e ordenável, querendo restringi-la a um período antes de olhar o total ou os lançamentos.

## Requisitos

- **R1** — Na página "Gastos", o usuário vê um seletor de mês com um nome de mês/ano, um botão "Mês anterior", um botão "Próximo mês" e a opção "Todo o período".
- **R2** — Por padrão, ao abrir a página sem período escolhido, a lista mostra o mês corrente, onde o resultado do período e o teto do mês aparecem; "Todo o período" mostra todos os lançamentos e fica no endereço da página.
- **R3** — Escolhendo um mês, o usuário vê só os gastos daquele mês inteiro (do dia 1 ao último dia).
- **R4** — "Mês anterior" e "Próximo mês" movem o filtro um mês para trás ou para frente a partir do mês selecionado; se nenhum mês estiver selecionado, partem do mês atual.
- **R5** — O usuário também pode informar um intervalo de datas (de/até) para filtrar por um período que não seja um mês inteiro; informar o intervalo substitui o filtro por mês, e escolher um mês substitui o intervalo.
- **R6** — O filtro de período vale para a lista inteira, não só para a página atual: virando de página, o filtro se mantém.
- **R7** — O filtro de período fica registrado no endereço da página, de forma que o usuário possa voltar, atualizar ou compartilhar o link e ver o mesmo período filtrado.
- **R8** — Ao mudar o filtro de período, a lista volta a mostrar a página 1.
- **R9** — O filtro de período convive com a ordenação escolhida (fatia 004): mudar um não reseta o outro.
- **R10** — O resumo da lista mostra a quantidade de gastos e o total em reais do período filtrado (por exemplo: "42 gastos · R$ 3.210,00 no período"), calculado sobre todos os gastos do período, não só os da página atual.
- **R11** — Se o período filtrado não tiver nenhum gasto, o usuário vê a mensagem "Nenhum gasto nesse período."
- **R12** — Os estados de carregando e erro (com "Tentar de novo") das fatias 003 e 004 continuam valendo, agora respeitando o filtro de período escolhido.

## Fora de escopo

- Filtrar por conta ou banco (fatia 006).
- Buscar por texto na descrição ou no recebedor (fatia 007).
- Agrupar o período filtrado por categoria (fatia 008).
- Ver o sinal do mês frente ao teto do plano de recuperação (fatia 014).
- Salvar o período preferido entre sessões (o padrão é sempre o mês corrente ao abrir a página sem parâmetro na URL).

## Pontos em aberto

- nenhum
