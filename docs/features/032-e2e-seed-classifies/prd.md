# PRD 032 — e2e-seed-classifies

## Valor

O dono do painel confia que as provas automáticas de ponta a ponta olham para a mesma base que ele vê depois de uma atualização: cada lançamento da base de provas nasce com grupo, natureza e essencialidade já classificados, como acontece na base real depois do botão de atualizar ou do comando diário.

## Usuários

O único usuário do painel, dono das contas, quando as provas automáticas conferem as telas numa base carregada fora do fluxo normal de atualização.

## Requisitos

- **R1** — A base das provas automáticas de ponta a ponta sai da carga inicial com todo lançamento classificado (grupo, natureza e essencialidade), pela mesma regra que a atualização normal aplica.
- **R2** — Classificar de novo a base das provas, logo depois da carga inicial, não muda nenhum lançamento: o estado de partida é o mesmo que uma atualização deixaria.
- **R3** — A tela de atualização, nas provas, continua começando em "Nunca atualizado": a carga inicial não conta como atualização.
- **R4** — Se a carga inicial for recusada, a base das provas não sobe e nada é classificado.

## Fora de escopo

- Recalcular compromissos e a escada de dívidas na carga das provas (o restante do pós-atualização).
- Mudar as regras de classificação.
- Mudar os dados de exemplo da base de provas.

## Pontos em aberto

- nenhum
