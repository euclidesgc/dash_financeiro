# PLAN 001 — login e saldos

Branch: `feature/001-login-e-saldos`

Decisões registradas aqui (a SPEC deixou a escolha ao plano; escolhido o mais simples):

- `attempt_login` recebe a conexão e não abre nem fecha `connect()`; quem abre é o router (como hoje). `LoginOutcome` é `@dataclass(frozen=True)` com `accepted: bool`, `epoch: int`, `retry_after: int` (`retry_after > 0` significa bloqueado; `accepted` só é `True` com `retry_after == 0`).
- Os endpoints `/api/*` são `def` síncronos (só SQLite, bloqueante) e usam `request.state.login` que o guard já preenche.
- `mount_spa` só monta `StaticFiles` se `dist/assets` existir; a rota de fallback existe sempre e é ela que responde 503 quando falta `dist/index.html`. Assim `create_app()` não quebra no CI Python sem `pnpm build`.
- O `e2e-backend.sh` não usa `python -m app.ingest` (que exige `.env` e reclassifica): chama `ingest()` diretamente via `uv run python -c`, com `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` num diretório temporário e `SESSION_SECRET` fixo. Usuário e senha do e2e: `e2e` / `senha-e2e-9k2`, exportados também para o Playwright.
- O `ProtectedRoute` mostra "Carregando…" com `role="status"` enquanto `useUser` está pendente; qualquer `ApiError` com `status === 401` redireciona; outro erro cai no `ErrorBoundary`.
- Os testes de componente/integração usam MSW com `onUnhandledRequest: 'error'` no `setup.ts`.

## Fase 1 — API JSON de autenticação e saldos, e o FastAPI servindo a SPA

Só Python. Ao final: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `GET /api/accounts/balances` respondem JSON; `GET /app/*` devolve a SPA quando compilada e 503 quando não; o login Jinja continua funcionando com a mesma lógica extraída.

- [ ] T1.1 — Extrair a verificação de credencial e a emissão/remoção do cookie para módulos de `app/auth`, e fazer o router Jinja usá-los
  - Arquivos: `app/auth/attempt.py` (criar); `app/auth/session.py` (alterar); `app/routers/auth.py` (alterar); `tests/test_login.py` (alterar)
  - O que fazer:
    - `app/auth/attempt.py`: constantes `REJECTED_MESSAGE = "Login ou senha inválidos."` e `THROTTLED_MESSAGE = "Muitas tentativas seguidas. Tente novamente mais tarde."` (movidas de `app/routers/auth.py`, com o comentário de porquê); `@dataclass(frozen=True) class LoginOutcome: accepted: bool; epoch: int; retry_after: int`; `def attempt_login(conn: sqlite3.Connection, ip: str, login: str, password: str) -> LoginOutcome` que: chama `blocked_seconds(conn, ip)` e, se `> 0`, devolve `LoginOutcome(False, 0, waiting)`; consulta `SELECT password_hash, session_epoch FROM users WHERE login = ?`; usa `verify_absent_user(password)` quando a linha não existe e `verify_password(password, row["password_hash"])` quando existe (mantendo o comentário de tempo constante); em recusa chama `record_failure(conn, ip)` e devolve `LoginOutcome(False, 0, 0)`; em aceite chama `record_success(conn, ip)` e devolve `LoginOutcome(True, int(row["session_epoch"]), 0)`.
    - `app/auth/session.py`: acrescentar `def attach_session(response: Response, login: str, *, secret: str, epoch: int) -> None` (faz o `set_cookie` com `COOKIE_NAME`, `issue_cookie(login, secret=secret, epoch=epoch)`, `max_age=MAX_AGE_SECONDS`, `path="/"`, `httponly=True`, `samesite="Lax"` com o mesmo `# type: ignore[arg-type]` e justificativa que está hoje no router) e `def detach_session(response: Response) -> None` (o `delete_cookie` com `path="/"`, `httponly=True`, `samesite="Lax"`). `Response` vem de `starlette.responses`.
    - `app/routers/auth.py`: `submit_login` passa a `outcome = attempt_login(conn, ip, login, senha)`; `retry_after > 0` → formulário 429 com `Retry-After`; `not accepted` → formulário 401; aceito → `RedirectResponse("/")` + `attach_session(response, login, secret=request.app.state.session_secret, epoch=outcome.epoch)`. `logout` usa `detach_session`. O router não importa mais `password`, `rate_limit`, `issue_cookie`, `COOKIE_NAME`, `MAX_AGE_SECONDS`; as duas mensagens são importadas de `app.auth.attempt` (o router deixa de defini-las).
    - `tests/test_login.py`: linha 10 passa a `from app.auth.attempt import REJECTED_MESSAGE`. Nenhum outro teste muda: o comportamento HTTP do Jinja é o mesmo.
  - Skills: authentication, security
  - Complexidade: média

- [ ] T1.2 — Guard com prefixo público e API JSON de autenticação
  - Arquivos: `app/auth/guard.py` (alterar); `app/routers/auth_api.py` (criar)
  - O que fazer:
    - `app/auth/guard.py`: `PUBLIC_PATHS = frozenset({"/login", "/api/auth/login"})`; novo `PUBLIC_PREFIXES = ("/app",)`; em `require_session`, é público se `path in PUBLIC_PATHS` ou `path == p or path.startswith(p + "/")` para algum `p` em `PUBLIC_PREFIXES` (assim `/app` e `/app/x` são públicos, `/apple` não). Comentário de porquê: o shell da SPA não devolve dado; o dado está em `/api/*`, que continua exigindo sessão (invariante 24).
    - `app/routers/auth_api.py`: `router = APIRouter(prefix="/api/auth")`; `class LoginRequest(BaseModel): login: str; password: str`; `class MeResponse(BaseModel): login: str`. `@router.post("/login", status_code=204)` `def api_login(request: Request, body: LoginRequest) -> Response`: abre `connect()`, chama `attempt_login(conn, ip, body.login, body.password)`, fecha; `retry_after > 0` → `JSONResponse({"detail": THROTTLED_MESSAGE}, status_code=429, headers={"Retry-After": str(retry_after)})`; recusado → `JSONResponse({"detail": REJECTED_MESSAGE}, status_code=401)`; aceito → `Response(status_code=204)` com `attach_session(...)`. `@router.post("/logout", status_code=204)` `def api_logout(request: Request) -> Response`: se `request.state.login` existir, `bump_session_epoch`; devolve `Response(status_code=204)` com `detach_session`. `@router.get("/me")` `def api_me(request: Request) -> MeResponse`: `MeResponse(login=request.state.login)`. O router não monta SQL além do que já está encapsulado (norma 30).
  - Skills: authentication, routing, error-handling
  - Complexidade: média

