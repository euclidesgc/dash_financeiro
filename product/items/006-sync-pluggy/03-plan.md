# Plano — 006-sync-pluggy

**Trilha:** rápida · **Brief:** `01-brief.md` · Uma fase.

## Fase 1 — A sincronização diz o que fez, e a tela diz quando foi

**Critérios de aceite:**

O banco é preparado por `rm -f /tmp/dash-006.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-006.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-006.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-006.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-006.key .venv/bin/python -m app`.

- [ ] `comando` — RF-01, RF-02, RF-04, RF-05
      Depois do preparo, `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-006.sqlite DASH_TODAY=2026-09-05 .venv/bin/python -m
      app.ingest` é executado **uma segunda vez** e sai com código 0. Então, com
      `Q` valendo `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-006.sqlite .venv/bin/python -m app.query`:
      `Q "select count(*) from transactions"` imprime `1942`;
      `Q "select transactions_count, transactions_present, status from sync_runs
      order by id"` imprime exatamente duas linhas, a primeira
      `1942 1942 ok` e a segunda `0 1942 ok`
- [ ] `comando` — RF-03
      `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-006-antigo.sqlite .venv/bin/python -c` com um trecho
      que cria o banco pela migração `001` apenas, insere uma linha em
      `sync_runs` com `transactions_count = 500`, roda `app.migrate` até o fim, e
      lê a linha de volta, imprime `transactions_present = 500` e
      `transactions_count = None`
- [ ] `comando` — RF-07, RF-10
      `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-006.sqlite
      DASH_TODAY=2026-09-05 .venv/bin/python -m app.sync` sai com código 0 e
      imprime uma linha que começa com `sync ok` e traz `inserted=0`
- [ ] `comando` — RF-09
      `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-006.sqlite
      DASH_SYNC_SOURCE=pluggy .venv/bin/python -m app.sync` sai com código **1**,
      imprime uma mensagem que nomeia a variável de credencial que falta, e
      `select count(*) from sync_runs` devolve o **mesmo** número de antes
- [ ] `comportamental` — RF-08, RF-11
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/sincronizar` é executado
      *Então* a resposta é `200`, o HTML traz o bloco `id="sincronizacao"` com a
      data da última sincronização bem-sucedida no formato `DD/MM/AAAA` e a
      contagem de linhas inseridas
- [ ] `comportamental` — RF-12
      *Dado* o servidor rodando, um cookie válido, e uma linha de falha inserida
      em `sync_runs` por `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-006.sqlite .venv/bin/python -m app.query "insert
      into sync_runs (started_at, finished_at, source, status, message) values
      ('2026-09-05T10:00:00', '2026-09-05T10:00:01', 'teste', 'failed', 'o item
      da Pluggy expirou')"`
      *Quando* `GET /?data=2026-09-05` é buscada
      *Então* o bloco `id="sincronizacao"` traz a string `o item da Pluggy
      expirou`, traz a palavra `falhou`, e **continua** trazendo a data da última
      sincronização bem-sucedida
- [ ] `comportamental` — RF-13, RF-14
      *Dado* um banco novo preparado só com `app.migrate` e `app.auth.seed`, e o
      servidor subido contra ele
      *Quando* `GET /?data=2026-09-05` é buscada com cookie válido
      *Então* a resposta é `200` e o bloco `id="sincronizacao"` traz
      `Nunca sincronizado.` e a string `python -m app.sync`
- [ ] `comportamental` — RF-13
      *Dado* o servidor rodando contra `/tmp/dash-006.sqlite`
      *Quando* `GET /?data=2026-12-25` é buscada com cookie válido
      *Então* o bloco `id="sincronizacao"` traz a palavra `dias` e um número
      maior que `100`, porque a última sincronização é de setembro
- [ ] `comportamental` — RF-15
      *Dado* o servidor rodando e um cookie válido
      *Quando* `GET /?data=2026-09-05` é buscada
      *Então* o HTML traz um `form` com `action="/sincronizar"` e `method="post"`,
      e o texto do botão é `Sincronizar agora`

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz sai com código 0
- [ ] `comando` — portão de lint
      `rtk proxy bash scripts/lint.sh` sai com código 0
- [ ] `comando` — RF-16
      `rtk proxy grep -REn --exclude-dir=__pycache__ "\b1942\b" app` não imprime
      nenhuma linha
- [ ] `comportamental` — RF-08 guarda
      *Dado* nenhuma sessão
      *Quando* `rtk proxy curl -s -o /dev/null -w "%{http_code}" -X POST
      http://127.0.0.1:8000/sincronizar` é executado
      *Então* a resposta é `302`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Migração `006_sync_semantics.sql`: renomeia a coluna de contagem para
      integridade e cria a de inserção, nula para o passado.
      Justificativa: RF-01 a RF-03 — o número que existe hoje é prova de
      integridade com o nome errado; inventar o histórico de inserções seria
      pior que declará-lo desconhecido.
- [ ] 1.2 `app/ingest/loader.py` passa a contar inserções, comparando o conjunto
      de identificadores presentes **antes** do upsert.
      Justificativa: RF-01, RF-05 — não inserir nada é sucesso, e a tela precisa
      saber a diferença entre "rodou e não mudou nada" e "não rodou".
- [ ] 1.3 `app/sync/__init__.py` e `app/sync/__main__.py`: uma função que o
      comando e a rota chamam, e a recusa por credencial ausente.
      Justificativa: RF-07 a RF-10 e D4 — sync que se comporta diferente pelo
      botão e pelo cron é o defeito que só aparece no dia em que importa.
- [ ] 1.4 `POST /sincronizar` em `app/routers/summary.py` e o fragmento
      `resumo_sincronizacao.html`.
      Justificativa: RF-08, RF-11 a RF-15 — sync que falha em silêncio faz o
      painel mostrar dado velho com cara de dado fresco.
- [ ] 1.5 `tests/test_sync.py`.
      Justificativa: RF-04 a RF-06 — a não-duplicação é a promessa central e ela
      não quebra a tela quando falha; ela só mente.

## Validações de campo pendentes

- A chamada real à API da Pluggy, que precisa de credencial válida e de item não
  expirado. Já registrada no roadmap desde antes deste item.
