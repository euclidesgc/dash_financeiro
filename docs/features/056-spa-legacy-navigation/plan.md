# PLAN 056 — spa-legacy-navigation

Branch: `feature/056-unified-navigation`

## Fase 1 — Uma navegação entre os dois painéis

- [x] T1.1 — "Mais telas" no cabeçalho da SPA com as seis telas antigas.
- [x] T1.2 — Grupo "Painel novo" no menu do painel antigo com as quatro telas da SPA.
- [x] T1.3 — Testes: componente do cabeçalho, `tests/test_navegacao.py` e `e2e/mobile-layout.spec.ts`.

### Critérios de aceite

- [x] CA1.1 — Com "Mais telas" aberto, a `nav` "Principal" tem os links Resumo `/`, Objetivo `/objetivo`, Dívidas `/dividas`, Simulador `/simulador`, Consultor `/consultor` e Configuração `/configuracao`. (comportamental)
- [x] CA1.2 — Toda tela do menu antigo tem, na ordem, os links `/app/` Saldos, `/app/expenses` Gastos, `/app/categories` Categorias e `/app/connections` Conexões; o login não tem. (estrutural)
- [x] CA1.3 — Em 375 px, `e2e/mobile-layout.spec.ts` passa com "Mais telas" aberto, todos os links inteiros na tela e sem rolagem horizontal. (comando)
- [x] CA1.4 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, `pnpm test:e2e`, `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
