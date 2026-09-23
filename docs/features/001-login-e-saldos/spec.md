# SPEC 001 — login e saldos

Primeira fatia da SPA React. O backend FastAPI + SQLite já existe na raiz (pacotes `app/`, `financas/`, `ingestao/`) e hoje serve Jinja2 + HTMX; esta fatia acrescenta uma API JSON sob `/api` e uma SPA nova em `src/`, servida sob `/app`. Os templates Jinja continuam intactos.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `POST /api/auth/login` reaproveita a verificação de senha, o limitador de tentativas e a emissão do cookie que já existem (`app/auth/*`); responde 401 com `{"detail": "Login ou senha inválidos."}` e 429 com `Retry-After`. A tela `login` mostra a mensagem em `role="alert"` e não navega. |
| R2 | Sucesso no login invalida a query `['auth','me']` e navega para `/app/` (`paths.dashboard`). |
| R3 | `GET /api/accounts/balances` devolve `id, name, institution, type, subtype, balance_cents, updated_at` por conta (SQL em `app/queries/balances.py`); `balances-list` renderiza nome, instituição, tipo traduzido, valor via `formatMoney` e data via `formatDateTime`. |
| R4 | `balance-item` aplica `text-red-700` a saldo negativo e `text-gray-900` ao positivo; o sinal vem do próprio valor em centavos (norma 22). |
| R5 | `useBalances` (`isPending`) mostra a receita "Carregando" do `design.md`, texto "Carregando saldos…". |
| R6 | Lista vazia mostra a receita "Vazio": "Nenhuma conta sincronizada ainda. Rode a sincronização para trazer suas contas da Pluggy." |
| R7 | `isError` mostra a receita "Erro" com botão "Tentar de novo" que chama `refetch()`. |
| R8 | Botão "Sair" chama `POST /api/auth/logout` (limpa cookie e incrementa `session_epoch`), limpa o cache do React Query e navega para `/app/login`. |
| R9 | Servidor: o guard já devolve 401 JSON para `/api/*` sem sessão. Cliente: `ProtectedRoute` consulta `GET /api/auth/me`; 401 redireciona para `/app/login`. |

## Decisões técnicas

### D1 — SPA sob o prefixo `/app`, Jinja continua em `/`

- Escolha: Vite `base: '/app/'`, react-router com `basename: '/app'`. Em produção local o FastAPI monta `dist/assets` como estático e responde `dist/index.html` para qualquer `GET /app/*` (fallback). A raiz `/` continua com o resumo Jinja.
- Alternativa descartada: servir a SPA em `/` e mover o Jinja — motivo: os templates não são removidos nesta fatia e as rotas Jinja (`/`, `/login`, `/sincronizar`, …) colidiriam com a SPA.

### D2 — O shell da SPA é público; o dado continua atrás do login

- Escolha: `app/auth/guard.py` ganha `PUBLIC_PREFIXES = ("/app",)` além de `PUBLIC_PATHS = {"/login", "/api/auth/login"}`. `index.html` e os bundles não devolvem dado nenhum; o que devolve dado é `/api/*`, que já exige sessão (norma 24 preservada).
- Alternativa descartada: exigir sessão também para o shell e redirecionar para `/app/login` — motivo: a própria tela de login é servida pelo mesmo fallback; a proteção real está na API.

### D3 — Verificação de credencial sai do router para `app/auth/attempt.py`

- Escolha: função `attempt_login(conn, ip, login, password) -> LoginOutcome` (dataclass com `accepted`, `epoch`, `retry_after`) que encapsula limitador, consulta a `users`, verificação com tempo constante e registro de tentativa. O router Jinja (`app/routers/auth.py`) e o novo `app/routers/auth_api.py` chamam a mesma função. Os atributos do cookie (`HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age=43200`) passam a um só lugar: `attach_session(response, login, *, secret, epoch)` e `detach_session(response)` em `app/auth/session.py`.
- Alternativa descartada: duplicar as ~30 linhas do `submit_login` no router novo — motivo: duas cópias de lógica de segurança divergem; e o router atual já viola a norma 30 (SQL no router), o que a extração corrige de passagem.

### D4 — Contratos JSON

