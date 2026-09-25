# Investigação: filtro de gastos perde a edição anterior quando duas mudanças chegam em sequência rápida

## Relato
- **Sintoma:** o teste ponta a ponta "filters the expenses by month and by date range and keeps the period on reload" (`e2e/expenses.spec.ts`) falhou uma vez em 25/09/2026: depois do `page.reload()` a lista trouxe 2 gastos em vez de 1. Rodado de novo, passou.
- **Esperado:** com "De" e "Até" preenchidos com 02/09/2026, a URL fica `?from=2026-09-02&to=2026-09-02` e a lista, antes e depois de recarregar, mostra só MERCADO DO BAIRRO.
- **Como reproduzir:** em `http://127.0.0.1:5173/app/expenses?month=2026-09`, mudar "De" para 02/09/2026 e, antes de a tela redesenhar, mudar "Até" para 02/09/2026. A URL termina em `?from=2026-09-01&to=2026-09-02` e a lista mostra POSTO CENTRAL (01/09) e MERCADO DO BAIRRO (02/09).
- **Onde:** tela de gastos (`/app/expenses`), em qualquer navegador; aparece quando a segunda edição chega no intervalo entre a URL mudar e a tela ser redesenhada. Na suíte e2e, o Playwright preenche o segundo campo logo depois de ver a URL nova, o que cai nesse intervalo de vez em quando.

## Causa raiz
`src/features/expenses/components/expenses-list.tsx:205-230` (`commitPeriod` e `handleRangeChange`) monta a URL nova a partir de `searchParams` e `period` **do último desenho da tela**. O roteador de dados do React Router 7 (`createBrowserRouter`, em `src/app/router.tsx`) grava a URL no histórico e só depois entrega o estado novo ao React dentro de `startTransition`, que o React desenha quando puder. Nesse intervalo a URL já diz `from=2026-09-02&to=2026-09-30`, mas a tela ainda está no mês de setembro inteiro. Se "Até" muda aí, `handleRangeChange('to', …)` lê `period = { kind: 'month', month: '2026-09' }`, completa o "De" com `2026-09-01` e grava `from=2026-09-01&to=2026-09-02`, apagando a edição do "De". Antes do reload o teste ainda vê 1 item porque a consulta anterior (`from=02` até `30`, só MERCADO) segue na tela por `placeholderData: keepPreviousData` enquanto a nova não chega; os textos esperados batem com ela e a expressão `/to=2026-09-02/` casa com a URL errada. O reload busca a URL gravada, `01` a `02`, e mostra os 2 gastos. Os outros filtros da tela (`handleSortChange`, `handleOrderToggle`, `handleAccountChange`, `handleViewChange`, `handleSearchCommit`) partem do mesmo `searchParams` e perdem a edição anterior do mesmo jeito.

## Evidência
- Teste de regressão: `src/features/expenses/components/__tests__/expenses-list-fast-edits.test.tsx` › `an end date typed before the start date renders keeps the start date` e `a sort chosen before the account filter renders keeps the account`. O escopo de `act` segura o desenho da transição até terminar, abrindo o mesmo intervalo do navegador entre a URL nova e a tela nova.
- Falha hoje com:
  - `expected '?from=2026-07-01&to=2026-07-20' to be '?from=2026-07-10&to=2026-07-20'`
  - `expected null to be 'acc-bank-1'`
- O primeiro erro reproduz a assinatura do e2e: o "De" volta ao primeiro dia do mês que estava na tela.
- `pnpm exec playwright test e2e/expenses.spec.ts -g "by month and by date range" --repeat-each=30` passou 30 de 30 isolado: o intervalo é curto e depende da carga da máquina, por isso a prova é o teste de componente, não a repetição do e2e.
- Com a correção: `pnpm exec playwright test e2e/expenses.spec.ts --repeat-each=20` deu 220 de 220, e o teste do período passou em todas as 440 execuções de duas rodadas.

## Correção proposta
- `src/app/router.tsx` — o `RouterProvider` recebe `flushSync` de `react-dom` (embrulhado numa função que devolve `undefined`, o tipo que a prop exige), o que permite a uma navegação pedir desenho síncrono.
- `src/features/expenses/components/expenses-list.tsx` — toda mudança de filtro feita pelo usuário — filtros e troca de página — passa por uma função só, `commitParams`, que chama `setSearchParams` com `flushSync: true` (a troca de página segue empilhando no histórico; as demais substituem). Com isso a URL e a tela mudam na mesma tarefa: a próxima edição já encontra `searchParams` e `period` atualizados.
- `src/features/expenses/components/__tests__/expenses-list-fast-edits.test.tsx` — os dois testes de regressão, montados com `createMemoryRouter` e `RouterProvider` com `flushSync`, como o app.
- **Risco:** o redesenho da lista depois de cada filtro fica síncrono em vez de transição. A lista tem no máximo 20 itens por página e a consulta nova segue assíncrona (`keepPreviousData`), então o custo é um desenho curto. Os dois `useEffect` que corrigem a URL sozinhos (página além da última, conta desconhecida) continuam sem `flushSync`: rodam depois de um desenho e não disputam com edição do usuário.
- **Fora da correção:** nenhuma outra tela usa `setSearchParams`. Rodar a suíte e2e inteira com `--repeat-each` para caçar a instabilidade mostrou que `e2e/sync.spec.ts` não aguenta segunda volta na mesma base (espera "Nunca atualizado"); vira o item 037 do roadmap. Na soma de 440 execuções de `e2e/expenses.spec.ts` (duas rodadas de `--repeat-each=20`, já com a correção), o teste do teto do mês falhou uma vez depois do reload, sem relação com a URL; vira o item 038.

## Pontos em aberto
Nenhum.
