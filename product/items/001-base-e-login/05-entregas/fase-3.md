## 1. O que foi implementado

**Item:** `001-base-e-login` · **Fase:** `3 — Senha, sessão e rate-limit`

Antes desta fase o app subia sem rota nenhuma. Agora existe a porta: a senha
vive como hash Argon2id semeado do ambiente, o login emite um cookie assinado de
12 horas, um middleware exige sessão em **toda** rota registrada — `/health`
incluído, com isenção apenas de `GET /login` e `POST /login` —, cinco erros do
mesmo IP em quinze minutos fecham a porta mesmo depois de o processo reiniciar,
e o logout invalida o cookie de forma durável.

A fase carrega ainda seis correções vindas de uma auditoria de segurança que
**executou cada exploração** — a primeira delas anulava o rate-limit inteiro.

Branch: `001-base-e-login/fase-3-autenticacao` · commit `a709d9b`.

---

## 2. Critérios atendidos

Os dezesseis critérios foram executados por um validador cego, com servidor real
e `curl`, sem receber plano nem brief. O veredicto integral, com a saída de cada
medida, está em [`05-veredictos/fase-3.md`](../05-veredictos/fase-3.md).

- [x] `[comportamental]` RF-19, RF-20 — o seed roda duas vezes e deixa uma linha
      com hash Argon2id. **Evidência:** → `1 $argon2id$`, os dois exits 0.
- [x] `[comportamental]` RF-23 (senha) — sem `PASSORD`/`PASSWORD` o seed recusa.
      **Evidência:** stderr `missing environment variable: PASSORD or PASSWORD`,
      exit 1, `users` → `0`.
- [x] `[comportamental]` RF-23 (login) — sem `LOGIN` o seed recusa.
      **Evidência:** stderr `missing environment variable: LOGIN`, exit 1.
- [x] `[comportamental]` RF-24 — o login devolve 302 para `/` com o cookie
      completo. **Evidência:** `set-cookie: dash_session=teste|0.…; HttpOnly;
      Max-Age=43200; Path=/; SameSite=Lax`.
- [x] `[comportamental]` RF-26 — `GET /` sem cookie → `302 /login`.
- [x] `[comportamental]` RF-27 — `GET /health` sem cookie → `401` JSON
      `{"detail":"nao autenticado"}`.
- [x] `[comportamental]` RF-28 — `GET /health` com cookie → `200 {"status":"ok"}`.
- [x] `[comando]` RF-25 — a varredura cobre todas as rotas registradas.
      **Evidência:** `pytest tests/test_route_guard.py` → `2 passed`; o
      validador reenumerou as 13 rotas por fora e confirmou que só as duas de
      `/login` ficam isentas.
- [x] `[comportamental]` RF-29 — cookie assinado com outra chave → `302 /login`
      e `401` na rota JSON.
- [x] `[comportamental]` RF-30 — cookie de 43.260 s atrás → `302 /login`.
- [x] `[comportamental]` RF-31, RF-32 — cinco erros 401 e o sexto `429` com
      `Retry-After: 900`; `login_attempts` com cinco falhas do IP.
- [x] `[comportamental]` RF-33, RF-34 — depois de `SIGTERM` e nova subida, o
      login com a senha **correta** ainda responde `429` (`retry-after: 876`) e
      não emite nenhum `Set-Cookie`.
- [x] `[comportamental]` RF-22 — a senha não aparece no log da subida, no HTML
      de `/login` nem em coluna de `users`. **Evidência:** `grep -c` → `0` nas
      três saídas.
- [x] `[comportamental]` RF-40 (persistência) — sem `SESSION_SECRET`, a chave é
      gerada, gravada em modo `600` e reusada: a sessão sobrevive ao reinício.
- [x] `[comportamental]` RF-40 (vazamento) — o segredo não aparece no log nem no
      HTML. **Evidência:** `grep -c` → `0` nos dois.
- [x] `[comportamental]` RF-39 — o logout responde `302 /login` com `Max-Age=0`,
      e o `GET /` seguinte com o cookie antigo responde `302 /login`.

**Portões:** `pytest -q` → `74 passed`, exit 0; `gates_runner.sh` →
`✓ gates: limpos (91 arquivos)`. Lint Python continua **não medido**.

**Ferramentas de segurança rodadas na auditoria:** `semgrep` 1.176.0
(`p/python`, `p/security-audit`, `p/secrets`) — nada em `app/`; `gitleaks`
8.30.1 — nenhum vazamento no histórico, e os achados da árvore são todos dentro
do `.env`, que é untracked; `osv-scanner` 2.5.1 sobre `uv.lock` — nenhuma
vulnerabilidade conhecida em 31 pacotes.

