# Investigação: depois de "Atualizar agora" só os saldos mudam

## Relato
- **Sintoma:** depois de "Atualizar agora" na tela de saldos, só os saldos são buscados de novo. A lista de gastos, o resultado do período, o seletor de contas, o uso por categoria e a lista de conexões continuam mostrando o dado de antes da atualização até a página ser recarregada.
- **Esperado:** terminada a atualização, toda tela que mostra dado bancário traz o dado novo na próxima vez que aparece (ou na hora, se estiver aberta), sem recarregar a página.
- **Como reproduzir:** abrir "Gastos", voltar para "Saldos", clicar em "Atualizar agora" e, ao terminar, abrir "Gastos" de novo em menos de 30 segundos: a lista é a do cache anterior e nenhuma requisição sai.
- **Onde:** `src/features/sync/api/run-sync.ts`, o hook `useRunSync`.

## Causa raiz
No sucesso da atualização, `useRunSync` grava a situação devolvida pelo servidor e invalida uma única chave de cache, `['accounts', 'balances']`. A atualização, porém, reescreve lançamentos, contas e conexões, que alimentam as consultas de `['expenses', …]`, `['transactions', …]`, `['categories']` e `['pluggy-connections']`. Nenhuma delas é invalidada; com o `staleTime` de 30 segundos do cliente (`src/lib/react-query.ts`), a tela reaberta nesse intervalo usa o cache antigo sem ir ao servidor, e depois dele mostra o dado velho primeiro. A lista enumerada de chaves é a origem do defeito: cada tela nova de dado bancário precisaria ser lembrada ali, e nenhuma foi.

## Evidência
- Teste de regressão (commit `caf4697`), falha antes da correção: `src/features/sync/api/__tests__/run-sync.test.tsx`, `marks every view built from bank data as stale after a sync` — a consulta `["expenses",{"page":1}]` continua válida depois da atualização.
- O mesmo arquivo prova o que não pode mudar: `keeps the signed-in user and stores the returned sync status` passa antes e depois.

## Correção proposta
- `src/features/sync/api/run-sync.ts` — no sucesso, invalidar todas as consultas do cache, menos o usuário atual (`['auth', …]`, que a atualização não muda) e a situação da atualização (`['sync', …]`, que acabou de ser gravada com a resposta do servidor). Em vez de enumerar o que muda, excluir o pouco que não muda: tela nova de dado bancário fica certa sem ninguém lembrar deste arquivo. As consultas visíveis são buscadas na hora; as outras ficam marcadas como velhas e são buscadas quando a tela abrir.
- `src/features/sync/components/__tests__/sync-panel.test.tsx` — o teste que esperava a invalidação só dos saldos passa a conferir que os saldos na tela são buscados de novo.
- **Risco:** o teto do mês (`['plan', 'ceiling']`) também é buscado de novo sem ter mudado; é uma requisição a mais, só se a tela estiver aberta.

## Fora da correção
- A atualização feita pela rotina diária enquanto o app está aberto não avisa a SPA; as telas só trazem o dado novo quando o cache vence. Não é regressão e não há relato de uso.

## Pontos em aberto
Nenhum.
