# PRD 070 — Consultor de IA: conversa e lista de lançamentos

## Valor

O dono abre "Consultor" no cabeçalho do painel, pergunta em português sobre os próprios lançamentos
("quais foram meus gastos com posto em agosto?") e recebe uma resposta cujos valores saem do mesmo
cálculo das telas, nunca da cabeça do modelo. A conversa fica guardada e continua de onde parou.

## Usuários

O dono do painel, logado, na tela nova `/app/advisor`.

## Requisitos

- **R1** — O cabeçalho da SPA tem o link "Consultor", que abre a tela do chat.
- **R2** — O dono escreve uma pergunta (até 500 caracteres), envia e vê a própria mensagem e, ao
  fim, a resposta do consultor; enquanto espera, a tela diz "Consultando suas contas…" e o envio fica
  bloqueado.
- **R3** — Para listar, somar ou contar lançamentos, o consultor usa a busca do painel, com filtros de
  período, conta, texto, categoria e gastos ou entradas; todo valor da resposta vem dessa busca, em
  reais no formato do painel. Transferência entre contas próprias e estorno não entram.
- **R4** — Uma resposta que cita valor em reais que a busca não devolveu não é mostrada; no lugar, a
  tela explica por quê e sugere reformular.
- **R5** — A conversa fica guardada: ao voltar à tela, a última conversa reaparece; "Nova conversa"
  começa outra.
- **R6** — Sem chave de IA configurada, a tela explica como configurar (chave da Anthropic no `.env`,
  ou chave do Gemini no `.env` ou na tela Configuração) e o resto do painel segue funcionando.
- **R7** — Falha do provedor (chave recusada, excesso de chamadas, sem rede, recusa do modelo) vira
  uma mensagem em português que diz o próximo passo, sem perder a conversa.
- **R8** — A tela diz qual provedor respondeu (Anthropic ou Gemini).

## Fora de escopo

- Resumo por categoria e mês a mês, recategorização pelo chat, projeção de parcelas e quitação de
  dívidas (itens 071 a 075).
- Streaming da resposta; guardar chave pela tela nova; mudar a tela antiga `/consultor`.

## Pontos em aberto

- Nenhum.
