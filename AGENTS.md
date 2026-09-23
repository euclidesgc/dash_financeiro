<!-- bulletproof:start v0.8.0 -->
<!-- Bloco gerenciado por /br:init. Não edite à mão: rode /br:init para atualizar. -->

## Regras do projeto (harness br)

**Premissa.** Entregar valor em **fatias verticais** pequenas e frequentes: cada entrega atravessa API, estado, tela e testes e termina utilizável. Nunca uma camada isolada. Item grande é fatiado no roadmap antes de qualquer PRD.

**Fluxo.** Todo desenvolvimento começa por `/br:dev` e não pula etapa: escopo → roadmap → PRD → SPEC → PLAN → fases → revisão → PR. Bug: relato → investigação (causa raiz provada por um teste que falha) → PLAN → correção → PR; nenhuma correção antes da causa provada. Só a conversa principal fala com o usuário; trabalho pesado vai para subagentes.

**Stack.** SPA com Vite, React 19, TypeScript strict, Tailwind, TanStack Query, Zustand, React Hook Form + Zod, Vitest, Testing Library, MSW, Playwright. Scripts: `dev`, `lint`, `typecheck`, `test`, `test:e2e`, `build`.

**Arquitetura.** (detalhes na skill `project-structure`)
- `src/`: compartilhado (`components`, `hooks`, `lib`, `types`, `utils`, `config`) → `features/` → `app/`. Imports só nesse sentido.
- Feature não importa de outra feature nem de `app/`; elas se encontram nas rotas. O que duas features (ou o `app`, como infraestrutura) usam vai para o compartilhado.
- Imports absolutos com `@/`. Sem barrel files. Arquivos e pastas em kebab-case.

**Git.**
- `main` e `develop` são fixas, sem commit direto. `feature/*` e `bugfix/*` saem de `develop` e voltam por PR; `hotfix/*` sai de `main` e volta para `main` e `develop`; `release/*` vai de `develop` para `main` e `develop`, com tag.
- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`).
- Trabalho termina com PR aberto, o projeto **na branch da entrega** (para o dev conferir o app) e nenhuma branch temporária sobrando. Depois do merge: volta para `develop`, atualiza e apaga a branch.

**Idioma.**
- **Aplicação: pt_BR** — tudo o que uma pessoa lê: o que o app mostra (textos de tela, mensagens), a conversa, `docs/` e PRs.
- **Codificação: en_US** — nomes de variáveis, funções, componentes, arquivos e pastas, **caminhos de URL e de API** (`/tasks`, não `/tarefas`), comentários, nomes de teste e commits.
- Texto de tela dentro do código é da aplicação: `TasksList` mostra "Carregando tarefas…", nunca "Loading tasks…".

**Interface.** Tudo o que o usuário vê segue `docs/design.md` e o piso de acabamento da skill `interface-design`. Tela funcionando sem acabamento não está pronta.

**Regras invioláveis.**
- Nenhum segredo em variável `VITE_*` (vai para o navegador).
- Nenhum `dangerouslySetInnerHTML` sem sanitização.
- Nenhum token em `localStorage`; sessão em cookie httpOnly.
- Nenhum `any` sem comentário justificando.
- Nunca desativar regra de lint nem pular teste para fazer passar. Exceção só com `// eslint-disable-next-line <regra> -- <motivo>`, citada no PR.
- Entrega termina sem erro nem aviso no painel de problemas do editor, no lint do projeto inteiro, nos tipos de todos os `tsconfig` e no console dos testes.
- `React.JSX.Element`, nunca o `JSX` global. Em componente novo, `ref` é prop comum (sem `forwardRef`).

<!-- bulletproof:end -->