---

## 3. Como testar à mão

1. `rm -rf /tmp/dash-m && mkdir -p /tmp/dash-m`
2. `rtk proxy env DASH_DB_PATH=/tmp/dash-m/dash.sqlite .venv/bin/python -m app.migrate`
3. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-m/dash.sqlite LOGIN=teste PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`
4. Suba: `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-m/dash.sqlite DASH_KEY_PATH=/tmp/dash-m/session.key LOGIN=teste PASSORD=senha-teste-9k2 .venv/bin/python -m app`
5. `curl -s -o /dev/null -w '%{http_code} %header{location}\n' http://127.0.0.1:8000/`
6. **Esperado:** `302 /login`.
7. `curl -i -s http://127.0.0.1:8000/health`
8. **Esperado:** `401` com `{"detail":"nao autenticado"}`.
9. `curl -i -s -X POST http://127.0.0.1:8000/login -d "login=teste&senha=senha-teste-9k2"`
10. **Esperado:** `302` para `/` e o `Set-Cookie` com `HttpOnly`, `Max-Age=43200`,
    `Path=/`, `SameSite=Lax`.
11. Erre a senha seis vezes seguidas.
12. **Esperado:** cinco `401` e um `429` com `Retry-After`.

---

## 4. Divergências

nenhuma

A limitação que a implementação encontrou — cookie assinado não tem como ser
revogado sem estado do lado do servidor — **não contraria nenhum documento
aprovado**: o brief não afirma que a sessão é sem estado, e `RF-39` exige o
oposto. Foi resolvida dentro da fase, com `users.session_epoch` e a migração
`002`, e registrada como decisão autônoma `D13`. Registrar uma divergência aqui
seria inflar o protocolo com uma decisão técnica de uma coluna.

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** A precisão medida do raio de impacto
> é **0,578** — cerca de 42% dos candidatos são falso-positivo. Os confirmados
> abaixo foram lidos; os candidatos, não.

**Confirmados** (lidos, a dependência existe):

- `app/auth/guard.py:34` — o middleware é a autorização inteira do produto. Toda
  rota que qualquer item futuro registrar nasce protegida por ele, e
  `tests/test_route_guard.py` cobra rota nova que tente escapar.
- `app/auth/session.py:31` — o cookie carrega `login|epoch`; quem emitir cookie
  fora do `POST /login` precisa passar a época corrente do usuário, ou o cookie
  nasce inválido.
- `app/auth/users.py` — `session_epoch` e `bump_session_epoch` são o mecanismo de
  revogação; o seed e o logout são hoje seus únicos chamadores.
- `app/migrations/sql/002_session_epoch.sql` — a segunda migração do projeto. Um
  critério da fase 1 media `select count(*), min(version) from schema_migrations`
  esperando `1 001`; contra a árvore de hoje ele daria `2 001`. A fase 1 já foi
  julgada contra a árvore dela, e migração é acréscimo, nunca edição da anterior.
- `app/__main__.py:9` — `proxy_headers=False`. Se algum dia o painel for servido
  atrás de um proxy reverso de verdade, esta linha precisa mudar **junto** com a
  decisão de bind e com o `Secure` do cookie; até lá ela é o que impede que
  qualquer cliente declare o próprio IP.
- `app/db.py` — `connect` agora garante `0600` no arquivo do banco. Vale para
  toda leitura e escrita do produto.

**Candidatos** (não conferidos):

- `app/routers/render.py` — a instância única de `Jinja2Templates` que a fase 4
  vai carregar com os tokens.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **Cookie sem `Secure`.** Coerente com HTTP em loopback — com `Secure` o cookie
  simplesmente não existiria —, e vira defeito no instante em que o painel for
  exposto por túnel ou proxy. **Não virou item de roadmap**: deploy está fora do
  escopo do produto (`docs/plano.md`), e a decisão está amarrada por escrito a
  `app/__main__.py:9`, para que bind, `proxy_headers` e `Secure` mudem juntos.
- **`JSON_PATHS` é lista fixa** (`app/auth/guard.py:14`). Hoje `/health` e o
  prefixo `/api/` cobrem tudo; uma rota JSON futura fora desses dois formatos
  receberia `302` onde espera `401`. Registrado para quem incluir a próxima rota
  de dados — o item `002-gastos-tres-eixos` é o primeiro candidato, e ele já
  serve por `/api/`.
- **Conexão SQLite aberta dentro do middleware assíncrono.** É I/O bloqueante no
  laço de eventos, aceitável num painel local de um usuário e o único ponto do
  app fora do threadpool. Fica registrado aqui porque é o tipo de coisa que só
  dói quando já é tarde.
