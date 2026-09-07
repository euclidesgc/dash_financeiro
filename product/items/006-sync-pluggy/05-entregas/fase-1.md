## 1. O que foi implementado

**Item:** `006-sync-pluggy` · **Fase:** `1 de 1`

Este item existe para matar um modo de falha: **sincronização que falha em
silêncio faz o painel mostrar dado velho com cara de dado fresco.** Três coisas.

**A contagem passou a ter semântica.** `sync_runs.transactions_count` guardava
quantas linhas existiam depois da carga, não quantas entraram: a segunda passada
sobre o mesmo arquivo gravava `1942` sem inserir nada. O número era uma prova de
integridade com o nome errado. A prova ficou, em `transactions_present`, e a
contagem passou a significar inserções — **nula** para as execuções anteriores à
migração, porque aquele número não existe em lugar nenhum e inventá-lo seria
pior.

**"Todo dia" virou comando mais idade cobrada na tela.** O painel morre com a
máquina; um agendador interno prometeria o que o processo não controla, e
falharia exatamente quando o computador ficou desligado — o caso em que o dado
envelhece. Existe `python -m app.sync`, existe o botão **Sincronizar agora**, e
a tela diz há quantos dias o dado está parado, qualquer que seja o motivo.

**Falha deixa rastro, sempre.** Três caminhos de falha que antes sumiam agora
gravam linha em `sync_runs` e aparecem na tela em português: a linha rejeitada, a
escrita recusada pelo banco, e o arquivo de origem que não pôde ser lido.

Branch: `006-sync-pluggy/fase-1-sync` · commits `59d8506`, `dab902b`, `f5575cf`.

---

## 2. Critérios atendidos

Dezesseis critérios, **dois validadores cegos**. O primeiro devolveu
`CRITERIO_INVALIDO` — o critério mandava gravar com `app.query`, somente-leitura
desde o `001` — e achou três defeitos que viraram requisito. O segundo aprovou.
Veredicto integral em [`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

O mais importante: `POST /sincronizar` com uma fonte que viola chave estrangeira
devolve **200 e uma frase em português**, não 500, e a base fica com as mesmas
1.942 transações.

---

## 3. Como testar à mão

1. Prepare `/tmp/dash-s.sqlite` com `app.ingest` e `app.auth.seed`.
2. Rode `app.ingest` **de novo**.
3. **Esperado:** `select transactions_count, transactions_present from sync_runs`
   devolve `1942 1942` e depois `0 1942`.
4. Suba o app, abra `/`, e olhe o bloco **Os dados**.
5. **Esperado:** data e hora da última sincronização, em hora local.
6. Aponte `DASH_TRANSACTIONS_PATH` para um arquivo que não existe e aperte
   **Sincronizar agora**.
7. **Esperado:** 200, e "o arquivo de origem não pôde ser lido... Rode o
   consolidador antes de sincronizar."

---

## 4. Divergências

Nenhuma. Um critério foi corrigido depois de um `CRITERIO_INVALIDO` justo, e os
quatro apontamentos do segundo veredicto foram corrigidos em `f5575cf` com teste,
sem terceira rodada — régua registrada em `D8`.

---

## 5. Raio de impacto

- `app/migrations/sql/006_sync_semantics.sql` — o renome e as duas colunas novas.
- `app/ingest/loader.py` — conta inserções comparando o conjunto de
  identificadores **antes** do upsert, e o caminho de exceção agora grava falha.
- `app/sync/__init__.py` — a função que o comando e o botão chamam, `readable()`
  (a tradução da mensagem técnica) e `finished_on()` (a conversão de fuso, que
  mora num lugar só).
- `app/routers/summary.py` — `POST /sincronizar` e o contexto do bloco.
- `app/config.py` — `sync_source` e as credenciais da Pluggy.

---

## 6. Validações de campo pendentes

- **`006-sync-pluggy`** — a chamada real à API da Pluggy precisa de credencial
  válida e item não expirado; o MFA é interativo e não se automatiza. Já
  registrada no roadmap desde antes deste item.

---

## 7. Pendências que viraram roadmap

- **`app/sync/_after` roda fora de handler.** Uma exceção em
  `classify`/`recompute`/`rebuild` derruba a rota deixando um `sync_runs` que
  afirma sucesso com as tabelas derivadas paradas. Observação estrutural do
  validador, lida no código e não provocada. Vai para o roadmap como
  `012-sync-pos-carga-atomica`.
