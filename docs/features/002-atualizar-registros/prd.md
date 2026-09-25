# PRD 002 — atualizar registros

## Valor

O dono do painel dispara a atualização dos registros bancários quando quiser e sabe, a qualquer momento, quando foi a última vez que os dados foram renovados e se deu certo.

## Usuários

O único usuário do painel, dono das contas, na página de saldos, conferindo se os dados que está vendo são recentes ou pedindo para renová-los agora.

## Requisitos

- **R1** — Na página de saldos, o usuário vê a data e a hora da última atualização dos registros bancários, em pt-BR.
- **R2** — Se nunca houve atualização, o usuário vê "Nunca atualizado" no lugar da data.
- **R3** — O usuário vê o resultado da última atualização: concluída, ou falhou com o motivo em linguagem simples.
- **R4** — O usuário aperta um botão "Atualizar agora" que busca na Pluggy as contas, saldos e lançamentos de todas as conexões e grava na base local.
- **R5** — Enquanto a atualização roda, o botão fica desabilitado com o texto "Atualizando…" e a tela informa que uma atualização está em andamento.
- **R6** — Ao terminar com sucesso, a lista de saldos e a informação de última atualização se renovam sozinhas, sem o usuário recarregar a página.
- **R7** — Se a atualização falhar (credencial da Pluggy ausente, rede fora, conexão bancária expirada), a tela mostra o erro com a opção "Tentar de novo".
- **R8** — Apertar "Atualizar agora" enquanto uma atualização já está em andamento não dispara uma segunda; só existe uma atualização por vez.
- **R9** — A atualização diária automática, que roda fora da tela, também atualiza a informação de última atualização e resultado — o usuário vê o efeito dela na tela do mesmo jeito que vê o de uma atualização manual.

## Fora de escopo

- Escolher quais conexões Pluggy atualizar.
- Histórico das atualizações anteriores (só a última fica visível).
- Lista de gastos e lançamentos (fatia 003).

## Pontos em aberto

- nenhum