- [ ] T1.3 — Consulta e endpoint de saldos
  - Arquivos: `app/queries/balances.py` (criar); `app/routers/accounts.py` (criar)
  - O que fazer:
    - `app/queries/balances.py`: `BALANCES = "SELECT id, name, institution, type, subtype, balance_cents, updated_at FROM accounts ORDER BY type, name"`; `def list_balances(conn: sqlite3.Connection) -> list[sqlite3.Row]` que executa e devolve `fetchall()`.
    - `app/routers/accounts.py`: `router = APIRouter(prefix="/api/accounts")`; `class AccountBalance(BaseModel): id: str; name: str | None; institution: str | None; type: str | None; subtype: str | None; balance_cents: int; updated_at: str | None`; `class BalancesResponse(BaseModel): accounts: list[AccountBalance]`. `@router.get("/balances")` `def balances() -> BalancesResponse`: abre `connect()`, `list_balances`, fecha, monta `BalancesResponse(accounts=[AccountBalance(**dict(row)) for row in rows])`.
  - Skills: api-requests
  - Complexidade: baixa

- [ ] T1.4 — Servir a SPA compilada sob `/app` e registrar os routers novos
  - Arquivos: `app/spa.py` (criar); `app/main.py` (alterar); `.gitignore` (alterar)
  - O que fazer:
    - `app/spa.py`: `SPA_MISSING = "SPA não compilada: rode pnpm build"`; `def mount_spa(app: FastAPI, dist: Path) -> None`: se `(dist / "assets").is_dir()`, `app.mount("/app/assets", StaticFiles(directory=dist / "assets"), name="spa-assets")`; sempre registra `@app.get("/app")` e `@app.get("/app/{path:path}")` (mesma função `def spa_index() -> Response`) que devolve `FileResponse(dist / "index.html", media_type="text/html")` se o arquivo existir, senão `JSONResponse({"detail": SPA_MISSING}, status_code=503)`. A verificação de existência é por requisição (o `dist/` pode nascer com o servidor de pé). Comentário de porquê no mount condicional: `StaticFiles` recusa diretório inexistente na construção, e o CI Python roda sem `pnpm build`.
    - `app/main.py`: importar `auth_api`, `accounts` de `app.routers` e `mount_spa` de `app.spa`; `app.include_router(auth_api.router)` e `app.include_router(accounts.router)` logo após `auth.router`; `mount_spa(app, Path("dist"))` depois do último `include_router`.
    - `.gitignore`: acrescentar `node_modules/`, `dist/`, `playwright-report/`, `test-results/`.
  - Skills: routing
  - Complexidade: baixa

- [ ] T1.5 — Testes da fase 1
  - Arquivos: `tests/test_auth_api.py` (criar); `tests/test_accounts_api.py` (criar); `tests/test_spa.py` (criar)
  - O que fazer: fixture `client` igual à de `tests/test_login.py` (`DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` em `tmp_path`, `SESSION_SECRET`, `seed_user`, `TestClient(follow_redirects=False)`). Casos:
    - `tests/test_auth_api.py`: `test_login_answers_204_and_sets_the_same_cookie_as_the_html_form` (204, sem corpo, `set-cookie` contém `dash_session=`, `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age=43200`); `test_wrong_password_answers_401_with_the_generic_message` (`{"detail":"Login ou senha inválidos."}`, sem `set-cookie`); `test_unknown_login_gets_the_same_401_message`; `test_the_sixth_failure_answers_429_with_retry_after` (`MAX_FAILURES` erros, depois 429 com `{"detail":"Muitas tentativas seguidas. Tente novamente mais tarde."}` e `retry-after` entre 1 e `WINDOW_SECONDS`); `test_login_without_session_is_public` (POST sem cookie não recebe 401 do guard, e sim 401/204 do próprio endpoint — provado com corpo inválido de credencial vindo com a mensagem genérica); `test_login_with_missing_fields_answers_422` (body `{}`); `test_me_without_session_answers_401` (`{"detail":"nao autenticado"}`); `test_me_with_session_returns_the_login` (`{"login":"teste"}`); `test_logout_expires_the_cookie_and_invalidates_the_previous_session` (204, `Max-Age=0` no `set-cookie`; reenviar o cookie antigo em `GET /api/auth/me` dá 401); `test_the_html_login_still_works_with_the_extracted_logic` (`POST /login` form continua 302 para `/` — guarda contra regressão de T1.1).
    - `tests/test_accounts_api.py`: `test_balances_without_session_answers_401`; `test_balances_returns_the_fixture_account_with_integer_cents` (ingerir `tests/fixtures/accounts_fixture.json` via `ingest(conn, transactions=[], accounts=..., source="tests")`; resposta `{"accounts":[{"id":"acc-fixture-1","name":"Conta de teste","institution":"Banco de teste","type":"BANK","subtype":"CHECKING_ACCOUNT","balance_cents":1234,"updated_at":"2026-09-05T21:36:27.516Z"}]}`); `test_balances_are_ordered_by_type_then_name` (uma `CREDIT` "Zeta", uma `BANK` "Beta", uma `BANK` "Alfa" → ordem Alfa, Beta, Zeta; a `CREDIT` com `balance: 50.0` chega como `-5000`); `test_balances_on_an_empty_base_returns_an_empty_list` (`{"accounts":[]}`); `test_balances_with_null_updated_at_returns_null`.
    - `tests/test_spa.py`: fixture que cria `dist/index.html` e `dist/assets/app.js` em `tmp_path` e monta via `mount_spa(app, tmp_path / "dist")` numa `FastAPI()` com `install_guard`. `test_app_root_returns_index_without_session` (`GET /app/` 200, `text/html`, corpo do `index.html`); `test_app_deep_path_returns_index_without_session` (`GET /app/qualquer/coisa`); `test_app_assets_are_served_statically` (`GET /app/assets/app.js` 200 com o conteúdo); `test_without_dist_answers_503` (`mount_spa` com pasta inexistente; `GET /app/` → 503 `{"detail":"SPA não compilada: rode pnpm build"}`); `test_apple_is_not_public` (`GET /apple` sem sessão → 302 para `/login`); `test_api_under_app_prefix_still_requires_session` (`GET /api/accounts/balances` sem cookie → 401 no app real de `create_app()`).
  - Skills: unit-testing, integration-testing, authentication, routing
  - Complexidade: média