- `POST /api/auth/login` · body `{"login": str, "password": str}` · 204 + cookie · 401 `{"detail":"Login ou senha inválidos."}` · 429 `{"detail":"Muitas tentativas seguidas. Tente novamente mais tarde."}` + `Retry-After`.
- `POST /api/auth/logout` · 204, cookie apagado, epoch incrementado.
- `GET /api/auth/me` · 200 `{"login": str}`.
- `GET /api/accounts/balances` · 200 `{"accounts": [{"id","name","institution","type":"BANK"|"CREDIT","subtype","balance_cents": int,"updated_at": str|null}]}`, ordenado por `type, name`. Não há histórico de saldo: `accounts.balance_cents` é sempre o saldo atual (a tabela é reescrita a cada carga, `app/ingest/loader.py`), então "saldo de hoje" é a linha da tabela e `updated_at` (o `updatedAt` da Pluggy) é a data/hora do último dado.
- Modelos de resposta em Pydantic no router (norma 33): o OpenAPI gerado pelo FastAPI (`/openapi.json`) é o contrato.
- Alternativa descartada: reutilizar `POST /login` com `Accept: application/json` — motivo: o handler atual renderiza HTML e recebe form `senha`; um endpoint por representação é mais simples de testar e de proteger.

### D5 — Sessão do usuário mora no React Query, não em Zustand

- Escolha: `useUser` = `useQuery(['auth','me'])`; login invalida e logout limpa o cache. Nenhum store Zustand nesta fatia: o pacote entra quando houver estado de cliente que não seja de servidor.
- Alternativa descartada: store Zustand com o usuário — motivo: é estado de servidor (o cookie manda); duplicá-lo cria dessincronia.

### D6 — Cliente HTTP mínimo com `fetch`

- Escolha: `src/lib/api-client.ts` com `credentials: 'same-origin'`, JSON automático e `ApiError { status, detail }`. `QueryClient` em `src/lib/react-query.ts` com `retry` desligado para 401 e `staleTime` de 30 s. Redirecionamento por 401 é feito no `ProtectedRoute`, não no cliente (o cliente não conhece o roteador).
- Alternativa descartada: axios — motivo: dependência a mais para quatro endpoints.

### D7 — Formatação no cliente, valores inteiros no fio

- Escolha: `formatMoney(cents)` com `Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'})`; `formatDateTime(iso)` com `Intl.DateTimeFormat('pt-BR', {dateStyle:'short', timeStyle:'short'})`, devolvendo `null` quando não há data. Ambos em `src/utils/`, com teste unitário.
- Alternativa descartada: formatar no servidor — motivo: norma 22 (centavos inteiros na API); apresentação é do cliente.

### D8 — Ferramental da SPA na raiz, convivendo com Python

- Escolha: `package.json` com pnpm, scripts `dev`, `lint`, `typecheck`, `test`, `test:e2e`, `build`. `vite.config.ts` com proxy `/api → http://127.0.0.1:8000`, `outDir: 'dist'`. Tailwind v4 via `@tailwindcss/vite`. ESLint flat config com `import/no-restricted-paths` (zonas `features/auth` e `features/accounts`). `.gitignore` ganha `node_modules/`, `dist/`, `playwright-report/`, `test-results/`.
- Alternativa descartada: pasta `web/` separada — motivo: os scripts do harness medem `src/` a partir da raiz.

### D9 — Playwright sobe os dois servidores

- Escolha: `playwright.config.ts` com `webServer` duplo: `scripts/e2e-backend.sh` (banco temporário, `run_migrations`, `seed_user('e2e', …)`, ingestão de `tests/fixtures/accounts_fixture.json`, uvicorn em 8000) e `pnpm dev`. Uma jornada: login → lista de saldos → sair → volta ao login.
- Alternativa descartada: e2e só com MSW — motivo: a fatia prova a ponta a ponta real do cookie; MSW fica para os testes de integração em Vitest.

## Interface

Receitas do `docs/design.md` usadas: contêiner de página, título de página, texto de apoio, lista, selo de status, botão principal, botão secundário, carregando, vazio, erro.

Receitas novas a acrescentar em "Padrões acrescentados pelas entregas":

| Padrão | Classes | Fatia |
|---|---|---|
| Campo de formulário | `<label className="block text-sm font-medium text-gray-900">` + `<input className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">`; erro de campo `mt-1 text-sm text-red-700` | 001 |
| Valor monetário | `tabular-nums font-medium`; negativo `text-red-700`; positivo `text-gray-900` | 001 |
| Cabeçalho de app | `<header className="border-b border-gray-200">` com `mx-auto flex max-w-2xl items-center justify-between p-4`; nome do painel à esquerda, ação à direita | 001 |

### Tela: Entrar (`/app/login`)

De cima para baixo, dentro do contêiner de página:

