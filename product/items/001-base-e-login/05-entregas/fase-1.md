## 1. O que foi implementado

**Item:** `001-base-e-login` · **Fase:** `1 — Base do projeto e schema`

Antes desta fase o repositório tinha documentos, dados extraídos e quatro
scripts soltos de ingestão e matemática financeira; não havia projeto Python,
banco nem forma de subir nada. Esta fase instala o projeto com `uv`, a leitura
de configuração do ambiente (aceitando as duas grafias de `PASSORD` e de
`GEMIMI_API_KEY`), a conexão SQLite, o runner de migração numerada e a migração
`001`, que cria `users`, `login_attempts`, `accounts`, `transactions` e
`sync_runs` — com valor em centavos inteiros no DDL e `pluggy_id` único.

Branch: `001-base-e-login/fase-1-base-e-schema` · commit `b055768`.

---

## 2. Critérios atendidos

Os doze critérios da fase foram executados por um validador cego, que não
recebeu plano nem brief. O veredicto integral, com a saída real de cada comando,
está em [`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

- [x] `[comando]` RF-01 — `rtk proxy uv sync --locked` sai com código 0.
      **Evidência:** → `Resolved 32 packages / Audited 30 packages`, EXIT=0.
- [x] `[estrutural]` RF-01 — `pyproject.toml` declara `fastapi`, `uvicorn`,
      `jinja2`, `itsdangerous`, `argon2-cffi`, `python-multipart` e
      `python-dotenv`; `pytest` e `httpx` no grupo de desenvolvimento; `uv.lock`
      na raiz.
      **Evidência:** `pyproject.toml:6-14` e `pyproject.toml:16-20`; `uv.lock`
      com 93,4 KB.
- [x] `[estrutural]` RF-02 — `app/__main__.py` chama `uvicorn.run` com
      `host="127.0.0.1"` e `port=8000`.
      **Evidência:** `app/__main__.py:7`.
- [x] `[comando]` RF-02 — `rtk proxy grep -rn "0\.0\.0\.0" app pyproject.toml`
      não imprime nenhuma linha.
      **Evidência:** nenhuma linha, EXIT=1 (código de "sem correspondência").
- [x] `[comando]` RF-03 — `rtk proxy git check-ignore -v data/dash.sqlite` sai
      com 0 citando o `.gitignore`.
      **Evidência:** → `.gitignore:5:data/	data/dash.sqlite`, EXIT=0.
- [x] `[estrutural]` RF-03 — `app/config.py` tem o caminho padrão do banco como
      `data/dash.sqlite`, sobrescrito por `DASH_DB_PATH`.
      **Evidência:** `app/config.py:7` e `app/config.py:40`.
- [x] `[comando]` RF-05 — a lista de tabelas do banco migrado é exatamente
      `accounts`, `login_attempts`, `schema_migrations`, `sync_runs`,
      `transactions`, `users`.
      **Evidência:** `app.query "select name from sqlite_master …"` imprimiu as
      seis linhas nessa ordem; `wc -l` → 6.
- [x] `[comportamental]` RF-04 — Dado `/tmp/dash-f1b.sqlite` inexistente, quando
      `create_app()` roda duas vezes, então a primeira imprime
      `applied 001_schema.sql` e `migrations applied: 1` e a segunda imprime
      `migrations applied: 0`.
      **Evidência:** as duas execuções, EXIT=0, e
      `select count(*), min(version) from schema_migrations` → `1 001`.
- [x] `[comando]` RF-07 — os tipos de `transactions.amount_cents` e
      `accounts.balance_cents` são `INTEGER`.
      **Evidência:** → `INTEGER INTEGER`, EXIT=0. Relido por `sqlite3` direto,
      sem passar pelo `app/`.
- [x] `[comportamental]` RF-11 — Dado o banco migrado com uma linha de
      `pluggy_id = 'abc-1'`, quando se insere a segunda com o mesmo valor, então
      o SQLite levanta `IntegrityError`.
      **Evidência:** `UNIQUE constraint failed: transactions.pluggy_id`
      (`app/migrations/sql/001_schema.sql:29`).
- [x] `[comportamental]` RF-21 (grafia com typo) — `PASSORD` e `GEMIMI_API_KEY`
      são lidos quando as canônicas faltam.
      **Evidência:** → `teste abc123 k-1`, EXIT=0.
- [x] `[comportamental]` RF-21 (grafia canônica) — `PASSWORD` e `GEMINI_API_KEY`
      vencem quando presentes.
      **Evidência:** → `teste xyz789 k-2`, EXIT=0 (`app/config.py:38-39`).

**Portões:** `rtk proxy .venv/bin/python -m pytest -q` → `14 passed`, EXIT=0;
`bash scripts/gates/gates_runner.sh` → `✓ gates: limpos`, EXIT=0. O portão de
lint não existe neste projeto — não há linter Python declarado — e o validador o
registrou como **não medido**, nem aprovado nem reprovado.

---

## 3. Como testar à mão

1. Na raiz do repositório, com o `.venv/` populado por `rtk proxy uv sync`.
2. `rm -f /tmp/dash-manual.sqlite && rtk proxy env DASH_DB_PATH=/tmp/dash-manual.sqlite .venv/bin/python -m app.migrate`
3. **Esperado:** duas linhas — `applied 001_schema.sql` e `migrations applied: 1`.
4. Repita o mesmo comando.
5. **Esperado:** uma linha — `migrations applied: 0`; nenhuma linha `applied`.
6. `rtk proxy env DASH_DB_PATH=/tmp/dash-manual.sqlite .venv/bin/python -m app.query "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"`
7. **Esperado:** as seis tabelas, em ordem alfabética.
8. `rtk proxy .venv/bin/python -m app` e, noutro terminal, `curl -i http://127.0.0.1:8000/`.
9. **Esperado:** `Uvicorn running on http://127.0.0.1:8000` e `HTTP/1.1 404` —
   esta fase não registra rota nenhuma; a porta chega na fase 3.

---

## 4. Divergências

nenhuma

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** A precisão medida do raio de impacto
> é **0,578** — cerca de 42% dos itens listados como candidatos são
> falso-positivo. Os confirmados abaixo foram lidos; os candidatos, não.

**Confirmados** (lidos, a dependência existe):

- `app/config.py:31` — `load_config` é o ponto único de leitura de ambiente. A
  fase 2 (ingestão) lê `transactions_path` e `accounts_glob` dele, e a fase 3
  lê `login`, `password` e `session_secret`.
- `app/db.py:7` — `connect` é o ponto único de abertura de conexão, com
  `PRAGMA foreign_keys = ON`. Toda escrita e leitura das fases seguintes passa
  por ele; a chave estrangeira de `transactions.account_id` só é cobrada porque
  o pragma está aqui.
- `app/migrations/sql/001_schema.sql` — o DDL é o contrato que as fases 2 e 3
  consomem. Coluna que faltar aqui vira migração `002`, nunca edição deste
  arquivo, que já foi aplicado.
- `app/query.py:20` — instrumento de evidência de quase todo critério deste
  item. Recusa qualquer instrução fora de `select` e `pragma`, e
  `tests/test_query.py` é quem prova que a recusa morde.
- `.github/workflows/harness.yml` — ganhou o job `testes`. Sem remote ele não
  executa nada nesta corrida; o portão local é `pytest` mais o `gates_runner.sh`.

**Candidatos** (não conferidos):

- `ingestao/pluggy_consolidate.py` — continua produzindo `data/processed/`, que
  a fase 2 vai ler. Nada nesta fase o toca.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **`.env.example` ensina a grafia errada.** O validador apontou: o modelo
  publica só `PASSORD=` e `GEMIMI_API_KEY=`, e quem clonar e copiar o modelo
  grava o typo no próprio `.env` — a compatibilidade com o ambiente existente
  vira o nome oficial que o projeto ensina. A correção é listar também
  `PASSWORD=` e `GEMINI_API_KEY=`, mantendo o fallback no código. **Não virou
  item de roadmap**: cabe na fase 3 deste mesmo item, que é a fase das
  credenciais, e mudar o arquivo agora invalidaria a árvore que o validador
  julgou nesta fase.
- **Não há portão de lint para Python.** É consequência declarada da ausência de
  pack de stack (`docs/plano.md`), não uma descoberta desta fase. Fica
  registrado aqui porque foi a primeira vez que um validador o mediu como
  ausente.