### Critérios de aceite da fase 1

- [ ] CA1.1 — `bash scripts/lint.sh` sai com código 0. (comando)
- [ ] CA1.2 — `uv run pytest tests/test_login.py tests/test_auth_api.py tests/test_accounts_api.py tests/test_spa.py tests/test_session.py tests/test_rate_limit.py` passa, e cada nome de teste listado em T1.5 existe no arquivo indicado. (comando)
- [ ] CA1.3 — `bash scripts/gates/gates_runner.sh` sai com código 0. (comando)
- [ ] CA1.4 — Existe `app/auth/attempt.py` com `LoginOutcome` (dataclass congelada com `accepted: bool`, `epoch: int`, `retry_after: int`), `attempt_login(conn: sqlite3.Connection, ip: str, login: str, password: str) -> LoginOutcome`, `REJECTED_MESSAGE = "Login ou senha inválidos."` e `THROTTLED_MESSAGE = "Muitas tentativas seguidas. Tente novamente mais tarde."`. `app/routers/auth.py` não contém a string `SELECT`, não importa `app.auth.password` nem `app.auth.rate_limit`, e não define as duas mensagens. (estrutural)
- [ ] CA1.5 — `app/auth/session.py` exporta `attach_session(response, login, *, secret, epoch) -> None` e `detach_session(response) -> None`; `set_cookie`/`delete_cookie` de `dash_session` aparecem apenas nesse arquivo em `app/`. (estrutural)
- [ ] CA1.6 — `app/auth/guard.py` tem `PUBLIC_PATHS = frozenset({"/login", "/api/auth/login"})` e `PUBLIC_PREFIXES = ("/app",)`; `/apple` sem sessão redireciona para `/login` (teste `test_apple_is_not_public`). (estrutural, comportamental)
- [ ] CA1.7 — `app/routers/auth_api.py` expõe `POST /api/auth/login` (204 + cookie; 401 `{"detail":"Login ou senha inválidos."}`; 429 `{"detail":"Muitas tentativas seguidas. Tente novamente mais tarde."}` com `Retry-After`), `POST /api/auth/logout` (204, `Max-Age=0`) e `GET /api/auth/me` (200 `{"login": str}`), com modelos `LoginRequest` e `MeResponse`. (comportamental)
- [ ] CA1.8 — `app/queries/balances.py` define `BALANCES` com `ORDER BY type, name` e `list_balances(conn)`; `app/routers/accounts.py` expõe `GET /api/accounts/balances` devolvendo `BalancesResponse` com `AccountBalance(id, name, institution, type, subtype, balance_cents: int, updated_at: str | None)`; a string `SELECT` não aparece em `app/routers/accounts.py`. (estrutural)
- [ ] CA1.9 — `app/spa.py` define `mount_spa(app: FastAPI, dist: Path) -> None`; `app/main.py` chama `mount_spa(app, Path("dist"))` e inclui `auth_api.router` e `accounts.router`; `.gitignore` contém `node_modules/`, `dist/`, `playwright-report/` e `test-results/`. (estrutural)
- [ ] CA1.10 — `uv run pytest --cov=app/auth --cov=app/routers/auth_api.py --cov=app/routers/accounts.py --cov=app/queries/balances.py --cov=app/spa.py --cov-report=term tests/test_login.py tests/test_auth_api.py tests/test_accounts_api.py tests/test_spa.py` reporta ≥ 80% em cada um desses arquivos. (comando)

## Fase 2 — Scaffold da SPA e tela de Entrar

Ao final: `pnpm dev` sobe a SPA em `http://127.0.0.1:5173/app/`, `/app/login` mostra o formulário, o login válido leva a `/app/` (que por ora mostra o cabeçalho de app com "Sair" e o `<h1>` "Saldos de hoje" com o texto de apoio — a lista chega na fase 3), e "Sair" volta ao login.

