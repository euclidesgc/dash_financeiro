# PLAN 052 — mobile-no-horizontal-scroll

Branch: `bugfix/052-mobile-no-horizontal-scroll`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a causa inteira está no cabeçalho comum, um componente.
- **O primeiro commit da branch marca a 065 como `done`** (mergeada em `develop` no PR #55).
- **Navegação em segunda linha no celular, na mesma linha a partir de `sm`**: duas linhas no celular (nome e usuário em cima, os quatro links embaixo) em vez de três, sem menu escondido atrás de um botão — são só quatro links e todos cabem numa linha de 343 px.
- **Ordem do DOM mantida**: nome, navegação, usuário. Só a posição visual da navegação muda no celular, com `order`, para o leitor de tela e o desktop seguirem iguais.
- **Prova no navegador, não no jsdom**: largura e rolagem só existem com layout real, por isso a regressão é um e2e do Playwright em 375 × 812 que mede todas as telas.

## Fase 1 — Cabeçalho que cabe no celular

Ao final: toda tela da SPA cabe em 375 px sem rolagem horizontal, com os quatro links do cabeçalho visíveis.

- [x] T1.1 — Cabeçalho em duas linhas no celular
  - Arquivos: `src/components/layouts/app-header.tsx` (alterar)
  - O que fazer: nome, navegação e usuário como filhos diretos da linha; navegação `order-last w-full flex-wrap` no celular e `sm:order-none sm:mr-auto sm:w-auto` a partir de 640 px; login com `truncate` num bloco `min-w-0`.
  - Skills: interface-design
  - Complexidade: baixa
- [x] T1.2 — Receitas do design
  - Arquivos: `docs/design.md` (alterar)
  - O que fazer: "Cabeçalho de app" e "Navegação do cabeçalho" descrevem a forma nova.
  - Skills: interface-design
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `e2e/mobile-layout.spec.ts`
  - O que fazer: o teste de regressão passa.
  - Skills: e2e-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `pnpm test:e2e` sai com código 0, e no commit `f4a5084` o e2e `every screen fits a 375 px phone without horizontal scroll` falhava. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh`, `uv run pytest`, `pnpm lint`, `pnpm typecheck`, `pnpm test` e `pnpm build` saem com código 0. (comando)
- [x] CA1.3 — Em 375 × 812, nas telas de entrar, saldos, gastos, categorias, conexões e página não encontrada, `document.documentElement.scrollWidth` não passa de 375 e nenhum elemento visível passa da borda direita; os links "Saldos", "Gastos", "Categorias" e "Conexões" aparecem inteiros. (comportamental)
- [x] CA1.4 — Em 640 px ou mais, nome do painel, navegação e usuário ficam numa só linha, com o usuário à direita. (comportamental)

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
