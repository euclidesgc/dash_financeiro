# PLAN 073 — advisor-installments-projection

Branch: `feature/073-advisor-installments-projection`

## Fase 1 — Projeção mês a mês e ferramenta do consultor

- [x] T1.1 — Função de projeção
  - Arquivos: `app/projection/schedule.py` (criar)
  - Complexidade: média

- [x] T1.2 — Ferramenta, contexto com data de referência e prompt
  - Arquivos: `app/advisor/tools.py`, `app/advisor/chat.py` (alterar)
  - Complexidade: baixa

- [x] T1.3 — Rótulo da ferramenta na nota da resposta
  - Arquivos: `src/features/advisor/components/chat-message-item.tsx` (alterar)
  - Complexidade: baixa

- [x] T1.4 — Testes
  - Arquivos: `tests/test_projection_schedule.py` (criar); `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`, `tests/test_advisor_providers.py`, `tests/test_advisor_proposals.py`, `src/features/advisor/components/__tests__/chat-message-item.test.tsx` (alterar)
  - Complexidade: média

### Critérios de aceite da fase 1

- [x] CA1.1 — (comportamental) Sem dados, a projeção devolve os meses pedidos zerados; parcela que termina no meio da janela conta até o mês da última parcela e aparece em "termina" nesse mês; fatura com parcelas futuras já lançadas é numerada para trás; parcela sem número e contrato sem valor de parcela vão para `unprojected`.
- [x] CA1.2 — (comportamental) Financiamento conta pelo contrato (k/n e mês final) e o boleto recorrente de mesmo valor (até 2%) não conta de novo; recorrente parada ou dispensada não conta; janela fora de 1 a 24 é recusada.
- [x] CA1.3 — (comportamental) `commitments_by_month` devolve cada valor em centavos e em reais, padrão de 6 meses, erro para `months` inválido; pela API com o provedor dublê, a resposta que copia os valores passa pela guarda e a que inventa um total é trocada pelo aviso; os dois adaptadores recebem a ferramenta.
- [x] CA1.4 — (comando) `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh`, `uv run pytest`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` passam.

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
