# PLAN 072 — advisor-recategorize-with-confirmation

Branch: `feature/072-advisor-recategorize-with-confirmation`

## Fase 1 — Proposta, aplicar, descartar e desfazer no servidor

- [ ] T1.1 — Migração das propostas
  - Arquivos: `app/migrations/sql/027_advisor_proposals.sql` (criar), `app/migrations/NUMBERING.md` (alterar)
  - Complexidade: baixa

- [ ] T1.2 — Troca em lote pelo caminho manual
  - Arquivos: `app/taxonomy/override.py` (alterar)
  - O que fazer: `recategorize(conn, changes)` sem commit, com as instruções de `set_manual` e `restore_auto`.
  - Complexidade: média

- [ ] T1.3 — Serviço e consultas das propostas
  - Arquivos: `app/queries/advisor_proposals.py`, `app/advisor/proposals.py` (criar)
  - Complexidade: alta

- [ ] T1.4 — Ferramenta, prompt e entradas com proposta
  - Arquivos: `app/advisor/tools.py`, `app/advisor/chat.py`, `app/routers/advisor_chat.py`, `tests/e2e_app.py` (alterar)
  - Complexidade: média

- [ ] T1.5 — Testes da fase 1
  - Arquivos: `tests/test_advisor_proposals.py` (criar); `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`, `tests/test_migrations.py` (alterar)
  - Complexidade: média

### Critérios de aceite da fase 1

- [ ] CA1.1 — (comportamental) `propose_recategorization` por filtro resolve os mesmos ids de `list_expenses` com o filtro, pula os que já estão no destino e não muda nenhuma categoria; categoria inexistente, id desconhecido, filtro vazio e mais de 200 lançamentos viram erro da ferramenta.
- [ ] CA1.2 — (comportamental) Aplicar muda todos os itens para o destino com origem `manual` e reclassifica; aplicar de novo devolve a mesma proposta sem gravar; categoria de destino apagada ou lançamento apagado não grava nada.
- [ ] CA1.3 — (comportamental) Desfazer devolve categoria e origem anteriores; item mudado depois da aplicação fica como está e conta em `undo_skipped`; desfazer duas vezes é idempotente; aplicar descartada é 409.
- [ ] CA1.4 — (comportamental) Pela API, com o provedor dublê: a pergunta cria a proposta na conversa, a entrada do assistente traz `proposals` com itens e status; reabrir a conversa mostra o status atual; as rotas de proposta exigem sessão.
- [ ] CA1.5 — (comando) `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh` e `uv run pytest` passam.

## Fase 2 — Cartão da proposta no chat

- [ ] T2.1 — Tipos, chamadas e cache
  - Arquivos: `src/features/advisor/types/advisor.ts`, `src/features/advisor/api/*-proposal.ts`, `src/features/advisor/api/proposal-cache.ts`
  - Complexidade: média

- [ ] T2.2 — Cartão
  - Arquivos: `src/features/advisor/components/proposal-card.tsx` (criar), `chat-message-item.tsx`, `advisor-chat.tsx` (alterar), `docs/design.md`
  - Complexidade: média

- [ ] T2.3 — Testes de componente e e2e
  - Arquivos: `src/features/advisor/components/__tests__/proposal-card.test.tsx` (criar), `src/testing/mocks/handlers.ts`, `e2e/advisor.spec.ts` (alterar)
  - Complexidade: média

### Critérios de aceite da fase 2

- [ ] CA2.1 — (comportamental) O cartão lista data, descrição, valor e "atual → nova" de cada item, o total, e Aplicar/Descartar enquanto pendente; aplicada mostra Desfazer; desfeita diz quantos ficaram como estavam; botões desabilitados durante a ação; erro vira alerta.
- [ ] CA2.2 — (comportamental) Aplicar e desfazer invalidam `['expenses']` e as categorias.
- [ ] CA2.3 — (comportamental) E2E: perguntar, pedir a troca, ver o cartão, aplicar, ver a categoria nova na tela de gastos, voltar e desfazer.
- [ ] CA2.4 — (comando) `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` passam.

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
