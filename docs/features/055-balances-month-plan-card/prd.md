# PRD 055 — balances-month-plan-card

## Problema

A tela inicial, "Saldos de hoje", mostra quanto há em cada conta, mas não
responde a pergunta que o dono faz ao abrir o painel: "estou dentro do plano
este mês?". Para saber, ele precisa ir a Gastos e escolher o mês corrente.

## O que muda para o usuário

Entre o painel de atualização e a lista de saldos aparece o cartão
"Plano de <mês> de <ano>", sempre do mês corrente, com:

- **Gasto no mês**, com o selo do teto (Dentro, Atenção, Acima) quando há teto;
- **Teto do mês**, ou "Sem teto" quando não foi definido;
- **Resultado até hoje**: entradas menos gastos do mês, verde se positivo,
  vermelho se negativo;
- uma linha dizendo quanto sobra até o teto ou quanto passou dele;
- o link "Ver o mês em detalhe", que abre Gastos já no mês corrente.

Sem teto definido, o cartão diz que não dá para saber se o mês cabe no plano e
o link vira "Definir o teto do mês", que abre Gastos no mesmo mês.

Enquanto carrega, "Carregando o plano do mês…". Se a busca falha, a mensagem
"Não foi possível carregar o plano do mês." com "Tentar de novo".

## Fora do escopo

- Editar o teto na tela de saldos (continua em Gastos).
- Escolher outro mês no cartão.
