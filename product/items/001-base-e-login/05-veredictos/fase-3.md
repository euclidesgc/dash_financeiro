# Veredicto — 001-base-e-login, fase 3

VEREDICTO: APROVADO

Envelope: o despacho trouxe objetivo, critérios e ponteiro do trabalho. Nenhum plano, spec, PRD ou histórico de fase veio junto — o arquivo de critérios contém só o bloco de critérios. Nada a ignorar.

**Portões**
```
  lint/gates:  OK — bash scripts/gates/gates_runner.sh
               "✓ gates: limpos (árvore completa, 91 arquivo(s) considerados)."  exit=0
  testes:      OK — .venv/bin/python -m pytest -q
               "74 passed, 2 warnings in 5.83s"
```
(A DoD global é do CI; rodei os portões como estopim, não como régua.)

**Critérios de aceite**

```
[x] RF-19/RF-20 — seed idempotente
    2× `env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-f3.sqlite LOGIN=teste
    PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`
      run1: "seeded user: teste"  exit=0
      run2: "seeded user: teste"  exit=0
    query "select count(*), substr(password_hash,1,10) from users" → `1 $argon2id$`

[x] RF-23 — PASSORD/PASSWORD ausentes
    `env -u PASSORD -u PASSWORD ... DASH_DB_PATH=/tmp/dash-f3b.sqlite LOGIN=teste`
      stderr (stdout descartado com 2>&1 1>/dev/null):
      "missing environment variable: PASSORD or PASSWORD"   exit=1
    query "select count(*) from users" → `0`

[x] RF-23 — LOGIN ausente
    `env -u LOGIN ... DASH_DB_PATH=/tmp/dash-f3d.sqlite PASSORD=senha-teste-9k2`
      stderr: "missing environment variable: LOGIN"          exit=1
    query "select count(*) from users" → `0`

[x] RF-24 — cookie de sessão no login
    POST /login login=teste&senha=senha-teste-9k2:
      HTTP/1.1 302 Found
      location: /
      set-cookie: dash_session=teste|0.apzGRw.w75S7jhN1dJ9T9JygrLTal-Mezs;
                  HttpOnly; Max-Age=43200; Path=/; SameSite=Lax

[x] RF-26 — raiz sem cookie
    curl -w "%{http_code} %header{location}" http://127.0.0.1:8000/ → `302 /login`

[x] RF-27 — /health sem cookie
      HTTP/1.1 401 Unauthorized
      content-type: application/json
      content-length: 28
      {"detail":"nao autenticado"}

[x] RF-28 — /health com cookie válido
      HTTP/1.1 200 OK · content-type: application/json
      {"status":"ok"}

[x] RF-25 — varredura de rotas
    `.venv/bin/python -m pytest -q tests/test_route_guard.py`
      "2 passed, 2 warnings in 0.43s"  exit=0
    A parte estrutural do critério eu confirmei por fora do teste: enumerei as
    rotas de `create_app()` com recursão própria sobre `_IncludedRouter` e
    comparei com o que o helper `_registered` produz —
      reais - varridas = []   varridas - reais = []
      13 pares (GET /, GET|HEAD /docs, /docs/oauth2-redirect, /openapi.json,
      /redoc, GET /health, GET|POST /login, POST /logout)
    O conjunto excluído é exatamente {("GET","/login"),("POST","/login")}, a
    asserção é `status_code in {302, 401}` por rota, e o teste ainda afirma
    explicitamente que ("GET","/health"), ("GET","/") e ("POST","/logout")
    entraram na lista guardada. FastAPI 0.141.1.

[x] RF-29 — cookie assinado com outra chave
    forjado = itsdangerous.TimestampSigner('outra-chave').sign(b'teste') =
              teste.apzGWQ.IRZ4MD9i_iT54Fyo9xX2lxA8iWA
      GET /       → `302 /login`
      GET /health → `401`

[x] RF-30 — cookie expirado (now - 43260)
    expirado = teste|0.apwdXQ.fKaVKM2gWWSiqfYMUtSpQtZaCvM
      GET / → `302 /login`

[x] RF-31/RF-32 — cinco erros fecham a porta
    seis POST /login login=teste&senha=errada, DASH_DB_PATH=/tmp/dash-f3c.sqlite:
      1: status=401 retry_after=
      2: status=401 retry_after=
      3: status=401 retry_after=
      4: status=401 retry_after=
      5: status=401 retry_after=
      6: status=429 retry_after=900
    query "select count(*) from login_attempts where ip='127.0.0.1' and success=0"
      → `5`
    Os cinco carimbos caem no mesmo segundo (01:49:54.245 a 01:49:54.621), bem
    dentro do minuto exigido.

[x] RF-33/RF-34 — o bloqueio sobrevive ao reinício
    SIGTERM no processo ("processo encerrado por SIGTERM"), servidor subido de
    novo com o mesmo DASH_DB_PATH, POST /login com a senha CORRETA:
      HTTP/1.1 429 Too Many Requests
      retry-after: 876
      content-type: text/html; charset=utf-8
    Segunda medição com -D para ler o cabeçalho inteiro: retry-after: 869 e
    `grep -i -c set-cookie` = 0 — nenhum Set-Cookie de qualquer espécie.

[x] RF-22 — a senha não aparece em lugar nenhum
    grep -c senha-teste-9k2 nas três saídas:
      /tmp/dash-f3-srv-a.log:0
      /tmp/dash-f3-login-a.html:0
      /tmp/dash-f3-users.txt:0
    A linha de users guarda só o hash:
      teste $argon2id$v=19$m=65536,t=3,p=4$OIdF7wX9qk+... 2026-09-06T01:47:23+00:00

[x] RF-40 — chave gerada persiste entre reinícios
    /tmp/dash-key inexistente antes de subir ("Arquivo ou diretório inexistente").
    Servidor sem SESSION_SECRET, DASH_KEY_PATH=/tmp/dash-key/session.key:
      cookie obtido = teste|1.apzG9A.RS9-3QybIzh7RfICo6QZ01loYgc
    SIGTERM, servidor subido com o mesmo comando, mesmo cookie:
      curl -w '%{http_code}' -b "dash_session=<cookie>" /health → `200`
      stat -c '%a' /tmp/dash-key/session.key → `600`

[x] RF-40 — o segredo não vaza para log nem HTML
    grep -c segredo-de-teste-7h4 /tmp/dash-f3-servidor.log /tmp/dash-f3-login.html
      /tmp/dash-f3-servidor.log:0
      /tmp/dash-f3-login.html:0

[x] RF-39 — logout
    POST /logout com cookie válido:
      HTTP/1.1 302 Found
      location: /login
      set-cookie: dash_session=""; expires=Sun, 06 Sep 2026 01:48:38 GMT;
                  HttpOnly; Max-Age=0; Path=/; SameSite=Lax
    GET / com o mesmo cookie antes do logout → 200; depois do logout → `302 /login`
```

