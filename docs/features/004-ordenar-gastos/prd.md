# PRD 004 — ordenar gastos

## Valor

O dono do painel encontra o gasto que procura mais rápido, escolhendo se a lista mostra primeiro o mais recente, o mais caro ou agrupa por categoria em ordem alfabética.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", já vendo a lista paginada, querendo reordená-la sem perder a paginação nem precisar refazer a busca do início.

## Requisitos

- **R1** — Na página "Gastos", o usuário vê um seletor "Ordenar por" com três opções: "Data", "Valor" e "Categoria".
- **R2** — O usuário vê um botão que inverte a direção da ordenação atual (crescente ou decrescente).
- **R3** — Por padrão, ao abrir a página sem nenhuma ordenação escolhida, a lista vem ordenada por data, do mais recente para o mais antigo.
- **R4** — Ordenando por "Data", o usuário alterna entre o mais recente primeiro e o mais antigo primeiro.
- **R5** — Ordenando por "Valor", o usuário alterna entre o maior gasto primeiro e o menor gasto primeiro, comparando o tamanho do gasto (quanto saiu), não o sinal.
- **R6** — Ordenando por "Categoria", o usuário alterna entre A→Z e Z→A pelo rótulo da categoria; "Sem categoria" fica sempre por último, nas duas direções.
- **R7** — A ordenação escolhida vale para a lista inteira, não só para a página atual: virando de página, a ordem se mantém.
- **R8** — A ordenação escolhida fica registrada no endereço da página, de forma que o usuário possa voltar, atualizar ou compartilhar o link e ver a mesma ordem.
- **R9** — Ao trocar o critério ou a direção de ordenação, a lista volta a mostrar a página 1.
- **R10** — Os estados de carregando, lista vazia e erro (com "Tentar de novo") da fatia 003 continuam valendo, agora respeitando a ordenação escolhida.

## Fora de escopo

- Filtrar por período, conta ou texto (fatias 005, 006, 007).
- Agrupar por categoria com totais (fatia 008).
- Ordenar por recebedor, descrição ou conta de origem.
- Salvar a preferência de ordenação entre sessões (o padrão é sempre data, mais recente primeiro, ao abrir a página sem parâmetro na URL).

## Pontos em aberto

- nenhum
