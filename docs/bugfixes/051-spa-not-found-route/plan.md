# PLAN 051 — spa-not-found-route

Branch: `bugfix/051-spa-not-found-route`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: as três telas quebram no mesmo roteador e se corrigem juntas.
- **O primeiro commit da branch marca a 050 como `done`** (mergeada em `develop` no PR #52).
- **`basename` sem barra final** em vez de redirecionar `/app` para `/app/` na API: o defeito é do cliente, e a correção vale também no Vite de desenvolvimento.
- **Erro da consulta do usuário mostrado no lugar**, com "Tentar de novo", em vez de lançado para o limite de erro do roteador: é leitura da API, e a regra da skill `error-handling` pede estado de erro com nova tentativa.

## Fase 1 — Endereço sem barra, 404 e erro em português

Ao final: `/app` abre o app, endereço desconhecido mostra "Página não encontrada" com link de volta e a falha da consulta do usuário é tentada de novo e, se persistir, avisa em português com "Tentar de novo".

- [ ] T1.1 — Roteador com raiz, erro e 404
  - Arquivos: `src/app/router.tsx` (alterar), `src/app/routes/not-found.tsx`, `src/app/routes/route-error.tsx` (criar)
  - O que fazer: `basename: '/app'`; rotas sob uma raiz sem caminho com `errorElement`; rota `'*'` por último com a página 404.
  - Skills: routing, error-handling, interface-design
  - Complexidade: baixa
- [ ] T1.2 — Consulta do usuário com nova tentativa e estado de erro
  - Arquivos: `src/lib/auth.tsx` (alterar)
  - O que fazer: tirar `retry: false` de `meQueryOptions`; `ProtectedRoute` mostra o aviso de erro com "Tentar de novo" que chama `refetch`.
  - Skills: authentication, error-handling
  - Complexidade: baixa
- [ ] T1.3 — Testes
  - Arquivos: `src/app/__tests__/not-found-and-errors.test.tsx` (já existe), `e2e/login-and-balances.spec.ts` (alterar)
  - O que fazer: o teste de regressão passa; limite de erro do roteador mostra "Algo deu errado" quando uma tela lança; jornada e2e abre `/app` e um endereço desconhecido no navegador.
  - Skills: component-testing, e2e-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `pnpm test` sai com código 0, e no commit `f032b59` os quatro testes de `src/app/__tests__/not-found-and-errors.test.tsx` falhavam. (comando)
- [ ] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [ ] CA1.3 — Em `src/app/router.tsx` o `basename` é `'/app'`, as rotas ficam sob uma raiz com `errorElement` e a última rota é `path: '*'`; em `src/lib/auth.tsx`, `meQueryOptions` não define `retry` e `ProtectedRoute` não lança o erro da consulta. (estrutural)
- [ ] CA1.4 — Uma tela que lança ao desenhar mostra "Algo deu errado" em português, com o link "Voltar para o início", sem o texto "Unexpected Application Error". (comportamental)
- [ ] CA1.5 — No navegador, `/app` mostra "Entrar" e `/app/nao-existe` mostra "Página não encontrada" com "Voltar para o início". (comportamental)

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
