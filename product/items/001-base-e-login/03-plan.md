# Plano — Base e login

**Item:** `001-base-e-login` · **Trilha:** rápida · **Brief:** `01-brief.md`
(aprovado em 2026-09-06)

## Objetivo

Ao fim das quatro fases existe um projeto Python com dependências travadas, um
banco SQLite em `data/dash.sqlite` criado por migração numerada, os 1.942
lançamentos e as 12 contas gravados em centavos inteiros com o sinal
normalizado, uma porta que exige sessão em toda rota registrada — `/health`
incluído — e a primeira superfície do produto saindo de uma linguagem visual
escrita antes dela.

A quebra é por **contrato**, não por camada: a fase 1 fixa a forma do dado
(schema e configuração) porque premissa errada de contrato se espalha de uma vez
para todos os consumidores; a fase 2 e a fase 3 consomem esse contrato por
frentes disjuntas (carga de dados × porta HTTP) e por isso correm em paralelo; a
fase 4 veste a única tela do item, e só ela existe depois de a tela crua existir.

Convenções que atravessam o plano e que os comandos dos critérios assumem:
identificadores de código em inglês e texto de interface em pt-BR (norma 16); o
caminho do banco vem de `DASH_DB_PATH` e cai em `data/dash.sqlite`; o arquivo de
ambiente vem de `DASH_ENV_FILE` e cai em `.env`; a fonte da ingestão vem de
`DASH_TRANSACTIONS_PATH` e `DASH_ACCOUNTS_GLOB`. Nenhum comando deste plano lê o
`.env` do dono: onde é preciso credencial determinística, ela é declarada na
própria linha do comando.

## Fase 1 — Base do projeto e schema (python)

**Objetivo da fase:** um clone limpo instala o ambiente com `uv`, sobe o app em
`127.0.0.1:8000` e aplica a migração `001` que cria as cinco tabelas do item mais
a tabela de controle.

**Critérios de aceite:**

- [ ] `comando` — RF-01
      `rtk proxy uv sync --locked` executado na raiz do repositório sai com
      código 0
- [ ] `estrutural` — RF-01
      `pyproject.toml` declara em `[project].dependencies` os pacotes `fastapi`,
      `uvicorn`, `jinja2`, `itsdangerous`, `argon2-cffi`, `python-multipart` e
      `python-dotenv`, declara `pytest` e `httpx` no grupo de desenvolvimento, e
      existe `uv.lock` na raiz do repositório
- [ ] `estrutural` — RF-02
      `app/__main__.py` chama `uvicorn.run` com os argumentos
      `host="127.0.0.1"` e `port=8000`
- [ ] `comando` — RF-02
      `rtk proxy grep -rn "0\.0\.0\.0" app pyproject.toml` não imprime nenhuma
      linha
- [ ] `comando` — RF-03
      `rtk proxy git check-ignore -v data/dash.sqlite` sai com código 0 e imprime
      uma linha citando `.gitignore`
- [ ] `estrutural` — RF-03
      `app/config.py` define o caminho padrão do banco como a string literal
      `data/dash.sqlite`, sobrescrito pela variável de ambiente `DASH_DB_PATH`
- [ ] `comando` — RF-05
      Depois de `rm -f /tmp/dash-f1.sqlite && rtk proxy env
      DASH_DB_PATH=/tmp/dash-f1.sqlite .venv/bin/python -m app.migrate`, o
      comando `rtk proxy env DASH_DB_PATH=/tmp/dash-f1.sqlite .venv/bin/python -m
      app.query "select name from sqlite_master where type='table' and name not
      like 'sqlite_%' order by name"` imprime exatamente seis linhas, nesta
      ordem: `accounts`, `login_attempts`, `schema_migrations`, `sync_runs`,
      `transactions`, `users`
- [ ] `comportamental` — RF-04
      *Dado* que `/tmp/dash-f1b.sqlite` não existe
      *Quando* `rtk proxy env DASH_DB_PATH=/tmp/dash-f1b.sqlite
      .venv/bin/python -c "from app.main import create_app; create_app()"` é
      executado duas vezes seguidas
      *Então* a primeira execução imprime a linha `applied 001_schema.sql` e a
      linha `migrations applied: 1`, a segunda imprime `migrations applied: 0` e
      nenhuma linha começando por `applied`, e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f1b.sqlite .venv/bin/python -m app.query "select
      count(*), min(version) from schema_migrations"` imprime `1 001`
- [ ] `comando` — RF-07
      Com o banco `/tmp/dash-f1.sqlite` migrado, `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f1.sqlite .venv/bin/python -m app.query "select
      (select type from pragma_table_info('transactions') where
      name='amount_cents'), (select type from pragma_table_info('accounts') where
      name='balance_cents')"` imprime `INTEGER INTEGER`
- [ ] `comportamental` — RF-11
      *Dado* o banco `/tmp/dash-f1.sqlite` com a migração `001` aplicada e uma
      linha em `transactions` com `pluggy_id = 'abc-1'`
      *Quando* se insere uma segunda linha em `transactions` com o mesmo
      `pluggy_id = 'abc-1'`
      *Então* o SQLite levanta `sqlite3.IntegrityError` com mensagem contendo
      `UNIQUE constraint failed: transactions.pluggy_id`
- [ ] `comportamental` — RF-21 · ver `04-divergencias/D-003.md`
      *Dado* o ambiente sem `PASSWORD` e sem `GEMINI_API_KEY`
      *Quando* `rtk proxy env -u PASSWORD -u GEMINI_API_KEY
      DASH_ENV_FILE=/dev/null LOGIN=teste PASSORD=abc123 GEMIMI_API_KEY=k-1
      .venv/bin/python -c "from app.config import load_config; c = load_config();
      print(c.login, c.password, c.gemini_api_key)"` é executado
      *Então* a saída é a linha `teste None None`: a grafia com typo não é lida
- [ ] `comportamental` — RF-21
      *Dado* o ambiente sem `PASSORD` e sem `GEMIMI_API_KEY`
      *Quando* `rtk proxy env -u PASSORD -u GEMIMI_API_KEY
      DASH_ENV_FILE=/dev/null LOGIN=teste PASSWORD=xyz789 GEMINI_API_KEY=k-2
      .venv/bin/python -c "from app.config import load_config; c = load_config();
      print(c.login, c.password, c.gemini_api_key)"` é executado
      *Então* a saída é a linha `teste xyz789 k-2`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Criar `pyproject.toml` com `requires-python = ">=3.12"`, as
      dependências de produção (`fastapi`, `uvicorn`, `jinja2`, `itsdangerous`,
      `argon2-cffi`, `python-multipart`, `python-dotenv`), o grupo de
      desenvolvimento (`pytest`, `httpx`) e `[tool.pytest.ini_options]` com
      `testpaths = ["tests"]`; gerar `uv.lock` com `uv lock`.
      Justificativa: norma 15 — dependência não declarada não existe; o lock é o
      que faz `uv sync --locked` num clone limpo produzir o mesmo ambiente que
      esta máquina, e `argon2-cffi` e `itsdangerous` entram já aqui porque
      trocar o manifesto no meio de uma fase paralela geraria conflito.