- [ ] T2.1 — Ferramental da SPA na raiz do repositório
  - Arquivos: `package.json` (criar); `pnpm-lock.yaml` (criar, gerado por `pnpm install`); `vite.config.ts` (criar); `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` (criar); `eslint.config.js` (criar); `index.html` (criar); `src/index.css` (criar)
  - O que fazer:
    - `package.json`: `"private": true`, `"type": "module"`, scripts `dev` (`vite`), `lint` (`eslint .`), `typecheck` (`tsc -b`), `test` (`vitest run`), `test:e2e` (`playwright test`), `build` (`tsc -b && vite build`). Dependências: react, react-dom, react-router, @tanstack/react-query, react-hook-form, zod, @hookform/resolvers, tailwindcss, @tailwindcss/vite. Dev: vite, typescript, @vitejs/plugin-react, vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom, msw, @playwright/test, eslint, typescript-eslint, eslint-plugin-import, eslint-plugin-react-hooks, @types/react, @types/react-dom, @types/node. Versões atuais estáveis (React 19, Vite 7, Vitest 3, MSW 2, react-router 7, Tailwind 4).
    - `vite.config.ts`: `base: '/app/'`, plugins `react()` e `tailwindcss()`, `resolve.alias['@'] = /src`, `server.proxy['/api'] = 'http://127.0.0.1:8000'`, `build.outDir = 'dist'`, bloco `test` (`environment: 'jsdom'`, `globals: false`, `setupFiles: ['src/testing/setup.ts']`, `exclude: ['e2e/**', 'node_modules/**']`, `coverage.include: ['src/**']`).
    - `tsconfig.json` referencia `tsconfig.app.json` e `tsconfig.node.json`; `tsconfig.app.json` com `strict`, `noUnusedLocals`, `noUnusedParameters`, `jsx: 'react-jsx'`, `baseUrl: '.'`, `paths: {"@/*": ["./src/*"]}`, `types: ['vite/client', '@testing-library/jest-dom']`, `include: ['src']`; `tsconfig.node.json` cobre `vite.config.ts`, `eslint.config.js`, `playwright.config.ts`.
    - `eslint.config.js`: flat config com `typescript-eslint` strict type-checked, `eslint-plugin-react-hooks` recommended, `import/no-restricted-paths` com zonas: `src/features/auth` não importa de `src/features/accounts` e vice-versa; `src/features/**` não importa de `src/app/**`; `src/{components,hooks,lib,types,utils,config}/**` não importa de `src/features/**` nem `src/app/**`. Ignora `dist/`, `node_modules/`, `playwright-report/`, `test-results/`, `app/`, `financas/`, `ingestao/`.
    - `index.html`: `<html lang="pt-BR">`, `<title>dash_financeiro</title>`, `<div id="root">`, `<script type="module" src="/src/main.tsx">`.
    - `src/index.css`: `@import "tailwindcss";`.
  - Skills: project-structure, api-client
  - Complexidade: média

- [ ] T2.2 — Cliente HTTP, React Query, sessão do usuário e provedores
  - Arquivos: `src/lib/api-client.ts` (criar); `src/lib/react-query.ts` (criar); `src/lib/auth.tsx` (criar); `src/config/paths.ts` (criar); `src/components/errors/error-boundary.tsx` (criar); `src/app/provider.tsx` (criar)
  - O que fazer:
    - `src/lib/api-client.ts`: `export class ApiError extends Error { status: number; detail: string }`; `export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T>`: `fetch(path, { credentials: 'same-origin', headers: { 'Content-Type': 'application/json', ...init?.headers }, ...init })`; resposta `!ok` lança `ApiError` com `status` e `detail` lido do JSON (`{detail}`) ou `response.statusText`; 204 devolve `undefined as T`; senão `response.json()`.
    - `src/lib/react-query.ts`: `export const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: (count, error) => !(error instanceof ApiError && error.status === 401) && count < 3 } } })`.
    - `src/config/paths.ts`: `export const paths = { login: '/login', dashboard: '/' } as const`.
    - `src/lib/auth.tsx`: `export type User = { login: string }`; `export function getMe(): Promise<User>` (`GET /api/auth/me`); `export const meQueryOptions = queryOptions({ queryKey: ['auth', 'me'], queryFn: getMe, retry: false })`; `export function useUser()` = `useQuery(meQueryOptions)`; `export function ProtectedRoute({ children }: { children: React.ReactNode }): React.JSX.Element`: pendente → `<p role="status">` "Carregando…" com a receita "Carregando" do `docs/design.md`; erro `ApiError` 401 → `<Navigate to={paths.login} replace />`; outro erro → `throw error` (cai no ErrorBoundary); sucesso → `children`.
    - `src/components/errors/error-boundary.tsx`: `ErrorBoundary` de classe (`getDerivedStateFromError`), fallback com a receita "Erro": texto "Algo deu errado." e botão `type="button"` "Recarregar a página" que chama `window.location.reload()`.
    - `src/app/provider.tsx`: `export function AppProvider({ children }: { children: React.ReactNode }): React.JSX.Element` = `<ErrorBoundary><QueryClientProvider client={queryClient}>{children}</QueryClientProvider></ErrorBoundary>`.
  - Skills: api-client, error-handling, authentication, routing
  - Complexidade: média

- [ ] T2.3 — Componentes de UI compartilhados e receitas novas no design
  - Arquivos: `src/components/ui/button.tsx` (criar); `src/components/ui/alert.tsx` (criar); `docs/design.md` (alterar)
  - O que fazer:
    - `button.tsx`: `export type ButtonProps = React.ComponentPropsWithRef<'button'> & { variant?: 'primary' | 'secondary' | 'danger' }`; `export function Button({ variant = 'primary', type = 'button', className, ref, ...rest }: ButtonProps): React.JSX.Element`; `primary` e `secondary` usam as receitas "Botão principal" e "Botão secundário" do `docs/design.md`; `danger` é o "botão de erro" (principal com `red-600`/`red-700`); todos com `disabled:opacity-50` e altura ≥ 40px. `ref` como prop comum, sem `forwardRef`.
    - `alert.tsx`: `export function Alert({ message, action }: { message: string; action?: { label: string; onClick: () => void } }): React.JSX.Element` com a receita "Erro" (`role="alert"`, borda/fundo vermelhos, texto `text-red-800`); se `action` existir, renderiza `<Button variant="danger">` com o rótulo.
    - `docs/design.md`, seção "Padrões acrescentados pelas entregas": três linhas copiadas da tabela "Receitas novas" da SPEC 001 — "Campo de formulário", "Valor monetário", "Cabeçalho de app" — com a coluna fatia = `001`.
  - Skills: ui-components, interface-design
  - Complexidade: baixa