- `<h1>` "Entrar"
- Texto de apoio: "Painel financeiro pessoal."
- Formulário (React Hook Form + Zod), `mt-6`, campos empilhados com `mt-4`:
  - rótulo "Login", `input type="text" autoComplete="username"`; erro de validação: "Informe o login."
  - rótulo "Senha", `input type="password" autoComplete="current-password"`; erro de validação: "Informe a senha."
  - botão principal `type="submit"`, texto "Entrar"; enquanto envia: `disabled` e texto "Entrando…"
- Estados:
  - credencial recusada (401): receita "Erro" acima do botão, texto "Login ou senha inválidos."; sem botão de tentar (o formulário já é a ação).
  - bloqueado (429): mesma receita, texto "Muitas tentativas seguidas. Tente novamente mais tarde."
  - falha de rede/5xx: mesma receita, texto "Não foi possível entrar. Verifique se o servidor está no ar e tente de novo."
- Usuário já autenticado que abre `/app/login`: redireciona para `/app/`.
- Título do documento: "Entrar · dash_financeiro".

### Tela: Saldos (`/app/`)

- Cabeçalho de app: "dash_financeiro" à esquerda; à direita o login do usuário em `text-gray-600` e botão secundário `type="button"` "Sair".
- Contêiner de página:
  - `<h1>` "Saldos de hoje"
  - Texto de apoio: "Contas e cartões sincronizados da Pluggy."
  - Carregando (`role="status"`): "Carregando saldos…"
  - Vazio: "Nenhuma conta sincronizada ainda. Rode a sincronização para trazer suas contas da Pluggy."
  - Erro (`role="alert"`): "Não foi possível carregar os saldos." + botão de erro "Tentar de novo".
  - Com dados: lista (receita "Lista"); cada item:
    - esquerda, `min-w-0`: nome da conta em `font-medium truncate`; abaixo, instituição em `text-sm text-gray-600 truncate`; abaixo, "Atualizado em {data e hora}" ou "Sem data de atualização", em `text-sm text-gray-600`.
    - direita, alinhado à direita: selo de tipo — "Conta" (`bg-gray-100 text-gray-700`) para `BANK`, "Cartão" (`bg-amber-100 text-amber-800`) para `CREDIT`; abaixo, o valor pela receita "Valor monetário".