- [ ] 1.2 Criar `app/config.py`.
      Método: `load_config(env: Mapping[str, str] | None = None) -> Config`, com
      `Config` guardando `login`, `password`, `gemini_api_key`, `db_path`,
      `session_secret`, `transactions_path`, `accounts_glob`. Uma grafia por
      variável, `PASSWORD` e `GEMINI_API_KEY`, sem alias;
      `load_dotenv(os.environ.get("DASH_ENV_FILE", ".env"), override=False)`.
      Justificativa: RF-21 — o `.env` do dono usa a grafia correta
      (`04-divergencias/D-003.md`); `override=False` faz a variável passada na linha de comando
      vencer o arquivo, que é o que torna todo critério deste plano determinístico
      sem nunca ler o `.env`. `DASH_ENV_FILE` existe para o critério poder
      apontar para `/dev/null` e medir só o que ele mesmo declarou.
- [ ] 1.3 Criar `app/db.py`.
      Método: `connect(path: str | None = None) -> sqlite3.Connection`, com
      `PRAGMA foreign_keys = ON` e `row_factory = sqlite3.Row`.
      Justificativa: um ponto único de abertura é o que garante que a chave
      estrangeira de `transactions.account_id` seja cobrada — no SQLite ela vem
      desligada por conexão, e ligar em cada chamada é a forma que esquece uma.
- [ ] 1.4 Criar `app/migrations/runner.py`.
      Método: `apply_migrations(conn: sqlite3.Connection, folder: Path) ->
      list[str]`, que cria `schema_migrations(version TEXT PRIMARY KEY,
      applied_at TEXT NOT NULL)` se faltar, aplica em ordem crescente de nome os
      `*.sql` ainda não registrados, cada um na sua própria transação, e devolve
      os nomes aplicados.
      Justificativa: RF-04 e D4 — acrescentar tabela nos itens `002` em diante
      precisa ser barato, e a tabela de controle é o que impede a segunda subida
      de reaplicar o schema.
- [ ] 1.5 Criar `app/migrations/sql/001_schema.sql` com `users(id INTEGER
      PRIMARY KEY, login TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL)`, `login_attempts(id INTEGER PRIMARY KEY, ip TEXT
      NOT NULL, occurred_at TEXT NOT NULL, success INTEGER NOT NULL DEFAULT 0)`
      com índice em `(ip, occurred_at)`, `accounts(id TEXT PRIMARY KEY, name
      TEXT, type TEXT, subtype TEXT, institution TEXT, balance_cents INTEGER NOT
      NULL, updated_at TEXT)`, `transactions(id INTEGER PRIMARY KEY, pluggy_id
      TEXT NOT NULL UNIQUE, account_id TEXT NOT NULL REFERENCES accounts(id),
      date TEXT NOT NULL, description TEXT, amount_cents INTEGER NOT NULL, type
      TEXT, category_pluggy TEXT, category TEXT, installment_current INTEGER,
      installment_total INTEGER, is_transfer INTEGER NOT NULL DEFAULT 0,
      transfer_reason TEXT NOT NULL DEFAULT '', is_refund INTEGER NOT NULL
      DEFAULT 0, refunded_by TEXT, is_cash_withdrawal INTEGER NOT NULL DEFAULT
      0)` e `sync_runs(id INTEGER PRIMARY KEY, started_at TEXT NOT NULL,
      finished_at TEXT, source TEXT NOT NULL, status TEXT NOT NULL,
      transactions_count INTEGER, accounts_count INTEGER, message TEXT)`.
      Justificativa: RF-05, RF-07 e RF-11 — os centavos são `INTEGER` no DDL,
      não por convenção de quem escreve o `INSERT`, e `pluggy_id` único é o que
      faz reimportar não duplicar. Sem `AUTOINCREMENT` em nenhuma tabela: ele
      criaria `sqlite_sequence` e a lista de tabelas deixaria de ser a declarada.
- [ ] 1.6 Criar `app/migrate.py`, executável por `python -m app.migrate`,
      imprimindo uma linha `applied <arquivo>` por migração e a linha final
      `migrations applied: <n>`.
      Justificativa: a ingestão e os critérios precisam preparar o banco sem
      subir servidor; a saída fixa é o que torna a segunda execução verificável
      sem consultar o banco.
- [ ] 1.7 Criar `app/query.py`, executável por `python -m app.query "<SELECT>"`,
      que recusa com código 1 qualquer instrução que não comece por `select` ou
      `pragma`, e imprime uma linha por registro com as colunas separadas por um
      espaço.
      Justificativa: a evidência de banco não pode depender do binário `sqlite3`,
      que não é dependência declarada deste projeto (norma 15). A recusa de
      escrita existe porque uma ferramenta de consulta com poder de `DELETE` é
      uma porta de escrita disfarçada.
- [ ] 1.8 Criar `app/main.py`.
      Método: `create_app() -> FastAPI`, que na criação abre a conexão por
      `app.db.connect` e chama `apply_migrations`.
      Justificativa: RF-04 fala de "quando o app sobe" — migrar na criação é o
      que impede o app de servir uma tela contra um schema velho.
- [ ] 1.9 Criar `app/__main__.py` chamando `uvicorn.run(create_app(),
      host="127.0.0.1", port=8000)`.
      Justificativa: RF-02 e `docs/plano.md` — o endereço fica num lugar só, e
      `0.0.0.0` deixa de ser alcançável por descuido de linha de comando.
- [ ] 1.10 Criar `tests/test_config.py` (as duas grafias de cada variável),
      `tests/test_migrations.py` (segunda aplicação não reaplica) e
      `tests/test_query.py`, este último com o caso que prova que
      `python -m app.query "delete from users"` sai com código diferente de 0.
      Justificativa: `app/query.py` é o instrumento de evidência de quase todo
      critério deste plano; sem o teste que prova que ele recusa escrita, o
      instrumento não tem quem o reprove quando ele parar de morder.
