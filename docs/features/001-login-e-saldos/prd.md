# PRD 001 — login e saldos

## Valor

O dono do painel entra com login e senha e vê, numa página só, o saldo de hoje de cada conta e cartão já sincronizado da Pluggy.

## Usuários

O único usuário do painel, dono das contas, acessando de um navegador local para conferir a situação financeira do dia.

## Requisitos

- **R1** — O usuário entra com login e senha; credenciais erradas mostram mensagem de erro clara e mantêm o usuário na tela de login.
- **R2** — Ao entrar com sucesso, o usuário é levado à página do painel.
- **R3** — Na página do painel, o usuário vê uma lista das contas bancárias e cartões já sincronizados, cada um com nome da conta, instituição, tipo, saldo em reais e a data/hora do último dado.
- **R4** — Saldo negativo aparece em destaque visual, diferenciado do saldo positivo.
- **R5** — Enquanto os dados carregam, o usuário vê um estado de carregamento.
- **R6** — Se não houver nenhuma conta sincronizada, o usuário vê uma mensagem informando isso, sem lista vazia sem explicação.
- **R7** — Se a busca dos dados falhar, o usuário vê uma mensagem de erro com opção de tentar de novo.
- **R8** — O usuário consegue sair do painel, encerrando a sessão.
- **R9** — Qualquer tentativa de acessar dados do painel sem estar autenticado leva o usuário à tela de login.

## Fora de escopo

- Cadastro ou alteração de usuário/senha.
- Atualizar (sincronizar) os dados na hora, sob demanda (fatia 002).
- Lista de gastos e lançamentos (fatia 003 em diante).
- Qualquer gráfico ou visualização além da lista de saldos.

## Pontos em aberto

- nenhum