- Título do documento: "Saldos · dash_financeiro".

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `app/auth/attempt.py` | `LoginOutcome`, `attempt_login(conn, ip, login, password)`, `REJECTED_MESSAGE`, `THROTTLED_MESSAGE`: limitador, consulta a `users`, verificação de tempo constante, registro da tentativa | `authentication`, `security` |
| alterar | `app/auth/session.py` | `attach_session(response, login, *, secret, epoch)` e `detach_session(response)` | `authentication` |
| alterar | `app/auth/guard.py` | `PUBLIC_PATHS` ganha `/api/auth/login`; `PUBLIC_PREFIXES = ("/app",)` para o shell da SPA | `authentication`, `routing` |
| alterar | `app/routers/auth.py` | `submit_login` e `logout` passam a chamar `attempt_login`, `attach_session`, `detach_session`; as mensagens vêm de `app/auth/attempt.py` | `authentication` |
| criar | `app/routers/auth_api.py` | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`; modelos Pydantic `LoginRequest`, `MeResponse`; só traduz HTTP | `authentication`, `error-handling` |
| criar | `app/queries/balances.py` | `BALANCES` SQL (`SELECT id, name, institution, type, subtype, balance_cents, updated_at FROM accounts ORDER BY type, name`) e `list_balances(conn)` | — |
| criar | `app/routers/accounts.py` | `GET /api/accounts/balances` com `AccountBalance`/`BalancesResponse` Pydantic | `api-requests` |
| criar | `app/spa.py` | `mount_spa(app, dist: Path)`: `StaticFiles` em `/app/assets`, rota `GET /app/{path:path}` que devolve `index.html`; sem `dist/`, responde 503 `{"detail": "SPA não compilada: rode pnpm build"}` | `routing` |
| alterar | `app/main.py` | inclui `auth_api.router`, `accounts.router` e chama `mount_spa(app, Path("dist"))` | — |
| criar | `tests/test_auth_api.py` | login 204 + cookie com os mesmos atributos do Jinja, 401, 429, logout apaga cookie e invalida a sessão anterior, `me` sem sessão 401 | `authentication` |
| criar | `tests/test_accounts_api.py` | sem sessão 401; com sessão devolve a conta da fixture com `balance_cents` inteiro e ordem por tipo/nome; base vazia devolve `{"accounts": []}` | — |
| criar | `tests/test_spa.py` | `/app/` e `/app/qualquer` devolvem `index.html` sem sessão; `/app/assets/x` é estático; sem `dist/` responde 503 | `routing` |
| alterar | `tests/test_login.py` | importa `REJECTED_MESSAGE` do novo módulo | — |
| criar | `scripts/e2e-backend.sh` | banco temporário, migrações, `seed_user`, ingestão de `tests/fixtures/accounts_fixture.json`, uvicorn 8000 | `e2e-testing` |

### Ferramental da SPA (raiz)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `package.json` | deps: react, react-dom, react-router, @tanstack/react-query, react-hook-form, zod, @hookform/resolvers, tailwindcss, @tailwindcss/vite; dev: vite, typescript, @vitejs/plugin-react, vitest, @testing-library/{react,jest-dom,user-event}, jsdom, msw, @playwright/test, eslint, typescript-eslint, eslint-plugin-import, eslint-plugin-react-hooks; scripts `dev`, `lint`, `typecheck`, `test`, `test:e2e`, `build` | `project-structure` |
| criar | `pnpm-lock.yaml` | gerado | — |
| criar | `vite.config.ts` | `base: '/app/'`, plugin react + tailwind, `server.proxy['/api']`, bloco `test` do Vitest (jsdom, setup em `src/testing/setup.ts`) | `api-client` |
| criar | `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` | strict, `paths: {"@/*": ["./src/*"]}` | `project-structure` |
| criar | `eslint.config.js` | typescript-eslint strict, react-hooks, `import/no-restricted-paths` com zonas `features/auth` e `features/accounts` e proibição de feature importar `app/` | `project-structure` |
| criar | `playwright.config.ts` | `webServer` duplo (D9), `baseURL: http://127.0.0.1:5173/app` | `e2e-testing` |
| criar | `index.html` | shell com `<div id="root">`, `lang="pt-BR"` | — |
| alterar | `.gitignore` | `node_modules/`, `dist/`, `playwright-report/`, `test-results/` | — |
| alterar | `docs/design.md` | três receitas novas (seção Interface) | `interface-design` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `src/main.tsx` | monta `<AppProvider><AppRouter/></AppProvider>` | `project-structure` |
| criar | `src/index.css` | `@import "tailwindcss";` | — |
| criar | `src/app/provider.tsx` | `QueryClientProvider` com o client de `lib/react-query` e `ErrorBoundary` de `components/errors` | `error-handling`, `api-client` |
| criar | `src/app/router.tsx` | `createBrowserRouter({ basename: '/app' })`: `/login` → rota de login; `/` → `ProtectedRoute` envolvendo a rota de saldos | `routing` |
| criar | `src/app/routes/login.tsx` | compõe `LoginForm`; se `useUser` já resolveu, `Navigate` para `paths.dashboard` | `routing`, `authentication` |
| criar | `src/app/routes/dashboard.tsx` | cabeçalho de app com `LogoutButton` e `BalancesList` | `routing`, `interface-design` |
| criar | `src/config/paths.ts` | `paths = { login: '/login', dashboard: '/' }` | `routing` |
| criar | `src/lib/api-client.ts` | `apiRequest<T>(path, init)`, `ApiError` | `api-client`, `error-handling` |
| criar | `src/lib/react-query.ts` | `QueryClient` (`retry` desligado em 401, `staleTime` 30 s) | `api-client` |
| criar | `src/lib/auth.tsx` | `getMe()`, `meQueryOptions`, `useUser()`, `ProtectedRoute` (pendente → "Carregando…"; 401 → `Navigate` para login com `replace`). Fica no compartilhado porque o `app` (rota protegida) e a feature `auth` consomem | `authentication`, `routing` |
| criar | `src/components/errors/error-boundary.tsx` | fallback com receita "Erro" e botão "Recarregar a página" | `error-handling` |
| criar | `src/components/ui/button.tsx` | variantes `primary`, `secondary`, `danger`; `ref` como prop comum | `ui-components` |
| criar | `src/components/ui/alert.tsx` | receita "Erro" com `role="alert"` e ação opcional | `ui-components` |
| criar | `src/utils/format-money.ts` | `formatMoney(cents: number): string` | `unit-testing` |
| criar | `src/utils/format-date-time.ts` | `formatDateTime(iso: string \| null): string \| null` | `unit-testing` |
| criar | `src/utils/__tests__/format-money.test.ts` | positivo, negativo, zero, centavos | `unit-testing` |
| criar | `src/utils/__tests__/format-date-time.test.ts` | ISO válido, nulo | `unit-testing` |
| criar | `src/features/auth/api/login.ts` | `login({login, password})` + `useLogin` (mutation que invalida `['auth','me']`) | `api-requests`, `authentication` |
| criar | `src/features/auth/api/logout.ts` | `logout()` + `useLogout` (mutation que faz `queryClient.clear()`) | `api-requests`, `authentication` |
| criar | `src/features/auth/types/login-schema.ts` | `loginSchema = z.object({ login: z.string().min(1, 'Informe o login.'), password: z.string().min(1, 'Informe a senha.') })` | `forms` |
| criar | `src/features/auth/components/login-form.tsx` | React Hook Form + Zod, estados de envio e de erro, textos da seção Interface | `forms`, `interface-design`, `error-handling` |
| criar | `src/features/auth/components/logout-button.tsx` | botão secundário "Sair", navega para login após sucesso | `authentication` |
| criar | `src/features/auth/components/__tests__/login-form.test.tsx` | validação vazia, 401 mostra mensagem, sucesso chama `onSuccess` (MSW) | `component-testing`, `api-mocking` |
| criar | `src/features/accounts/api/get-balances.ts` | `getBalances()`, `balancesQueryOptions`, `useBalances()` | `api-requests` |
| criar | `src/features/accounts/types/account-balance.ts` | `AccountBalance`, `AccountType = 'BANK' \| 'CREDIT'` | — |
| criar | `src/features/accounts/components/balances-list.tsx` | quatro estados + lista | `interface-design`, `error-handling`, `component-robustness` |
| criar | `src/features/accounts/components/balance-item.tsx` | um item da lista, selo de tipo e valor | `interface-design` |
| criar | `src/features/accounts/components/__tests__/balances-list.test.tsx` | carregando, vazio, erro + tentar de novo, dados com negativo em vermelho (MSW) | `component-testing`, `api-mocking` |
| criar | `src/testing/setup.ts` | jest-dom, `server.listen/resetHandlers/close` | `api-mocking` |
| criar | `src/testing/test-utils.tsx` | `renderWithProviders` com `QueryClient` novo e `MemoryRouter` | `component-testing` |
| criar | `src/testing/mocks/server.ts` | `setupServer(...handlers)` | `api-mocking` |
| criar | `src/testing/mocks/handlers.ts` | handlers de `/api/auth/*` e `/api/accounts/balances` com dados simulados | `api-mocking` |
| criar | `src/app/__tests__/login-to-balances.test.tsx` | integração: sem sessão em `/` vai para `/login`; login válido chega em "Saldos de hoje"; sair volta ao login | `integration-testing`, `api-mocking` |
| criar | `e2e/login-and-balances.spec.ts` | jornada real contra o FastAPI (D9) | `e2e-testing` |

