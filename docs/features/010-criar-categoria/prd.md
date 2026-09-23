# PRD 010 — criar categoria

## Valor

O dono do painel molda o catálogo de categorias ao seu jeito de organizar os gastos, em vez de ficar preso às categorias que vieram prontas.

## Usuários

O único usuário do painel, dono das contas, numa página "Categorias" acessada pelo cabeçalho, querendo criar uma categoria que falta, corrigir o rótulo de uma existente ou remover uma que não usa mais.

## Requisitos

- **R1** — No cabeçalho do app, o usuário vê um link "Categorias" ao lado de "Saldos" e "Gastos", que leva à página "Categorias".
- **R2** — Na página "Categorias", o usuário vê a lista completa do catálogo: rótulo, quantidade de gastos que usam a categoria e se ela é do sistema ou criada por ele.
- **R3** — O usuário cria uma categoria nova informando um rótulo; o rótulo é obrigatório e precisa ser único no catálogo (comparação sem diferenciar maiúsculas de minúsculas).
- **R4** — Ao tentar salvar com rótulo vazio ou já existente, o usuário vê o erro junto do campo, sem perder o que digitou.
- **R5** — Assim que criada, a categoria nova aparece na lista e passa a estar disponível no seletor de categoria de cada gasto (fatia 009) e no bloco "Por categoria" (fatia 008).
- **R6** — O usuário renomeia qualquer categoria, do sistema ou criada por ele, sujeito às mesmas regras de rótulo obrigatório e único do R3 e R4.
- **R7** — Depois de renomear, o novo rótulo aparece em toda parte que mostra a categoria: a lista de categorias, o bloco "Por categoria" e o seletor de categoria dos gastos, sem exigir recarregar a página.
- **R8** — O usuário apaga uma categoria criada por ele que não tenha nenhum gasto usando-a.
- **R9** — Se a categoria a apagar tiver algum gasto usando-a, o usuário vê uma explicação com a quantidade de gastos e a categoria não é apagada.
- **R10** — Uma categoria do sistema não tem opção de apagar, só de renomear.
- **R11** — Enquanto o catálogo carrega, o usuário vê um indicador de carregamento; se a busca falhar, vê o erro com a opção "Tentar de novo".
- **R12** — Enquanto uma criação, renomeação ou exclusão está sendo salva, o usuário vê um indicador de salvando; se a operação falhar, vê o erro e o estado anterior permanece.

## Fora de escopo

- Definir limite mensal por categoria (fatia 012).
- Aplicar categoria a gastos parecidos de uma vez (fatia 011).
- Mesclar duas categorias em uma.
- Página vazia sem categorias: sempre há pelo menos as do sistema, vindas do seed.

## Pontos em aberto

- nenhum
