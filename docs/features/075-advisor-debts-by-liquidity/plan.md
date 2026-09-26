# PLAN 075 — advisor-debts-by-liquidity

Branch: `feature/075-advisor-debts-by-liquidity`

## Fase 1 — Ranking por liquidez, escolha com valor disponível e ferramenta do consultor

- [ ] T1.1 — Ranking e seleção
  - Arquivos: `app/debts/payoff.py` (alterar)
  - Complexidade: média

- [ ] T1.2 — Ferramenta e prompt
  - Arquivos: `app/advisor/tools.py`, `app/advisor/chat.py` (alterar)
  - Complexidade: média

- [ ] T1.3 — Rótulo da ferramenta na nota da resposta
  - Arquivos: `src/features/advisor/components/chat-message-item.tsx` (alterar)
  - Complexidade: baixa

- [ ] T1.4 — Testes
  - Arquivos: `tests/test_debts_payoff.py`, `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`, `tests/test_advisor_providers.py`, `src/features/advisor/components/__tests__/chat-message-item.test.tsx` (alterar)
  - Complexidade: média

### Critérios de aceite da fase 1

- [ ] CA1.1 — (comportamental) O ranking ordena por parcela ÷ valor para quitar hoje, do maior para o menor; empate vai para o menor valor e depois para a chave; saldo de quitação ausente usa a soma das parcelas que faltam e marca a estimativa pelo teto; compra parcelada entra pelo valor nominal; dívida sem parcela fica fora do ranking, listada à parte com o valor.
- [ ] CA1.2 — (comportamental) Com valor disponível, a escolha desce o ranking pulando o que não cabe; valor menor que qualquer dívida não escolhe nada e sobra inteiro; valor exato não deixa sobra; escolha pelo teto é sinalizada; valor zero ou negativo é recusado.
- [ ] CA1.3 — (comportamental) `debts_by_liquidity` devolve a lista com valores em centavos e em reais, a razão em porcentagem, a marca "estimativa pelo teto — informe o saldo de quitação", a lista à parte e a escolha com o valor disponível, e recusa entrada inválida; pela API com o provedor dublê, a resposta que copia os valores passa pela guarda e a que inventa um valor é trocada pelo aviso; os dois adaptadores recebem a ferramenta.
- [ ] CA1.4 — (comando) `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh`, `uv run pytest`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` passam.

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