- [ ] 1.11 Modificar `.github/workflows/harness.yml` acrescentando o job
      `testes`, que instala o `uv` por `run: curl -LsSf
      https://astral.sh/uv/install.sh | sh`, roda `uv sync --locked` e
      `uv run pytest -q`.
      Justificativa: esta é a peça que some — a suíte nasce nesta fase e nenhum
      fluxo a executa; sem o job, todo teste escrito daqui em diante só roda na
      máquina de quem o escreveu. O `uv` entra por script de instalação e não por
      ação de terceiro porque as ações deste fluxo são fixadas em SHA de 40
      caracteres, e acrescentar uma exige uma pinagem que este item não tem como
      auditar.
- [ ] 1.12 Criar `.env.example` com os nomes `LOGIN`, `PASSWORD`,
      `GEMINI_API_KEY`, `SESSION_SECRET`, `DASH_DB_PATH` e nenhum valor.
      Justificativa: RF-21 e RF-23 dependem dos nomes exatos, e o `.gitignore` já
      libera `!.env.example` — é o único lugar onde o nome de um segredo pode
      aparecer no repositório (norma 14).

## Fase 2 — Ingestão dos 1.942 lançamentos (python)

**Objetivo da fase:** carregar `data/processed/transacoes.json` e
`data/raw/accounts_*.json` para o banco em centavos inteiros, com transferência
e estorno marcados, sem duplicar e sem deixar carga pela metade.

**Critérios de aceite:**

- [ ] `comando` — RF-06, RF-10
      Depois de `rm -f /tmp/dash-f2.sqlite && rtk proxy env
      DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -m app.ingest`, o comando
      `rtk proxy env DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -m
      app.query "select (select count(*) from transactions), (select count(*)
      from accounts), (select sum(balance_cents) from accounts)"` imprime
      `1942 12 -2744971`
- [ ] `comando` — RF-07
      Com `/tmp/dash-f2.sqlite` carregado, `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -m app.query "select
      (select count(*) from transactions where typeof(amount_cents) <>
      'integer') + (select count(*) from accounts where typeof(balance_cents) <>
      'integer')"` imprime `0`
- [ ] `comando` — RF-08
      Com `/tmp/dash-f2.sqlite` carregado, `rtk proxy .venv/bin/python -c "import
      json, sqlite3; d = json.load(open('data/processed/transacoes.json')); m =
      dict(sqlite3.connect('/tmp/dash-f2.sqlite').execute('select pluggy_id,
      amount_cents from transactions')); print(sum(1 for l in d if m.get(l['id'])
      != round(l['valor'] * 100)))"` imprime `0`
- [ ] `comportamental` — RF-09
      *Dado* que `data/raw/v2_transactions_7486098e_2026-09-05_p2.json` traz o
      lançamento `c5120b3b-cb76-4e35-b2ec-2b6784e80cd9` com `"amount": -3310.23`
      e `"type": "CREDIT"` numa conta cujo `type` é `CREDIT`
      *Quando* `rtk proxy env DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python
      -m app.ingest` é executado
      *Então* `rtk proxy env DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -m
      app.query "select amount_cents from transactions where
      pluggy_id='c5120b3b-cb76-4e35-b2ec-2b6784e80cd9'"` imprime `331023`
- [ ] `comando` — RF-11
      Com `/tmp/dash-f2.sqlite` carregado, `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -m app.query "select
      count(*) from (select pluggy_id from transactions group by pluggy_id having
      count(*) > 1)"` imprime `0`
- [ ] `comportamental` — RF-12
      *Dado* o banco `/tmp/dash-f2c.sqlite` inexistente
      *Quando* `rtk proxy env DASH_DB_PATH=/tmp/dash-f2c.sqlite
      .venv/bin/python -m app.ingest` é executado duas vezes seguidas
      *Então* as duas execuções saem com código 0 e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f2c.sqlite .venv/bin/python -m app.query "select
      (select count(*) from transactions), (select count(*) from accounts),
      (select count(*) from sync_runs)"` imprime `1942 12 2`
- [ ] `comportamental` — RF-13
      *Dado* o banco `/tmp/dash-f2.sqlite` com 1942 linhas em `transactions`
      *Quando* o processo `rtk proxy env DASH_DB_PATH=/tmp/dash-f2.sqlite
      .venv/bin/python -m app` é iniciado, encerrado com `SIGTERM` e iniciado de
      novo
      *Então* `rtk proxy env DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -m
      app.query "select count(*) from transactions"` continua imprimindo `1942`
- [ ] `comando` — RF-14
      Com `/tmp/dash-f2.sqlite` carregado, `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -m app.query "select
      count(*) from transactions where is_transfer = 1 and trim(transfer_reason)
      <> ''"` imprime `152`
- [ ] `comportamental` — RF-15
      *Dado* que `data/processed/transacoes.json` traz o estorno
      `d4714f41-10cd-493d-b870-364c127dd6d0` (`ESTORNO PRESTACAO HAB`, valor
      `2462.56`) e o débito anterior `8b073fe4-d7e9-47e9-a24e-f8b6fcbeac43`
      (`DEBITO PRESTACAO HAB`, valor `-2462.56`)
      *Quando* a carga é feita em `/tmp/dash-f2.sqlite`
      *Então* `rtk proxy env DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -m
      app.query "select (select count(*) from transactions where is_refund = 1),
      (select refunded_by from transactions where
      pluggy_id='d4714f41-10cd-493d-b870-364c127dd6d0'), (select amount_cents
      from transactions where
      pluggy_id='8b073fe4-d7e9-47e9-a24e-f8b6fcbeac43')"` imprime
      `9 8b073fe4-d7e9-47e9-a24e-f8b6fcbeac43 -246256`
- [ ] `comando` — RF-16
      Com `/tmp/dash-f2.sqlite` carregado, `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f2.sqlite .venv/bin/python -c "import json; from
      app.db import connect; from app.queries.spending import
      total_spending_cents; d = json.load(open('data/processed/transacoes.json'));
      e = sum(round(l['valor'] * 100) for l in d if l['valor'] < 0 and not
      l['eh_transferencia'] and not l['eh_estorno'] and not l['estornada_por']);
      a = total_spending_cents(connect()); print(a, e); raise SystemExit(0 if a
      == e else 1)"` imprime os dois valores e sai com código 0
