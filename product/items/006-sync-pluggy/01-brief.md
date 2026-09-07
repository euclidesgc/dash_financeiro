# Brief — 006-sync-pluggy

Escrito no presente. Cada requisito é `RF-nn`.

## A contagem que tem semântica

- **RF-01** — `sync_runs.transactions_count` guarda **quantas transações foram
  inseridas** na execução, e `accounts_count`, quantas contas. Na base de
  05/09/2026 a primeira carga grava `1942` e a segunda, `0`.
- **RF-02** — A prova de integridade — toda linha aceita chegou à tabela — ganha
  colunas próprias, `transactions_present` e `accounts_present`, e continua
  reprovando a carga quando não bate com o aceito.
- **RF-03** — A migração converte as linhas já gravadas: o valor antigo passa
  para a coluna de integridade, e a de inserção fica nula, porque aquele número
  não existe para execuções passadas. Nulo é a resposta honesta.

## Sem duplicata

- **RF-04** — Carregar o mesmo arquivo duas vezes deixa a contagem de transações
  idêntica: 1.942 antes e 1.942 depois.
- **RF-05** — A segunda carga grava uma linha em `sync_runs` com
  `transactions_count = 0` e `status = 'ok'`. Não inserir nada é sucesso, não
  falha.
- **RF-06** — Uma carga que falha no meio não deixa metade escrita, e a linha de
  falha sobrevive ao rollback que ela descreve.

## O comando e o botão

- **RF-07** — `python -m app.sync` executa uma sincronização e imprime o
  resultado numa linha, saindo com código 0 em sucesso e 1 em falha.
- **RF-08** — `POST /sincronizar` executa a mesma sincronização e devolve a tela
  de Resumo com o resultado.
- **RF-09** — Sem credencial da Pluggy, a sincronização **recusa antes de
  tentar**, com mensagem que diz qual variável falta, e **não** grava linha de
  falha em `sync_runs` — não houve execução para registrar.
- **RF-10** — Com o arquivo consolidado no disco, a sincronização roda sem rede.
  É esse o caminho que o painel usa hoje.

## A tela

- **RF-11** — O Resumo mostra a data e a hora da última sincronização
  bem-sucedida e quantas linhas ela inseriu.
- **RF-12** — Se a última execução **falhou**, a tela diz isso em destaque, com a
  mensagem, e continua mostrando a data da última que deu certo.
- **RF-13** — Se a última sincronização bem-sucedida é mais velha que **um dia**,
  a tela diz há quantos dias o dado está parado.
- **RF-14** — Base sem sincronização nenhuma diz que nunca houve, e nomeia o
  comando.
- **RF-15** — O botão de sincronizar é acionável e diz o que acontece:
  **Sincronizar agora**.
- **RF-16** — A tela obedece à linguagem visual, e nenhum número medido aparece
  como literal no código.

## O que uma falha de escrita não pode fazer

- **RF-17** — Uma carga que estoura no meio da escrita **grava linha de falha**
  em `sync_runs` e não derruba a rota. Hoje o caminho de exceção desfaz a escrita
  e repropaga sem registrar nada: a sincronização falhou, não deixou rastro, e a
  tela seguinte continua exibindo a última execução bem-sucedida com cara de dado
  fresco — que é exatamente o modo de falha que este item existe para matar.
- **RF-18** — A mensagem que a tela mostra é **em português**. A do carregador é
  técnica e em inglês (`rejected=1`, `transactions accepted=1942 present=1900`) e
  serve ao log, não ao dono, que é quem precisa decidir o que fazer com a falha.
- **RF-19** — A hora gravada é UTC e a data de referência é local. A tela e a
  contagem de idade **convertem** para o fuso local antes de comparar: sem isso,
  uma carga rodada depois das 21h aparece com a data do dia seguinte e a idade
  sai um dia menor que a real — justamente o número que este item existe para
  tornar honesto.
