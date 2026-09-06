# Veredicto — 001-base-e-login, fase 1

VEREDICTO: APROVADO

```
Portões
  lint/analyze: NÃO REGISTRADO — o projeto não declara linter/typechecker Python.
                `grep -rn -E "ruff|mypy|flake8|black|pyright" pyproject.toml .github/workflows/`
                sai com código 1 (nenhuma linha) e `.venv/bin/` não tem nenhum
                desses binários. Não há portão de lint para medir; não foi
                tratado como aprovado nem como falha.
  testes:       OK — `rtk proxy .venv/bin/python -m pytest -q`
                → "..............  [100%]  /  14 passed in 0.35s", EXIT=0
  gates:        OK — `rtk proxy bash scripts/gates/gates_runner.sh`
                → "✓ gates: limpos (árvore completa, 50 arquivo(s) considerados)", EXIT=0

Critérios de aceite
  [x] comando RF-01 — `uv sync --locked` sai com 0
      → "Resolved 32 packages in 0.75ms / Audited 30 packages in 0.18ms", EXIT=0

  [x] estrutural RF-01 — dependências declaradas + uv.lock
      /home/euclidesgc/development/dash_financeiro/pyproject.toml:6-14 traz em
      [project].dependencies: fastapi, uvicorn, jinja2, itsdangerous,
      argon2-cffi, python-multipart, python-dotenv (os sete pedidos).
      pyproject.toml:16-20 traz [dependency-groups].dev = ["pytest", "httpx"].
      uv.lock existe na raiz (93.4K).

  [x] estrutural RF-02 — uvicorn.run com host/port fixos
      app/__main__.py:7 → `uvicorn.run(create_app(), host="127.0.0.1", port=8000)`

  [x] comando RF-02 — nenhuma ocorrência de 0.0.0.0
      `rtk proxy grep -rn "0\.0\.0\.0" app pyproject.toml` → nenhuma linha
      impressa, EXIT=1 (código de "sem correspondência" do grep).

  [x] comando RF-03 — banco ignorado pelo git
      `rtk proxy git check-ignore -v data/dash.sqlite`
      → ".gitignore:5:data/	data/dash.sqlite", EXIT=0

  [x] estrutural RF-03 — caminho padrão do banco
      app/config.py:7 → `DEFAULT_DB_PATH = "data/dash.sqlite"`
      app/config.py:40 → `db_path=_first(env, "DASH_DB_PATH") or DEFAULT_DB_PATH`

  [x] comando RF-05 — seis tabelas, na ordem
      Após `rm -f /tmp/dash-f1.sqlite && ... -m app.migrate`
      ("applied 001_schema.sql / migrations applied: 1", EXIT=0), o
      `... -m app.query "select name from sqlite_master ..."` imprimiu:
        accounts
        login_attempts
        schema_migrations
        sync_runs
        transactions
        users
      `| wc -l` → 6. EXIT=0.

  [x] comportamental RF-04 — migração idempotente no create_app
      /tmp/dash-f1b.sqlite inexistente (ls: "Arquivo ou diretório inexistente").
      RUN 1 → "applied 001_schema.sql" + "migrations applied: 1", EXIT=0
      RUN 2 → "migrations applied: 0", sem nenhuma linha iniciada por "applied", EXIT=0
      `... -m app.query "select count(*), min(version) from schema_migrations"`
      → "1 001", EXIT=0

  [x] comando RF-07 — valor em inteiro
      `... -m app.query "select (select type from pragma_table_info('transactions')
      where name='amount_cents'), (select type from pragma_table_info('accounts')
      where name='balance_cents')"` → "INTEGER INTEGER", EXIT=0

  [x] comportamental RF-11 — pluggy_id único
      Inserida `('abc-1','acc-1','2026-09-05',-100)` → "primeira linha inserida: 1".
      Segunda inserção com o mesmo pluggy_id:
        tipo: sqlite3.IntegrityError
        mensagem: UNIQUE constraint failed: transactions.pluggy_id
      Origem no schema: app/migrations/sql/001_schema.sql:29 —
      `pluggy_id TEXT NOT NULL UNIQUE`

  [x] comportamental RF-21 (nomes com erro de digitação)
      `env -u PASSWORD -u GEMINI_API_KEY DASH_ENV_FILE=/dev/null LOGIN=teste
      PASSORD=abc123 GEMIMI_API_KEY=k-1 ...` → "teste abc123 k-1", EXIT=0

  [x] comportamental RF-21 (nomes canônicos)
      `env -u PASSORD -u GEMIMI_API_KEY DASH_ENV_FILE=/dev/null LOGIN=teste
      PASSWORD=xyz789 GEMINI_API_KEY=k-2 ...` → "teste xyz789 k-2", EXIT=0
      Fonte: app/config.py:38-39 aceita os dois nomes, com o canônico primeiro.

Instrumentos do implementer
  Nenhum critério dependeu da suíte de testes do avaliado — não executei
  tests/test_config.py, tests/test_migrations.py nem tests/test_query.py como
  evidência de critério algum (rodei a suíte só como portão).
  Ressalva declarada: os critérios RF-04, RF-05 e RF-07 mandam medir através de
  `python -m app.query`, que é código escrito nesta mesma fase
  (app/query.py). Para não aceitar o instrumento pela palavra dele, reli o
  mesmo estado com sqlite3 direto, sem passar por app/:
    tabelas → ['accounts','login_attempts','schema_migrations','sync_runs','transactions','users']
    schema_migrations → (1, '001')
    amount_cents → ('INTEGER',)   balance_cents → ('INTEGER',)
  Confere com o que app.query imprimiu.

Apontamentos
  .env.example:2-3 — o arquivo-modelo publica apenas `PASSORD=` e
  `GEMIMI_API_KEY=`, os nomes com erro de digitação. O código aceita as duas
  grafias e prefere a canônica (app/config.py:38-39), então nenhum critério
  quebra; o problema é que quem clona e copia o modelo grava a grafia errada no
  próprio `.env`, e a variante com erro deixa de ser compatibilidade com o
  ambiente já existente e vira o nome oficial que o projeto ensina. Sugestão de
  correção fora desta fase: listar `PASSWORD=` e `GEMINI_API_KEY=` no modelo,
  mantendo o fallback no código para quem já tem `.env` antigo.
  Não afeta o veredicto.
```

Observações fora do formato, para a thread principal:

- **Nada do plano/spec/brief vazou no despacho.** Recebi objetivo da fase, critérios tipados e ponteiro para o trabalho — o envelope estava correto. O repositório contém documentos de planejamento (commit `64446d3`), e eu não os abri.
- **Verificação extra, não coberta por critério:** o objetivo da fase fala em "sobe o app em 127.0.0.1:8000", mas o critério RF-02 é só estrutural. Subi de fato — `DASH_DB_PATH=/tmp/dash-f1c.sqlite .venv/bin/python -m app` imprimiu `Uvicorn running on http://127.0.0.1:8000` e `curl http://127.0.0.1:8000/` devolveu `HTTP 404` (esperado: a fase 1 não registra rota nenhuma). Confirma o objetivo sem ampliar a régua.
- **Árvore de trabalho:** `product/state.json` está modificado e não commitado. É arquivo de estado do harness, fora do diff julgado (`c59df85..HEAD`); registro só para não passar despercebido na abertura do PR.