- [ ] `comportamental` — RF-17
      *Dado* `tests/fixtures/transacoes_invalidas.json` com três lançamentos, em
      que o de índice 1 não tem a chave `id` e o de índice 2 tem `"valor":
      10.005`, e `tests/fixtures/accounts_fixture.json` com uma conta
      *Quando* `rtk proxy env DASH_DB_PATH=/tmp/dash-f2-rejeita.sqlite
      DASH_TRANSACTIONS_PATH=tests/fixtures/transacoes_invalidas.json
      DASH_ACCOUNTS_GLOB=tests/fixtures/accounts_fixture.json .venv/bin/python -m
      app.ingest` é executado sobre um banco inexistente
      *Então* o código de saída é diferente de 0, a saída de erro contém as
      linhas `rejected index=1 reason=missing_pluggy_id` e `rejected index=2
      reason=fractional_cents`, e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f2-rejeita.sqlite .venv/bin/python -m app.query
      "select count(*) from transactions"` imprime `0`
- [ ] `comportamental` — RF-18
      *Dado* `tests/fixtures/transacoes_id_duplicado.json` com três lançamentos
      válidos em que o de índice 0 e o de índice 2 têm o mesmo `id`
      *Quando* `rtk proxy env DASH_DB_PATH=/tmp/dash-f2-rollback.sqlite
      DASH_TRANSACTIONS_PATH=tests/fixtures/transacoes_id_duplicado.json
      DASH_ACCOUNTS_GLOB=tests/fixtures/accounts_fixture.json .venv/bin/python -m
      app.ingest` é executado sobre um banco inexistente
      *Então* o código de saída é diferente de 0 e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f2-rollback.sqlite .venv/bin/python -m app.query
      "select (select count(*) from transactions), (select status from sync_runs),
      (select message from sync_runs)"` imprime uma linha começando por
      `0 failed` e contendo `accepted=3 written=2`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 2.1 Criar `app/ingest/source.py`.
      Métodos: `load_transactions(path: str) -> list[dict]` e
      `load_accounts(pattern: str) -> list[dict]`, este aceitando tanto o
      envelope `{"results": [...]}` quanto lista crua.
      Justificativa: D7 — a fonte é o consolidado que já rodou e os
      `accounts_*.json` brutos; os dois formatos convivem em `data/`, e tratar
      isso na borda mantém o carregador sem `if` de formato.
- [ ] 2.2 Criar `app/ingest/money.py`.
      Método: `to_cents(value: float | str) -> int`, usando
      `Decimal(str(value))`, levantando `FractionalCentsError` quando o resultado
      não é inteiro.
      Justificativa: invariante 22 — `float` arredonda por conta própria e o erro
      só aparece no total, longe da linha que o causou; RF-17 precisa que a
      recusa seja da linha, com o índice dela.
- [ ] 2.3 Criar `app/ingest/loader.py`.
      Método: `ingest(conn: sqlite3.Connection, *, transactions: list[dict],
      accounts: list[dict], source: str, now: datetime | None = None) ->
      IngestResult`, gravando tudo numa única transação SQL com
      `INSERT ... ON CONFLICT(pluggy_id) DO UPDATE`, comparando aceitos contra
      gravados ao fim e, em divergência, executando `rollback` e gravando a linha
      de `sync_runs` com `status = 'failed'` e `message` contendo
      `accepted=<n> written=<m>` **numa transação separada**.
      Justificativa: RF-18 — a linha de falha precisa sobreviver ao `rollback`
      que ela descreve, e é por isso que ela não pode estar dentro dele. A
      contagem de comparação sai da fonte, nunca de constante: `1942` e `12` são
      o que a fonte de 05/09/2026 tem, e congelá-los no código faria a ingestão do
      mês seguinte falhar por estar certa.
- [ ] 2.4 Criar `app/ingest/__main__.py`, executável por `python -m app.ingest`,
      que aplica as migrações pendentes antes de carregar, imprime em stderr uma
      linha `rejected index=<n> reason=<motivo> description=<descrição>` por
      linha recusada e sai com código 1 quando houve recusa ou divergência.
      Justificativa: RF-17 e RF-18 pedem código de saída diferente de zero — um
      carregador que só imprime o erro é indistinguível de um que funcionou para
      qualquer script que o chame.
- [ ] 2.5 No mapeamento de conta, gravar `balance_cents = -to_cents(balance)`
      quando `type == "CREDIT"` e `to_cents(balance)` no resto.
      Justificativa: RF-10 — a Pluggy devolve `balance: 8666.7` positivo para o
      Itaú Black, e saldo de cartão é dívida; sem a inversão a soma das contas dá
      +R$ 6.039,53 em vez de −R$ 27.449,71.
- [ ] 2.6 No mapeamento de transação, gravar `amount_cents = to_cents(l["valor"])`,
      `is_transfer` de `eh_transferencia`, `transfer_reason` de
      `motivo_transferencia`, `is_refund` de `eh_estorno`, `refunded_by` de
      `estornada_por` (vazio vira `NULL`) e `is_cash_withdrawal` de `eh_saque`.
      Justificativa: D7 e RF-08/RF-09 — o campo `valor` do consolidado **já** vem
      com o sinal invertido para cartão (`ingestao/pluggy_consolidate.py`, linha
      `valor = -bruto if conta.get("type") == "CREDIT"`); inverter de novo aqui
      dobraria a inversão e faria a compra de cartão virar receita.
- [ ] 2.7 Criar `app/queries/spending.py`.
      Método: `total_spending_cents(conn: sqlite3.Connection, start: str | None =
      None, end: str | None = None) -> int`, somando `amount_cents` negativos com
      `is_transfer = 0`, `is_refund = 0` e `refunded_by IS NULL`.
      Justificativa: invariantes 23 e 25 — cálculo financeiro é função testada, e
      o filtro que exclui os R$ 20.272,00 de transferência precisa morar em um
      lugar só; repetido em cada tela, ele será esquecido em uma delas.
- [ ] 2.8 Criar `tests/fixtures/transacoes_invalidas.json`,
      `tests/fixtures/transacoes_id_duplicado.json`,
      `tests/fixtures/accounts_fixture.json`, `tests/test_money.py`,
      `tests/test_ingest.py` (recusa de linha e rollback por divergência) e
      `tests/test_spending.py`.
      Justificativa: os dois modos de falha da ingestão são o que este item tem
      de mais caro para descobrir tarde. Quem executa é o `pytest`, rodado pelo
      job `testes` de `.github/workflows/harness.yml`.

## Fase 3 — Senha, sessão e rate-limit (python)

**Objetivo da fase:** ninguém alcança rota nenhuma sem sessão válida, e cinco
erros de senha do mesmo IP fecham a porta por quinze minutos mesmo depois de o
processo reiniciar.

**Critérios de aceite:**

