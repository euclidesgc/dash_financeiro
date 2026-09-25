# PRD 016 — entradas

## Valor

O dono do painel vê salário e outras receitas do período separados dos gastos, e enxerga de cara se sobrou ou faltou dinheiro no mês.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", querendo saber o que entrou (não só o que saiu) e se o período fechou no positivo ou no negativo.

## Requisitos

- **R1** — Na barra da página "Gastos", o controle "Mostrar" ganha uma terceira opção: "Gastos | Não são gastos | Entradas".
- **R2** — No modo "Entradas", o usuário vê os lançamentos com valor positivo que não sejam estorno nem transferência entre contas próprias, na mesma lista (mesmas colunas de data, descrição, recebedor, conta, valor), com os mesmos filtros de período, conta e busca por texto e a mesma ordenação das outras vistas.
- **R3** — No modo "Entradas", o resumo mostra a quantidade e o total do período, no formato "N entradas · R$ X no período", com o valor em verde.
- **R4** — Quando há período filtrado, o usuário vê um bloco "Resultado do período" com entradas, gastos e saldo (entradas − gastos), visível em qualquer uma das três vistas; o saldo aparece em verde quando positivo e em vermelho quando negativo.
- **R5** — Sem período filtrado (todo o período), o bloco "Resultado do período" não aparece.
- **R6** — No modo "Entradas", cada linha não tem categoria nem a ação "Não é gasto"; em vez disso tem a ação "Não é entrada".
- **R7** — Ao acionar "Não é entrada", o usuário escolhe um motivo entre "Transferência entre minhas contas", "Estorno" e "Outro", do mesmo jeito que em "Não é gasto" (fatia 015); ao confirmar, o lançamento sai da lista de entradas e do bloco "Resultado do período" imediatamente, sem recarregar a página, com aviso e opção "Desfazer".
- **R8** — Um lançamento marcado como "Não é entrada" aparece no modo "Não são gastos" junto com os demais, com o motivo escolhido, e pode ser desmarcado por lá pela ação "Voltar a ser gasto" (renomeada de forma que sirva para os dois casos), voltando a contar como entrada.
- **R9** — Os blocos "Por categoria" e "Teto do mês" continuam aparecendo só no modo "Gastos".
- **R10** — Um lançamento que a automação já classifica como estorno ou transferência entre contas próprias não aparece no modo "Entradas" nem precisa ser marcado; ele não é afetado nem editável por esta fatia.
- **R11** — A marcação de "Não é entrada" sobrevive à próxima atualização dos registros: reingerir os lançamentos da Pluggy não desfaz a marcação manual.

## Fora de escopo

- Categorizar entradas.
- Projeção de entradas futuras (recorrência de salário, etc.).
- Editar ou desmarcar em lote.
- Editar o motivo de "Não é entrada" depois de marcado.

## Pontos em aberto

- nenhum

### Premissas assumidas

- O modo "Não são gastos" da fatia 015 passa a listar tanto lançamentos negativos marcados quanto positivos marcados, sem virar uma quarta vista.
- "Entradas" segue o mesmo texto de estado vazio, carregando e erro das demais vistas, adaptado ("Nenhuma entrada nesse período.").