## Estimativa de tamanho

Jornadas: 1 (entrar e ver saldos; sair fecha a mesma jornada) · Telas novas: 1 principal (Saldos); a de login é porta, não conteúdo · Linhas alteradas (sem testes): ~180 Python + ~330 em `src/` + ~130 de configuração do ferramental (`package.json`, `vite.config.ts`, `tsconfig*`, `eslint.config.js`, `playwright.config.ts`, `index.html`) · Fases previstas: 3 (API JSON + servir a SPA; scaffold da SPA + login; tela de saldos + e2e).

O sinal 4 (>400 linhas) só dispara se o scaffold contar; ele nasce uma vez e a fatia 002 não o paga de novo. Mantida como está, por decisão do dono.

## Dívida encontrada

- `app/routers/auth.py` monta consulta SQL (`SELECT password_hash, session_epoch FROM users`) e chama `record_failure`/`record_success`, que dão `commit` — viola a norma 30 (router só traduz HTTP). Esta fatia extrai a lógica para `app/auth/attempt.py` por necessidade (D3), o que zera a dívida de passagem; registrado para o revisor saber que a mudança no arquivo antigo é deliberada.
- `app/routers/summary.py` e demais routers Jinja abrem `connect()` e executam SQL direto (`_COUNT`) — mesma violação, fora do escopo; item de roadmap.
- O guard testa `PUBLIC_PATHS` por igualdade exata, sem prefixo. A fatia introduz `PUBLIC_PREFIXES` (D2); aceitável enquanto forem poucos prefixos públicos.
