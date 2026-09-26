# PLAN 070 — advisor-chat-transactions

Branch: `feature/070-advisor-chat-transactions`

## Fase 1 — API do chat com laço de ferramentas, busca de lançamentos e conversa guardada

- [ ] T1.1 — Filtro por categoria e formatação de reais fora do router
  - Arquivos: `app/queries/expenses.py` (alterar); `app/formatting.py` (criar); `app/routers/render.py` (alterar)
  - O que fazer: `_where`, `list_expenses` e `sum_expenses` aceitam `category: str | None` (chave exata em `t.category`). `brl` e `MINUS` passam a morar em `app/formatting.py`; `render.py` os importa.
  - Complexidade: baixa

- [ ] T1.2 — Porta de provedor, adaptadores Anthropic e Gemini e seleção
  - Arquivos: `app/advisor/provider.py`, `app/advisor/anthropic_provider.py`, `app/advisor/gemini_provider.py`, `app/advisor/providers.py` (criar); `app/config.py`, `pyproject.toml`, `uv.lock`, `.env.example` (alterar)
  - O que fazer: formato neutro, protocolo `ChatProvider`, `ProviderError` em pt-BR; adaptador Anthropic sobre o SDK `anthropic` (cliente injetável); adaptador Gemini sobre `httpx.Client` injetável; `select_provider` na ordem Anthropic → Gemini → nenhum.
  - Complexidade: alta

- [ ] T1.3 — Ferramenta, laço, persistência e rotas
  - Arquivos: `app/advisor/tools.py`, `app/advisor/chat.py`, `app/queries/advisor_chat.py`, `app/routers/advisor_chat.py`, `app/migrations/sql/026_advisor_chat.sql` (criar); `app/main.py`, `app/migrations/NUMBERING.md` (alterar)
  - O que fazer: `search_transactions`; laço com teto de 8 voltas e guarda de números; migração 026; rotas `/api/advisor/*` com `require_provider` (503).
  - Complexidade: alta

- [ ] T1.4 — Testes da fase 1
  - Arquivos: `tests/test_advisor_chat.py`, `tests/test_advisor_providers.py`, `tests/test_advisor_tools.py`, `tests/test_expenses_api.py`, `tests/test_migrations.py`
  - Complexidade: média

### Critérios de aceite da fase 1

- [ ] CA1.1 — (estrutural) `app/migrations/sql/026_advisor_chat.sql` cria `advisor_conversations` e `advisor_messages` com `role IN ('user','assistant','tool')`.
- [ ] CA1.2 — (estrutural) `app/routers/advisor_chat.py` não contém SQL nem `commit` (G7) e as rotas são `def`.
- [ ] CA1.3 — (comportamental) Com um provedor falso que pede `search_transactions` e depois responde, `POST /api/advisor/conversations/{id}/messages` devolve a resposta e grava pergunta, pedido, resultado e resposta; provado em `tests/test_advisor_chat.py`.
- [ ] CA1.4 — (comportamental) Sem chave, `GET /api/advisor/status` devolve `available: false` e o envio devolve 503 com o texto de configuração; sem sessão, toda rota `/api/advisor/*` devolve 401.
- [ ] CA1.5 — (comportamental) Resposta com valor em reais que nenhuma ferramenta devolveu é trocada pelo aviso; o laço para em 8 voltas.
- [ ] CA1.6 — (comportamental) Os adaptadores traduzem pedido de ferramenta e resultado nos dois sentidos, reenviam os blocos crus ao mesmo provedor e traduzem erro de chave, excesso e rede em pt-BR, sem rede nos testes.
- [ ] CA1.7 — (comando) `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh` e `uv run pytest` passam.

## Fase 2 — Tela do consultor na SPA

- [ ] T2.1 — Tipos, chamadas e mock
  - Arquivos: `src/features/advisor/types/advisor.ts`, `src/features/advisor/api/*.ts` (criar); `src/testing/mocks/handlers.ts` (alterar)
  - Complexidade: baixa

- [ ] T2.2 — Tela e navegação
  - Arquivos: `src/features/advisor/components/*.tsx`, `src/app/routes/advisor.tsx` (criar); `src/app/router.tsx`, `src/config/paths.ts`, `src/components/layouts/app-header.tsx`, `docs/design.md` (alterar)
  - Complexidade: média

- [ ] T2.3 — Testes e e2e
  - Arquivos: `src/features/advisor/**/__tests__/*`, `e2e/advisor.spec.ts`, `tests/e2e_app.py` (criar); `scripts/e2e-backend.sh`, `src/components/layouts/__tests__/app-header.test.tsx` (alterar)
  - Complexidade: média

### Critérios de aceite da fase 2

- [ ] CA2.1 — (comportamental) O cabeçalho mostra "Consultor" e leva a `/app/advisor`.
- [ ] CA2.2 — (comportamental) Enviar pergunta mostra "Consultando suas contas…", depois a resposta; a conversa reaparece ao recarregar; "Nova conversa" limpa a tela.
- [ ] CA2.3 — (comportamental) Sem provedor, a tela mostra como configurar e não mostra o campo de pergunta.
- [ ] CA2.4 — (comportamental) Erro do provedor aparece em alerta com o texto do servidor e o campo mantém a pergunta.
- [ ] CA2.5 — (comando) `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` passam.

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
