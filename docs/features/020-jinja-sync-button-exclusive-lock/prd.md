# PRD 020 — jinja-sync-button-exclusive-lock

## Valor

O painel tem dois botões que atualizam os registros bancários: o da tela nova e o da tela antiga de resumo. Só o da tela nova respeita a regra de uma atualização por vez. O da tela antiga dispara uma segunda atualização mesmo com outra em andamento, e as duas escrevem na base ao mesmo tempo, com risco de registro duplicado ou histórico de atualização contraditório. Com a fatia, os dois botões obedecem à mesma regra e o dono vê o mesmo aviso nos dois.

## Usuários

O único usuário do painel, dono das contas, que às vezes aperta o botão de atualizar na tela antiga de resumo.

## Requisitos

- **R1** — Apertar o botão de atualizar da tela de resumo enquanto outra atualização está em andamento não inicia uma segunda atualização nem grava nada no histórico de atualizações.
- **R2** — Nesse caso a tela de resumo mostra o aviso "Já existe uma atualização em andamento.", o mesmo texto da tela nova.
- **R3** — Sem outra atualização em andamento, o botão da tela de resumo continua atualizando e mostrando o resultado como hoje.

## Fora de escopo

- Trocar a trava do processo por uma trava no banco (o comando diário roda em outro horário).
- Retirar a tela antiga de resumo.

## Pontos em aberto

- nenhum