- [ ] `comportamental` — RF-19, RF-20
      *Dado* o banco `/tmp/dash-f3.sqlite` migrado e com `users` vazia
      *Quando* `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-f3.sqlite LOGIN=teste PASSORD=senha-teste-9k2
      .venv/bin/python -m app.auth.seed` é executado duas vezes seguidas
      *Então* as duas execuções saem com código 0 e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f3.sqlite .venv/bin/python -m app.query "select
      count(*), substr(password_hash, 1, 10) from users"` imprime
      `1 $argon2id$`
- [ ] `comportamental` — RF-23
      *Dado* o banco `/tmp/dash-f3b.sqlite` migrado e com `users` vazia
      *Quando* `rtk proxy env -u PASSORD -u PASSWORD DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-f3b.sqlite LOGIN=teste .venv/bin/python -m
      app.auth.seed` é executado
      *Então* o código de saída é diferente de 0, a saída de erro contém a linha
      `missing environment variable: PASSWORD`, e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f3b.sqlite .venv/bin/python -m app.query "select
      count(*) from users"` imprime `0`
- [ ] `comportamental` — RF-23
      *Dado* o banco `/tmp/dash-f3d.sqlite` migrado e com `users` vazia
      *Quando* `rtk proxy env -u LOGIN DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-f3d.sqlite PASSORD=senha-teste-9k2
      .venv/bin/python -m app.auth.seed` é executado
      *Então* o código de saída é diferente de 0, a saída de erro contém a linha
      `missing environment variable: LOGIN`, e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f3d.sqlite .venv/bin/python -m app.query "select
      count(*) from users"` imprime `0`
- [ ] `comportamental` — RF-24
      *Dado* o servidor iniciado com `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-f3.sqlite LOGIN=teste PASSORD=senha-teste-9k2
      SESSION_SECRET=chave-do-servidor .venv/bin/python -m app` e o usuário
      `teste` semeado
      *Quando* `rtk proxy curl -i -s -X POST http://127.0.0.1:8000/login -d
      "login=teste&senha=senha-teste-9k2"` é executado
      *Então* a resposta é `302` com `Location: /`, e o cabeçalho `Set-Cookie`
      traz `dash_session=`, `HttpOnly`, `SameSite=Lax`, `Path=/` e `Max-Age=43200`
- [ ] `comportamental` — RF-26
      *Dado* o servidor rodando em `http://127.0.0.1:8000`
      *Quando* `rtk proxy curl -s -o /dev/null -w "%{http_code} %header{location}"
      http://127.0.0.1:8000/` é executado sem nenhum cookie
      *Então* a saída é `302 /login`
- [ ] `comportamental` — RF-27
      *Dado* o servidor rodando em `http://127.0.0.1:8000`
      *Quando* `rtk proxy curl -i -s http://127.0.0.1:8000/health` é executado
      sem nenhum cookie
      *Então* a resposta é `401`, o cabeçalho `content-type` contém
      `application/json` e o corpo é exatamente `{"detail":"nao autenticado"}`
- [ ] `comportamental` — RF-28
      *Dado* o servidor rodando e um cookie `dash_session` obtido de um
      `POST /login` com a credencial correta
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      http://127.0.0.1:8000/health` é executado
      *Então* a resposta é `200` e o corpo é exatamente `{"status":"ok"}`
- [ ] `comando` — RF-25
      `rtk proxy .venv/bin/python -m pytest -q tests/test_route_guard.py` sai com
      código 0, e o teste
      `tests/test_route_guard.py::test_every_registered_route_requires_session`
      percorre todas as rotas de `app.main.create_app()`, exclui apenas
      `GET /login` e `POST /login`, e afirma que cada rota restante — `/health`
      incluída — responde 302 ou 401 quando chamada sem cookie
- [ ] `comportamental` — RF-29
      *Dado* o servidor rodando com `SESSION_SECRET=chave-do-servidor` e o valor
      de cookie produzido por
      `itsdangerous.TimestampSigner("outra-chave").sign(b"teste").decode()`
      *Quando* `GET http://127.0.0.1:8000/` e `GET http://127.0.0.1:8000/health`
      são chamados com esse valor no cookie `dash_session`
      *Então* a primeira resposta é `302` com `Location: /login` e a segunda é
      `401`
- [ ] `comportamental` — RF-30
      *Dado* o servidor rodando com `SESSION_SECRET=chave-do-servidor` e o cookie
      produzido por `app.auth.session.issue_cookie("teste",
      secret="chave-do-servidor", now=time.time() - 43260)`
      *Quando* `GET http://127.0.0.1:8000/` é chamado com esse cookie
      *Então* a resposta é `302` com `Location: /login`
- [ ] `comportamental` — RF-31, RF-32
      *Dado* o servidor rodando com `DASH_DB_PATH=/tmp/dash-f3c.sqlite`, o
      usuário `teste` semeado e `login_attempts` vazia
      *Quando* seis `POST http://127.0.0.1:8000/login` com
      `login=teste&senha=errada` partem de `127.0.0.1` dentro de um minuto
      *Então* as cinco primeiras respondem `401`, a sexta responde `429` com
      `Retry-After` entre 1 e 900, e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f3c.sqlite .venv/bin/python -m app.query "select
      count(*) from login_attempts where ip = '127.0.0.1' and success = 0"`
      imprime `5`
- [ ] `comportamental` — RF-33, RF-34
      *Dado* cinco `POST /login` com senha errada já respondidos com `401` contra
      `DASH_DB_PATH=/tmp/dash-f3c.sqlite`
      *Quando* o processo do servidor é encerrado com `SIGTERM`, iniciado de novo
      com o mesmo `DASH_DB_PATH`, e recebe um `POST /login` com
      `login=teste&senha=senha-teste-9k2` (a senha **correta**)
      *Então* a resposta é `429` com `Retry-After` entre 1 e 900 e nenhum
      cabeçalho `Set-Cookie` com `dash_session`
- [ ] `comportamental` — RF-22
      *Dado* o servidor iniciado com `PASSORD=senha-teste-9k2` e o usuário
      semeado com essa senha
      *Quando* se coletam a saída de subida do processo, o HTML de
      `GET http://127.0.0.1:8000/login` e a saída de `rtk proxy env
      DASH_DB_PATH=/tmp/dash-f3.sqlite .venv/bin/python -m app.query "select
      login, password_hash, created_at from users"`
      *Então* a string `senha-teste-9k2` não aparece em nenhuma das três saídas
