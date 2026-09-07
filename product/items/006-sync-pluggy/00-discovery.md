# Discovery — 006-sync-pluggy

**Item do roadmap:** `006-sync-pluggy` — As movimentações se atualizam sob
demanda e todo dia, sem duplicar nenhuma transação, e a tela diz quando foi a
última sincronização e se ela falhou.

**Data:** 2026-09-07

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Depende do `001` (ingestão e `sync_runs`) e do `004` (a tela onde o aviso mora). |
| Negociável | sim | Fixo: sem duplicata, a tela diz quando foi e se falhou, e `transactions_count` passa a ter semântica. Conversável: o que é "todo dia" num app local, e o que a tela faz quando o dado está velho. |
| Valioso | sim | Sync que falha em silêncio é pior que sync nenhum: o painel passa a mostrar dado velho com cara de dado fresco, e todas as decisões saem erradas juntas. |
| Estimável | sim | Uma fase. |
| Pequeno | sim | Uma migração, um pacote fino, um bloco na tela existente. |
| Testável | sim | A não-duplicação se prova rodando a mesma carga duas vezes; a idade do dado, por data de referência. |

**Veredicto do INVEST:** segue como está.

## História

Como dono deste painel, quero saber quando os dados foram atualizados pela
última vez e se a atualização falhou, e poder atualizar na hora, para não tomar
decisão em cima de extrato de duas semanas atrás achando que é de hoje.

## Regras e exemplos

### R1 — Herdado do `001`: `transactions_count` não conta o que entrou

- **E1.1** — Hoje `sync_runs.transactions_count` guarda **quantas linhas existem
  depois da carga**, não quantas entraram nela. Rodar a mesma carga duas vezes
  grava `1942` nas duas execuções, e a segunda não inseriu nada.
- **E1.2** — O número que existe hoje **não é inútil**: ele é a prova de
  integridade de que toda linha aceita chegou à tabela, e a carga reprova quando
  ele não bate com o aceito. O erro é o nome, não a conta.
- **E1.3** — A coluna passa a guardar **quantas linhas foram inseridas nesta
  execução**, e a prova de integridade ganha coluna própria. Na base de
  05/09/2026, a primeira carga insere **1.942** e a segunda **0**.

### R2 — Sincronizar duas vezes não duplica nada

- **E2.1** — A ingestão casa por `pluggy_id`, e a segunda passada sobre o mesmo
  arquivo deixa a contagem de transações **igual**: 1.942 antes e 1.942 depois.
- **E2.2** — Uma sincronização que falha no meio **não deixa metade**: a
  transação do banco é uma só, e a linha de falha em `sync_runs` sobrevive ao
  rollback que ela descreve — o `001` já fez isso e continua valendo.

### R3 — A tela diz quando foi, e diz quando está velho

- **E3.1** — O Resumo mostra a data e a hora da última sincronização bem-sucedida
  e quantas linhas ela inseriu.
- **E3.2** — Se a última sincronização **falhou**, a tela diz isso em destaque,
  com a mensagem da falha, e continua mostrando a data da última que deu certo.
  Sync que falha em silêncio é o modo de falha que este item existe para matar.
- **E3.3** — Se a última sincronização é mais velha que **um dia**, a tela diz
  há quanto tempo o dado está parado. O número que o dono lê tem idade, e a
  idade é parte do número.
- **E3.4** — Base sem nenhuma sincronização diz que nunca houve, e diz o comando.

### R4 — "Todo dia" num app local é comando, não daemon

- **E4.1** — O painel roda em `127.0.0.1` e não fica de pé quando a máquina está
  desligada. Prometer sincronização diária dentro do processo seria prometer o
  que o processo não controla.
- **E4.2** — O item entrega um **comando** (`python -m app.sync`) que a máquina
  agenda como quiser, e a tela **cobra a idade**: se o dado está velho, ela diz,
  independentemente de por que o agendamento não rodou.
- **E4.3** — Sob demanda é um botão na tela, que roda o mesmo comando e devolve
  a mesma tela com o resultado.

### R5 — Sem credencial, a sincronização recusa e diz por quê

- **E5.1** — A extração da Pluggy precisa de credencial e de item não expirado.
  Sem credencial, a sincronização **não roda e diz isso**, em vez de gravar uma
  falha genérica.
- **E5.2** — A carga a partir do arquivo já consolidado continua funcionando sem
  rede: é ela que o painel usa hoje, e é ela que os testes exercitam.

## Perguntas em aberto

Nenhuma.

A única coisa que não se prova nesta corrida é a chamada real à API da Pluggy,
que precisa de credencial válida e de item não expirado — o MFA da Pluggy é
interativo e não se automatiza. Já está registrado como validação de campo
pendente no roadmap, desde antes deste item.

## Trilha

**Trilha: rápida.** Zero perguntas em aberto; uma stack só; sem mudança de
contrato; sem dependência nova.
