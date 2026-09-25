# PLAN 047 — expired-session-redirect-loop

Branch: `bugfix/047-expired-session-redirect-loop`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a consulta do usuário e a rota protegida mudam juntas; separadas, a rota protegida deixaria de ver o 401.
- **O primeiro commit da branch marca a 046 como `done`** (mergeada em `develop` no PR #48).
- **401 de `/api/auth/me` é resposta, não erro**: vira `null`, como a skill `authentication` prescreve; os demais erros continuam subindo.
- **O 401 das outras chamadas fica fora**: é outro comportamento (avisar o app de que a sessão acabou a partir de qualquer tela) e entra no roadmap como item próprio.

## Fase 1 — Sessão expirada vai para o login e fica lá

Ao final: com a sessão expirada, o app mostra "Entrar" uma vez e fica nessa tela; entrar de novo leva aos saldos.

- [x] T1.1 — Usuário ausente como resposta
  - Arquivos: `src/lib/auth.tsx` (alterar)
  - O que fazer: `getMe` devolve `User | null`, transformando o 401 em `null`; `ProtectedRoute` redireciona ao login quando o dado é `null` e deixa subir qualquer outro erro.
  - Skills: authentication, error-handling
  - Complexidade: baixa
- [x] T1.2 — Testes
  - Arquivos: `src/app/__tests__/login-to-balances.test.tsx`, `e2e/login-and-balances.spec.ts` (alterar), `src/lib/__tests__/auth.test.ts` (criar)
  - O que fazer: o teste de regressão passa; `getMe` devolve `null` no 401 e rejeita com o erro em outro status; jornada e2e em que a sessão acaba no servidor com o app aberto.
  - Skills: component-testing, unit-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm test` sai com código 0, e no commit `c94193e` o teste `a session that expires while the app is open lands on the login page and stays there` falhava. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — Em `src/lib/auth.tsx`, `getMe` devolve `Promise<User | null>`, só o status 401 vira `null`, e `ProtectedRoute` não consulta mais o status do erro para redirecionar. (estrutural)
- [x] CA1.4 — `getMe` devolve `null` quando `/api/auth/me` responde 401 e rejeita com `ApiError` de status 500 quando a API responde 500. (comportamental)
- [x] CA1.5 — No navegador, com a sessão encerrada no servidor, voltar o foco à aba dos saldos leva a "Entrar" e a URL fica em `/app/login`; entrar de novo mostra "Saldos de hoje". (comportamental)

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