- [ ] `comportamental` — RF-40
      *Dado* `SESSION_SECRET` ausente do ambiente, o arquivo `/tmp/dash-key/session.key`
      inexistente, e o servidor iniciado com `rtk proxy env -u SESSION_SECRET
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-f3.sqlite
      DASH_KEY_PATH=/tmp/dash-key/session.key LOGIN=teste PASSORD=senha-teste-9k2
      .venv/bin/python -m app`, do qual se obteve um cookie `dash_session` pelo
      login
      *Quando* o processo é encerrado com `SIGTERM`, subido de novo com o mesmo
      comando, e `rtk proxy curl -s -o /dev/null -w '%{http_code}' -b
      "dash_session=<cookie>" http://127.0.0.1:8000/health` é executado
      *Então* a saída é `200` e `rtk proxy stat -c '%a'
      /tmp/dash-key/session.key` imprime `600`
- [ ] `comportamental` — RF-40
      *Dado* o servidor iniciado com `rtk proxy env DASH_ENV_FILE=/dev/null
      DASH_DB_PATH=/tmp/dash-f3.sqlite LOGIN=teste PASSORD=senha-teste-9k2
      SESSION_SECRET=segredo-de-teste-7h4 .venv/bin/python -m app
      > /tmp/dash-f3-servidor.log 2>&1`
      *Quando* `rtk proxy curl -s http://127.0.0.1:8000/login >
      /tmp/dash-f3-login.html` é executado e o processo é encerrado
      *Então* `rtk proxy grep -c segredo-de-teste-7h4 /tmp/dash-f3-servidor.log
      /tmp/dash-f3-login.html` imprime `/tmp/dash-f3-servidor.log:0` e
      `/tmp/dash-f3-login.html:0`
- [ ] `comportamental` — RF-39
      *Dado* o servidor rodando e um cookie `dash_session` válido
      *Quando* `rtk proxy curl -i -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/logout` é executado
      *Então* a resposta é `302` com `Location: /login`, o `Set-Cookie` de
      `dash_session` traz `Max-Age=0`, e um `GET http://127.0.0.1:8000/` feito em
      seguida com o cookie antigo responde `302` com `Location: /login`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 3.1 Criar `app/auth/password.py`.
      Métodos: `hash_password(plain: str) -> str` e `verify_password(plain: str,
      stored: str) -> bool`, sobre `argon2.PasswordHasher`.
      Justificativa: RF-19 — o prefixo `$argon2id$` é do formato da própria
      biblioteca; escrever o hash à mão perderia os parâmetros de custo junto.
- [ ] 3.2 Criar `app/auth/seed.py`.
      Método: `seed_user(conn: sqlite3.Connection, login: str, password: str) ->
      None`, com `INSERT ... ON CONFLICT(login) DO UPDATE`, e CLI
      `python -m app.auth.seed` que sai com código 1 imprimindo
      `missing environment variable: LOGIN` ou
      `missing environment variable: PASSWORD` quando falta a variável.
      Justificativa: RF-20 e RF-23 — redefinir senha neste produto é editar o
      `.env` e rodar o seed, então rodar duas vezes não pode criar um segundo
      usuário; e a mensagem nomeia a variável sem imprimir valor, que é o que
      transforma o erro mudo desta corrida em erro legível em um ciclo.
- [ ] 3.3 Criar `app/auth/session.py`.
      Métodos: `issue_cookie(login: str, *, secret: str, now: float | None =
      None) -> str` e `read_cookie(raw: str, *, secret: str, now: float | None =
      None) -> str | None`, sobre `itsdangerous.TimestampSigner` com
      `max_age=43200`.
      Justificativa: D5 e RF-30 — o `now` explícito é o que torna a expiração
      verificável sem relógio falso nem espera de doze horas. O segredo vem de
      `SESSION_SECRET`; na ausência dele, `app/config.py` gera e persiste
      `data/session.key` com modo 600, porque `data/` está fora do controle de
      versão (norma 14) e uma chave sorteada a cada subida derrubaria a sessão a
      cada `--reload`.
- [ ] 3.4 Criar `app/auth/rate_limit.py`.
      Métodos: `record_failure(conn, ip: str, *, now: datetime | None = None) ->
      None` e `blocked_seconds(conn, ip: str, *, now: datetime | None = None) ->
      int`, com janela deslizante de 900 s e limite de 5 falhas; tentativa já
      bloqueada **não** é gravada.
      Justificativa: D6 e RF-34 — contador em memória zera a cada reinício e um
      limite que some quando o processo reinicia não é limite. Gravar a tentativa
      bloqueada estenderia a janela sozinha e o bloqueio nunca expiraria.
- [ ] 3.5 Criar `app/auth/guard.py` — middleware que exige sessão em toda rota
      registrada, com exceção apenas de `GET /login` e `POST /login`, respondendo
      401 com `{"detail":"nao autenticado"}` quando o caminho começa por `/api/`
      ou é `/health`, e 302 para `/login` no restante.
      Justificativa: invariante 24 e RF-25/26/27 — a exceção do próprio `/login`
      é o que impede o laço de redirecionamento que RF-26 criaria sozinho; ela é
      a única, e `/health` não é uma delas (D8).
- [ ] 3.6 Criar `app/routers/auth.py` com `GET /login` (formulário),
      `POST /login` (form `login` e `senha`) e `POST /logout`.
      Justificativa: os nomes dos campos são o contrato que a fase 4 consome no
      template; inventá-los na tela depois custaria a rota inteira.
- [ ] 3.7 Criar `app/routers/pages.py` com `GET /` e `app/routers/health.py` com
      `GET /health` devolvendo `{"status": "ok"}`.
      Justificativa: RF-28 — `/health` existe para provar que a guarda vale
      inclusive onde a convenção do mercado abriria exceção.
- [ ] 3.8 Criar `app/templates/base.html` e `app/templates/login.html` em versão
      crua — formulário, rótulos em pt-BR, área de mensagem de erro — sem
      nenhuma decisão de cor, espaçamento ou tipografia.
      Justificativa: a linguagem visual ainda não existe, e escolher cor aqui
      criaria valor cru para a fase 4 desfazer (RF-36).
- [ ] 3.9 Modificar `app/main.py` para registrar os routers e o middleware de
      guarda, **sem** montar `StaticFiles`.
      Justificativa: um mount de estáticos é uma rota registrada servindo arquivo
      sem sessão, e RF-25 não abre exceção; a folha de estilo entra na página por
      injeção no template (etapa 4.4). Enquanto a única tela é o login, não há o
      que servir estaticamente.
