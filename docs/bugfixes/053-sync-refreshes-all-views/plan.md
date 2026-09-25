# PLAN 053 — sync-refreshes-all-views

Branch: `bugfix/053-sync-refreshes-all-views`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a causa inteira está no hook da atualização, um arquivo.
- **O primeiro commit da branch marca a 052 como `done`** (mergeada em `develop` no PR #56).
- **Invalidar tudo menos usuário e situação da atualização**: a atualização troca a base bancária inteira, então o que não muda é a exceção. Enumerar as chaves foi o que deixou as telas velhas.
- **Prova no hook, não na tela**: o teste semeia o cache com uma consulta de cada tela de dado bancário e confere que todas ficam marcadas como velhas, sem depender de qual tela está montada.

## Fase 1 — Atualização que renova todas as telas

Ao final: depois de "Atualizar agora", gastos, contas, categorias e conexões trazem o dado novo sem recarregar a página.

- [ ] T1.1 — Invalidar o cache inteiro no sucesso
  - Arquivos: `src/features/sync/api/run-sync.ts` (alterar)
  - O que fazer: no `onSuccess`, depois de gravar a situação, invalidar todas as consultas cujo primeiro segmento da chave não seja `auth` nem `sync`.
  - Skills: api-requests, client-state
  - Complexidade: baixa
- [ ] T1.2 — Testes
  - Arquivos: `src/features/sync/api/__tests__/run-sync.test.tsx`, `src/features/sync/components/__tests__/sync-panel.test.tsx`
  - O que fazer: o teste de regressão passa; o teste do painel deixa de exigir a chave única dos saldos e confere que os saldos são buscados de novo.
  - Skills: component-testing
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `pnpm test` sai com código 0, e no commit `caf4697` o teste `marks every view built from bank data as stale after a sync` falhava. (comando)
- [ ] CA1.2 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh`, `uv run pytest`, `pnpm lint`, `pnpm typecheck`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [ ] CA1.3 — Depois de uma atualização bem-sucedida, as consultas de saldos, gastos, contas do filtro, totais por categoria, resultado do período, sinal do mês, lançamentos parecidos, categorias e conexões ficam marcadas como velhas; a do usuário atual não, e a situação da atualização guarda a resposta do servidor. (comportamental)
- [ ] CA1.4 — Com a atualização falhando (409, 503 ou 500), só a situação da atualização é buscada de novo, como antes. (comportamental)

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
