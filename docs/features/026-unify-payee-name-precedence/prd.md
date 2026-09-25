# PRD 026 — unify-payee-name-precedence

## Valor

O nome de quem recebeu um gasto aparece em várias telas (lista de gastos, recebedores, telas antigas) e também decide o que a busca por texto encontra. Hoje a regra que escolhe esse nome — apelido do dono, nome fantasia da Pluggy, nome consultado pelo CNPJ, razão social — está escrita duas vezes: uma para mostrar e outra para buscar. Se alguém mudar uma e esquecer a outra, a busca passa a achar gastos por um nome que a tela não mostra, ou deixa de achar pelo nome que ela mostra, sem nenhum aviso. Com uma regra só, o que a tela mostra é sempre o que a busca procura.

## Usuários

O único usuário do painel, dono das contas, ao buscar um gasto pelo nome de quem recebeu e ao dar apelido a um recebedor.

## Requisitos

- **R1** — O nome de quem recebeu mostrado na lista de gastos é o mesmo nome mostrado na tela de recebedores para aquele recebedor.
- **R2** — A busca por texto na lista de gastos encontra um gasto pelo nome de quem recebeu exatamente como a lista o mostra, e não encontra por um nome que a lista não mostra (por exemplo, o nome fantasia quando o dono deu um apelido).
- **R3** — A ordem de preferência do nome continua a de hoje: apelido do dono, nome fantasia da Pluggy, nome consultado pelo CNPJ, razão social ou nome do recebedor; sem nenhum deles, a lista não mostra nome e a tela de recebedores mostra a descrição normalizada.
- **R4** — Nenhum total, contagem ou página da lista muda por causa desta mudança.

## Fora de escopo

- Mudar a ordem de preferência dos nomes.
- Mudar a tela de recebedores ou a lista de gastos na aparência.

## Pontos em aberto

- nenhum
