# SPEC 056 — spa-legacy-navigation

## Decisões

- As telas antigas ficam fora do roteador da SPA: `legacyScreens` em `src/config/paths.ts` são `<a href>` comuns, com carga de página inteira.
- "Mais telas" é um `<details>` dentro da `nav` "Principal": sem estado novo, com teclado e leitor de tela nativos. Aberto, ocupa a linha inteira (`open:basis-full`) e a lista quebra linha, então não passa da borda em 375 px.
- No painel antigo, `SPA_SCREENS` em `app/routers/navigation.py` vira o global Jinja `spa_screens`; o fragmento `navegacao.html` desenha uma segunda lista com o rótulo "Painel novo" e a classe `rail-spa-link` (fora do padrão `rail-link`, que o teste do menu usa para as telas antigas). No celular o rótulo continua visível, para separar os dois "Gastos".

## Arquivos

- `src/config/paths.ts`, `src/components/layouts/app-header.tsx` e seu teste.
- `app/routers/navigation.py`, `app/main.py`, `app/templates/fragments/navegacao.html`, `app/static/css/app.css`, `tests/test_navegacao.py`.
- `e2e/mobile-layout.spec.ts`.