- [ ] 3.10 Criar `tests/test_route_guard.py` (a varredura de todas as rotas
      registradas), `tests/test_session.py` (assinatura estranha e expiração por
      `now`), `tests/test_rate_limit.py` (a sexta tentativa e a persistência) e
      `tests/test_login.py`, usando `fastapi.testclient` sobre `httpx`.
      Justificativa: a varredura de rotas é o instrumento que cobra RF-25 em toda
      rota que os itens `002` em diante acrescentarem — é ele que impede a
      próxima rota de nascer aberta. Quem executa é o `pytest`, rodado pelo job
      `testes` de `.github/workflows/harness.yml`.

## Fase 4 — Linguagem visual e tela de login (tela)

**Objetivo da fase:** existe a linguagem visual escrita do produto, e a tela de
login sai dela — legível nos dois temas, navegável por teclado e sem rolagem
horizontal em 375, 768 e 1440 px.

**Critérios de aceite:**

- [ ] `estrutural` — RF-35
      `product/00-linguagem-visual.md` contém as seções `## Paleta`,
      `## Tipografia`, `## Espaçamento`, `## Raio`, `## Foco`, `## Movimento` e
      `## Pares de contraste`, e cada uma das seis primeiras lista os tokens com
      o valor de cada um (por exemplo `--color-bg: #0b0e14`)
- [ ] `estrutural` — RF-36
      `app/static/css/tokens.css` declara em `:root` toda custom property
      listada em `product/00-linguagem-visual.md`, e traz um bloco
      `@media (prefers-color-scheme: dark)` que redefine as properties de cor
- [ ] `comando` — RF-36
      `rtk proxy grep -rnE "#[0-9a-fA-F]{3,8}|rgb\(|hsl\(" app/templates
      app/static/css --include=*.html --include=*.css --exclude=tokens.css` não
      imprime nenhuma linha
- [ ] `comportamental` — RF-37
      *Dado* o servidor rodando e a página `http://127.0.0.1:8000/login` aberta
      no Chromium
      *Quando* a janela é ajustada para as larguras de viewport 375, 768 e 1440
      px, com altura de 800 px
      *Então* em cada uma das três larguras
      `document.documentElement.scrollWidth <= window.innerWidth` avalia como
      `true`
- [ ] `estrutural` — RF-37
      Existem os arquivos `product/items/001-base-e-login/06-capturas/login-375.png`,
      `login-768.png`, `login-1440.png`, `login-erro-375.png` e
      `login-dark-1440.png`, cada um com mais de 1024 bytes
- [ ] `comportamental` — RF-38
      *Dado* o formulário de `http://127.0.0.1:8000/login` aberto no Chromium
      *Quando* é enviado com `login=teste` e `senha=errada`, e depois com
      `login=nao-existe` e `senha=qualquer`
      *Então* os dois envios reexibem o formulário com a mesma mensagem,
      `Login ou senha inválidos.`, aparecendo uma única vez no HTML, o HTML
      devolvido não contém as strings `errada` nem `qualquer`, e o campo de senha
      volta com valor vazio
- [ ] `comportamental` — RF-42
      *Dado* a página `http://127.0.0.1:8000/login` aberta no Chromium
      *Quando* a tecla `Tab` move o foco para o campo de senha e, em seguida,
      para o botão de entrar
      *Então* em cada um deles `getComputedStyle(el).outlineStyle` é diferente de
      `none` e `parseFloat(getComputedStyle(el).outlineWidth)` é maior ou igual a
      2
- [ ] `comportamental` — RF-43
      *Dado* os pares listados na seção `## Pares de contraste` de
      `product/00-linguagem-visual.md`
      *Quando* `app.design.contrast.contrast_ratio` é aplicada aos valores desses
      tokens lidos de `app/static/css/tokens.css`, uma vez com o bloco `:root` e
      uma vez com o bloco `@media (prefers-color-scheme: dark)`
      *Então* nenhum par de texto sobre fundo devolve razão menor que 4.5 e
      nenhum par de borda de foco sobre fundo devolve razão menor que 3.0
- [ ] `estrutural` — RF-43
      Existe `app/design/contrast.py` exportando
      `contrast_ratio(hex_a: str, hex_b: str) -> float`, e `tests/test_contrast.py`
      contém um caso que espera `contrast_ratio("#000000", "#ffffff") == 21` e um
      caso que espera `contrast_ratio("#777777", "#888888") < 4.5`
- [ ] `comportamental` — RF-44
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado
      *Quando* `http://127.0.0.1:8000/login` é carregada
      *Então* para todo elemento devolvido por `document.querySelectorAll("*")`,
      `getComputedStyle(el).animationDuration` e
      `getComputedStyle(el).transitionDuration` valem `0s`
- [ ] `comportamental` — RF-45
      *Dado* o Chromium com `prefers-color-scheme: dark` emulado
      *Quando* `http://127.0.0.1:8000/login` é carregada em 1440 px
      *Então* `getComputedStyle(document.body).backgroundColor` corresponde ao
      valor de `--color-bg` declarado no bloco
      `@media (prefers-color-scheme: dark)` de `app/static/css/tokens.css`, e é
      diferente do valor de `--color-bg` declarado em `:root`

**Critérios de integração:**

- [ ] `comando` — portão local, no lugar do CI que este repositório não tem
      `rtk proxy .venv/bin/python -m pytest -q` executado na raiz sai com código 0
- [ ] `estrutural` — RF-24
      `app/templates/login.html` contém um `<form>` com `method="post"` e
      `action="/login"`, um campo `name="login"` e um campo `name="senha"`, e a
      rota `POST /login` em `app/routers/auth.py` lê exatamente esses dois nomes
      de campo
- [ ] `comportamental` — RF-06, RF-24, RF-28
      *Dado* o banco `/tmp/dash-e2e.sqlite` inexistente
      *Quando* são executados em sequência `rtk proxy env
      DASH_DB_PATH=/tmp/dash-e2e.sqlite .venv/bin/python -m app.ingest`, `rtk
      proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-e2e.sqlite
      LOGIN=teste PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`, a
      subida do servidor com as mesmas variáveis, um `POST /login` com
      `login=teste&senha=senha-teste-9k2` e um `GET /health` com o cookie
      recebido
      *Então* o `POST /login` responde `302` com `Location: /`, o `GET /health`
      responde `200` com corpo `{"status":"ok"}`, e `rtk proxy env
      DASH_DB_PATH=/tmp/dash-e2e.sqlite .venv/bin/python -m app.query "select
      count(*) from transactions"` imprime `1942`
- [ ] `comportamental` — RF-41
      *Dado* o servidor rodando com a tela de login vestida
      *Quando* `GET /`, `GET /health`, `POST /logout` e
      `GET /static/css/tokens.css` são chamados sem nenhum cookie
      *Então* as respostas são, na ordem, `302` com `Location: /login`, `401`,
      `302` com `Location: /login` e `302` com `Location: /login`
