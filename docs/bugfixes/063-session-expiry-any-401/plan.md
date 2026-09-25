# PLAN 063 — session-expiry-any-401

Branch: `bugfix/063-session-expiry-any-401`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: o tratamento do 401 mora num ponto só e a tela que reage a ele (rota protegida) já existe desde a 047.
- **O primeiro commit da branch marca a 051 como `done`** (mergeada em `develop` no PR #53).
- **Invalidar, não apagar, o usuário guardado**: quem diz que a sessão acabou é o servidor, pela resposta de `/api/auth/me`. Apagar o usuário direto no 401 dispensaria essa confirmação e levaria ao login por um 401 que não fosse de sessão.
- **Cache de consultas e de mutações, não o cliente `fetch`**: o cliente de API (`src/lib/api-client.ts`) não conhece o cache do React Query; o cache é quem guarda o usuário, e o roadmap já apontava `src/lib/react-query.ts`.
- **Sem recarregar a página**: a rota protegida já leva ao login quando o usuário vira `null`; o recarregamento da skill `authentication` serve a apps sem essa rota reagindo ao cache.

## Fase 1 — Qualquer 401 leva o app a "Entrar"

Ao final: com a sessão encerrada no servidor, a primeira chamada recusada, de qualquer tela, leva o app a "Entrar".

- [x] T1.1 — Tratamento único do 401
  - Arquivos: `src/lib/react-query.ts` (alterar)
  - O que fazer: `createQueryClient()` monta o cliente com `QueryCache` e `MutationCache` cujo `onError` invalida a consulta do usuário (refazendo-a mesmo sem tela observando) quando o erro é `ApiError` 401 e há usuário guardado; `queryClient` passa a ser `createQueryClient()`.
  - Skills: api-client, authentication, error-handling
  - Complexidade: baixa
- [x] T1.2 — Testes
  - Arquivos: `src/lib/__tests__/react-query.test.ts` (criar), `src/app/__tests__/login-to-balances.test.tsx`, `e2e/login-and-balances.spec.ts` (alterar)
  - O que fazer: os testes de regressão passam; erro que não é 401 e 401 sem ninguém logado não refazem a consulta do usuário.
  - Skills: unit-testing, component-testing, e2e-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm test` sai com código 0, e no commit `2dcf6bd` os testes `a 401 from another call while the app is open lands on the login page`, `a 401 from any query clears the signed-in user` e `a 401 from any mutation clears the signed-in user` falhavam. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm build` e `pnpm test:e2e` saem com código 0, e no commit `2dcf6bd` o e2e `a session that ends while the user moves between screens goes to the login page` falhava. (comando)
- [x] CA1.3 — O status 401 só é comparado em `src/lib/react-query.ts` e em `getMe` de `src/lib/auth.tsx`; nenhum arquivo de `src/features/` trata 401. (estrutural)
- [x] CA1.4 — Um erro 500 de outra consulta mantém o usuário guardado sem nova chamada a `/api/auth/me`, e um 401 com ninguém logado também não chama `/api/auth/me` de novo. (comportamental)
- [x] CA1.5 — No navegador, com a sessão encerrada no servidor, clicar em "Gastos" menos de 30 s depois leva a "Entrar" com a URL em `/app/login`. (comportamental)

## DoD da entrega

- [x] DoD1 — Todas as tarefas e critérios do plano marcados
- [x] DoD2 — Suíte de testes inteira passa
- [x] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [x] DoD4 — Tipos de todos os `tsconfig` sem erros
- [x] DoD5 — Console dos testes sem erro nem aviso
- [x] DoD6 — `build` passa
- [x] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [x] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [x] DoD9 — Nenhuma worktree ou branch temporária sobrando
