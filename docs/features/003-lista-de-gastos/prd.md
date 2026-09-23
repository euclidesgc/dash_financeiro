# PRD 003 — lista de gastos

## Valor

O dono do painel vê todos os gastos que já aconteceu, de todas as contas e cartões, numa única lista, sem precisar entrar em cada extrato.

## Usuários

O único usuário do painel, dono das contas, entrando na página "Gastos" para conferir o que saiu do dinheiro, lançamento a lançamento.

## Requisitos

- **R1** — No cabeçalho do app, ao lado de "Saldos", o usuário vê um link "Gastos" que abre a lista de gastos.
- **R2** — O usuário vê os gastos de todas as contas e cartões numa única lista, do mais recente ao mais antigo.
- **R3** — A lista é paginada em 20 gastos por página, com indicação "Página X de Y", botões "Anterior" e "Próxima", e a contagem total de gastos.
- **R4** — Cada linha mostra: data (dd/mm/aaaa), descrição, nome de quem recebeu (quando houver), conta ou cartão de origem (nome e instituição), categoria (ou "Sem categoria") e o valor em reais, com o sinal negativo em vermelho, do mesmo jeito que aparece na base.
- **R5** — "Gasto" é todo lançamento com valor negativo (dinheiro saindo) que não seja transferência entre contas próprias nem estorno; entradas não aparecem nesta lista.
- **R6** — Enquanto a lista carrega, o usuário vê um indicador de carregamento.
- **R7** — Se não houver nenhum gasto, o usuário vê a mensagem "Nenhum gasto registrado ainda."
- **R8** — Se a busca dos gastos falhar, o usuário vê o erro com a opção "Tentar de novo".
- **R9** — Sem login, o usuário que tenta abrir "Gastos" vai para a tela de login.

## Fora de escopo

- Ordenar por outro critério além de data (fatia 004).
- Filtrar por período, conta ou texto (fatias 005, 006, 007).
- Agrupar por categoria (fatia 008).
- Editar a categoria de um gasto (fatia 009).
- Marcar um lançamento como não-gasto (fatia 015).
- Ver as entradas (fatia 016).

## Pontos em aberto

- nenhum