- [ ] `estrutural` — RF-41
      A tabela de rotas de `app.main.create_app()` não contém nenhuma rota cujo
      caminho comece por `/static`, e `app/main.py` não chama
      `app.mount` nem importa `StaticFiles`
- [ ] `comportamental` — RF-41
      *Dado* o servidor rodando com a tela de login vestida
      *Quando* `rtk proxy curl -s http://127.0.0.1:8000/login` é executado
      *Então* o HTML devolvido contém um bloco `<style>` com a declaração
      `--color-bg`, e a mesma declaração existe em `app/static/css/tokens.css`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 4.1 Carregar a skill `frontend-design` antes de escrever qualquer marcação
      ou folha de estilo.
      Justificativa: invariante 27 — ela é a norma visual deste projeto e cobre a
      lacuna que a ausência de pack de stack Python abriu; carregá-la depois de a
      tela existir só serve para revisá-la.
- [ ] 4.2 Criar `product/00-linguagem-visual.md` com paleta, escala tipográfica,
      escala de espaçamento, raio, foco, movimento e a tabela de pares de
      contraste, cada token com o valor.
      Justificativa: RF-35 — o documento é canônico do projeto e nasce antes da
      primeira tela; é dele que as telas dos itens `002` em diante saem sem
      renegociar cor a cada item. Sem a tabela de pares, "contraste AA" não tem
      o que medir.
- [ ] 4.3 Criar `app/static/css/tokens.css` com as custom properties em `:root`
      e o bloco `@media (prefers-color-scheme: dark)`, incluindo
      `font-variant-numeric: tabular-nums` na classe de cifra e um bloco
      `@media (prefers-reduced-motion: reduce)` zerando duração de animação e
      transição.
      Justificativa: `docs/plano.md` — algarismo tabular é requisito e não gosto,
      e movimento reduzido precisa nascer no token, não ser lembrado em cada
      componente.
- [ ] 4.4 Modificar `app/main.py` para expor o conteúdo de
      `app/static/css/tokens.css` ao Jinja como global (`tokens_css`), e
      `app/templates/base.html` para injetá-lo dentro de uma tag `<style>`.
      Justificativa: RF-25 não abre exceção nem para arquivo estático, e o login
      precisa da folha de estilo antes de haver sessão; injetar do arquivo mantém
      `tokens.css` como fonte única (RF-36) sem abrir uma rota pública.
- [ ] 4.5 Reescrever `app/templates/login.html` vestido: rótulos visíveis,
      `autocomplete="username"` e `autocomplete="current-password"`, mensagem de
      erro única associada ao campo por `aria-describedby`, e nenhum valor de cor
      no arquivo.
      Justificativa: RF-38 e RF-36 — a mensagem que não distingue login
      inexistente de senha errada é o que impede a tela de virar oráculo de
      usuário válido, e `aria-describedby` é o que faz o erro chegar a quem usa
      leitor de tela.
- [ ] 4.6 Criar `app/design/contrast.py` com `contrast_ratio(hex_a: str, hex_b:
      str) -> float` (WCAG 2.1) e `tests/test_contrast.py` com o caso de razão
      conhecida (`#000000` sobre `#ffffff` = 21), o caso que prova que o
      instrumento reprova (`#777777` sobre `#888888` abaixo de 4.5) e o caso que
      lê os pares declarados em `product/00-linguagem-visual.md` a partir de
      `app/static/css/tokens.css` nos dois temas.
      Justificativa: contraste é a única régua visual que um agent consegue medir
      sem olho humano; sem o caso que reprova, um instrumento que devolvesse
      sempre 21 passaria despercebido. Quem executa é o `pytest`, rodado pelo job
      `testes` de `.github/workflows/harness.yml`.
- [ ] 4.7 Usar a pilha de fontes do sistema, sem `<link>` para CDN de fonte.
      Justificativa: uma requisição externa na tela de login é rede que o produto
      não controla e um valor visual fora dos tokens; o produto roda local e a
      tela precisa abrir sem rede.
- [ ] 4.8 Gerar as capturas em
      `product/items/001-base-e-login/06-capturas/`: `login-375.png`,
      `login-768.png`, `login-1440.png`, `login-erro-375.png` (o formulário
      reexibido com a mensagem de erro) e `login-dark-1440.png`.
      Justificativa: RF-37 — a captura é a evidência que sobrevive à sessão em
      que a tela foi feita, e o estado de erro é o que mais some de revisão
      visual por não estar no caminho feliz.

## Resposta ao aviso do `criteria-lint`

O lint deixa três avisos, todos com a mesma causa e a mesma resposta: "o
critério afirma um número e nada o mede", nos `estrutural` de `RF-03` (fase 1),
`RF-24` (integração) e `RF-41` (integração). O número que a regra enxerga é o do
próprio identificador do requisito — ela procura dígito na prosa e não o
encontra dentro de crase. Os três ficam como estão: cada um nomeia arquivo,
símbolo e atributo, que é tudo que um critério `estrutural` precisa carregar.

## Execução sugerida

1. **Fase 1** — bloqueante. Ela fixa o contrato que as outras três consomem:
   `app/config.py`, `app/db.py`, o schema e o `pyproject.toml`. Uma premissa
   errada de coluna ou de nome de variável aqui se espalha para todos os
   consumidores de uma vez.
2. **Paralelo:** **Fase 2** (ingestão) ‖ **Fase 3** (autenticação). Worktrees
   separados. A fase 2 toca `app/ingest/**`, `app/queries/**`,
   `tests/fixtures/**`, `tests/test_money.py`, `tests/test_ingest.py` e
   `tests/test_spending.py`. A fase 3 toca `app/auth/**`, `app/routers/**`,
   `app/templates/**`, `app/main.py`, `tests/test_route_guard.py`,
   `tests/test_session.py`, `tests/test_rate_limit.py` e `tests/test_login.py`.
   A interseção é o diretório `tests/`, com arquivos distintos, e nenhum arquivo
   é escrito pelas duas: a fase 2 roda por CLI e não registra rota, por isso não
   encosta em `app/main.py`.
3. **Fase 4** depois da fase 3 — ela reescreve `app/templates/login.html`, que a
   fase 3 cria cru, e modifica `app/main.py`, que a fase 3 registra. Depois da
   fase 2 também, porque os critérios de integração dela atravessam a ingestão
   ponta a ponta.

## Validações de campo pendentes

Nenhuma.