**Instrumentos do implementer**
```
  RF-25 — o critério nomeia `tests/test_route_guard.py` e não há como cumpri-lo
          sem executar a suíte do avaliado. Reduzi a dependência verificando por
          fora a afirmação estrutural: enumerei as rotas de create_app() com
          código meu e confirmei que a varredura do teste cobre as 13 e exclui
          só as duas de /login. Os outros quinze critérios foram medidos com
          servidor real, curl e app.query — nenhum se apoiou na suíte.
```

**Apontamentos**
```
  app/auth/guard.py:14 — JSON_PATHS = frozenset({"/health"}) fixa à mão quais
    caminhos respondem 401 em vez de 302. Hoje está correto e /api/* já está
    coberto pelo prefixo, mas uma rota JSON futura fora desses dois formatos
    devolve um redirect 302 a um cliente que espera JSON. Não fere critério
    nenhum desta fase; é dívida de manutenção, registrada para quem incluir a
    próxima rota de dados.

  Leitura de limite declarada, para não reabrir depois: em RF-31/RF-32 o
    Retry-After medido foi exatamente 900, o topo da janela. Li "entre 1 e 900"
    como inclusivo — 900 é o valor máximo possível de uma janela de 900s
    logo após a quinta falha, e qualquer outra leitura tornaria o critério
    inatingível por construção. Na medição de RF-33/RF-34 o valor já cai para
    876/869, confirmando que o contador anda.
```

Os dezesseis critérios foram medidos com evidência executada e todos foram cumpridos.