- [ ] T2.4 — Feature `auth`: chamadas de login/logout, schema, formulário e botão de sair
  - Arquivos: `src/features/auth/api/login.ts` (criar); `src/features/auth/api/logout.ts` (criar); `src/features/auth/types/login-schema.ts` (criar); `src/features/auth/components/login-form.tsx` (criar); `src/features/auth/components/logout-button.tsx` (criar)
  - O que fazer:
    - `login-schema.ts`: `export const loginSchema = z.object({ login: z.string().min(1, 'Informe o login.'), password: z.string().min(1, 'Informe a senha.') })`; `export type LoginInput = z.infer<typeof loginSchema>`.
    - `login.ts`: `export function login(input: LoginInput): Promise<void>` (`POST /api/auth/login`, body JSON); `export function useLogin()` = `useMutation({ mutationFn: login, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth', 'me'] }) })` usando `useQueryClient()`.
    - `logout.ts`: `export function logout(): Promise<void>` (`POST /api/auth/logout`); `export function useLogout()` = mutation que em `onSuccess` faz `queryClient.clear()`.
    - `login-form.tsx`: `export function LoginForm({ onSuccess }: { onSuccess: () => void }): React.JSX.Element`. React Hook Form com `zodResolver(loginSchema)`. Estrutura e textos (seção Interface da SPEC): campo "Login" (`type="text"`, `autoComplete="username"`, `<label htmlFor>`), campo "Senha" (`type="password"`, `autoComplete="current-password"`), erros de campo abaixo do campo com a receita "Campo de formulário"; botão `<Button type="submit">` "Entrar", que fica `disabled` com o texto "Entrando…" enquanto `isPending`. Acima do botão, `<Alert>` sem ação quando a mutation falhou: `ApiError` 401 → "Login ou senha inválidos."; 429 → "Muitas tentativas seguidas. Tente novamente mais tarde."; qualquer outro erro → "Não foi possível entrar. Verifique se o servidor está no ar e tente de novo.". No sucesso chama `onSuccess()`. Campos empilhados com `mt-4`, formulário com `mt-6`.
    - `logout-button.tsx`: `export function LogoutButton(): React.JSX.Element` = `<Button variant="secondary" type="button">` "Sair"; `disabled` enquanto envia; no sucesso `navigate(paths.login, { replace: true })`.
  - Skills: api-requests, authentication, forms, interface-design, error-handling
  - Complexidade: média

- [ ] T2.5 — Rotas, tela de Entrar, casca da tela de Saldos e ponto de entrada
  - Arquivos: `src/app/router.tsx` (criar); `src/app/routes/login.tsx` (criar); `src/app/routes/dashboard.tsx` (criar); `src/main.tsx` (criar)
  - O que fazer:
    - `router.tsx`: `export const routes: RouteObject[]` = [`{ path: paths.login, element: <LoginRoute /> }`, `{ path: paths.dashboard, element: <ProtectedRoute><DashboardRoute /></ProtectedRoute> }`]; `export const router = createBrowserRouter(routes, { basename: '/app' })`; `export function AppRouter()` = `<RouterProvider router={router} />`. Exportar `routes` separado permite ao teste de integração montar um `createMemoryRouter(routes, { initialEntries })`.
    - `routes/login.tsx`: `export function LoginRoute(): React.JSX.Element`; `useEffect` define `document.title = 'Entrar · dash_financeiro'`; se `useUser()` tem `data`, `<Navigate to={paths.dashboard} replace />`; senão, dentro do contêiner de página: `<h1>` "Entrar", texto de apoio "Painel financeiro pessoal.", `<LoginForm onSuccess={() => navigate(paths.dashboard, { replace: true })} />`.
    - `routes/dashboard.tsx`: `export function DashboardRoute(): React.JSX.Element`; `document.title = 'Saldos · dash_financeiro'`; cabeçalho de app (receita "Cabeçalho de app"): "dash_financeiro" à esquerda; à direita o `login` de `useUser().data` em `text-gray-600` e `<LogoutButton />`. Abaixo, contêiner de página com `<h1>` "Saldos de hoje" e texto de apoio "Contas e cartões sincronizados da Pluggy.". A `BalancesList` entra na fase 3.
    - `main.tsx`: importa `./index.css`, `createRoot(document.getElementById('root')!)` (comentário justificando o `!`: o `index.html` é nosso) e renderiza `<StrictMode><AppProvider><AppRouter /></AppProvider></StrictMode>`.
  - Skills: routing, authentication, interface-design
  - Complexidade: média

