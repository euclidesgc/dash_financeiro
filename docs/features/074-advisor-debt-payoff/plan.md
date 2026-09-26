# PLAN 074 — advisor-debt-payoff

Branch: `feature/074-advisor-debt-payoff`

## Fase 1 — Valor para quitar, plano de poupança e ferramenta do consultor

- [x] T1.1 — Funções de quitação
  - Arquivos: `app/debts/payoff.py` (criar)
  - Complexidade: média

- [x] T1.2 — Ferramenta e prompt
  - Arquivos: `app/advisor/tools.py`, `app/advisor/chat.py` (alterar)
  - Complexidade: média

- [x] T1.3 — Rótulo da ferramenta na nota da resposta
  - Arquivos: `src/features/advisor/components/chat-message-item.tsx` (alterar)
  - Complexidade: baixa

- [x] T1.4 — Testes
  - Arquivos: `tests/test_debts_payoff.py` (criar); `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`, `tests/test_advisor_providers.py`, `src/features/advisor/components/__tests__/chat-message-item.test.tsx` (alterar)
  - Complexidade: média

### Critérios de aceite da fase 1

- [x] CA1.1 — (comportamental) Saldo de quitação informado e válido é o valor de hoje; sem ele, ou vencido, ou para data em outro mês, o valor vem nulo, o alvo é a soma nominal das parcelas que faltam e a falta é sinalizada; saldo de cheque especial e cartão vale em qualquer data; compra parcelada quita pelo nominal restante.
- [x] CA1.2 — (comportamental) Data no passado é recusada; data no mês corrente pede o valor inteiro; data próxima divide o alvo arredondando para cima; data depois da última parcela não pede nada; valor mensal acha o primeiro mês que cobre o alvo; valor zero é recusado.
- [x] CA1.3 — (comportamental) `debt_payoff` lista as dívidas com chave e valores em centavos e em reais, planeja por data, por meses e por valor mensal, e recusa entrada inválida; pela API com o provedor dublê, a resposta que copia os valores passa pela guarda e a que inventa um desconto é trocada pelo aviso; os dois adaptadores recebem a ferramenta.
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
