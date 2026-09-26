# PRD 072 — Consultor de IA: trocar a categoria de lançamentos com confirmação

## Valor

O dono lista gastos no Consultor ("gastos com farmácia em agosto") e pede "passe esses para Plano de
saúde". Em vez de abrir a tela de gastos e trocar um por um, ele vê no chat exatamente o que vai
mudar e aplica com um clique, sabendo que pode desfazer. O consultor nunca muda nada sozinho.

## Usuários

O dono do painel, logado, na tela `/app/advisor`.

## Requisitos

- **R1** — Pedida a troca de categoria de lançamentos listados (ou de um filtro: texto, categoria atual,
  conta, período), o consultor prepara uma proposta e não muda nada. A resposta diz quantos
  lançamentos mudam e a soma, e pede para conferir e aplicar.
- **R2** — Abaixo da resposta aparece um cartão com cada lançamento da proposta: data, descrição,
  valor e "categoria atual → nova", o total, e os botões **Aplicar** e **Descartar**.
- **R3** — A categoria de destino precisa existir no painel. Categoria que não existe vira resposta que
  diz as categorias disponíveis e que uma nova se cria na tela Categorias; o chat não cria categoria.
- **R4** — Aplicar muda a categoria de todos os lançamentos da proposta de uma vez, como a troca manual
  da tela de gastos (a escolha do dono vale sobre a regra automática e sobrevive à próxima
  atualização). Ou muda tudo, ou nada. Clicar duas vezes não aplica duas vezes.
- **R5** — Depois de aplicada, o cartão mostra "Aplicada" e o botão **Desfazer**, que devolve a
  categoria anterior de cada lançamento. Lançamento que o dono mudou de novo depois da aplicação fica
  como está, e o cartão diz quantos ficaram.
- **R6** — Descartada, a proposta não muda nada e o cartão diz "Descartada". A proposta fica guardada
  com a conversa: reabrindo a conversa, o cartão aparece no mesmo estado, com quando foi aplicada,
  descartada ou desfeita.
- **R7** — Depois de aplicar ou desfazer, a tela de gastos, os totais por categoria e a tela de
  categorias mostram os números novos sem recarregar a página.

## Fora de escopo

- Criar, renomear ou apagar categoria pelo chat; criar regra de classificação; marcar "não é gasto".
- Aplicar ou desfazer pedindo ao consultor por texto: só os botões do cartão gravam.

## Pontos em aberto

- Nenhum.