- [ ] T2.6 — Testes da fase 2
  - Arquivos: `src/testing/setup.ts` (criar); `src/testing/test-utils.tsx` (criar); `src/testing/mocks/server.ts` (criar); `src/testing/mocks/handlers.ts` (criar); `src/features/auth/components/__tests__/login-form.test.tsx` (criar); `src/lib/__tests__/api-client.test.ts` (criar)
  - O que fazer:
    - `setup.ts`: `import '@testing-library/jest-dom/vitest'`; `beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))`, `afterEach(() => server.resetHandlers())`, `afterAll(() => server.close())`.
    - `handlers.ts`: `export const fakeUser = { login: 'teste' }`; `export const fakeAccounts` com duas contas (uma `BANK` "Conta corrente"/"Banco de teste"/`balance_cents: 123456`/`updated_at: '2026-09-05T21:36:27.516Z'`, uma `CREDIT` "Cartão"/"Emissor de teste"/`balance_cents: -54321`/`updated_at: null`); `export const handlers` com `POST /api/auth/login` (204 se `login === 'teste' && password === 'senha'`, senão 401 `{detail:'Login ou senha inválidos.'}`), `POST /api/auth/logout` (204), `GET /api/auth/me` (200 `fakeUser`), `GET /api/accounts/balances` (200 `{accounts: fakeAccounts}`). Um estado de módulo `signedIn` alternado por login/logout faz `/me` devolver 401 `{detail:'nao autenticado'}` quando deslogado; `export function resetSession()` chamado no `afterEach`.
    - `server.ts`: `export const server = setupServer(...handlers)`.
    - `test-utils.tsx`: `export function renderWithProviders(ui: React.ReactElement, { route = '/' } = {})` cria `QueryClient` novo (`retry: false`), envolve em `QueryClientProvider` e `MemoryRouter initialEntries=[route]`, devolve o resultado de `render` mais o `queryClient`.
    - `login-form.test.tsx` (component-testing): `shows field errors when submitted empty` (aparecem "Informe o login." e "Informe a senha."; nenhuma requisição); `shows the generic message on 401` (`role="alert"` com "Login ou senha inválidos."; `onSuccess` não chamado); `shows the throttled message on 429` (`server.use` devolvendo 429); `shows the network message on 500` ("Não foi possível entrar. Verifique se o servidor está no ar e tente de novo."); `disables the button and shows "Entrando…" while submitting`; `calls onSuccess after a valid login`.
    - `api-client.test.ts` (unit-testing): `resolves json on 200`; `resolves undefined on 204`; `throws ApiError with status and detail on 401`; `falls back to statusText when the body is not json`; `sends credentials same-origin`.
  - Skills: component-testing, api-mocking, unit-testing
  - Complexidade: média

### Critérios de aceite da fase 2

- [ ] CA2.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0; `bash scripts/lint.sh` e `bash scripts/gates/gates_runner.sh` também. (comando)
- [ ] CA2.2 — `package.json` tem os scripts `dev`, `lint`, `typecheck`, `test`, `test:e2e`, `build`; `vite.config.ts` tem `base: '/app/'`, `server.proxy['/api']` apontando para `http://127.0.0.1:8000` e `build.outDir: 'dist'`; `eslint.config.js` configura `import/no-restricted-paths` com zonas que proíbem `src/features/auth` ↔ `src/features/accounts` e `src/features/**` → `src/app/**`. (estrutural)
- [ ] CA2.3 — Existe `apiRequest<T>(path: string, init?: RequestInit): Promise<T>` e `class ApiError extends Error` com `status: number` e `detail: string` em `src/lib/api-client.ts`; `src/lib/react-query.ts` exporta `queryClient` com `staleTime: 30_000` e `retry` que devolve `false` para `ApiError` 401. (estrutural)
- [ ] CA2.4 — `src/lib/auth.tsx` exporta `getMe`, `meQueryOptions` (queryKey `['auth','me']`), `useUser` e `ProtectedRoute`; o pendente de `ProtectedRoute` tem `role="status"` e texto "Carregando…"; 401 rende `<Navigate to="/login" replace>`. (estrutural)
- [ ] CA2.5 — `src/features/auth/types/login-schema.ts` exporta `loginSchema` com as mensagens "Informe o login." e "Informe a senha."; `login.ts` exporta `login` e `useLogin` (invalida `['auth','me']`); `logout.ts` exporta `logout` e `useLogout` (chama `queryClient.clear()`). (estrutural)
- [ ] CA2.6 — `login-form.tsx` contém os textos literais "Login", "Senha", "Entrar", "Entrando…", "Login ou senha inválidos.", "Muitas tentativas seguidas. Tente novamente mais tarde." e "Não foi possível entrar. Verifique se o servidor está no ar e tente de novo."; cada `<input>` tem `<label htmlFor>` associado; o de login tem `autoComplete="username"` e o de senha `type="password"` e `autoComplete="current-password"`; o erro de credencial é renderizado por `<Alert>` (que tem `role="alert"`). (estrutural)
- [ ] CA2.7 — Piso visual, verificado lendo o código: `routes/login.tsx` e `routes/dashboard.tsx` envolvem o conteúdo em `<main>` com as classes do "Contêiner de página" do `docs/design.md` e têm um único `<h1>` com as classes de "Título de página" ("Entrar" e "Saldos de hoje"); o texto de apoio usa as classes de "Texto de apoio"; os campos usam as classes de "Campo de formulário" do `docs/design.md`; `Button` aplica, por variante, exatamente as classes de "Botão principal"/"Botão secundário"/botão de erro, define `type` explícito, `disabled:opacity-50` e `focus-visible:outline-2`; o cabeçalho de `dashboard.tsx` usa as classes de "Cabeçalho de app"; nenhum arquivo em `src/` contém `style={{` ou `<a href`. (estrutural)
- [ ] CA2.8 — `docs/design.md` tem, em "Padrões acrescentados pelas entregas", as linhas "Campo de formulário", "Valor monetário" e "Cabeçalho de app", com fatia `001`. (estrutural)
- [ ] CA2.9 — Os testes nomeados em T2.6 existem em `src/features/auth/components/__tests__/login-form.test.tsx` e `src/lib/__tests__/api-client.test.ts`; `pnpm test -- --coverage` reporta ≥ 80% de linhas em `src/lib/api-client.ts`, `src/features/auth/components/login-form.tsx` e `src/features/auth/types/login-schema.ts`. (comando)
- [ ] CA2.10 — `src/features/auth/**` não importa de `src/app/**` nem de `src/features/accounts/**` (basta `pnpm lint` passar com a regra de CA2.2 ativa). (estrutural)

## Fase 3 — Lista de saldos, jornada completa e e2e real

Ao final: `/app/` lista contas e cartões com os quatro estados; `pnpm build` gera `dist/` e o FastAPI o serve em `http://127.0.0.1:8000/app/`; o Playwright prova login → saldos → sair contra o backend real.

- [ ] T3.1 — Formatadores de dinheiro e data
  - Arquivos: `src/utils/format-money.ts` (criar); `src/utils/format-date-time.ts` (criar)
  - O que fazer: `export function formatMoney(cents: number): string` = `new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)` (formatter criado uma vez no módulo). `export function formatDateTime(iso: string | null): string | null`: `null` → `null`; string inválida (`Number.isNaN(Date.parse(iso))`) → `null`; válida → `new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(iso))`.
  - Skills: unit-testing
  - Complexidade: baixa

