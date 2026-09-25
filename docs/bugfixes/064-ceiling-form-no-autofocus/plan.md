# PLAN 064 — ceiling-form-no-autofocus

Branch: `bugfix/064-ceiling-form-no-autofocus`

Causa em `investigation.md`.

## Fase 1 — Formulário do teto só abre por ação da pessoa

Ao final: num mês sem teto, "Gastos" carrega com o convite e o botão "Definir teto", sem formulário aberto e sem mexer no foco.

Critérios de aceite:
- `comportamental` — sem teto, o bloco mostra "Definir teto do mês", não mostra "Teto mensal (R$)" e o foco continua no documento (`month-ceiling.test.tsx`).
- `comportamental` — "Definir teto" abre o formulário vazio com o campo focado; "Cancelar" fecha e devolve o botão (`month-ceiling.test.tsx`).
- `comportamental` — no navegador, trocar de mês para um mês sem teto não abre o formulário; a jornada do teto abre o formulário por "Definir teto" (`e2e/expenses.spec.ts`).
- `comando` — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` passam.
