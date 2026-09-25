# PRD 018 — sync-runs-source-field

## Valor

Os registros bancários são atualizados de dois jeitos: pela rotina diária, que roda sozinha, e pelo botão "Atualizar agora" da tela. Hoje o painel guarda quando cada atualização terminou e se deu certo, mas não quem a pediu. Quando a rotina diária para de rodar, o dono não percebe: o botão mantém a data recente e a tela parece em dia. Sabendo de onde veio a última atualização, o dono vê na hora que os dados só estão frescos porque ele mesmo apertou o botão.

## Usuários

O único usuário do painel, dono das contas.

## Requisitos

- **R1** — Toda atualização registrada a partir desta entrega guarda quem a pediu: a tela (botão da tela nova ou da tela antiga) ou um comando (a rotina diária ou a carga manual pelo terminal).
- **R2** — A situação da atualização, na tela de saldos, diz abaixo da data da última atualização se ela foi pedida na tela ou feita pela rotina diária.
- **R3** — Atualizações registradas antes desta entrega não ganham origem inventada; para elas a tela não diz nada sobre a origem.
- **R4** — Uma atualização que falha também guarda quem a pediu.

## Fora de escopo

- Passar o botão da tela antiga pela trava de execução única (item próprio do roadmap).
- Histórico de atualizações na tela.

## Pontos em aberto

- nenhum
