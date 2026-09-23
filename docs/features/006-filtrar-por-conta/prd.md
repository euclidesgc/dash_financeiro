# PRD 006 — filtrar por conta

## Valor

O dono do painel isola os gastos de uma conta ou cartão específico para saber quanto saiu dali, sem misturar com o resto.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", já vendo a lista paginada, ordenável e filtrável por período, querendo restringi-la a uma conta ou cartão antes de olhar o total ou os lançamentos.

## Requisitos

- **R1** — Na página "Gastos", o usuário vê um seletor "Conta" com a opção "Todas as contas" e uma opção para cada conta ou cartão sincronizado.
- **R2** — Cada opção de conta mostra "Nome · Instituição" e um selo indicando se é Conta ou Cartão.
- **R3** — Por padrão, ao abrir a página sem nenhuma conta escolhida, a lista mostra gastos de todas as contas e cartões.
- **R4** — Escolhendo uma conta ou cartão, o usuário vê só os gastos daquela origem.
- **R5** — O filtro de conta vale para a lista inteira, não só para a página atual: virando de página, o filtro se mantém.
- **R6** — O filtro de conta fica registrado no endereço da página, de forma que o usuário possa voltar, atualizar ou compartilhar o link e ver o mesmo filtro.
- **R7** — Ao mudar o filtro de conta, a lista volta a mostrar a página 1.
- **R8** — O filtro de conta convive com a ordenação (fatia 004) e com o filtro de período (fatia 005): mudar um não reseta o outro.
- **R9** — O resumo da lista mostra a quantidade de gastos e o total em reais considerando o filtro de conta junto com os demais filtros ativos.
- **R10** — Se o endereço da página trouxer uma conta que não existe mais na base, o usuário vê a lista como se tivesse escolhido "Todas as contas", sem erro.
- **R11** — Se a combinação de filtros não tiver nenhum gasto, o usuário vê a mensagem "Nenhum gasto para esse filtro."
- **R12** — Os estados de carregando e erro (com "Tentar de novo") das fatias 003, 004 e 005 continuam valendo, agora respeitando o filtro de conta escolhido.

## Fora de escopo

- Buscar por texto na descrição ou no recebedor (fatia 007).
- Agrupar por categoria (fatia 008).
- Selecionar mais de uma conta ao mesmo tempo.
- Salvar a conta preferida entre sessões (o padrão é sempre "Todas as contas" ao abrir a página sem parâmetro na URL).

## Pontos em aberto

- nenhum