- [ ] T3.2 — Feature `accounts`: tipo, chamada de saldos, item e lista com os quatro estados
  - Arquivos: `src/features/accounts/types/account-balance.ts` (criar); `src/features/accounts/api/get-balances.ts` (criar); `src/features/accounts/components/balance-item.tsx` (criar); `src/features/accounts/components/balances-list.tsx` (criar); `src/app/routes/dashboard.tsx` (alterar)
  - O que fazer:
    - `account-balance.ts`: `export type AccountType = 'BANK' | 'CREDIT'`; `export type AccountBalance = { id: string; name: string | null; institution: string | null; type: AccountType | null; subtype: string | null; balance_cents: number; updated_at: string | null }`; `export type BalancesResponse = { accounts: AccountBalance[] }`.
    - `get-balances.ts`: `export function getBalances(): Promise<BalancesResponse>` (`GET /api/accounts/balances`); `export const balancesQueryOptions = queryOptions({ queryKey: ['accounts', 'balances'], queryFn: getBalances })`; `export function useBalances()` = `useQuery(balancesQueryOptions)`.
    - `balance-item.tsx`: `export function BalanceItem({ account }: { account: AccountBalance }): React.JSX.Element` = `<li>` com a receita de item de "Lista". Esquerda (`min-w-0`): nome (`font-medium truncate`; se `name` for nulo, "Conta sem nome"), instituição (`text-sm text-gray-600 truncate`; se nula, omitida), e "Atualizado em {formatDateTime(updated_at)}" ou "Sem data de atualização" (`text-sm text-gray-600`). Direita (`text-right`): selo "Conta" (`bg-gray-100 text-gray-700`) para `BANK`, "Cartão" (`bg-amber-100 text-amber-800`) para `CREDIT` (tipo nulo → "Conta"); abaixo, `formatMoney(balance_cents)` com a receita "Valor monetário": `tabular-nums font-medium` + `text-red-700` se `balance_cents < 0`, senão `text-gray-900`.
    - `balances-list.tsx`: `export function BalancesList(): React.JSX.Element`; `useBalances()`; `isPending` → receita "Carregando" (`role="status"`) "Carregando saldos…"; `isError` → `<Alert message="Não foi possível carregar os saldos." action={{ label: 'Tentar de novo', onClick: () => void refetch() }} />`; `data.accounts.length === 0` → receita "Vazio" "Nenhuma conta sincronizada ainda. Rode a sincronização para trazer suas contas da Pluggy."; senão `<ul>` com a receita "Lista" e um `<BalanceItem key={account.id}>` por conta.
    - `dashboard.tsx`: renderiza `<BalancesList />` depois do texto de apoio.
  - Skills: api-requests, interface-design, error-handling, component-robustness
  - Complexidade: média

- [ ] T3.3 — Backend de e2e e configuração do Playwright
  - Arquivos: `scripts/e2e-backend.sh` (criar); `playwright.config.ts` (criar); `e2e/login-and-balances.spec.ts` (criar)
  - O que fazer:
    - `scripts/e2e-backend.sh`: `set -euo pipefail`; `E2E_DIR=$(mktemp -d)`; exporta `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH="$E2E_DIR/dash.sqlite"`, `SESSION_SECRET=e2e-secret`; roda `uv run python -c` que faz `run_migrations()`, `seed_user(conn, "e2e", "senha-e2e-9k2")` e `ingest(conn, transactions=[], accounts=load_accounts("tests/fixtures/accounts_fixture.json"), source="e2e")`, saindo com 1 se `status != "ok"`; `trap 'rm -rf "$E2E_DIR"' EXIT`; `exec uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000`. Se `--factory` não for aceito pela versão de uvicorn instalada, criar `app/asgi.py` com `app = create_app()` e apontar para `app.asgi:app` (registrar no plano como decidido: prefira `--factory`).
    - `playwright.config.ts`: `testDir: 'e2e'`, `use.baseURL: 'http://127.0.0.1:5173/app'`, `webServer: [{ command: 'bash scripts/e2e-backend.sh', url: 'http://127.0.0.1:8000/app/', reuseExistingServer: false, timeout: 60_000, ignoreHTTPSErrors: true }, { command: 'pnpm dev --port 5173 --strictPort', url: 'http://127.0.0.1:5173/app/', reuseExistingServer: false }]`; um projeto `chromium`. Como o backend responde 503 em `/app/` sem `dist/`, o `url` de saúde do backend deve ser `http://127.0.0.1:8000/login` (200 público).
    - `e2e/login-and-balances.spec.ts`: um teste `signs in, sees the balances and signs out`: `page.goto('/')` → espera URL `/app/login` e `<h1>` "Entrar"; preenche "Login" com `e2e` e "Senha" com `senha-e2e-9k2`, clica "Entrar" → URL `/app/` e `<h1>` "Saldos de hoje"; item com texto "Conta de teste", "Banco de teste", selo "Conta" e valor "R$ 12,34"; clica "Sair" → URL `/app/login`; `page.goto('/')` de novo → volta a `/app/login` (sessão encerrada). Segundo teste `rejects the wrong password`: senha errada → `role="alert"` "Login ou senha inválidos." e URL continua `/app/login`.
  - Skills: e2e-testing
  - Complexidade: alta

