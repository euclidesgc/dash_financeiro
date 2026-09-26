# PRD 068 — Origem e novidades da atualização

## Valor

O dono do painel vê, depois de clicar em "Atualizar agora", de onde vieram os dados e quantos lançamentos novos entraram, sem precisar adivinhar.

## Usuários

O dono do painel financeiro, na tela de Atualização, painel "Atualização dos registros", depois de disparar uma atualização manual.

## Requisitos

- **R1** — Depois de uma atualização concluída com sucesso, a tela mostra a origem e a quantidade de lançamentos novos no formato "Buscou na Pluggy · 25 lançamentos novos" ou "Releu o arquivo local · nenhum lançamento novo".
- **R2** — A contagem usa singular quando é exatamente um lançamento: "1 lançamento novo".
- **R3** — A tela não mostra contagem de contas nessa mensagem.
- **R4** — Quando a atualização falha, a tela mostra a origem que foi tentada, sem contagem de lançamentos (a falha já tem seu próprio alerta).
- **R5** — Para atualizações já registradas antes desta fatia, cuja origem verdadeira não é conhecida, a tela não mostra a linha de origem.
- **R6** — A subida do projeto pelo atalho de desenvolvimento (F5) não aparece no histórico de atualizações nem é atribuída a "Feita pela rotina diária"; a tela sempre reflete o último clique do dono em "Atualizar agora".

## Fora de escopo

- Qualquer rotina de atualização agendada/automática (não existe hoje).
- Alterar o que conta como "lançamento novo" ou as regras de sincronização com a Pluggy.
- Exibir contagem de contas atualizadas.

## Pontos em aberto

- Nenhum.
