# PRD 008 — total por categoria

## Valor

O dono do painel enxerga, sem contar linha por linha, para onde vai o dinheiro dentro do período que está olhando: qual categoria pesa mais e quanto.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", já com a lista filtrada por período, conta e busca, querendo entender a composição do total por categoria antes de mexer em qualquer filtro adicional.

## Requisitos

- **R1** — Na página "Gastos", acima da lista, o usuário vê um bloco "Por categoria" com uma linha por categoria presente nos gastos do filtro atual.
- **R2** — Cada linha mostra o rótulo da categoria, a quantidade de gastos e o total em reais daquela categoria, considerando o mesmo período, conta e busca aplicados à lista abaixo.
- **R3** — As linhas ficam ordenadas da categoria de maior total para a de menor total, incluindo "Sem categoria" nessa mesma ordenação (sem posição fixa).
- **R4** — A soma dos totais de todas as categorias é igual ao total mostrado no resumo da lista ("N gastos · R$ X no período").
- **R5** — Mudar o período, a conta ou o texto buscado atualiza o bloco "Por categoria" junto com a lista, sem exigir ação separada do usuário.
- **R6** — Com até 8 categorias no filtro atual, o usuário vê todas as linhas. Com mais de 8, vê as 8 de maior total e um controle "Mostrar todas (N)" que revela as demais.
- **R7** — Enquanto os totais carregam, o usuário vê um indicador de carregamento no lugar do bloco.
- **R8** — Se a busca dos totais por categoria falhar, o usuário vê o erro com a opção "Tentar de novo", sem que isso impeça a lista de gastos abaixo de funcionar.
- **R9** — Se o filtro atual não tiver nenhum gasto, o bloco "Por categoria" não aparece.
- **R10** — Clicar numa categoria não faz nada além do que já é possível hoje (sem filtro, sem navegação).

## Fora de escopo

- Filtrar a lista de gastos ao clicar numa categoria (fica para quando essa interação for pedida).
- Limite mensal por categoria (fatia 012).
- Sinal de dentro/acima/abaixo do limite por categoria (fatia 013).
- Editar a categoria de um gasto (fatia 009).
- Gráfico ou visualização diferente de lista de linhas (por exemplo, pizza ou barras).

## Pontos em aberto

- nenhum
