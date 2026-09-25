# Investigação: a SPA sem página de "não encontrada" nem de erro

## Relato
- **Sintoma:** três telas quebradas no mesmo ponto do roteador.
  1. Abrir `http://localhost:8000/app` (sem a barra final) mostra uma página em branco.
  2. Abrir um endereço que não existe, como `/app/nao-existe`, mostra a tela padrão do React Router em inglês ("Unexpected Application Error! 404 Not Found", "Hey developer 👋").
  3. Se a pergunta "quem está logado" (`GET /api/auth/me`) falha por um motivo que não é sessão (servidor reiniciando, erro 500, rede), o app cai nessa mesma tela em inglês, sem nova tentativa e sem botão para tentar de novo.
- **Esperado:** `/app` abre o app como `/app/`; endereço desconhecido mostra "Página não encontrada" em português com um link de volta; falha passageira da consulta do usuário é tentada de novo e, se persistir, a tela diz em português que não conseguiu confirmar a sessão e oferece "Tentar de novo".
- **Como reproduzir:** `pnpm build`, subir a API e abrir os três casos acima no navegador.
- **Onde:** `src/app/router.tsx`, `src/lib/auth.tsx`.

## Causa raiz
- **Página em branco em `/app`.** O roteador é criado com `basename: '/app/'`, com a barra final. O React Router só aceita um endereço que comece pelo `basename` inteiro; `/app` não começa por `/app/`, e o roteador não desenha nada (ele avisa no console: "is not able to match the URL \"/app\" because it does not start with the basename"). A API entrega o `index.html` em `/app` e em `/app/...` (`app/spa.py`), então o problema é só do lado do cliente.
- **Tela em inglês em caminho desconhecido.** A lista de rotas não tem a rota `'*'` nem um `errorElement`. Sem rota que case, o React Router lança um 404 e, sem limite de erro no roteador, mostra o próprio aviso de desenvolvimento. O `ErrorBoundary` de `src/app/provider.tsx` fica por fora do roteador e nunca recebe esse erro.
- **Consulta do usuário que não tenta de novo.** `meQueryOptions` fixa `retry: false`, herança de quando o 401 era erro (antes da 047). Desde a 047 o 401 de `/api/auth/me` vira `null`, então o `retry: false` só desliga a nova tentativa dos erros de verdade. E `ProtectedRoute` lança esse erro para cima, onde cai no mesmo aviso em inglês do roteador.

## Evidência
- Teste de regressão (commit `f032b59`): `src/app/__tests__/not-found-and-errors.test.tsx`, os quatro casos falham:
  - `opening /app without the trailing slash shows the app` — a tela fica vazia;
  - `an unknown path shows the not found page in Portuguese with a way back` — aparece "Unexpected Application Error! 404 Not Found";
  - `a transient failure of the user query is retried instead of breaking the page` — um único 500 leva à tela de erro em vez de "Entrar";
  - `a user query that keeps failing shows a Portuguese error with a retry` — não há aviso em português nem botão.

## Correção proposta
- `src/app/router.tsx` — `basename: '/app'`, sem a barra final: o React Router aceita `/app`, `/app/` e `/app/...`. As rotas passam a ficar sob uma rota raiz sem caminho com `errorElement` (erro de código em qualquer tela vira "Algo deu errado" em português, com link de volta), e a última é `'*'`, com a página "Página não encontrada".
- `src/app/routes/not-found.tsx` (novo) — a página 404, com "Voltar para o início".
- `src/app/routes/route-error.tsx` (novo) — o limite de erro do roteador: "Página não encontrada" para 404 e "Algo deu errado" para o resto, sempre com link de volta.
- `src/lib/auth.tsx` — sai o `retry: false` de `meQueryOptions` (vale a regra geral de `src/lib/react-query.ts`: até 3 novas tentativas, nunca para 401). `ProtectedRoute` mostra o erro no lugar, com `role="alert"`, "Não foi possível confirmar a sua sessão." e o botão "Tentar de novo" que refaz a consulta, na receita de erro do `docs/design.md`.
- **Risco:** com o servidor fora do ar, "Carregando…" dura as três novas tentativas (cerca de 7 s) antes do aviso; é a mesma espera de qualquer outra leitura do app.

## Fora da correção
Nada.

## Pontos em aberto
Nenhum.