- [ ] T3.4 — Testes da fase 3
  - Arquivos: `src/utils/__tests__/format-money.test.ts` (criar); `src/utils/__tests__/format-date-time.test.ts` (criar); `src/features/accounts/components/__tests__/balances-list.test.tsx` (criar); `src/app/__tests__/login-to-balances.test.tsx` (criar)
  - O que fazer:
    - `format-money.test.ts` (unit-testing): `formats a positive amount` (`123456` → contém "1.234,56" e "R$"); `formats a negative amount` (`-54321` → contém "-" e "543,21"); `formats zero` ("0,00"); `keeps the cents` (`5` → "0,05"). Comparar com o espaço não separável normalizado (`replace(/ /g, ' ')`).
    - `format-date-time.test.ts` (unit-testing): `formats a valid iso string` (`'2026-09-05T21:36:27.516Z'` → contém "05/09/2026"); `returns null for null`; `returns null for an invalid string`.
    - `balances-list.test.tsx` (component-testing, MSW): `shows the loading state` (`role="status"` com "Carregando saldos…"); `shows the empty state` (`server.use` com `{accounts: []}` → texto "Nenhuma conta sincronizada ainda. Rode a sincronização para trazer suas contas da Pluggy."); `shows the error state and retries` (500 → `role="alert"` "Não foi possível carregar os saldos." + botão "Tentar de novo"; ao clicar, handler passa a 200 e a lista aparece); `renders accounts with the negative balance in red` (dois itens de `fakeAccounts`; o do cartão tem classe `text-red-700` e selo "Cartão"; o da conta tem `text-gray-900` e selo "Conta"); `shows "Sem data de atualização" when updated_at is null`; `shows "Atualizado em" with the formatted date`.
    - `login-to-balances.test.tsx` (integration-testing, MSW, `createMemoryRouter(routes, …)` + `QueryClientProvider`): `redirects to /login without a session` (inicia em `/` deslogado → `<h1>` "Entrar"); `a valid login lands on the balances page` (preenche `teste`/`senha`, clica "Entrar" → `<h1>` "Saldos de hoje" e "Conta corrente" na lista); `signing out returns to the login page` (clica "Sair" → `<h1>` "Entrar"); `an authenticated user opening /login is sent to the dashboard`.
  - Skills: unit-testing, component-testing, integration-testing, api-mocking
  - Complexidade: média

### Critérios de aceite da fase 3

- [ ] CA3.1 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` saem com código 0; `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` também. (comando)
- [ ] CA3.2 — `pnpm test:e2e` sai com código 0, com os testes `signs in, sees the balances and signs out` e `rejects the wrong password` em `e2e/login-and-balances.spec.ts`. (comando)
- [ ] CA3.3 — Depois de `pnpm build`, `uv run pytest tests/test_spa.py` passa e `dist/index.html` existe; `git status --porcelain` não lista `dist/` nem `node_modules/`. (comando)
- [ ] CA3.4 — `src/utils/format-money.ts` exporta `formatMoney(cents: number): string`; `src/utils/format-date-time.ts` exporta `formatDateTime(iso: string | null): string | null`; ambos usam `Intl` com locale `'pt-BR'`. (estrutural)
- [ ] CA3.5 — `src/features/accounts/api/get-balances.ts` exporta `getBalances(): Promise<BalancesResponse>`, `balancesQueryOptions` (queryKey `['accounts','balances']`) e `useBalances()`; `src/features/accounts/types/account-balance.ts` exporta `AccountType = 'BANK' | 'CREDIT'` e `AccountBalance` com `balance_cents: number` e `updated_at: string | null`. (estrutural)
- [ ] CA3.6 — `balances-list.tsx` contém os textos literais "Carregando saldos…" (num elemento com `role="status"`), "Nenhuma conta sincronizada ainda. Rode a sincronização para trazer suas contas da Pluggy.", "Não foi possível carregar os saldos." e "Tentar de novo"; o erro é renderizado por `<Alert>` com `action` que chama `refetch`. (estrutural)
- [ ] CA3.7 — `balance-item.tsx` contém "Conta", "Cartão", "Atualizado em" e "Sem data de atualização"; aplica `text-red-700` quando `balance_cents < 0` e `text-gray-900` caso contrário; o selo usa `bg-gray-100 text-gray-700` para `BANK` e `bg-amber-100 text-amber-800` para `CREDIT` com as classes de "Selo de status"; o valor tem `tabular-nums font-medium`; o bloco da esquerda tem `min-w-0` e o nome `truncate`. (estrutural)
- [ ] CA3.8 — Piso visual: a lista em `balances-list.tsx` usa as classes de "Lista" do `docs/design.md`; o vazio usa as classes de "Vazio"; o carregando usa as de "Carregando"; `dashboard.tsx` renderiza `<BalancesList />` dentro do `<main>` do contêiner de página, abaixo do texto de apoio; nenhum arquivo em `src/` contém `style={{`, `<a href` ou `!important`. (estrutural)
- [ ] CA3.9 — `scripts/e2e-backend.sh` exporta `DASH_ENV_FILE=/dev/null`, usa `DASH_DB_PATH` num diretório de `mktemp -d`, chama `seed_user` com login `e2e`, ingere `tests/fixtures/accounts_fixture.json` e sobe uvicorn em `127.0.0.1:8000`; `playwright.config.ts` tem dois `webServer` e `baseURL: 'http://127.0.0.1:5173/app'`. (estrutural)
- [ ] CA3.10 — Os testes nomeados em T3.4 existem nos arquivos indicados; `pnpm test -- --coverage` reporta ≥ 80% de linhas em `src/utils/format-money.ts`, `src/utils/format-date-time.ts`, `src/features/accounts/components/balances-list.tsx`, `src/features/accounts/components/balance-item.tsx` e `src/lib/auth.tsx`. (comando)

## DoD da entrega

- [ ] DoD1 — Todas as tarefas e critérios do plano marcados
- [ ] DoD2 — Suíte de testes inteira passa
- [ ] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [ ] DoD4 — Tipos de todos os `tsconfig` sem erros
- [ ] DoD5 — Console dos testes sem erro nem aviso
- [ ] DoD6 — `build` passa
- [ ] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [ ] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [ ] DoD9 — Nenhuma worktree ou branch temporária sobrando
